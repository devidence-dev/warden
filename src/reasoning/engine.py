import json
import logging
from typing import Callable

from src.domain.decision import RemediationDecision
from src.domain.enums import ActionType
from src.domain.event import DegradationEvent
from src.domain.history import HistoryEntry
from src.history.service import HistoryService
from src.llm.provider import ReasoningProvider
from src.policies.safety_policy import SafetyPolicy

logger = logging.getLogger(__name__)

PromptBuilder = Callable[[DegradationEvent, list[HistoryEntry]], tuple[str, str]]
ResponseParser = Callable[[str], RemediationDecision]

_FALLBACK_REASON = "Error during reasoning, defaulting to notify_human."


class ReasoningEngine:
    def __init__(
        self,
        provider: ReasoningProvider,
        prompt_builder: PromptBuilder,
        response_parser: ResponseParser,
        safety_policy: SafetyPolicy,
        history_service: HistoryService,
    ):
        self._provider = provider
        self._prompt_builder = prompt_builder
        self._response_parser = response_parser
        self._safety_policy = safety_policy
        self._history_service = history_service

    def decide(self, event: DegradationEvent, event_id: str) -> RemediationDecision:
        history = self._history_service.get_recent(event.project_id, event_id)
        system_prompt, user_prompt = self._prompt_builder(event, history)

        try:
            raw = self._provider.complete(system_prompt, user_prompt)
            logger.info(json.dumps({"event": "llm_response", "raw": raw}))
            decision = self._response_parser(raw)
        except Exception as exc:
            logger.error(json.dumps({"event": "reasoning_error", "event_id": event_id, "error": str(exc)}))
            decision = RemediationDecision(
                action=ActionType.NOTIFY_HUMAN,
                confidence=1.0,
                reasoning=_FALLBACK_REASON,
                safe_to_auto=False,
            )

        decision = self._safety_policy.apply(event, decision)

        logger.info(
            json.dumps(
                {
                    "event": "decision_created",
                    "event_id": event_id,
                    "action": decision.action.value,
                    "confidence": decision.confidence,
                    "safe_to_auto": decision.safe_to_auto,
                    "history_used": len(history) > 0,
                }
            )
        )
        return decision
