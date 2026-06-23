from typing import Optional

from pydantic import BaseModel

from src.domain.enums import ActionType


class HistoryEntry(BaseModel):
    signal: str
    action: ActionType
    executed: bool
    outcome: Optional[str] = None
    feedback: Optional[str] = None
