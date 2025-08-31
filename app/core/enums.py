from enum import Enum


class APIVersion(str, Enum):
    v1 = "v1"
    v2 = "v2"


class RouterTag(str, Enum):
    user = "user"
    agent = "agent"


class Environment(str, Enum):
    dev = "dev"
    prod = "prod"
    test = "test"


class AgentType(str, Enum):
    conversational = "conversational"
    retriever = "retriever"
    planner = "planner"


class ErrorCode(str, Enum):
    not_found = "NOT_FOUND"
    validation_error = "VALIDATION_ERROR"
    internal_error = "INTERNAL_ERROR"
