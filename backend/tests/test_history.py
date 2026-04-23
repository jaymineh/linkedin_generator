def test_history_empty(client):
    response = client.get("/api/history")
    assert response.status_code == 200
    assert response.json() == []


def test_history_after_generate(client, mock_openai):
    client.post(
        "/api/generate",
        json={
            "topic": "test topic",
            "audience": "developers",
            "tone": "casual",
        },
    )
    response = client.get("/api/history")
    assert response.status_code == 200
    items = response.json()
    assert len(items) == 1
    assert items[0]["topic"] == "test topic"
    assert items[0]["style_mode"] == "off"
    assert len(items[0]["posts"]) == 1


def test_delete_generation(client, mock_openai):
    generation = client.post(
        "/api/generate",
        json={
            "topic": "to delete",
            "audience": "general",
            "tone": "professional",
        },
    ).json()

    delete_response = client.delete(f"/api/history/{generation['generation_id']}")
    assert delete_response.status_code == 204

    history = client.get("/api/history").json()
    assert len(history) == 0
