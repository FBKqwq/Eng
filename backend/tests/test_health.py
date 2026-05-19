from fastapi.testclient import TestClient
from app.main import app
from app.services.simulation.log_generator import build_mock_log


def test_health() -> None:
    client = TestClient(app)
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_log_search_returns_stable_page_shape() -> None:
    client = TestClient(app)
    response = client.post("/api/v1/logs/search", json={"page": 1, "page_size": 2})

    assert response.status_code == 200
    body = response.json()
    assert "items" in body
    assert "total" in body
    assert body["page"] == 1
    assert body["page_size"] == 2
    assert "has_more" in body


def test_diagnosis_accepts_keyword_and_returns_context_summary() -> None:
    client = TestClient(app)
    response = client.post(
        "/api/v1/diagnosis",
        json={
            "request_id": "diag-test-1",
            "keyword": "payment timeout",
            "include_context_logs": False,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["diagnosis"]["anomaly_type"] == "接口超时"
    assert "context_summary" in body["diagnosis"]


def test_log_generator_can_emit_nginx_web_server_log() -> None:
    web_log = None
    for _ in range(200):
        candidate = build_mock_log()
        if candidate.get("log_type") == "web_server":
            web_log = candidate
            break

    assert web_log is not None
    assert web_log["nginx_log_kind"] in {"access", "error"}
    assert web_log["request"]
    assert web_log["remote_addr"]
    assert web_log["request_method"] in {"GET", "POST", "PUT", "PATCH", "DELETE"}
    assert 100 <= int(web_log["status_code"]) <= 599
