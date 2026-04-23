import asyncio

import structlog
from openai import OpenAI
from pydantic import BaseModel

from app.config import settings

logger = structlog.get_logger()
client = OpenAI(api_key=settings.OPENAI_API_KEY, timeout=30.0)

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


def _request_style_profile(user_message: str) -> tuple[StyleProfileOutput, object]:
    response = client.beta.chat.completions.parse(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": STYLE_ANALYZER_PROMPT},
            {"role": "user", "content": user_message},
        ],
        response_format=StyleProfileOutput,
    )
    parsed = response.choices[0].message.parsed
    return parsed, response.usage


async def build_style_profile(posts: list[str]) -> StyleProfileOutput:
    logger.info("style_profile_generation_start", sample_count=len(posts))
    user_message = build_style_profile_user_message(posts)
    profile, usage = await asyncio.to_thread(_request_style_profile, user_message)
    logger.info(
        "style_profile_generated",
        sample_count=len(posts),
        prompt_tokens=usage.prompt_tokens,
        completion_tokens=usage.completion_tokens,
    )
    return profile
