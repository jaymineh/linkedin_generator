from datetime import datetime
from typing import Literal, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

VALID_AUDIENCES = Literal["developers", "executives", "job_seekers", "general"]
VALID_TONES = Literal["professional", "casual", "storytelling", "thought_leader"]
VALID_STYLE_MODES = Literal["off", "faithful", "improve"]
VALID_LLM_PROVIDERS = Literal["openai", "google", "zai"]


class GenerateRequest(BaseModel):
    topic: str = Field(..., min_length=3, max_length=1000)
    audience: VALID_AUDIENCES
    tone: VALID_TONES
    style_mode: VALID_STYLE_MODES = "off"
    url: Optional[str] = None
    llm_provider: Optional[VALID_LLM_PROVIDERS] = None
    llm_model: Optional[str] = Field(default=None, min_length=1, max_length=120)


class PostVariant(BaseModel):
    style: str
    hook: str
    body: str
    hashtags: list[str]

    model_config = ConfigDict(from_attributes=True)


class GenerateResponse(BaseModel):
    generation_id: UUID
    posts: list[PostVariant]


class HistoryItem(BaseModel):
    id: UUID
    topic: str
    audience: str
    tone: str
    style_mode: VALID_STYLE_MODES
    created_at: datetime
    posts: list[PostVariant]

    model_config = ConfigDict(from_attributes=True)


class StyleImportRequest(BaseModel):
    posts: list[str] = Field(..., min_length=3, max_length=20)
    llm_provider: Optional[VALID_LLM_PROVIDERS] = None
    llm_model: Optional[str] = Field(default=None, min_length=1, max_length=120)


class StyleProfileResponse(BaseModel):
    voice_summary: str
    opening_patterns: list[str]
    sentence_length_preference: str
    emoji_usage: str
    hashtag_style: str
    cta_style: str
    preferred_topics: list[str]
    phrases_to_mimic: list[str]
    phrases_to_avoid: list[str]
    sample_count: int
    created_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class ModelProviderOption(BaseModel):
    provider: VALID_LLM_PROVIDERS
    default_model: str
    models: list[str]


class ModelOptionsResponse(BaseModel):
    providers: list[ModelProviderOption]
