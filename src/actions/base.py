from typing import Protocol, TypedDict

from src.domain.decision import RemediationDecision
from src.domain.event import DegradationEvent


class ActionResult(TypedDict):
    action: str
    status: str
    detail: str


class ActionHandler(Protocol):
    def execute(self, event: DegradationEvent, decision: RemediationDecision, event_id: str) -> ActionResult: ...
