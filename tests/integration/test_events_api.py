import json

from src.api.deps import get_reasoning_provider
from src.main import app

VALID_PAYLOAD = {
    "project_id": "payments-api",
    "environment_id": "prod",
    "severity": "high",
    "signal": "P99 latency spiked to 4s after the 14:30 deploy",
    "context": {"last_deploy": "v2.3.1", "cpu_usage": "85%", "error_rate": "12%"},
    "timestamp": "2024-04-03T14:45:00Z",
}


class FakeProvider:
    def __init__(self, response: str):
        self._response = response

    def complete(self, system_prompt: str, user_prompt: str) -> str:
        return self._response


def _override_provider(client, response: str) -> None:
    app.dependency_overrides[get_reasoning_provider] = lambda: FakeProvider(response)


def test_ingest_event_forces_pending_approval_for_disruptive_prod_action(client):
    _override_provider(
        client,
        json.dumps(
            {"action": "rollback", "confidence": 0.8, "reasoning": "Recent deploy caused latency spike.", "safe_to_auto": True}
        ),
    )

    response = client.post("/events/", json=VALID_PAYLOAD)

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "pending_approval"
    assert body["decision"]["safe_to_auto"] is False
    assert "approval_id" in body


def test_ingest_event_invalid_severity(client):
    payload = {**VALID_PAYLOAD, "severity": "extreme"}
    response = client.post("/events/", json=payload)
    assert response.status_code == 422


def test_ingest_event_invalid_environment(client):
    payload = {**VALID_PAYLOAD, "environment_id": "staging"}
    response = client.post("/events/", json=payload)
    assert response.status_code == 422


def test_ingest_event_missing_fields(client):
    response = client.post("/events/", json={"project_id": "payments-api"})
    assert response.status_code == 422


def test_ingest_event_safe_to_auto_true_is_processed_immediately(client):
    _override_provider(
        client,
        json.dumps({"action": "restart", "confidence": 0.9, "reasoning": "Service is unresponsive.", "safe_to_auto": True}),
    )
    payload = {**VALID_PAYLOAD, "environment_id": "dev", "severity": "low"}

    response = client.post("/events/", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "processed"
    assert "approval_id" not in body or body["approval_id"] is None


def test_list_and_get_event(client):
    _override_provider(
        client,
        json.dumps({"action": "restart", "confidence": 0.9, "reasoning": "Service is unresponsive.", "safe_to_auto": True}),
    )
    payload = {**VALID_PAYLOAD, "environment_id": "dev", "severity": "low"}
    ingest_response = client.post("/events/", json=payload)
    event_id = ingest_response.json()["event_id"]

    list_response = client.get("/events/")
    assert list_response.status_code == 200
    assert any(e["id"] == event_id for e in list_response.json())

    detail_response = client.get(f"/events/{event_id}")
    assert detail_response.status_code == 200
    assert detail_response.json()["decision"]["action"] == "restart"


def test_get_unknown_event_returns_404(client):
    response = client.get("/events/does-not-exist")
    assert response.status_code == 404
