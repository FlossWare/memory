"""PostgreSQL-backed REST contract tests.

Set MEMORY_TEST_DATABASE_URL to a disposable PostgreSQL database and install
service/requirements.txt plus pytest before running these integration tests.
"""
import importlib
import json
import os

import pytest

TEST_DB = os.getenv("MEMORY_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not TEST_DB, reason="set MEMORY_TEST_DATABASE_URL to run PostgreSQL integration tests")
pytest.importorskip("fastapi")
pytest.importorskip("psycopg")
from fastapi.testclient import TestClient


@pytest.fixture()
def client(monkeypatch):
    monkeypatch.setenv("MEMORY_DATABASE_URL", TEST_DB)
    monkeypatch.setenv("MEMORY_PROJECT_TOKENS", json.dumps({"alpha": "token-alpha", "beta": "token-beta"}))
    monkeypatch.setenv("MEMORY_ADMIN_TOKEN", "token-admin")
    import service.app as module
    module = importlib.reload(module)
    with TestClient(module.app) as test_client:
        with module.db() as conn:
            conn.execute("DELETE FROM memory_idempotency")
            conn.execute("DELETE FROM memory_records")
        yield test_client


def headers(project="alpha", token=None):
    return {"Authorization": f"Bearer {token or 'token-' + project}", "X-Project-Id": project}


def test_health_and_ready(client):
    assert client.get("/health").status_code == 200
    assert client.get("/ready").status_code == 200


def test_token_is_bound_to_project(client):
    response = client.get("/api/v1/memories", headers=headers("beta", "token-alpha"))
    assert response.status_code == 403


def test_raw_round_trip_enumeration_and_idempotency(client):
    h = {**headers(), "Idempotency-Key": "same-request"}
    body = {"id": "raw-1", "content": "Original unmodified content", "metadata": {"kind": "note"}, "provenance": {"source": "test"}}
    created = client.post("/api/v1/memories", headers=h, json=body)
    assert created.status_code == 200 or created.status_code == 201
    assert created.json()["content"] == body["content"]
    assert created.json()["metadata"] == body["metadata"]
    retry = client.post("/api/v1/memories", headers=h, json=body)
    assert retry.status_code == 200
    fetched = client.get("/api/v1/memories/raw-1", headers=headers())
    assert fetched.status_code == 200
    assert fetched.json()["content"] == body["content"]
    assert any(item["id"] == "raw-1" for item in client.get("/api/v1/memories", headers=headers()).json()["items"])


def test_conflicting_idempotency_key_is_rejected(client):
    h = {**headers(), "Idempotency-Key": "same-key"}
    assert client.post("/api/v1/memories", headers=h, json={"id":"one","content":"first"}).status_code in (200, 201)
    response = client.post("/api/v1/memories", headers=h, json={"id":"one","content":"different"})
    assert response.status_code == 409


def test_project_isolation_and_not_found(client):
    client.post("/api/v1/memories", headers={**headers(), "Idempotency-Key":"private"}, json={"id":"alpha-only","content":"private"})
    assert client.get("/api/v1/memories/alpha-only", headers=headers("beta")).status_code == 404
    assert client.get("/api/v1/memories", headers=headers("beta")).json()["total"] == 0


def test_search_is_separate_from_direct_access(client):
    client.post("/api/v1/memories", headers={**headers(), "Idempotency-Key":"search"}, json={"id":"searchable","content":"quartz river"})
    results = client.get("/api/v1/search?query=quartz", headers=headers())
    assert results.status_code == 200
    assert any(item["id"] == "searchable" for item in results.json()["items"])
    assert client.get("/api/v1/memories/searchable", headers=headers()).json()["content"] == "quartz river"


def test_global_write_requires_admin_token(client):
    h = {**headers(), "Idempotency-Key":"global"}
    response = client.post("/api/v1/memories", headers=h, json={"id":"global-1","content":"shared","scope_type":"global"})
    assert response.status_code == 403
    admin = {"Authorization":"Bearer token-admin","X-Project-Id":"alpha","Idempotency-Key":"global"}
    assert client.post("/api/v1/memories", headers=admin, json={"id":"global-1","content":"shared","scope_type":"global"}).status_code in (200, 201)
    assert client.get("/api/v1/memories/global-1", headers=headers("beta")).status_code == 200
