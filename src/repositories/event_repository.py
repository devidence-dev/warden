from sqlalchemy.orm import Session

from src.db.models import EventRecord
from src.domain.event import DegradationEvent


class EventRepository:
    def __init__(self, session: Session):
        self._session = session

    def create(self, event: DegradationEvent) -> EventRecord:
        record = EventRecord(
            project_id=event.project_id,
            environment_id=event.environment_id.value,
            severity=event.severity.value,
            signal=event.signal,
            context=event.context,
            timestamp=event.timestamp,
            status="received",
        )
        self._session.add(record)
        self._session.commit()
        self._session.refresh(record)
        return record

    def get(self, event_id: str) -> EventRecord | None:
        return self._session.query(EventRecord).filter(EventRecord.id == event_id).first()

    def list(self) -> list[EventRecord]:
        return self._session.query(EventRecord).order_by(EventRecord.created_at.desc()).all()

    def list_by_project(self, project_id: str, exclude_event_id: str, limit: int) -> list[EventRecord]:
        return (
            self._session.query(EventRecord)
            .filter(EventRecord.project_id == project_id, EventRecord.id != exclude_event_id)
            .order_by(EventRecord.created_at.desc())
            .limit(limit)
            .all()
        )

    def mark_status(self, event_id: str, status: str) -> None:
        record = self.get(event_id)
        record.status = status
        self._session.commit()
