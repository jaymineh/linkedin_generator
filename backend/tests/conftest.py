import os
import sys
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

TEST_DB_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/linkedin_gen_test",
)
os.environ.setdefault("DATABASE_URL", TEST_DB_URL)
os.environ.setdefault("OPENAI_API_KEY", "test-key")
os.environ.setdefault("APPLICATIONINSIGHTS_CONNECTION_STRING", "")
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.database import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402

engine = create_engine(TEST_DB_URL)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session():
    session = TestSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(db_session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def mock_openai():
    mock_posts = [
        {"style": "professional", "hook": "Test hook 1", "body": "Test body 1", "hashtags": ["AI"]}
    ]
    with patch("app.services.openai_service.generate_posts", new_callable=AsyncMock) as mock:
        from app.services.openai_service import PostVariantOutput

        mock.return_value = [PostVariantOutput(**post) for post in mock_posts]
        yield mock


@pytest.fixture
def mock_style_analyzer():
    with patch("app.services.style_service.build_style_profile", new_callable=AsyncMock) as mock:
        from app.services.style_service import StyleProfileOutput

        mock.return_value = StyleProfileOutput(
            voice_summary="Warm, practical, reflective",
            opening_patterns=["Starts with a bold opinion", "Uses short hooks"],
            sentence_length_preference="medium",
            emoji_usage="rare",
            hashtag_style="3-5 concise hashtags",
            cta_style="ends with a reflective question",
            preferred_topics=["AI", "careers"],
            phrases_to_mimic=["One thing I've learned"],
            phrases_to_avoid=["game changer"],
        )
        yield mock
