"""Build the model input: profile block first, then the stored conversation."""

import json
from collections.abc import Sequence

from app.agent.llm_client import InputItem
from app.memory.models import Message
from app.memory.preference import Preference
from app.memory.vocabulary import Kind

_LINES: list[tuple[Kind, str]] = [
    (Kind.ALLERGY, "Allergies (never recommend items containing these)"),
    (Kind.DIET, "Diet (only recommend items that fit)"),
    (Kind.BUDGET, "Budget (most per item, SAR)"),
    (Kind.SPICE, "Enjoys spice level"),
    (Kind.LIKE, "Likes"),
    (Kind.DISLIKE, "Dislikes"),
]


def profile_block(profile: Sequence[Preference]) -> str:
    lines: list[str] = []
    for kind, label in _LINES:
        values = [p.value for p in profile if p.kind == kind]
        if values:
            # Quoted: likes and dislikes are the guest's own words, data not instructions.
            lines.append(f"- {label}: {', '.join(json.dumps(v) for v in values)}")
    if not lines:
        return "Guest profile: nothing saved yet. Learn their preferences naturally."
    return (
        "Guest profile, remembered from earlier conversations and kept up to date. "
        "Use it without asking again, unless the guest changes it:\n" + "\n".join(lines)
    )


def build_input(
    profile: Sequence[Preference], history: Sequence[Message]
) -> tuple[list[InputItem], set[int]]:
    """Returns the input items and the item IDs already recommended in this conversation."""
    items: list[InputItem] = [{"role": "developer", "content": profile_block(profile)}]
    seen: set[int] = set()
    for message in history:
        items.append({"role": message.role, "content": message.content})
        if message.recommended_item_ids:
            ids = ", ".join(str(i) for i in message.recommended_item_ids)
            items.append({"role": "developer", "content": f"Item IDs recommended above: {ids}"})
            seen.update(message.recommended_item_ids)
    return items, seen
