import json
import logging
from dataclasses import dataclass

from mocks import notifications
from src.actions.registry import ActionRegistry
from src.domain.decision import RemediationDecision
from src.domain.event import DegradationEvent
from src.reasoning.engine import ReasoningEngine
from src.repositories.approval_repository import ApprovalRepository
from src.repositories.decision_repository import DecisionRepository
from src.repositories.event_repository import EventRepository

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class IngestResult:
    event_id: str
    status: str
    decision: RemediationDecision
    approval_id: str | None = None


class EventIngestionService:
    def __init__(
        self,
        event_repo: EventRepository,
        decision_repo: DecisionRepository,
        approval_repo: ApprovalRepository,
        engine: ReasoningEngine,
        action_registry: ActionRegistry,
    ):
        self._event_repo = event_repo
        self._decision_repo = decision_repo
        self._approval_repo = approval_repo
        self._engine = engine
        self._action_registry = action_registry

    def ingest(self, payload: DegradationEvent) -> IngestResult:
        event_record = self._event_repo.create(payload)
        logger.info(
            json.dumps(
                {
                    "event": "event_received",
                    "event_id": event_record.id,
                    "project_id": event_record.project_id,
                    "severity": event_record.severity,
                }
            )
        )

        decision = self._engine.decide(payload, event_record.id)
        decision_record = self._decision_repo.create(event_record.id, decision)

        if decision.safe_to_auto:
            self._action_registry.execute(decision.action, payload, decision, event_record.id)
            self._decision_repo.mark_executed(decision_record.id)
            self._event_repo.mark_status(event_record.id, "processed")
            return IngestResult(event_id=event_record.id, status="processed", decision=decision)

        approval_record = self._approval_repo.create(decision_record.id)
        self._event_repo.mark_status(event_record.id, "pending_approval")
        notifications.notify_oncall(payload.project_id, event_record.id, decision.action.value, decision.reasoning)
        logger.info(
            json.dumps(
                {
                    "event": "approval_request_created",
                    "approval_id": approval_record.id,
                    "event_id": event_record.id,
                    "action": decision.action.value,
                }
            )
        )
        return IngestResult(
            event_id=event_record.id,
            status="pending_approval",
            decision=decision,
            approval_id=approval_record.id,
        )
