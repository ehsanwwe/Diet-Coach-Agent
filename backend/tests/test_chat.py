"""
Tests for companion chat endpoints.

Covers:
  - Greeting bypass: "سلام" returns short local response, no bad phrases
  - Greeting provider metadata: provider="local", is_mock=True
  - English greeting bypass
  - Chat message is persisted in history
  - Clear memory removes all messages
  - Non-greeting returns an AI (mock) response
"""
from __future__ import annotations

from types import SimpleNamespace
from datetime import datetime, timedelta
import uuid

import pytest
from sqlalchemy import select

from app.models.chat import ChatMessage, ChatSession
from app.models.user import User
from app.models.audit import AuditLog
from app.services import chat_service
from app.services.mock_ai_provider import MockAIProvider

_BAD_PHRASES = [
    "دسترسی به اطلاعات مربی",
    "اگر کاربر",
    "خوشحالیم که اومدی",
    "خوشحالیم که برگشتی",
    "اینقدر از اپ",
]


def test_greeting_returns_short_response(client):
    resp = client.post("/api/v1/chat/message", json={"message": "سلام"})
    assert resp.status_code == 201, resp.text
    data = resp.json()["data"]
    assert data["role"] == "assistant"
    assert len(data["content"]) < 600, f"Greeting reply too long: {data['content']!r}"


def test_greeting_no_bad_phrases(client):
    resp = client.post("/api/v1/chat/message", json={"message": "سلام"})
    assert resp.status_code == 201
    content = resp.json()["data"]["content"]
    for phrase in _BAD_PHRASES:
        assert phrase not in content, f"Bad phrase found: {phrase!r}"


def test_greeting_is_local_provider(client):
    resp = client.post("/api/v1/chat/message", json={"message": "سلام"})
    assert resp.status_code == 201
    data = resp.json()["data"]
    assert data["provider"] == "local"
    assert data["is_mock"] is True


def test_english_greeting_bypass(client):
    resp = client.post("/api/v1/chat/message", json={"message": "hello"})
    assert resp.status_code == 201
    data = resp.json()["data"]
    assert data["provider"] == "local"


def test_chat_message_persisted_in_history(client):
    client.post("/api/v1/chat/message", json={"message": "سلام"})

    hist = client.get("/api/v1/chat/history")
    assert hist.status_code == 200
    messages = hist.json()["data"]["messages"]
    roles = [m["role"] for m in messages]
    assert "user" in roles
    assert "assistant" in roles


def test_clear_chat_removes_history(client):
    client.post("/api/v1/chat/message", json={"message": "سلام"})

    resp = client.post("/api/v1/chat/clear")
    assert resp.status_code == 200

    hist = client.get("/api/v1/chat/history")
    assert hist.json()["data"]["messages"] == []


def test_non_greeting_returns_mock_response(client):
    resp = client.post(
        "/api/v1/chat/message",
        json={"message": "برنامه غذایی برای کاهش وزن چیه؟"},
    )
    assert resp.status_code == 201
    data = resp.json()["data"]
    assert data["role"] == "assistant"
    assert len(data["content"]) > 0


def test_history_includes_status_field(client):
    client.post("/api/v1/chat/message", json={"message": "سلام"})
    hist = client.get("/api/v1/chat/history")
    messages = hist.json()["data"]["messages"]
    assert len(messages) >= 1
    for msg in messages:
        assert "status" in msg
        assert msg["status"] in ("completed", "pending", "failed")


def test_completed_messages_visible_in_history(client):
    client.post("/api/v1/chat/message", json={"message": "سلام"})
    hist = client.get("/api/v1/chat/history")
    messages = hist.json()["data"]["messages"]
    completed = [m for m in messages if m["status"] == "completed"]
    assert len(completed) >= 2  # user + assistant


def test_client_message_id_prevents_duplicate_user_message(client):
    cid = "test-idempotency-key-001"
    resp1 = client.post("/api/v1/chat/message", json={"message": "سلام", "client_message_id": cid})
    assert resp1.status_code == 201

    resp2 = client.post("/api/v1/chat/message", json={"message": "سلام", "client_message_id": cid})
    assert resp2.status_code == 201

    hist = client.get("/api/v1/chat/history")
    messages = hist.json()["data"]["messages"]
    user_msgs = [m for m in messages if m["role"] == "user"]
    assert len(user_msgs) == 1, f"Expected 1 user message, got {len(user_msgs)}"


def test_send_without_client_message_id_still_works(client):
    resp = client.post("/api/v1/chat/message", json={"message": "درود"})
    assert resp.status_code == 201
    data = resp.json()["data"]
    assert data["role"] == "assistant"


@pytest.fixture
def fast_chat_generation(monkeypatch):
    provider = MockAIProvider()
    monkeypatch.setattr("app.services.agent_orchestrator.get_ai_provider", lambda: provider)

    def fake_chat_message(self, ctx, message, history):
        return {"reply": f"answer for {message}"}, SimpleNamespace(provider="test", is_mock=True)

    monkeypatch.setattr(
        "app.services.nutrition_agent_service.NutritionAgentService.chat_message",
        fake_chat_message,
    )


def _seed_chat_pairs(client, db_session, test_user, count: int) -> dict:
    session = ChatSession(
        user_id=test_user.id,
        session_type="companion",
        message_count=count * 2,
    )
    db_session.add(session)
    db_session.flush()
    base_time = datetime(2026, 1, 1)
    for index in range(count):
        db_session.add_all(
            [
                ChatMessage(
                    session_id=session.id,
                    role="user",
                    content=f"nutrition question {index + 1}",
                    status="completed",
                    created_at=base_time + timedelta(seconds=index * 2),
                ),
                ChatMessage(
                    session_id=session.id,
                    role="assistant",
                    content=f"nutrition answer {index + 1}",
                    status="completed",
                    created_at=base_time + timedelta(seconds=index * 2 + 1),
                ),
            ]
        )
    db_session.flush()
    history = client.get("/api/v1/chat/history")
    assert history.status_code == 200
    return history.json()["data"]


def _edit_url(session_id: str, message_id: str) -> str:
    return f"/api/v1/chat/sessions/{session_id}/messages/{message_id}"


def test_edit_latest_user_message_regenerates_and_keeps_stable_id(
    client, db_session, test_user, fast_chat_generation
):
    before = _seed_chat_pairs(client, db_session, test_user, 2)
    target = [message for message in before["messages"] if message["role"] == "user"][-1]

    response = client.patch(
        _edit_url(before["session_id"], target["message_id"]),
        json={"content": "edited latest nutrition question"},
    )

    assert response.status_code == 200, response.text
    after = client.get("/api/v1/chat/history").json()["data"]["messages"]
    edited = next(message for message in after if message["message_id"] == target["message_id"])
    assert edited["content"] == "edited latest nutrition question"
    assert after[-1]["role"] == "assistant"
    assert len(after) == len(before["messages"])


def test_edit_older_message_removes_all_later_pairs_and_preserves_earlier_messages(
    client, db_session, test_user, fast_chat_generation
):
    before = _seed_chat_pairs(client, db_session, test_user, 4)
    target = before["messages"][2]
    preserved_ids = [message["message_id"] for message in before["messages"][:2]]
    removed_ids = {message["message_id"] for message in before["messages"][3:]}

    response = client.patch(
        _edit_url(before["session_id"], target["message_id"]),
        json={"content": "edited second question"},
    )

    assert response.status_code == 200, response.text
    after = client.get("/api/v1/chat/history").json()["data"]["messages"]
    after_ids = {message["message_id"] for message in after}
    assert [message["message_id"] for message in after[:2]] == preserved_ids
    assert removed_ids.isdisjoint(after_ids)
    assert after[2]["message_id"] == target["message_id"]
    assert after[2]["content"] == "edited second question"
    assert [message["role"] for message in after] == ["user", "assistant", "user", "assistant"]


def test_edit_first_message_removes_five_complete_later_pairs(
    client, db_session, test_user, fast_chat_generation
):
    before = _seed_chat_pairs(client, db_session, test_user, 6)
    target = before["messages"][0]
    stale_ids = {message["message_id"] for message in before["messages"][1:]}

    response = client.patch(
        _edit_url(before["session_id"], target["message_id"]),
        json={"content": "new first question"},
    )

    assert response.status_code == 200, response.text
    persisted = client.get("/api/v1/chat/history").json()["data"]["messages"]
    assert len(persisted) == 2
    assert persisted[0]["message_id"] == target["message_id"]
    assert persisted[0]["content"] == "new first question"
    assert stale_ids.isdisjoint({message["message_id"] for message in persisted})


def test_edit_rejects_assistant_message_without_changing_history(
    client, db_session, test_user, fast_chat_generation
):
    before = _seed_chat_pairs(client, db_session, test_user, 1)
    assistant = next(message for message in before["messages"] if message["role"] == "assistant")

    response = client.patch(
        _edit_url(before["session_id"], assistant["message_id"]),
        json={"content": "not allowed"},
    )

    assert response.status_code == 422
    after = client.get("/api/v1/chat/history").json()["data"]
    assert after["messages"] == before["messages"]


def test_edit_from_another_user_returns_safe_not_found(client, db_session, fast_chat_generation):
    other_user = User(
        id=str(uuid.uuid4()),
        phone="+989100000001",
        is_active=True,
        is_onboarded=False,
    )
    db_session.add(other_user)
    db_session.flush()
    other_session = ChatSession(user_id=other_user.id, session_type="companion", message_count=1)
    db_session.add(other_session)
    db_session.flush()
    other_message = ChatMessage(
        session_id=other_session.id,
        role="user",
        content="private message",
        status="completed",
    )
    db_session.add(other_message)
    db_session.flush()

    response = client.patch(
        _edit_url(other_session.id, other_message.id),
        json={"content": "unauthorized edit"},
    )

    assert response.status_code == 404
    db_session.refresh(other_message)
    assert other_message.content == "private message"


def test_edit_rejects_whitespace_only_content(
    client, db_session, test_user, fast_chat_generation
):
    before = _seed_chat_pairs(client, db_session, test_user, 1)
    target = before["messages"][0]

    response = client.patch(
        _edit_url(before["session_id"], target["message_id"]),
        json={"content": "  \n\t "},
    )

    assert response.status_code == 422
    after = client.get("/api/v1/chat/history").json()["data"]
    assert after["messages"] == before["messages"]


def test_edit_rebuilds_context_without_stale_messages(
    client, db_session, test_user, monkeypatch, fast_chat_generation
):
    before = _seed_chat_pairs(client, db_session, test_user, 3)
    target = before["messages"][2]
    captured: dict[str, object] = {}

    def fake_chat_message(self, ctx, message, history):
        captured["message"] = message
        captured["history"] = history
        return {"reply": "regenerated answer"}, SimpleNamespace(provider="test", is_mock=True)

    monkeypatch.setattr(
        "app.services.nutrition_agent_service.NutritionAgentService.chat_message",
        fake_chat_message,
    )
    response = client.patch(
        _edit_url(before["session_id"], target["message_id"]),
        json={"content": "edited context question"},
    )

    assert response.status_code == 200, response.text
    assert captured["message"] == "edited context question"
    assert captured["history"] == [
        {"role": before["messages"][0]["role"], "content": before["messages"][0]["content"]},
        {"role": before["messages"][1]["role"], "content": before["messages"][1]["content"]},
    ]


def test_edit_records_audit_without_adding_a_chat_message(
    client, db_session, test_user, fast_chat_generation
):
    before = _seed_chat_pairs(client, db_session, test_user, 2)
    target = before["messages"][0]

    response = client.patch(
        _edit_url(before["session_id"], target["message_id"]),
        json={"content": "audited edit"},
    )

    assert response.status_code == 200
    audit = db_session.execute(
        select(AuditLog).where(AuditLog.resource_id == target["message_id"])
    ).scalar_one()
    assert audit.action == "chat_message_edited"
    history = client.get("/api/v1/chat/history").json()["data"]["messages"]
    assert all(message["role"] in {"user", "assistant"} for message in history)


def test_concurrent_edit_is_rejected_before_duplicate_generation(
    client, db_session, test_user, fast_chat_generation
):
    before = _seed_chat_pairs(client, db_session, test_user, 1)
    target = before["messages"][0]

    with chat_service._exclusive_generation(test_user.id):
        response = client.patch(
            _edit_url(before["session_id"], target["message_id"]),
            json={"content": "conflicting edit"},
        )

    assert response.status_code == 409
    after = client.get("/api/v1/chat/history").json()["data"]
    assert after["messages"] == before["messages"]


def test_generation_failure_keeps_edited_branch_and_marks_placeholder_failed(
    client, db_session, test_user, monkeypatch, fast_chat_generation
):
    before = _seed_chat_pairs(client, db_session, test_user, 3)
    target = before["messages"][0]
    stale_ids = {message["message_id"] for message in before["messages"][1:]}

    def fail_generation(*args, **kwargs):
        raise RuntimeError("forced generation failure")

    monkeypatch.setattr(
        "app.services.agent_orchestrator.process_user_message",
        fail_generation,
    )
    response = client.patch(
        _edit_url(before["session_id"], target["message_id"]),
        json={"content": "edited despite generation failure"},
    )

    assert response.status_code == 500
    persisted = client.get("/api/v1/chat/history").json()["data"]["messages"]
    assert persisted[0]["message_id"] == target["message_id"]
    assert persisted[0]["content"] == "edited despite generation failure"
    assert persisted[1]["role"] == "assistant"
    assert persisted[1]["status"] == "failed"
    assert stale_ids.isdisjoint({message["message_id"] for message in persisted})
