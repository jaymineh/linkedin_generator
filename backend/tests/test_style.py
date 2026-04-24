from unittest.mock import ANY, AsyncMock, patch

from app.models import StyleProfile, StyleSample


def test_import_style_posts_saves_samples_and_profile(client, db_session, mock_style_analyzer):
    response = client.post(
        "/api/style/import",
        json={
            "posts": [
                "Post one about AI in production",
                "Post two about learning in public",
                "Post three about cloud deployment",
            ]
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["voice_summary"] == "Warm, practical, reflective"
    assert data["sample_count"] == 3
    assert db_session.query(StyleSample).count() == 3
    assert db_session.query(StyleProfile).count() == 1


def test_import_style_posts_records_metrics(client, mock_style_analyzer):
    with (
        patch("app.routes.style.telemetry.record_style_import_started") as started,
        patch("app.routes.style.telemetry.record_style_import_completed") as completed,
    ):
        response = client.post(
            "/api/style/import",
            json={
                "posts": [
                    "Post one about AI in production",
                    "Post two about learning in public",
                    "Post three about cloud deployment",
                ]
            },
        )

    assert response.status_code == 200
    started.assert_called_once_with(sample_count=3)
    completed.assert_called_once_with(sample_count=3, duration_ms=ANY)


def test_import_style_posts_records_failure_metrics(client):
    with (
        patch("app.services.style_service.build_style_profile", new_callable=AsyncMock) as build_style_profile,
        patch("app.routes.style.telemetry.record_style_import_failed") as failed,
    ):
        build_style_profile.side_effect = RuntimeError("style failed")
        response = client.post(
            "/api/style/import",
            json={
                "posts": [
                    "Post one about AI in production",
                    "Post two about learning in public",
                    "Post three about cloud deployment",
                ]
            },
        )

    assert response.status_code == 500
    failed.assert_called_once_with(sample_count=3, error_type="RuntimeError", duration_ms=ANY)


def test_get_style_profile(client, mock_style_analyzer):
    client.post(
        "/api/style/import",
        json={
            "posts": [
                "Post one",
                "Post two",
                "Post three",
            ]
        },
    )
    response = client.get("/api/style/profile")
    assert response.status_code == 200
    assert "voice_summary" in response.json()


def test_get_style_profile_not_found(client):
    response = client.get("/api/style/profile")
    assert response.status_code == 404
