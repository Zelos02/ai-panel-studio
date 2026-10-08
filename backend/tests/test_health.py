def test_health_reports_fake_provider(client):
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "environment": "test",
        "llmProvider": "fake",
    }
    assert response.headers["x-request-id"]
