import structlog
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import StyleProfile, StyleSample
from app.schemas import StyleImportRequest, StyleProfileResponse
from app.services import style_service

router = APIRouter()
logger = structlog.get_logger()


@router.post("/style/import", response_model=StyleProfileResponse)
async def import_style(request: StyleImportRequest, db: Session = Depends(get_db)):
    cleaned_posts = [post.strip() for post in request.posts if post.strip()]
    if len(cleaned_posts) < 3:
        raise HTTPException(status_code=400, detail="Import at least 3 previous posts.")

    try:
        db.query(StyleSample).delete()
        db.query(StyleProfile).delete()

        for post in cleaned_posts:
            db.add(StyleSample(content=post))

        profile = await style_service.build_style_profile(cleaned_posts)
        stored_profile = StyleProfile(
            voice_summary=profile.voice_summary,
            opening_patterns=profile.opening_patterns,
            sentence_length_preference=profile.sentence_length_preference,
            emoji_usage=profile.emoji_usage,
            hashtag_style=profile.hashtag_style,
            cta_style=profile.cta_style,
            preferred_topics=profile.preferred_topics,
            phrases_to_mimic=profile.phrases_to_mimic,
            phrases_to_avoid=profile.phrases_to_avoid,
            sample_count=len(cleaned_posts),
        )
        db.add(stored_profile)
        db.commit()
        db.refresh(stored_profile)
    except Exception as exc:
        db.rollback()
        logger.error("style_profile_generation_failed", error=str(exc))
        raise HTTPException(status_code=500, detail="Style profile generation failed.") from exc

    logger.info("style_import_complete", sample_count=len(cleaned_posts))
    return stored_profile


@router.get("/style/profile", response_model=StyleProfileResponse)
def get_style_profile(db: Session = Depends(get_db)):
    profile = db.query(StyleProfile).order_by(StyleProfile.created_at.desc()).first()
    if not profile:
        raise HTTPException(status_code=404, detail="No style profile found yet.")
    return profile
