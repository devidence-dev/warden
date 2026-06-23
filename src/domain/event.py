from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict

from src.domain.enums import EnvironmentType, Severity


class DegradationEvent(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "project_id": "payments-api",
                "environment_id": "prod",
                "severity": "high",
                "signal": "P99 latency spiked to 4s after the 14:30 deploy",
                "context": {"last_deploy": "v2.3.1", "cpu_usage": "85%", "error_rate": "12%"},
                "timestamp": "2024-04-03T14:45:00Z",
            }
        },
    )

    project_id: str
    environment_id: EnvironmentType
    severity: Severity
    signal: str
    context: Optional[dict[str, Any]] = None
    timestamp: datetime
