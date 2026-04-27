import asyncio
import json
import time

import structlog
from openai import APIConnectionError, APITimeoutError, OpenAI, RateLimitError
from pydantic import BaseModel
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from app import telemetry
from app.services.llm_provider import make_client, resolve_provider_and_model

logger = structlog.get_logger()

SYSTEM_PROMPT = """
You are an expert LinkedIn content strategist. Generate exactly 1 LinkedIn post.

The post must:
- Match the user's selected audience and preferred tone
- Open with a strong hook
- Be 150-280 words
- Feel authentic, not corporate
- End with a clear thought, question, or call to action
- Include 3-5 relevant hashtags

Return structured JSON only.
The response must contain exactly one item in `posts`.
Set the `style` field to the user's preferred tone exactly.
""".strip()


class PostVariantOutput(BaseModel):
    style: str
    hook: str
    body: str
    hashtags: list[str]


class PostsOutput(BaseModel):
    posts: list[PostVariantOutput]


def build_style_block(style_mode: str, style_profile: dict | None) -> str:
    if style_mode == "off" or not style_profile:
        return ""

    mode_instruction = (
        "Stay as close as possible to this writing style."
        if style_mode == "faithful"
        else "Use this writing style as the baseline, but improve clarity, hook strength, and engagement."
    )

    return (
        "Writing style profile:\n"
        f"- mode: {style_mode}\n"
        f"- instruction: {mode_instruction}\n"
        f"- voice_summary: {style_profile.get('voice_summary')}\n"
        f"- opening_patterns: {', '.join(style_profile.get('opening_patterns', []))}\n"
        f"- sentence_length_preference: {style_profile.get('sentence_length_preference')}\n"
        f"- emoji_usage: {style_profile.get('emoji_usage')}\n"
        f"- hashtag_style: {style_profile.get('hashtag_style')}\n"
        f"- cta_style: {style_profile.get('cta_style')}\n"
        f"- preferred_topics: {', '.join(style_profile.get('preferred_topics', []))}\n"
        f"- phrases_to_mimic: {', '.join(style_profile.get('phrases_to_mimic', []))}\n"
        f"- phrases_to_avoid: {', '.join(style_profile.get('phrases_to_avoid', []))}"
    )


def build_generate_user_message(
    topic: str,
    audience: str,
    tone: str,
    style_mode: str = "off",
    style_profile: dict | None = None,
    article_content: str | None = None,
) -> str:
    message = (
        f"Topic: {topic}\n"
        f"Target audience: {audience}\n"
        f"Preferred tone: {tone}"
    )

    if article_content:
        message += f"\n\nReference article (summarize key points, do not copy):\n{article_content[:3000]}"

    style_block = build_style_block(style_mode, style_profile)
    if style_block:
        message += f"\n\n{style_block}"

    return message


def _request_posts(
    user_message: str,
    llm_provider: str,
    llm_model: str,
) -> tuple[PostsOutput, int, int]:
    client: OpenAI = make_client(llm_provider)
    response = client.chat.completions.create(
        model=llm_model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        response_format={"type": "json_object"},
    )
    raw_content = response.choices[0].message.content or "{}"
    parsed = PostsOutput.model_validate(json.loads(raw_content))
    usage = response.usage
    prompt_tokens = usage.prompt_tokens if usage and usage.prompt_tokens else 0
    completion_tokens = usage.completion_tokens if usage and usage.completion_tokens else 0
    logger.info(
        "openai_call_complete",
        llm_provider=llm_provider,
        llm_model=llm_model,
        posts_generated=len(parsed.posts),
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
    )
    return parsed, prompt_tokens, completion_tokens


@retry(
    retry=retry_if_exception_type((APITimeoutError, RateLimitError, APIConnectionError)),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    before_sleep=lambda retry_state: logger.warning(
        "openai_retry",
        attempt=retry_state.attempt_number,
        error=str(retry_state.outcome.exception()) if retry_state.outcome else "unknown",
    ),
)
async def generate_posts(
    topic: str,
    audience: str,
    tone: str,
    style_mode: str = "off",
    style_profile: dict | None = None,
    article_content: str | None = None,
    llm_provider: str | None = None,
    llm_model: str | None = None,
) -> list[PostVariantOutput]:
    resolved_provider, resolved_model = resolve_provider_and_model(llm_provider, llm_model)
    user_message = build_generate_user_message(
        topic=topic,
        audience=audience,
        tone=tone,
        style_mode=style_mode,
        style_profile=style_profile,
        article_content=article_content,
    )

    logger.info(
        "openai_call_start",
        llm_provider=resolved_provider,
        llm_model=resolved_model,
        topic=topic,
        audience=audience,
        tone=tone,
        style_mode=style_mode,
    )
    if style_mode != "off":
        logger.info("generate_with_style_mode", style_mode=style_mode)

    started = time.perf_counter()
    with telemetry.tracer.start_as_current_span("openai_generate_posts"):
        try:
            result, prompt_tokens, completion_tokens = await asyncio.to_thread(
                _request_posts,
                user_message,
                resolved_provider,
                resolved_model,
            )
        except Exception as exc:
            telemetry.record_openai_completed(
                operation="generate_post",
                audience=audience,
                tone=tone,
                style_mode=style_mode,
                llm_provider=resolved_provider,
                llm_model=resolved_model,
                success=False,
                duration_ms=(time.perf_counter() - started) * 1000,
                error_type=type(exc).__name__,
            )
            raise

        telemetry.record_openai_completed(
            operation="generate_post",
            audience=audience,
            tone=tone,
            style_mode=style_mode,
            llm_provider=resolved_provider,
            llm_model=resolved_model,
            success=True,
            duration_ms=(time.perf_counter() - started) * 1000,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
        )
    selected_post = result.posts[0]
    selected_post.style = tone
    return [selected_post]
