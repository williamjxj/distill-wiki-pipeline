from fastapi.testclient import TestClient
from pipeline.api.main import create_app


def test_status_endpoint():
    client = TestClient(create_app())
    resp = client.get("/api/status")
    assert resp.status_code == 200
    data = resp.json()
    assert "pending_raw_count" in data
    assert "lint_error_count" in data
