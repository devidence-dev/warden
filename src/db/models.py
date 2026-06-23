import uuid
from datetime import UTC, datetime

from sqlalchemy import JSON, Boolean, Column, DateTime, Float, ForeignKey, String, Text
from sqlalchemy.orm import relationship

from src.db.base import Base


def generate_uuid() -> str:
    return str(uuid.uuid4())


def utcnow() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


class EventRecord(Base):
    __tablename__ = "events"

    id = Column(String, primary_key=True, default=generate_uuid)
    project_id = Column(String, nullable=False)
    environment_id = Column(String, nullable=False)
    severity = Column(String, nullable=False)
    signal = Column(Text, nullable=False)
    context = Column(JSON, nullable=True)
    timestamp = Column(DateTime, nullable=False)
    status = Column(String, default="received")
    created_at = Column(DateTime, default=utcnow)

    decision = relationship("DecisionRecord", back_populates="event", uselist=False)


class DecisionRecord(Base):
    __tablename__ = "decisions"

    id = Column(String, primary_key=True, default=generate_uuid)
    event_id = Column(String, ForeignKey("events.id"), nullable=False)
    action = Column(String, nullable=False)
    confidence = Column(Float, nullable=False)
    reasoning = Column(Text, nullable=False)
    safe_to_auto = Column(Boolean, nullable=False)
    executed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=utcnow)

    event = relationship("EventRecord", back_populates="decision")
    approval = relationship("ApprovalRequestRecord", back_populates="decision", uselist=False)


class ApprovalRequestRecord(Base):
    __tablename__ = "approval_requests"

    id = Column(String, primary_key=True, default=generate_uuid)
    decision_id = Column(String, ForeignKey("decisions.id"), nullable=False)
    status = Column(String, default="pending")
    feedback = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utcnow)
    resolved_at = Column(DateTime, nullable=True)

    decision = relationship("DecisionRecord", back_populates="approval")
