import json

from src.domain.enums import ActionType
from src.llm.response_parser import parse


def test_parse_valid_response():
    raw = json.dumps(
        {
            "action": "rollback",
            "confidence": 0.85,
            "reasoning": "Recent deploy caused latency spike.",
            "safe_to_auto": False,
        }
    )

    decision = parse(raw)

    assert decision.action == ActionType.ROLLBACK
    assert decision.confidence == 0.85
    assert decision.safe_to_auto is False


def test_parse_unknown_action_falls_back_to_notify_human():
    raw = json.dumps(
        {"action": "reboot_the_world", "confidence": 0.9, "reasoning": "test", "safe_to_auto": True}
    )

    decision = parse(raw)

    assert decision.action == ActionType.NOTIFY_HUMAN


def test_parse_invalid_json_falls_back_to_notify_human():
    decision = parse("not valid json")

    assert decision.action == ActionType.NOTIFY_HUMAN
    assert decision.safe_to_auto is False
    assert decision.confidence == 1.0


def test_parse_missing_fields_falls_back_to_notify_human():
    decision = parse(json.dumps({"action": "rollback"}))

    assert decision.action == ActionType.NOTIFY_HUMAN
