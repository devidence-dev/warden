from sqlalchemy.orm import Session

from src.db.models import DecisionRecord
from src.domain.decision import RemediationDecision


class DecisionRepository:
    def __init__(self, session: Session):
        self._session = session

    def create(self, event_id: str, decision: RemediationDecision) -> DecisionRecord:
        record = DecisionRecord(
            event_id=event_id,
            action=decision.action.value,
            confidence=decision.confidence,
            reasoning=decision.reasoning,
            safe_to_auto=decision.safe_to_auto,
            executed=decision.executed,
        )
        self._session.add(record)
        self._session.commit()
        self._session.refresh(record)
        return record

    def get(self, decision_id: str) -> DecisionRecord | None:
        return self._session.query(DecisionRecord).filter(DecisionRecord.id == decision_id).first()

    def get_by_event_id(self, event_id: str) -> DecisionRecord | None:
        return self._session.query(DecisionRecord).filter(DecisionRecord.event_id == event_id).first()

    def mark_executed(self, decision_id: str) -> None:
        record = self.get(decision_id)
        record.executed = True
        self._session.commit()
