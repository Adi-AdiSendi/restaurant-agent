"""The structured final answer and its strict JSON schema."""

from pydantic import BaseModel, Field, ValidationError

from app.agent.llm_client import Spec


class FinalAnswer(BaseModel):
    reply: str = Field(min_length=1)
    recommended_item_ids: list[int] = Field(max_length=5)


TEXT_FORMAT: Spec = {
    "type": "json_schema",
    "name": "final_answer",
    "strict": True,
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "required": ["reply", "recommended_item_ids"],
        "properties": {
            "reply": {"type": "string", "minLength": 1},
            "recommended_item_ids": {
                "type": "array",
                "items": {"type": "integer"},
                "maxItems": 5,
            },
        },
    },
}


def retry_instruction(exc: ValidationError) -> str:
    """The retry prompt names only the failed fields and their errors."""
    fields = sorted({".".join(str(p) for p in err["loc"]) or "answer" for err in exc.errors()})
    return (
        f"Your last answer was not valid. Failed fields: {', '.join(fields)}. "
        f"Error: {exc.errors(include_url=False)}. Return the corrected JSON answer only."
    )
