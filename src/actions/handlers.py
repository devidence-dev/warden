import json
import logging
from abc import ABC, abstractmethod

from mocks import notifications, orchestrator
from src.actions.base import ActionResult
from src.domain.decision import RemediationDecision
from src.domain.event import DegradationEvent

logger = logging.getLogger(__name__)


class BaseActionHandler(ABC):
    def execute(self, event: DegradationEvent, decision: RemediationDecision, event_id: str) -> ActionResult:
        result = self._call_mock(event, decision, event_id)
        self._log_execution(event_id, event.project_id, result)
        return result

    @abstractmethod
    def _call_mock(self, event: DegradationEvent, decision: RemediationDecision, event_id: str) -> ActionResult: ...

    def _log_execution(self, event_id: str, project_id: str, result: ActionResult) -> None:
        logger.info(
            json.dumps(
                {
                    "event": "action_executed",
                    "action": result["action"],
                    "event_id": event_id,
                    "project_id": project_id,
                    "status": result["status"],
                }
            )
        )


class RollbackHandler(BaseActionHandler):
    def _call_mock(self, event: DegradationEvent, decision: RemediationDecision, event_id: str) -> ActionResult:
        mock_result = orchestrator.rollback(event.project_id)
        return {
            "action": "rollback",
            "status": "executed",
            "detail": f"Rollback executed for event {event_id} in project {event.project_id}. {mock_result['message']}",
        }


class RestartHandler(BaseActionHandler):
    def _call_mock(self, event: DegradationEvent, decision: RemediationDecision, event_id: str) -> ActionResult:
        mock_result = orchestrator.restart(event.project_id)
        return {
            "action": "restart",
            "status": "executed",
            "detail": f"Restart executed for event {event_id} in project {event.project_id}. {mock_result['message']}",
        }


class ScaleUpHandler(BaseActionHandler):
    def _call_mock(self, event: DegradationEvent, decision: RemediationDecision, event_id: str) -> ActionResult:
        mock_result = orchestrator.scale_up(event.project_id)
        return {
            "action": "scale_up",
            "status": "executed",
            "detail": f"Scale up executed for event {event_id} in project {event.project_id}. {mock_result['message']}",
        }


class NotifyHumanHandler(BaseActionHandler):
    def _call_mock(self, event: DegradationEvent, decision: RemediationDecision, event_id: str) -> ActionResult:
        mock_result = notifications.notify_oncall(event.project_id, event_id, decision.action.value, decision.reasoning)
        return {
            "action": "notify_human",
            "status": "executed",
            "detail": f"Human notified for event {event_id} in project {event.project_id}. {mock_result['message']}",
        }


class NoActionHandler(BaseActionHandler):
    def _call_mock(self, event: DegradationEvent, decision: RemediationDecision, event_id: str) -> ActionResult:
        return {
            "action": "no_action",
            "status": "recorded",
            "detail": f"No action taken for event {event_id} in project {event.project_id}.",
        }
