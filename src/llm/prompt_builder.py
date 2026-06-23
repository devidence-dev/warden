import json

from src.domain.event import DegradationEvent
from src.domain.history import HistoryEntry

SYSTEM_PROMPT = """You are Warden, an autonomous remediation agent for an Internal Developer Platform.
You receive degradation signals from services and must decide the best remediation action.

You must respond ONLY with a valid JSON object with this exact structure:
{
    "action": "<rollback|restart|scale_up|notify_human|no_action>",
    "confidence": <float between 0.0 and 1.0>,
    "reasoning": "<explanation of your decision>",
    "safe_to_auto": <true|false>
}

Guidelines:
- rollback: use when a recent deploy caused the issue
- restart: use when the service is unresponsive or crashing
- scale_up: use when the issue is caused by high load
- notify_human: use when the situation is unclear or too risky
- no_action: use when the signal is informational only

Always respond in Spanish.
"""


def build(event: DegradationEvent, history: list[HistoryEntry]) -> tuple[str, str]:
    user_prompt = f"""
Degradation event received:
- Project: {event.project_id}
- Environment: {event.environment_id.value}
- Severity: {event.severity.value}
- Signal: {event.signal}
- Context: {json.dumps(event.context)}
- Timestamp: {event.timestamp}
    """

    if history:
        user_prompt += "\nRecent history of related events and actions:\n"
        for entry in history:
            user_prompt += (
                f"- Signal: {entry.signal} | Action: {entry.action.value} | "
                f"Auto executed: {entry.executed} | Outcome: {entry.outcome or 'none'} | "
                f"Feedback: {entry.feedback or 'none'}\n"
            )

    return SYSTEM_PROMPT, user_prompt
