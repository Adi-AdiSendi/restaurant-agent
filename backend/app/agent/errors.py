"""Agent failures. The API layer turns these into HTTP errors."""


class AgentLoopError(Exception):
    """The model kept calling tools past the iteration limit."""


class AgentAnswerError(Exception):
    """The model's final answer failed validation twice."""
