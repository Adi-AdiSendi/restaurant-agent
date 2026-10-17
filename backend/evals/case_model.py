"""Eval cases: who says what, and what must be true. Loaded from cases/*.yaml.

Expectations come from the case, never from the DB: if extraction misses
"I'm allergic to peanuts", a peanut card must still count as unsafe.
"""

from decimal import Decimal
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, TypeAdapter

from app.memory.vocabulary import Diet, Kind
from app.menu.allergens import Allergen

CASES_DIR = Path(__file__).resolve().parent / "cases"

Category = Literal[
    "allergen_safety",
    "diet_compliance",
    "grounding",
    "memory_recall",
    "preference_update",
    "isolation",
    "extraction_precision",
]
SAFETY_CATEGORIES: frozenset[str] = frozenset({"allergen_safety", "diet_compliance", "isolation"})
"""A safety case passes only if it passes in every run (worst run is reported)."""


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class Expect(_Strict):
    cards: Literal["any", "some", "none"] = "any"
    forbid_allergens: list[Allergen] = Field(default_factory=list[Allergen])
    diet: Diet | None = None
    max_price_sar: Decimal | None = None
    prices: bool = False
    """Every "NN SAR" in the reply must be a menu price or a number the user said."""
    refused: bool = False
    """The turn must be refused (posting into another user's conversation)."""
    judge: str | None = None
    """A pass criterion for the reply text, graded by the LLM judge."""


class Step(_Strict):
    user: str
    say: str
    new_conversation: bool = False
    into_conversation_of: str | None = None
    expect: Expect = Expect()


Fact = tuple[Kind, str]


class ProfileExpect(_Strict):
    active: list[Fact] = Field(default_factory=list[Fact])
    superseded: list[Fact] = Field(default_factory=list[Fact])
    not_active: list[Fact] = Field(default_factory=list[Fact])
    exact: bool = False
    """The active facts must be exactly `active`, nothing more."""


class Case(_Strict):
    id: str
    category: Category
    description: str
    users: list[str]
    steps: list[Step]
    profiles: dict[str, ProfileExpect] = Field(default_factory=dict[str, ProfileExpect])


_cases = TypeAdapter(list[Case])


def load_cases(directory: Path = CASES_DIR) -> list[Case]:
    cases: list[Case] = []
    for path in sorted(directory.glob("*.yaml")):
        loaded = _cases.validate_python(yaml.safe_load(path.read_text(encoding="utf-8")))
        if any(case.category != path.stem for case in loaded):
            raise ValueError(f"{path.name}: every case must have category {path.stem}")
        cases.extend(loaded)
    ids = [case.id for case in cases]
    if len(ids) != len(set(ids)):
        raise ValueError("case ids must be unique")
    return cases
