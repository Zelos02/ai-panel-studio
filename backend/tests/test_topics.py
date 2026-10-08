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


def test_delete_topic_removes_its_panel_and_sessions(client):
    topic = client.post(
        "/api/v1/topics", json={"title": "待删除讨论", "requestedExpertCount": 2}
    ).json()
    panel = client.post(f"/api/v1/topics/{topic['id']}/panel:generate", json={}).json()
    client.put(
        f"/api/v1/topics/{topic['id']}/panel:admit",
        json={"generation": panel["generation"]},
    )
    panel_session = client.post(f"/api/v1/topics/{topic['id']}/sessions", json={}).json()

    deleted = client.delete(f"/api/v1/topics/{topic['id']}")

    assert deleted.status_code == 204
    assert client.get(f"/api/v1/topics/{topic['id']}").status_code == 404
    assert client.get(f"/api/v1/sessions/{panel_session['id']}").status_code == 404


def test_running_topic_cannot_be_deleted(client):
    topic = client.post(
        "/api/v1/topics", json={"title": "运行中讨论", "requestedExpertCount": 2}
    ).json()
    panel = client.post(f"/api/v1/topics/{topic['id']}/panel:generate", json={}).json()
    client.put(
        f"/api/v1/topics/{topic['id']}/panel:admit",
        json={"generation": panel["generation"]},
    )
    panel_session = client.post(f"/api/v1/topics/{topic['id']}/sessions", json={}).json()
    with client.app.state.session_factory() as db:
        from app.models import PanelSession

        stored = db.get(PanelSession, panel_session["id"])
        stored.status = "running"
        db.commit()

    deleted = client.delete(f"/api/v1/topics/{topic['id']}")

    assert deleted.status_code == 409
    assert deleted.json()["error"]["code"] == "TOPIC_DELETE_LOCKED"
