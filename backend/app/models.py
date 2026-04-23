import uuid
from datetime import UTC, datetime

from sqlalchemy import ARRAY, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


def utc_now() -> datetime:
    return datetime.now(UTC)


class Generation(Base):
    __tablename__ = "generations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    topic = Column(Text, nullable=False)
    audience = Column(String(100), nullable=False)
    tone = Column(String(100), nullable=False)
    style_mode = Column(String(20), nullable=False, default="off")
    url = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)
    posts = relationship("Post", back_populates="generation", cascade="all, delete-orphan")


class Post(Base):
    __tablename__ = "posts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    generation_id = Column(UUID(as_uuid=True), ForeignKey("generations.id"), nullable=False)
    style = Column(String(50), nullable=False)
    hook = Column(Text, nullable=False)
    body = Column(Text, nullable=False)
    hashtags = Column(ARRAY(Text), default=list)
    created_at = Column(DateTime(timezone=True), default=utc_now)
    generation = relationship("Generation", back_populates="posts")


class StyleSample(Base):
    __tablename__ = "style_samples"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now)


class StyleProfile(Base):
    __tablename__ = "style_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    voice_summary = Column(Text, nullable=False)
    opening_patterns = Column(ARRAY(Text), default=list)
    sentence_length_preference = Column(String(50), nullable=False)
    emoji_usage = Column(String(50), nullable=False)
    hashtag_style = Column(Text, nullable=False)
    cta_style = Column(Text, nullable=False)
    preferred_topics = Column(ARRAY(Text), default=list)
    phrases_to_mimic = Column(ARRAY(Text), default=list)
    phrases_to_avoid = Column(ARRAY(Text), default=list)
    sample_count = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), default=utc_now)
