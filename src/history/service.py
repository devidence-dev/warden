from src.domain.enums import ActionType
from src.domain.history import HistoryEntry
from src.repositories.approval_repository import ApprovalRepository
from src.repositories.decision_repository import DecisionRepository
from src.repositories.event_repository import EventRepository


class HistoryService:
    def __init__(
        self,
        event_repo: EventRepository,
        decision_repo: DecisionRepository,
        approval_repo: ApprovalRepository,
        default_limit: int,
    ):
        self._event_repo = event_repo
        self._decision_repo = decision_repo
        self._approval_repo = approval_repo
        self._default_limit = default_limit

    def get_recent(self, project_id: str, exclude_event_id: str, limit: int | None = None) -> list[HistoryEntry]:
        events = self._event_repo.list_by_project(project_id, exclude_event_id, limit or self._default_limit)

        entries = []
        for event in events:
            decision = self._decision_repo.get_by_event_id(event.id)
            if not decision:
                continue

            approval = self._approval_repo.get_by_decision_id(decision.id)
            entries.append(
                HistoryEntry(
                    signal=event.signal,
                    action=ActionType(decision.action),
                    executed=decision.executed,
                    outcome=approval.status if approval else None,
                    feedback=approval.feedback if approval else None,
                )
            )
        return entries
