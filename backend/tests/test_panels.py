def create_topic(client, expert_count=4):
    response = client.post(
        "/api/v1/topics",
        json={"title": "AI 是否应该参与招聘终审？", "requestedExpertCount": expert_count},
    )
    assert response.status_code == 201
    return response.json()


def test_generate_admit_and_create_session(client):
    topic = create_topic(client)

    generated = client.post(f"/api/v1/topics/{topic['id']}/panel:generate", json={})
    assert generated.status_code == 200
    panel = generated.json()
    assert panel["generation"] == 1
    assert panel["host"]["kind"] == "host"
    assert len(panel["experts"]) == 4
    assert len({expert["color"] for expert in panel["experts"]}) == 4
    assert all(not expert["admitted"] for expert in panel["experts"])

    admitted = client.put(
        f"/api/v1/topics/{topic['id']}/panel:admit",
        json={"generation": panel["generation"]},
    )
    assert admitted.status_code == 200
    assert admitted.json()["host"]["admitted"] is True
    assert all(expert["admitted"] for expert in admitted.json()["experts"])

    created_session = client.post(
        f"/api/v1/topics/{topic['id']}/sessions", json={"maxTurns": 12}
    )
    assert created_session.status_code == 201
    assert created_session.json()["status"] == "admitted"
    assert created_session.json()["maxTurns"] == 12


def test_stale_generation_cannot_be_admitted(client):
    topic = create_topic(client)
    first = client.post(f"/api/v1/topics/{topic['id']}/panel:generate", json={}).json()
    second = client.post(f"/api/v1/topics/{topic['id']}/panel:generate", json={}).json()

    assert second["generation"] == first["generation"] + 1
    response = client.put(
        f"/api/v1/topics/{topic['id']}/panel:admit",
        json={"generation": first["generation"]},
    )
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "PANEL_GENERATION_STALE"


def test_admitted_panel_cannot_be_regenerated_and_session_is_unique(client):
    topic = create_topic(client)
    panel = client.post(f"/api/v1/topics/{topic['id']}/panel:generate", json={}).json()
    client.put(
        f"/api/v1/topics/{topic['id']}/panel:admit", json={"generation": panel["generation"]}
    )

    regenerated = client.post(f"/api/v1/topics/{topic['id']}/panel:generate", json={})
    assert regenerated.status_code == 409
    assert regenerated.json()["error"]["code"] == "PANEL_ALREADY_ADMITTED"

    first_session = client.post(f"/api/v1/topics/{topic['id']}/sessions", json={})
    assert first_session.status_code == 201
    duplicate = client.post(f"/api/v1/topics/{topic['id']}/sessions", json={})
    assert duplicate.status_code == 409
    assert duplicate.json()["error"]["code"] == "SESSION_ALREADY_ACTIVE"
