"""Build the model input: profile block first, then the stored conversation."""

import json
from collections.abc import Sequence

from app.agent.llm_client import InputItem
from app.memory.models import Message
from app.memory.preference import Preference
from app.memory.vocabulary import HARD_KINDS, SINGLE_VALUED_KINDS, Kind

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


def memory_update_note(before: Sequence[Preference], after: Sequence[Preference]) -> str | None:
    """What this turn's message changed in the profile, so the reply can confirm it.

    Without this the model only sees the new profile and changes memory silently.
    """
    old = {(p.kind, p.value) for p in before}
    new = {(p.kind, p.value) for p in after}
    if old == new:
        return None
    gone, added_kinds = old - new, {kind for kind, _ in new - old}
    # Diet, budget and spice hold one value, so a new one replaces the old one.
    replaced = {k: v for k, v in gone if k in SINGLE_VALUED_KINDS and k in added_kinds}
    saved = [
        f"{kind} {json.dumps(value)}"
        + (f" (replaces {json.dumps(replaced[kind])})" if kind in replaced else "")
        for kind, value in sorted(new - old)
    ]
    dropped = [f"{k} {json.dumps(v)}" for k, v in sorted(gone) if k not in replaced]
    parts = [f"Saved: {'; '.join(saved)}."] if saved else []
    parts += [f"No longer on file: {'; '.join(dropped)}."] if dropped else []
    if added_kinds & HARD_KINDS:
        # A guest who just declared an allergy or diet should hear that the pick respects it.
        parts.append("If you recommend items, say in a few words that they fit this.")
    return (
        "The guest's profile was just updated from their latest message. "
        + " ".join(parts)
        + " Confirm this change in one short sentence of your reply, so they know what you"
        " will remember."
    )


def build_input(
    profile: Sequence[Preference], history: Sequence[Message], update_note: str | None = None
) -> tuple[list[InputItem], set[int]]:
    """Returns the input items and the item IDs already recommended in this conversation.

    `update_note` (see memory_update_note) goes last, right after the guest's message.
    """
    items: list[InputItem] = [{"role": "developer", "content": profile_block(profile)}]
    seen: set[int] = set()
    for message in history:
        items.append({"role": message.role, "content": message.content})
        if message.recommended_item_ids:
            ids = ", ".join(str(i) for i in message.recommended_item_ids)
            items.append({"role": "developer", "content": f"Item IDs recommended above: {ids}"})
            seen.update(message.recommended_item_ids)
    if update_note:
        items.append({"role": "developer", "content": update_note})
    return items, seen
