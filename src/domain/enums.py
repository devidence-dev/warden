from enum import Enum


class Severity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class EnvironmentType(str, Enum):
    DEV = "dev"
    QA = "qa"
    STG = "stg"
    PROD = "prod"


class ActionType(str, Enum):
    ROLLBACK = "rollback"
    RESTART = "restart"
    SCALE_UP = "scale_up"
    NOTIFY_HUMAN = "notify_human"
    NO_ACTION = "no_action"
