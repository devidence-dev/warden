from datetime import datetime

from src.domain.decision import RemediationDecision
from src.domain.enums import ActionType, EnvironmentType, Severity
from src.domain.event import DegradationEvent
from src.policies.safety_policy import (
    CriticalSeverityRule,
    LowConfidenceRule,
    ProdDisruptiveActionRule,
    SafetyPolicy,
)


def make_event(severity=Severity.HIGH, environment_id=EnvironmentType.PROD) -> DegradationEvent:
    return DegradationEvent(
        project_id="payments-api",
        environment_id=environment_id,
        severity=severity,
        signal="signal",
        context=None,
        timestamp=datetime(2024, 4, 3, 14, 45, 0),
    )


def make_decision(action=ActionType.RESTART, confidence=0.9, safe_to_auto=True) -> RemediationDecision:
    return RemediationDecision(action=action, confidence=confidence, reasoning="test", safe_to_auto=safe_to_auto)


def make_policy() -> SafetyPolicy:
    return SafetyPolicy([CriticalSeverityRule(), LowConfidenceRule(0.7), ProdDisruptiveActionRule()])


def test_critical_severity_forces_safe_to_auto_false():
    event = make_event(severity=Severity.CRITICAL)
    decision = make_decision()

    result = make_policy().apply(event, decision)

    assert result.safe_to_auto is False


def test_low_confidence_forces_safe_to_auto_false():
    event = make_event(severity=Severity.LOW)
    decision = make_decision(confidence=0.5)

    result = make_policy().apply(event, decision)

    assert result.safe_to_auto is False


def test_prod_rollback_forces_safe_to_auto_false():
    event = make_event(severity=Severity.HIGH, environment_id=EnvironmentType.PROD)
    decision = make_decision(action=ActionType.ROLLBACK)

    result = make_policy().apply(event, decision)

    assert result.safe_to_auto is False


def test_prod_scale_up_forces_safe_to_auto_false():
    event = make_event(severity=Severity.HIGH, environment_id=EnvironmentType.PROD)
    decision = make_decision(action=ActionType.SCALE_UP)

    result = make_policy().apply(event, decision)

    assert result.safe_to_auto is False


def test_dev_restart_high_confidence_stays_safe_to_auto_true():
    event = make_event(severity=Severity.HIGH, environment_id=EnvironmentType.DEV)
    decision = make_decision(action=ActionType.RESTART, confidence=0.9, safe_to_auto=True)

    result = make_policy().apply(event, decision)

    assert result.safe_to_auto is True


def test_apply_does_not_mutate_original_decision():
    event = make_event(severity=Severity.CRITICAL)
    decision = make_decision(safe_to_auto=True)

    make_policy().apply(event, decision)

    assert decision.safe_to_auto is True
