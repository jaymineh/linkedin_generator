import asyncio

import structlog
from openai import APIConnectionError, APITimeoutError, OpenAI, RateLimitError
from pydantic import BaseModel
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.config import settings

logger = structlog.get_logger()
client = OpenAI(api_key=settings.OPENAI_API_KEY, timeout=30.0)

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


def _request_posts(user_message: str) -> PostsOutput:
    response = client.beta.chat.completions.parse(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        response_format=PostsOutput,
    )
    parsed = response.choices[0].message.parsed
    logger.info(
        "openai_call_complete",
        posts_generated=len(parsed.posts),
        prompt_tokens=response.usage.prompt_tokens,
        completion_tokens=response.usage.completion_tokens,
    )
    return parsed


@retry(
    retry=retry_if_exception_type((APITimeoutError, RateLimitError, APIConnectionError)),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    before_sleep=lambda retry_state: logger.warning(
        "openai_retry",
        attempt=retry_state.attempt_number,
        error=str(retry_state.outcome.exception()),
    ),
)
async def generate_posts(
    topic: str,
    audience: str,
    tone: str,
    style_mode: str = "off",
    style_profile: dict | None = None,
    article_content: str | None = None,
) -> list[PostVariantOutput]:
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
        topic=topic,
        audience=audience,
        tone=tone,
        style_mode=style_mode,
    )
    if style_mode != "off":
        logger.info("generate_with_style_mode", style_mode=style_mode)

    result = await asyncio.to_thread(_request_posts, user_message)
    selected_post = result.posts[0]
    selected_post.style = tone
    return [selected_post]
