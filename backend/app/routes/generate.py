import time

import structlog
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Generation, Post, StyleProfile
from app.schemas import GenerateRequest, GenerateResponse
from app.services import openai_service, scraper
from app import telemetry

router = APIRouter()
logger = structlog.get_logger()


@router.post("/generate", response_model=GenerateResponse)
async def generate(request: GenerateRequest, db: Session = Depends(get_db)):
    request_started = time.perf_counter()
    source_type = "url" if request.url else "manual"

    with telemetry.tracer.start_as_current_span("generate_post"):
        article_content = None
        scrape_succeeded = False
        if request.url:
            article_content = await scraper.scrape_url(request.url)
            scrape_succeeded = article_content is not None

        style_profile = None
        effective_style_mode = request.style_mode
        if request.style_mode != "off":
            stored_profile = db.query(StyleProfile).order_by(StyleProfile.created_at.desc()).first()
            if stored_profile:
                style_profile = {
                    "voice_summary": stored_profile.voice_summary,
                    "opening_patterns": stored_profile.opening_patterns,
                    "sentence_length_preference": stored_profile.sentence_length_preference,
                    "emoji_usage": stored_profile.emoji_usage,
                    "hashtag_style": stored_profile.hashtag_style,
                    "cta_style": stored_profile.cta_style,
                    "preferred_topics": stored_profile.preferred_topics,
                    "phrases_to_mimic": stored_profile.phrases_to_mimic,
                    "phrases_to_avoid": stored_profile.phrases_to_avoid,
                }
            else:
                logger.warning("style_profile_missing_falling_back_to_off")
                effective_style_mode = "off"

        style_profile_available = style_profile is not None
        telemetry.record_generation_started(
            audience=request.audience,
            tone=request.tone,
            style_mode=effective_style_mode,
            source_type=source_type,
            style_profile_available=style_profile_available,
        )

        try:
            posts = await openai_service.generate_posts(
                topic=request.topic,
                audience=request.audience,
                tone=request.tone,
                style_mode=effective_style_mode,
                style_profile=style_profile,
                article_content=article_content,
            )
        except Exception as exc:
            logger.error("generation_failed", error=str(exc))
            telemetry.record_generation_failed(
                audience=request.audience,
                tone=request.tone,
                style_mode=effective_style_mode,
                source_type=source_type,
                style_profile_available=style_profile_available,
                scrape_succeeded=scrape_succeeded,
                error_type=type(exc).__name__,
                duration_ms=(time.perf_counter() - request_started) * 1000,
            )
            raise HTTPException(status_code=500, detail="Post generation failed. Try again.") from exc

        generation = Generation(
            topic=request.topic,
            audience=request.audience,
            tone=request.tone,
            style_mode=effective_style_mode,
            url=request.url,
        )
        db.add(generation)
        db.flush()

        for post in posts:
            db.add(
                Post(
                    generation_id=generation.id,
                    style=post.style,
                    hook=post.hook,
                    body=post.body,
                    hashtags=post.hashtags,
                )
            )

        db.commit()
        db.refresh(generation)

        combined_word_count = sum(len(post.body.split()) for post in posts)
        combined_hashtag_count = sum(len(post.hashtags) for post in posts)
        telemetry.record_generation_completed(
            audience=request.audience,
            tone=request.tone,
            style_mode=effective_style_mode,
            source_type=source_type,
            style_profile_available=style_profile_available,
            scrape_succeeded=scrape_succeeded,
            post_count=len(posts),
            word_count=combined_word_count,
            hashtag_count=combined_hashtag_count,
            duration_ms=(time.perf_counter() - request_started) * 1000,
        )

        return GenerateResponse(generation_id=generation.id, posts=posts)
