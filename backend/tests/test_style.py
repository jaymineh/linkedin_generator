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
