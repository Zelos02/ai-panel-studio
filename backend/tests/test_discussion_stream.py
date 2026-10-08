import json
import time

import pytest

from app.events import EventStore, encode_sse
from app.models import ExpertStatus, PanelSession
from app.services.discussions import DiscussionRunner


def create_ready_session(client, title, max_turns=4):
    topic = client.post(
        "/api/v1/topics", json={"title": title, "requestedExpertCount": 3}
    ).json()
    panel = client.post(f"/api/v1/topics/{topic['id']}/panel:generate", json={}).json()
    client.put(
        f"/api/v1/topics/{topic['id']}/panel:admit",
        json={"generation": panel["generation"]},
    )
    panel_session = client.post(
        f"/api/v1/topics/{topic['id']}/sessions", json={"maxTurns": max_turns}
    ).json()
    return topic, panel, panel_session


def test_start_endpoint_launches_background_discussion(client):
    _, _, panel_session = create_ready_session(client, "后台启动测试")

    started = client.post(f"/api/v1/sessions/{panel_session['id']}:start", json={})
    assert started.status_code == 202

    snapshot = started.json()
    for _ in range(50):
        snapshot = client.get(f"/api/v1/sessions/{panel_session['id']}").json()
        if snapshot["status"] == "completed":
            break
        time.sleep(0.01)
    assert snapshot["status"] == "completed"
    assert snapshot["lastEventSequence"] > 0


@pytest.mark.asyncio
async def test_discussion_is_persisted_as_incremental_public_events(client):
    _, _, panel_session = create_ready_session(client, "AI 是否应该参与招聘终审？")
    runner = DiscussionRunner(
        session_factory=client.app.state.session_factory,
        provider=client.app.state.llm_provider,
        hub=client.app.state.event_hub,
    )

    await runner.run(panel_session["id"])

    snapshot = client.get(f"/api/v1/sessions/{panel_session['id']}").json()
    transcript = client.get(f"/api/v1/sessions/{panel_session['id']}/transcript").json()["items"]
    assert snapshot["status"] == "completed"
    assert snapshot["turnCount"] == 4
    assert len(transcript) == 6  # host opening + four expert turns + host conclusion
    assert all("eventType" not in item for item in transcript)
    assert all(item["speaker"]["name"] for item in transcript)

    with client.app.state.session_factory() as db:
        events = EventStore(db).list_after(panel_session["id"], 0)
        statuses = db.query(ExpertStatus).filter_by(session_id=panel_session["id"]).all()
    assert [event["eventId"] for event in events] == list(range(1, len(events) + 1))
    assert any(event["eventType"] == "transcript.append" for event in events)
    assert any(event["eventType"] == "expert.status" for event in events)
    assert all(status.state == "waiting" for status in statuses)

    frame = encode_sse(events[0])
    assert f"id: {events[0]['eventId']}" in frame
    assert f"event: {events[0]['eventType']}" in frame
    payload_line = next(line for line in frame.splitlines() if line.startswith("data: "))
    assert json.loads(payload_line.removeprefix("data: "))["sessionId"] == panel_session["id"]


@pytest.mark.asyncio
async def test_running_one_session_does_not_emit_into_another(client):
    _, _, first = create_ready_session(client, "第一个话题")
    _, _, second = create_ready_session(client, "第二个话题")
    runner = DiscussionRunner(
        session_factory=client.app.state.session_factory,
        provider=client.app.state.llm_provider,
        hub=client.app.state.event_hub,
    )

    await runner.run(first["id"])

    with client.app.state.session_factory() as db:
        first_events = EventStore(db).list_after(first["id"], 0)
        second_events = EventStore(db).list_after(second["id"], 0)
        second_model = db.get(PanelSession, second["id"])
    assert first_events
    assert second_events == []
    assert second_model.status == "admitted"
    assert all(event["sessionId"] == first["id"] for event in first_events)
