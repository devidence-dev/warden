from datetime import datetime

from src.domain.decision import RemediationDecision
from src.domain.enums import ActionType, EnvironmentType, Severity
from src.domain.event import DegradationEvent
from src.history.service import HistoryService
from src.repositories.approval_repository import ApprovalRepository
from src.repositories.decision_repository import DecisionRepository
from src.repositories.event_repository import EventRepository


def make_event(signal="signal") -> DegradationEvent:
    return DegradationEvent(
        project_id="payments-api",
        environment_id=EnvironmentType.PROD,
        severity=Severity.HIGH,
        signal=signal,
        context=None,
        timestamp=datetime(2024, 4, 3, 14, 45, 0),
    )


def make_service(db_session) -> tuple[HistoryService, EventRepository, DecisionRepository, ApprovalRepository]:
    event_repo = EventRepository(db_session)
    decision_repo = DecisionRepository(db_session)
    approval_repo = ApprovalRepository(db_session)
    service = HistoryService(event_repo, decision_repo, approval_repo, default_limit=5)
    return service, event_repo, decision_repo, approval_repo


def test_no_history_returns_empty_list(db_session):
    service, event_repo, _, _ = make_service(db_session)
    current = event_repo.create(make_event())

    history = service.get_recent("payments-api", current.id)

    assert history == []


def test_events_without_decision_are_skipped(db_session):
    service, event_repo, _, _ = make_service(db_session)
    current = event_repo.create(make_event())
    event_repo.create(make_event("no decision yet"))

    history = service.get_recent("payments-api", current.id)

    assert history == []


def test_history_includes_outcome_and_feedback_when_resolved(db_session):
    service, event_repo, decision_repo, approval_repo = make_service(db_session)
    current = event_repo.create(make_event())
    past_event = event_repo.create(make_event("cpu spike"))
    decision = decision_repo.create(
        past_event.id,
        RemediationDecision(action=ActionType.SCALE_UP, confidence=0.6, reasoning="high load", safe_to_auto=False),
    )
    approval = approval_repo.create(decision.id)
    approval_repo.resolve(approval, "approved", "Looks good, go ahead")

    history = service.get_recent("payments-api", current.id)

    assert len(history) == 1
    entry = history[0]
    assert entry.signal == "cpu spike"
    assert entry.action == ActionType.SCALE_UP
    assert entry.outcome == "approved"
    assert entry.feedback == "Looks good, go ahead"


def test_history_without_approval_has_no_outcome_or_feedback(db_session):
    service, event_repo, decision_repo, _ = make_service(db_session)
    current = event_repo.create(make_event())
    past_event = event_repo.create(make_event("auto resolved"))
    decision_repo.create(
        past_event.id,
        RemediationDecision(action=ActionType.RESTART, confidence=0.95, reasoning="unresponsive", safe_to_auto=True),
    )

    history = service.get_recent("payments-api", current.id)

    assert len(history) == 1
    assert history[0].outcome is None
    assert history[0].feedback is None


def test_history_respects_limit(db_session):
    service, event_repo, decision_repo, _ = make_service(db_session)
    current = event_repo.create(make_event())
    for i in range(4):
        past_event = event_repo.create(make_event(f"signal-{i}"))
        decision_repo.create(
            past_event.id,
            RemediationDecision(action=ActionType.NO_ACTION, confidence=1.0, reasoning="informational", safe_to_auto=True),
        )

    history = service.get_recent("payments-api", current.id, limit=2)

    assert len(history) == 2
