from sqlalchemy.orm import Session

from src.db.models import ApprovalRequestRecord, utcnow


class ApprovalRepository:
    def __init__(self, session: Session):
        self._session = session

    def create(self, decision_id: str) -> ApprovalRequestRecord:
        record = ApprovalRequestRecord(decision_id=decision_id, status="pending")
        self._session.add(record)
        self._session.commit()
        self._session.refresh(record)
        return record

    def get(self, approval_id: str) -> ApprovalRequestRecord | None:
        return self._session.query(ApprovalRequestRecord).filter(ApprovalRequestRecord.id == approval_id).first()

    def get_by_decision_id(self, decision_id: str) -> ApprovalRequestRecord | None:
        return (
            self._session.query(ApprovalRequestRecord)
            .filter(ApprovalRequestRecord.decision_id == decision_id)
            .first()
        )

    def list_pending(self) -> list[ApprovalRequestRecord]:
        return (
            self._session.query(ApprovalRequestRecord)
            .filter(ApprovalRequestRecord.status == "pending")
            .order_by(ApprovalRequestRecord.created_at.desc())
            .all()
        )

    def resolve(self, approval: ApprovalRequestRecord, status: str, feedback: str | None) -> ApprovalRequestRecord:
        approval.status = status
        approval.feedback = feedback
        approval.resolved_at = utcnow()
        self._session.commit()
        self._session.refresh(approval)
        return approval
