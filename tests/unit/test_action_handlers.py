from datetime import datetime
from unittest.mock import patch

from src.actions.handlers import (
    NoActionHandler,
    NotifyHumanHandler,
    RestartHandler,
    RollbackHandler,
    ScaleUpHandler,
)
from src.actions.registry import ActionRegistry
from src.domain.decision import RemediationDecision
from src.domain.enums import ActionType, EnvironmentType, Severity
from src.domain.event import DegradationEvent


def make_event() -> DegradationEvent:
    return DegradationEvent(
        project_id="payments-api",
        environment_id=EnvironmentType.PROD,
        severity=Severity.HIGH,
        signal="P99 latency spiked",
        context=None,
        timestamp=datetime(2024, 4, 3, 14, 45, 0),
    )


def make_decision(action=ActionType.ROLLBACK) -> RemediationDecision:
    return RemediationDecision(action=action, confidence=0.9, reasoning="test reasoning", safe_to_auto=True)


def test_rollback_handler_calls_orchestrator_mock():
    with patch("src.actions.handlers.orchestrator.rollback") as mock_rollback:
        mock_rollback.return_value = {"status": "ok", "message": "Rolled back"}
        result = RollbackHandler().execute(make_event(), make_decision(ActionType.ROLLBACK), "event-1")

    mock_rollback.assert_called_once_with("payments-api")
    assert result["action"] == "rollback"
    assert result["status"] == "executed"


def test_restart_handler_calls_orchestrator_mock():
    with patch("src.actions.handlers.orchestrator.restart") as mock_restart:
        mock_restart.return_value = {"status": "ok", "message": "Restarted"}
        result = RestartHandler().execute(make_event(), make_decision(ActionType.RESTART), "event-1")

    mock_restart.assert_called_once_with("payments-api")
    assert result["action"] == "restart"
    assert result["status"] == "executed"


def test_scale_up_handler_calls_orchestrator_mock():
    with patch("src.actions.handlers.orchestrator.scale_up") as mock_scale_up:
        mock_scale_up.return_value = {"status": "ok", "message": "Scaled up"}
        result = ScaleUpHandler().execute(make_event(), make_decision(ActionType.SCALE_UP), "event-1")

    mock_scale_up.assert_called_once_with("payments-api")
    assert result["action"] == "scale_up"
    assert result["status"] == "executed"


def test_notify_human_handler_calls_notifications_mock():
    decision = make_decision(ActionType.NOTIFY_HUMAN)
    with patch("src.actions.handlers.notifications.notify_oncall") as mock_notify:
        mock_notify.return_value = {"status": "ok", "message": "On-call notified"}
        result = NotifyHumanHandler().execute(make_event(), decision, "event-1")

    mock_notify.assert_called_once_with("payments-api", "event-1", "notify_human", "test reasoning")
    assert result["action"] == "notify_human"
    assert result["status"] == "executed"


def test_no_action_handler_does_not_call_any_mock():
    result = NoActionHandler().execute(make_event(), make_decision(ActionType.NO_ACTION), "event-1")

    assert result["action"] == "no_action"
    assert result["status"] == "recorded"


def test_registry_dispatches_to_correct_handler():
    registry = ActionRegistry(
        {
            ActionType.ROLLBACK: RollbackHandler(),
            ActionType.NO_ACTION: NoActionHandler(),
        }
    )

    with patch("src.actions.handlers.orchestrator.rollback") as mock_rollback:
        mock_rollback.return_value = {"status": "ok", "message": "Rolled back"}
        result = registry.execute(ActionType.ROLLBACK, make_event(), make_decision(ActionType.ROLLBACK), "event-1")

    assert result["action"] == "rollback"


def test_registry_returns_error_for_unregistered_action():
    registry = ActionRegistry({ActionType.NO_ACTION: NoActionHandler()})

    result = registry.execute(ActionType.ROLLBACK, make_event(), make_decision(ActionType.ROLLBACK), "event-1")

    assert result["status"] == "error"
