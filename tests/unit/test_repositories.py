from datetime import datetime

from src.domain.decision import RemediationDecision
from src.domain.enums import ActionType, EnvironmentType, Severity
from src.domain.event import DegradationEvent
from src.repositories.approval_repository import ApprovalRepository
from src.repositories.decision_repository import DecisionRepository
from src.repositories.event_repository import EventRepository


def make_event() -> DegradationEvent:
    return DegradationEvent(
        project_id="payments-api",
        environment_id=EnvironmentType.PROD,
        severity=Severity.HIGH,
        signal="P99 latency spiked",
        context={"cpu": "85%"},
        timestamp=datetime(2024, 4, 3, 14, 45, 0),
    )


def test_event_repository_create_and_get(db_session):
    repo = EventRepository(db_session)
    record = repo.create(make_event())

    fetched = repo.get(record.id)
    assert fetched is not None
    assert fetched.project_id == "payments-api"
    assert fetched.status == "received"


def test_event_repository_list_by_project_excludes_current_and_respects_limit(db_session):
    repo = EventRepository(db_session)
    current = repo.create(make_event())
    older = [repo.create(make_event()) for _ in range(3)]

    history = repo.list_by_project("payments-api", current.id, limit=2)

    assert current.id not in [e.id for e in history]
    assert len(history) == 2
    assert all(e.id in [o.id for o in older] for e in history)


def test_event_repository_mark_status(db_session):
    repo = EventRepository(db_session)
    record = repo.create(make_event())

    repo.mark_status(record.id, "processed")

    assert repo.get(record.id).status == "processed"


def test_decision_repository_create_and_get_by_event_id(db_session):
    event_repo = EventRepository(db_session)
    decision_repo = DecisionRepository(db_session)
    event = event_repo.create(make_event())

    decision = RemediationDecision(
        action=ActionType.ROLLBACK, confidence=0.9, reasoning="deploy", safe_to_auto=False
    )
    record = decision_repo.create(event.id, decision)

    fetched = decision_repo.get_by_event_id(event.id)
    assert fetched.id == record.id
    assert fetched.action == "rollback"
    assert fetched.executed is False


def test_decision_repository_mark_executed(db_session):
    event_repo = EventRepository(db_session)
    decision_repo = DecisionRepository(db_session)
    event = event_repo.create(make_event())
    decision = RemediationDecision(
        action=ActionType.RESTART, confidence=0.9, reasoning="unresponsive", safe_to_auto=True
    )
    record = decision_repo.create(event.id, decision)

    decision_repo.mark_executed(record.id)

    assert decision_repo.get(record.id).executed is True


def test_approval_repository_create_resolve_and_list_pending(db_session):
    event_repo = EventRepository(db_session)
    decision_repo = DecisionRepository(db_session)
    approval_repo = ApprovalRepository(db_session)
    event = event_repo.create(make_event())
    decision = decision_repo.create(
        event.id,
        RemediationDecision(action=ActionType.NOTIFY_HUMAN, confidence=0.5, reasoning="unclear", safe_to_auto=False),
    )

    approval = approval_repo.create(decision.id)
    assert approval_repo.list_pending() == [approval]

    resolved = approval_repo.resolve(approval, "approved", "Looks fine")
    assert resolved.status == "approved"
    assert resolved.feedback == "Looks fine"
    assert resolved.resolved_at is not None
    assert approval_repo.list_pending() == []
    assert approval_repo.get_by_decision_id(decision.id).id == approval.id
