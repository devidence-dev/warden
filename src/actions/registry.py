import json
import logging

from src.actions.base import ActionHandler, ActionResult
from src.domain.decision import RemediationDecision
from src.domain.enums import ActionType
from src.domain.event import DegradationEvent

logger = logging.getLogger(__name__)


class ActionRegistry:
    def __init__(self, handlers: dict[ActionType, ActionHandler]):
        self._handlers = handlers

    def execute(
        self, action: ActionType, event: DegradationEvent, decision: RemediationDecision, event_id: str
    ) -> ActionResult:
        handler = self._handlers.get(action)
        if not handler:
            logger.error(json.dumps({"event": "action_not_found", "action": action, "detail": "Unknown action"}))
            return {
                "action": str(action),
                "status": "error",
                "detail": f"Action '{action}' not found for event {event_id} in project {event.project_id}.",
            }
        return handler.execute(event, decision, event_id)
