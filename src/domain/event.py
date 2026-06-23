from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict

from src.domain.enums import EnvironmentType, Severity


class DegradationEvent(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    project_id: str
    environment_id: EnvironmentType
    severity: Severity
    signal: str
    context: Optional[dict[str, Any]] = None
    timestamp: datetime
