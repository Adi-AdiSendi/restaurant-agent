"""The one error shape every tool returns to the model."""

from typing import Literal

from pydantic import BaseModel, ValidationError

ErrorCategory = Literal["invalid_arguments", "not_found", "unknown_tool"]


class ToolError(BaseModel):
    error_category: ErrorCategory
    retryable: bool
    message: str


def invalid_arguments(exc: ValidationError) -> ToolError:
    """Validation errors are not retryable: the same call would fail again."""
    problems = "; ".join(
        f"{'.'.join(str(p) for p in err['loc']) or 'arguments'}: {err['msg']}"
        for err in exc.errors()
    )
    return ToolError(error_category="invalid_arguments", retryable=False, message=problems)
