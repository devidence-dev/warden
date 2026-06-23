import json
from datetime import datetime

from src.domain.enums import EnvironmentType, Severity
from src.domain.event import DegradationEvent
from src.history.service import HistoryService
from src.llm.prompt_builder import build as build_prompt
from src.llm.response_parser import parse as parse_response
from src.policies.safety_policy import CriticalSeverityRule, LowConfidenceRule, ProdDisruptiveActionRule, SafetyPolicy
from src.reasoning.engine import ReasoningEngine
from src.repositories.approval_repository import ApprovalRepository
from src.repositories.decision_repository import DecisionRepository
from src.repositories.event_repository import EventRepository


class FakeReasoningProvider:
    def __init__(self, response: str):
        self._response = response

    def complete(self, system_prompt: str, user_prompt: str) -> str:
        return self._response


class RaisingReasoningProvider:
    def complete(self, system_prompt: str, user_prompt: str) -> str:
        raise RuntimeError("LLM unavailable")


def make_event() -> DegradationEvent:
    return DegradationEvent(
        project_id="payments-api",
        environment_id=EnvironmentType.DEV,
        severity=Severity.LOW,
        signal="P99 latency spiked",
        context=None,
        timestamp=datetime(2024, 4, 3, 14, 45, 0),
    )


def make_engine(db_session, provider) -> ReasoningEngine:
    history_service = HistoryService(
        EventRepository(db_session), DecisionRepository(db_session), ApprovalRepository(db_session), default_limit=5
    )
    safety_policy = SafetyPolicy([CriticalSeverityRule(), LowConfidenceRule(0.7), ProdDisruptiveActionRule()])
    return ReasoningEngine(provider, build_prompt, parse_response, safety_policy, history_service)


def test_decide_returns_safe_to_auto_decision_on_high_confidence(db_session):
    provider = FakeReasoningProvider(
        json.dumps({"action": "restart", "confidence": 0.95, "reasoning": "unresponsive", "safe_to_auto": True})
    )
    engine = make_engine(db_session, provider)

    decision = engine.decide(make_event(), "event-1")

    assert decision.action.value == "restart"
    assert decision.safe_to_auto is True


def test_decide_applies_safety_policy_after_parsing(db_session):
    provider = FakeReasoningProvider(
        json.dumps({"action": "rollback", "confidence": 0.95, "reasoning": "bad deploy", "safe_to_auto": True})
    )
    engine = make_engine(db_session, provider)
    event = DegradationEvent(
        project_id="payments-api",
        environment_id=EnvironmentType.PROD,
        severity=Severity.HIGH,
        signal="bad deploy",
        context=None,
        timestamp=datetime(2024, 4, 3, 14, 45, 0),
    )

    decision = engine.decide(event, "event-1")

    assert decision.action.value == "rollback"
    assert decision.safe_to_auto is False


def test_decide_falls_back_to_notify_human_when_provider_raises(db_session):
    engine = make_engine(db_session, RaisingReasoningProvider())

    decision = engine.decide(make_event(), "event-1")

    assert decision.action.value == "notify_human"
    assert decision.safe_to_auto is False
