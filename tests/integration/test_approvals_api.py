import json
from unittest.mock import patch

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


def _create_pending_approval(client) -> dict:
    app.dependency_overrides[get_reasoning_provider] = lambda: FakeProvider(
        json.dumps({"action": "rollback", "confidence": 0.5, "reasoning": "uncertain", "safe_to_auto": True})
    )
    response = client.post("/events/", json=VALID_PAYLOAD)
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "pending_approval"
    return body


def test_list_approvals_returns_pending_request(client):
    body = _create_pending_approval(client)

    response = client.get("/approvals/")

    assert response.status_code == 200
    assert any(a["id"] == body["approval_id"] for a in response.json())


def test_approve_executes_action_and_records_free_text_feedback(client):
    body = _create_pending_approval(client)
    approval_id = body["approval_id"]

    with patch("src.actions.handlers.orchestrator.rollback") as mock_rollback:
        mock_rollback.return_value = {"status": "ok", "message": "Rolled back"}
        response = client.post(f"/approvals/{approval_id}/approve", json={"feedback": "Looks safe, go ahead"})

    assert response.status_code == 200
    assert response.json()["status"] == "approved"
    mock_rollback.assert_called_once_with("payments-api")

    event_response = client.get(f"/events/{body['event_id']}")
    assert event_response.json()["status"] == "processed"
    assert event_response.json()["decision"]["safe_to_auto"] is False


def test_approve_already_resolved_approval_returns_400(client):
    body = _create_pending_approval(client)
    approval_id = body["approval_id"]

    with patch("src.actions.handlers.orchestrator.rollback") as mock_rollback:
        mock_rollback.return_value = {"status": "ok", "message": "Rolled back"}
        client.post(f"/approvals/{approval_id}/approve")
        second_response = client.post(f"/approvals/{approval_id}/approve")

    assert second_response.status_code == 400


def test_reject_marks_as_rejected_without_executing_action(client):
    body = _create_pending_approval(client)
    approval_id = body["approval_id"]

    with patch("src.actions.handlers.orchestrator.rollback") as mock_rollback:
        response = client.post(f"/approvals/{approval_id}/reject", json={"feedback": "Too risky"})
        mock_rollback.assert_not_called()

    assert response.status_code == 200
    assert response.json()["status"] == "rejected"

    event_response = client.get(f"/events/{body['event_id']}")
    assert event_response.json()["status"] == "rejected"


def test_approve_unknown_approval_returns_404(client):
    response = client.post("/approvals/does-not-exist/approve")
    assert response.status_code == 404


def test_reject_unknown_approval_returns_404(client):
    response = client.post("/approvals/does-not-exist/reject")
    assert response.status_code == 404
