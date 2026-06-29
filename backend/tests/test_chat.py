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
