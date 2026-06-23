from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict


class DecisionDTO(BaseModel):
    action: str
    confidence: float
    reasoning: str
    safe_to_auto: bool


class IngestResponse(BaseModel):
    event_id: str
    status: str
    decision: DecisionDTO
    approval_id: Optional[str] = None


class DecisionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    action: str
    confidence: float
    reasoning: str
    safe_to_auto: bool
    executed: bool


class EventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    project_id: str
    environment_id: str
    severity: str
    signal: str
    context: Optional[dict[str, Any]] = None
    timestamp: datetime
    status: str
    created_at: datetime


class EventDetailResponse(EventResponse):
    decision: Optional[DecisionResponse] = None


class ApprovalResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    decision_id: str
    status: str
    feedback: Optional[str] = None
    created_at: datetime
    resolved_at: Optional[datetime] = None


class ApprovalActionRequest(BaseModel):
    feedback: Optional[str] = None


class ApprovalActionResponse(BaseModel):
    approval_id: str
    status: str
    result: Optional[dict[str, Any]] = None
