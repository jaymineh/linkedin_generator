from unittest.mock import ANY, AsyncMock, patch

import pytest

from app.models import StyleProfile
from app.services.openai_service import build_generate_user_message


def test_generate_success(client, mock_openai):
    response = client.post(
        "/api/generate",
        json={
            "topic": "AI in production",
            "audience": "developers",
            "tone": "professional",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "generation_id" in data
    assert len(data["posts"]) == 1
    assert data["posts"][0]["style"] == "professional"


def test_generate_records_observability_metrics(client, mock_openai):
    with (
        patch("app.routes.generate.telemetry.record_generation_started") as started,
        patch("app.routes.generate.telemetry.record_generation_completed") as completed,
    ):
        response = client.post(
            "/api/generate",
            json={
                "topic": "AI in production",
                "audience": "developers",
                "tone": "professional",
            },
        )

    assert response.status_code == 200
    started.assert_called_once_with(
        audience="developers",
        tone="professional",
        style_mode="off",
        source_type="manual",
        style_profile_available=False,
    )
    completed.assert_called_once()
    completed_kwargs = completed.call_args.kwargs
    assert completed_kwargs["source_type"] == "manual"
    assert completed_kwargs["scrape_succeeded"] is False
    assert completed_kwargs["post_count"] == 1
    assert completed_kwargs["duration_ms"] >= 0


def test_generate_records_failure_metrics(client):
    with (
        patch("app.services.openai_service.generate_posts", new_callable=AsyncMock) as mock_generate_posts,
        patch("app.routes.generate.telemetry.record_generation_failed") as failed,
    ):
        mock_generate_posts.side_effect = RuntimeError("boom")
        response = client.post(
            "/api/generate",
            json={
                "topic": "AI in production",
                "audience": "developers",
                "tone": "professional",
            },
        )

    assert response.status_code == 500
    failed.assert_called_once_with(
        audience="developers",
        tone="professional",
        style_mode="off",
        source_type="manual",
        style_profile_available=False,
        scrape_succeeded=False,
        error_type="RuntimeError",
        duration_ms=ANY,
    )


def test_generate_invalid_audience(client):
    response = client.post(
        "/api/generate",
        json={
            "topic": "AI in production",
            "audience": "invalid_audience",
            "tone": "professional",
        },
    )
    assert response.status_code == 422


def test_generate_empty_topic(client):
    response = client.post(
        "/api/generate",
        json={
            "topic": "",
            "audience": "developers",
            "tone": "professional",
        },
    )
    assert response.status_code == 422


def test_health_check(client):
    response = client.get("/health/live")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@pytest.mark.parametrize("style_mode", ["off", "faithful", "improve"])
def test_generate_endpoint_supports_style_modes(client, db_session, mock_openai, style_mode):
    db_session.add(
        StyleProfile(
            voice_summary="Warm and thoughtful",
            opening_patterns=["Bold opinion"],
            sentence_length_preference="medium",
            emoji_usage="rare",
            hashtag_style="3-5 hashtags",
            cta_style="question at the end",
            preferred_topics=["AI"],
            phrases_to_mimic=["One thing I've learned"],
            phrases_to_avoid=["synergy"],
            sample_count=8,
        )
    )
    db_session.commit()

    response = client.post(
        "/api/generate",
        json={
            "topic": "AI in production",
            "audience": "developers",
            "tone": "professional",
            "style_mode": style_mode,
        },
    )
    assert response.status_code == 200
    assert len(response.json()["posts"]) == 1


def test_prompt_builder_only_includes_style_block_when_enabled():
    profile = {
        "voice_summary": "Warm and clear",
        "opening_patterns": ["Question first"],
        "sentence_length_preference": "medium",
        "emoji_usage": "rare",
        "hashtag_style": "3-5 concise hashtags",
        "cta_style": "light question",
        "preferred_topics": ["AI"],
        "phrases_to_mimic": ["One thing I've learned"],
        "phrases_to_avoid": ["synergy"],
    }

    off_message = build_generate_user_message(
        topic="AI in production",
        audience="developers",
        tone="professional",
        style_mode="off",
        style_profile=profile,
    )
    faithful_message = build_generate_user_message(
        topic="AI in production",
        audience="developers",
        tone="professional",
        style_mode="faithful",
        style_profile=profile,
    )

    assert "Writing style profile:" not in off_message
    assert "Writing style profile:" in faithful_message
    assert "voice_summary: Warm and clear" in faithful_message
