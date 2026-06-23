from pydantic import BaseModel, ConfigDict

from src.domain.enums import ActionType


class RemediationDecision(BaseModel):
    model_config = ConfigDict(from_attributes=True, frozen=True)

    action: ActionType
    confidence: float
    reasoning: str
    safe_to_auto: bool
    executed: bool = False

    def with_safe_to_auto(self, value: bool) -> "RemediationDecision":
        return self.model_copy(update={"safe_to_auto": value})

    def with_executed(self, value: bool) -> "RemediationDecision":
        return self.model_copy(update={"executed": value})
