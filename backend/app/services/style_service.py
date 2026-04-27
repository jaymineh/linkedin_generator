import asyncio
import json
import time

import structlog
from pydantic import BaseModel

from app import telemetry
from app.services.llm_provider import make_client, resolve_provider_and_model

logger = structlog.get_logger()

STYLE_ANALYZER_PROMPT = """
You are an expert writing-style analyst.

You will receive a set of LinkedIn posts written by one person.
Analyze them and create a compact style profile that can later be used to generate new posts in the same voice.

Return a profile with:
- voice_summary
- opening_patterns
- sentence_length_preference
- emoji_usage
- hashtag_style
- cta_style
- preferred_topics
- phrases_to_mimic
- phrases_to_avoid

Be specific, but keep the profile compact and reusable.
Return only structured JSON.
""".strip()


class StyleProfileOutput(BaseModel):
    voice_summary: str
    opening_patterns: list[str]
    sentence_length_preference: str
    emoji_usage: str
    hashtag_style: str
    cta_style: str
    preferred_topics: list[str]
    phrases_to_mimic: list[str]
    phrases_to_avoid: list[str]


def build_style_profile_user_message(posts: list[str]) -> str:
    return "\n\n---\n\n".join(posts)[:12000]


def _request_style_profile(
    user_message: str,
    llm_provider: str,
    llm_model: str,
) -> tuple[StyleProfileOutput, int, int]:
    client = make_client(llm_provider)
    response = client.chat.completions.create(
        model=llm_model,
        messages=[
            {"role": "system", "content": STYLE_ANALYZER_PROMPT},
            {"role": "user", "content": user_message},
        ],
        response_format={"type": "json_object"},
    )
    raw_content = response.choices[0].message.content or "{}"
    parsed = StyleProfileOutput.model_validate(json.loads(raw_content))
    usage = response.usage
    prompt_tokens = usage.prompt_tokens if usage and usage.prompt_tokens else 0
    completion_tokens = usage.completion_tokens if usage and usage.completion_tokens else 0
    return parsed, prompt_tokens, completion_tokens


async def build_style_profile(
    posts: list[str],
    llm_provider: str | None = None,
    llm_model: str | None = None,
) -> StyleProfileOutput:
    resolved_provider, resolved_model = resolve_provider_and_model(llm_provider, llm_model)
    logger.info("style_profile_generation_start", sample_count=len(posts))
    user_message = build_style_profile_user_message(posts)
    started = time.perf_counter()
    with telemetry.tracer.start_as_current_span("openai_build_style_profile"):
        try:
            profile, prompt_tokens, completion_tokens = await asyncio.to_thread(
                _request_style_profile,
                user_message,
                resolved_provider,
                resolved_model,
            )
        except Exception as exc:
            telemetry.record_openai_completed(
                operation="build_style_profile",
                audience="n/a",
                tone="n/a",
                style_mode="n/a",
                success=False,
                duration_ms=(time.perf_counter() - started) * 1000,
                error_type=type(exc).__name__,
            )
            raise

        telemetry.record_openai_completed(
            operation="build_style_profile",
            audience="n/a",
            tone="n/a",
            style_mode="n/a",
            success=True,
            duration_ms=(time.perf_counter() - started) * 1000,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
        )
    logger.info(
        "style_profile_generated",
        sample_count=len(posts),
        llm_provider=resolved_provider,
        llm_model=resolved_model,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
    )
    return profile
