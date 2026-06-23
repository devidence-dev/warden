from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from src.actions.handlers import NoActionHandler, NotifyHumanHandler, RestartHandler, RollbackHandler, ScaleUpHandler
from src.actions.registry import ActionRegistry
from src.config import Settings, get_settings
from src.db.base import get_db
from src.domain.enums import ActionType
from src.history.service import HistoryService
from src.llm import prompt_builder, response_parser
from src.llm.groq_provider import GroqProvider
from src.llm.provider import ReasoningProvider
from src.policies.safety_policy import CriticalSeverityRule, LowConfidenceRule, ProdDisruptiveActionRule, SafetyPolicy
from src.reasoning.engine import ReasoningEngine
from src.repositories.approval_repository import ApprovalRepository
from src.repositories.decision_repository import DecisionRepository
from src.repositories.event_repository import EventRepository
from src.services.approval_service import ApprovalService
from src.services.event_service import EventIngestionService

SettingsDep = Annotated[Settings, Depends(get_settings)]


def get_event_repository(db: Session = Depends(get_db)) -> EventRepository:
    return EventRepository(db)


def get_decision_repository(db: Session = Depends(get_db)) -> DecisionRepository:
    return DecisionRepository(db)


def get_approval_repository(db: Session = Depends(get_db)) -> ApprovalRepository:
    return ApprovalRepository(db)


def get_history_service(
    settings: SettingsDep,
    event_repo: EventRepository = Depends(get_event_repository),
    decision_repo: DecisionRepository = Depends(get_decision_repository),
    approval_repo: ApprovalRepository = Depends(get_approval_repository),
) -> HistoryService:
    return HistoryService(event_repo, decision_repo, approval_repo, settings.history_limit)


def get_reasoning_provider(settings: SettingsDep) -> ReasoningProvider:
    return GroqProvider(api_key=settings.groq_api_key, model=settings.groq_model)


def get_safety_policy(settings: SettingsDep) -> SafetyPolicy:
    disruptive_actions = frozenset(ActionType(action) for action in settings.disruptive_actions)
    return SafetyPolicy(
        [
            CriticalSeverityRule(),
            LowConfidenceRule(settings.low_confidence_threshold),
            ProdDisruptiveActionRule(disruptive_actions),
        ]
    )


def get_reasoning_engine(
    provider: ReasoningProvider = Depends(get_reasoning_provider),
    safety_policy: SafetyPolicy = Depends(get_safety_policy),
    history_service: HistoryService = Depends(get_history_service),
) -> ReasoningEngine:
    return ReasoningEngine(provider, prompt_builder.build, response_parser.parse, safety_policy, history_service)


def get_action_registry() -> ActionRegistry:
    return ActionRegistry(
        {
            ActionType.ROLLBACK: RollbackHandler(),
            ActionType.RESTART: RestartHandler(),
            ActionType.SCALE_UP: ScaleUpHandler(),
            ActionType.NOTIFY_HUMAN: NotifyHumanHandler(),
            ActionType.NO_ACTION: NoActionHandler(),
        }
    )


def get_event_service(
    event_repo: EventRepository = Depends(get_event_repository),
    decision_repo: DecisionRepository = Depends(get_decision_repository),
    approval_repo: ApprovalRepository = Depends(get_approval_repository),
    engine: ReasoningEngine = Depends(get_reasoning_engine),
    action_registry: ActionRegistry = Depends(get_action_registry),
) -> EventIngestionService:
    return EventIngestionService(event_repo, decision_repo, approval_repo, engine, action_registry)


def get_approval_service(
    approval_repo: ApprovalRepository = Depends(get_approval_repository),
    decision_repo: DecisionRepository = Depends(get_decision_repository),
    event_repo: EventRepository = Depends(get_event_repository),
    action_registry: ActionRegistry = Depends(get_action_registry),
) -> ApprovalService:
    return ApprovalService(approval_repo, decision_repo, event_repo, action_registry)
