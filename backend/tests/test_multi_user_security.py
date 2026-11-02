import os
import uuid

import pytest
from fastapi.testclient import TestClient

from app.main import app


pytestmark = pytest.mark.skipif(
    not os.getenv("DATABASE_URL"),
    reason="Set DATABASE_URL to run the multi-user integration test.",
)


def test_users_cannot_cross_access_documents_or_conversations():
    suffix = uuid.uuid4().hex[:10]
    client_a = TestClient(app)
    client_b = TestClient(app)

    account_a = {
        "full_name": "Security User A",
        "email": f"security-a-{suffix}@example.test",
        "password": "SecurePass123",
        "confirm_password": "SecurePass123",
    }
    account_b = {
        "full_name": "Security User B",
        "email": f"security-b-{suffix}@example.test",
        "password": "SecurePass123",
        "confirm_password": "SecurePass123",
    }
    assert client_a.post("/api/auth/register", json=account_a).status_code == 201
    assert client_b.post("/api/auth/register", json=account_b).status_code == 201

    conversation = client_a.post("/api/conversations", json={"title": "Private A"})
    assert conversation.status_code == 201
    conversation_id = conversation.json()["conversation"]["conversation_id"]
    assert client_a.get("/api/conversations").json()["conversations"]

    assert client_b.get(f"/api/conversations/{conversation_id}").status_code == 404
    assert client_b.patch(
        f"/api/conversations/{conversation_id}", json={"title": "Hijacked"}
    ).status_code == 404
    assert client_b.delete(f"/api/conversations/{conversation_id}").status_code == 404

    assert client_a.get("/api/documents").status_code == 200
    assert client_b.get("/api/documents").status_code == 200
    assert client_a.post("/api/search", json={"query": "private evidence"}).status_code == 200
    assert client_b.post("/api/search", json={"query": "private evidence"}).status_code == 200
