import json
import logging
from dataclasses import dataclass

from src.actions.base import ActionResult
from src.actions.registry import ActionRegistry
from src.db.models import ApprovalRequestRecord
from src.domain.decision import RemediationDecision
from src.domain.event import DegradationEvent
from src.repositories.approval_repository import ApprovalRepository
from src.repositories.decision_repository import DecisionRepository
from src.repositories.event_repository import EventRepository
from src.services.exceptions import ApprovalAlreadyResolvedError, ApprovalNotFoundError

logger = logging.getLogger(__name__)

DEFAULT_APPROVE_FEEDBACK = "Human approved the action"
DEFAULT_REJECT_FEEDBACK = "Human rejected the action"


@dataclass(frozen=True)
class ApprovalResult:
    approval_id: str
    status: str
    result: ActionResult | None = None


class ApprovalService:
    def __init__(
        self,
        approval_repo: ApprovalRepository,
        decision_repo: DecisionRepository,
        event_repo: EventRepository,
        action_registry: ActionRegistry,
    ):
        self._approval_repo = approval_repo
        self._decision_repo = decision_repo
        self._event_repo = event_repo
        self._action_registry = action_registry

    def approve(self, approval_id: str, feedback: str | None) -> ApprovalResult:
        approval = self._get_pending_approval(approval_id)
        decision_record = self._decision_repo.get(approval.decision_id)
        event_record = self._event_repo.get(decision_record.event_id)

        event = DegradationEvent.model_validate(event_record)
        decision = RemediationDecision.model_validate(decision_record)

        result = self._action_registry.execute(decision.action, event, decision, event_record.id)
        self._decision_repo.mark_executed(decision_record.id)
        self._approval_repo.resolve(approval, "approved", feedback or DEFAULT_APPROVE_FEEDBACK)

        logger.info(
            json.dumps(
                {
                    "event": "approval_resolved",
                    "approval_id": approval_id,
                    "status": "approved",
                    "action": decision.action.value,
                }
            )
        )
        return ApprovalResult(approval_id=approval_id, status="approved", result=result)

    def reject(self, approval_id: str, feedback: str | None) -> ApprovalResult:
        approval = self._get_pending_approval(approval_id)
        self._approval_repo.resolve(approval, "rejected", feedback or DEFAULT_REJECT_FEEDBACK)

        logger.info(json.dumps({"event": "approval_resolved", "approval_id": approval_id, "status": "rejected"}))
        return ApprovalResult(approval_id=approval_id, status="rejected")

    def _get_pending_approval(self, approval_id: str) -> ApprovalRequestRecord:
        approval = self._approval_repo.get(approval_id)
        if not approval:
            raise ApprovalNotFoundError(approval_id)
        if approval.status != "pending":
            raise ApprovalAlreadyResolvedError(approval.status)
        return approval
