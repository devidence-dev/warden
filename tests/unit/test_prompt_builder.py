from datetime import datetime

from src.domain.enums import ActionType, EnvironmentType, Severity
from src.domain.event import DegradationEvent
from src.domain.history import HistoryEntry
from src.llm.prompt_builder import build


def make_event() -> DegradationEvent:
    return DegradationEvent(
        project_id="payments-api",
        environment_id=EnvironmentType.PROD,
        severity=Severity.HIGH,
        signal="P99 latency spiked",
        context={"cpu": "85%"},
        timestamp=datetime(2024, 4, 3, 14, 45, 0),
    )


def test_build_without_history_has_no_history_section():
    system_prompt, user_prompt = build(make_event(), history=[])

    assert "payments-api" in user_prompt
    assert "Recent history" not in user_prompt
    assert "Spanish" in system_prompt


def test_build_with_history_includes_outcome_and_feedback():
    history = [
        HistoryEntry(signal="cpu spike", action=ActionType.SCALE_UP, executed=True, outcome="approved", feedback="ok"),
        HistoryEntry(signal="memory leak", action=ActionType.RESTART, executed=False, outcome=None, feedback=None),
    ]

    _, user_prompt = build(make_event(), history=history)

    assert "Recent history" in user_prompt
    assert "Signal: cpu spike" in user_prompt
    assert "Outcome: approved" in user_prompt
    assert "Feedback: ok" in user_prompt
    assert "Outcome: none" in user_prompt
    assert "Feedback: none" in user_prompt
