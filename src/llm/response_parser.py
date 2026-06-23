import json

from src.domain.decision import RemediationDecision
from src.domain.enums import ActionType

_FALLBACK_REASON = "Error parsing reasoning response, defaulting to notify_human."


def parse(raw: str) -> RemediationDecision:
    try:
        data = json.loads(raw)
        action = data["action"]
        if action not in ActionType._value2member_map_:
            action = ActionType.NOTIFY_HUMAN.value

        return RemediationDecision(
            action=ActionType(action),
            confidence=float(data["confidence"]),
            reasoning=data["reasoning"],
            safe_to_auto=bool(data["safe_to_auto"]),
        )
    except (json.JSONDecodeError, KeyError, TypeError, ValueError):
        return RemediationDecision(
            action=ActionType.NOTIFY_HUMAN,
            confidence=1.0,
            reasoning=_FALLBACK_REASON,
            safe_to_auto=False,
        )
