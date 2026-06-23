import json
import logging
from abc import ABC, abstractmethod

from src.domain.decision import RemediationDecision
from src.domain.enums import ActionType, EnvironmentType, Severity
from src.domain.event import DegradationEvent

logger = logging.getLogger(__name__)


class SafetyRule(ABC):
    @abstractmethod
    def applies(self, event: DegradationEvent, decision: RemediationDecision) -> str | None: ...


class CriticalSeverityRule(SafetyRule):
    def applies(self, event: DegradationEvent, decision: RemediationDecision) -> str | None:
        if event.severity == Severity.CRITICAL:
            return "Critical severity requires human review."
        return None


class LowConfidenceRule(SafetyRule):
    def __init__(self, threshold: float = 0.7):
        self._threshold = threshold

    def applies(self, event: DegradationEvent, decision: RemediationDecision) -> str | None:
        if decision.confidence < self._threshold:
            return f"Confidence below {self._threshold}"
        return None


class ProdDisruptiveActionRule(SafetyRule):
    def __init__(self, disruptive_actions: frozenset[ActionType] = frozenset({ActionType.ROLLBACK, ActionType.SCALE_UP})):
        self._disruptive_actions = disruptive_actions

    def applies(self, event: DegradationEvent, decision: RemediationDecision) -> str | None:
        if event.environment_id == EnvironmentType.PROD and decision.action in self._disruptive_actions:
            return "Production environment requires human review for disruptive actions."
        return None


class SafetyPolicy:
    def __init__(self, rules: list[SafetyRule]):
        self._rules = rules

    def apply(self, event: DegradationEvent, decision: RemediationDecision) -> RemediationDecision:
        reasons = [reason for rule in self._rules if (reason := rule.applies(event, decision))]

        if not reasons:
            return decision

        logger.info(json.dumps({"event": "restriction_applied", "reasons": reasons, "safe_to_auto": False}))
        return decision.with_safe_to_auto(False)
