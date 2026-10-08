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


def panel_update_payload(panel, *, host_name="新主持人"):
    def member_payload(member):
        return {
            "id": member["id"],
            "name": host_name if member["kind"] == "host" else member["name"],
            "title": member["title"],
            "stance": member["stance"],
            "publicProfile": member["publicProfile"],
            "color": member["color"],
        }

    return {
        "generation": panel["generation"],
        "host": member_payload(panel["host"]),
        "experts": [member_payload(item) for item in panel["experts"]],
    }


def test_edit_panel_before_session_starts_and_preserve_member_ids(client):
    topic = create_topic(client, expert_count=2)
    panel = client.post(f"/api/v1/topics/{topic['id']}/panel:generate", json={}).json()
    admitted = client.put(
        f"/api/v1/topics/{topic['id']}/panel:admit",
        json={"generation": panel["generation"]},
    ).json()
    client.post(f"/api/v1/topics/{topic['id']}/sessions", json={})

    updated = client.put(
        f"/api/v1/topics/{topic['id']}/panel",
        json=panel_update_payload(admitted),
    )

    assert updated.status_code == 200
    body = updated.json()
    assert body["generation"] == admitted["generation"] + 1
    assert body["host"]["name"] == "新主持人"
    assert body["host"]["id"] == admitted["host"]["id"]
    assert [item["id"] for item in body["experts"]] == [
        item["id"] for item in admitted["experts"]
    ]


def test_edit_panel_is_locked_after_session_has_started(client):
    topic = create_topic(client, expert_count=2)
    panel = client.post(f"/api/v1/topics/{topic['id']}/panel:generate", json={}).json()
    admitted = client.put(
        f"/api/v1/topics/{topic['id']}/panel:admit",
        json={"generation": panel["generation"]},
    ).json()
    panel_session = client.post(f"/api/v1/topics/{topic['id']}/sessions", json={}).json()

    with client.app.state.session_factory() as db:
        from app.models import PanelSession

        stored = db.get(PanelSession, panel_session["id"])
        stored.status = "running"
        db.commit()

    updated = client.put(
        f"/api/v1/topics/{topic['id']}/panel",
        json=panel_update_payload(admitted),
    )

    assert updated.status_code == 409
    assert updated.json()["error"]["code"] == "PANEL_EDIT_LOCKED"
