def test_create_list_and_get_topic(client):
    created = client.post(
        "/api/v1/topics",
        json={
            "title": "AI 是否应该参与招聘终审？",
            "background": "公司计划引入自动化评估。",
            "goal": "讨论公平性与责任边界。",
            "requestedExpertCount": 4,
        },
    )

    assert created.status_code == 201
    body = created.json()
    assert body["title"] == "AI 是否应该参与招聘终审？"
    assert body["requestedExpertCount"] == 4
    assert body["status"] == "draft"

    listed = client.get("/api/v1/topics")
    assert listed.status_code == 200
    assert [item["id"] for item in listed.json()["items"]] == [body["id"]]

    fetched = client.get(f"/api/v1/topics/{body['id']}")
    assert fetched.status_code == 200
    assert fetched.json() == body


def test_rejects_invalid_expert_count_with_safe_error(client):
    response = client.post(
        "/api/v1/topics",
        json={"title": "测试话题", "requestedExpertCount": 1},
    )

    assert response.status_code == 422
    payload = response.json()["error"]
    assert payload["code"] == "VALIDATION_ERROR"
    assert payload["requestId"]
    assert "traceback" not in response.text.lower()


def test_missing_topic_returns_stable_error(client):
    response = client.get("/api/v1/topics/not-found")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "RESOURCE_NOT_FOUND"
