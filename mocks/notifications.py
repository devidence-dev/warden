import json
import logging

logger = logging.getLogger(__name__)


def notify_oncall(project_id: str, event_id: str, action: str, reasoning: str):
    logger.info(
        json.dumps(
            {
                "mock": "notifications",
                "channel": "oncall",
                "project_id": project_id,
                "event_id": event_id,
                "action": action,
                "reasoning": reasoning,
            }
        )
    )
    return {"status": "ok", "message": f"On-call notified for {project_id}"}
