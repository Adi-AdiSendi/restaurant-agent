"""Memory operations proposed by extraction, validated before they touch the DB."""

import re
from decimal import Decimal, InvalidOperation
from typing import Literal, Self

from pydantic import BaseModel, Field, field_validator, model_validator

from app.memory.vocabulary import (
    CALORIES_MAX,
    CALORIES_MIN,
    DAY_RULE_KINDS,
    DAY_RULE_PATTERN,
    OPPOSITE_KINDS,
    SINGLE_VALUED_KINDS,
    WEEKDAYS,
    Diet,
    Kind,
    Spice,
)
from app.menu.allergens import Allergen

_VOCAB: dict[Kind, set[str]] = {
    Kind.ALLERGY: {a.value for a in Allergen},
    Kind.DIET: {d.value for d in Diet},
    Kind.SPICE: {s.value for s in Spice},
}


class Operation(BaseModel):
    op: Literal["add", "supersede", "remove"]
    kind: Kind
    value: str = Field(min_length=1, max_length=60)
    target_id: int | None = None

    @field_validator("value")
    @classmethod
    def _normalize(cls, value: str) -> str:
        return " ".join(value.lower().split())

    @model_validator(mode="after")
    def _check(self) -> Self:
        if self.op in ("supersede", "remove") and self.target_id is None:
            raise ValueError(f"{self.op} needs a target_id")
        if self.op == "remove":
            return self
        allowed = _VOCAB.get(self.kind)
        if allowed is not None and self.value not in allowed:
            raise ValueError(f"{self.kind} value must be one of {sorted(allowed)}")
        if self.kind == Kind.BUDGET:
            self.value = _budget(self.value)
        if self.kind == Kind.CALORIES:
            self.value = _calories(self.value)
        if self.kind in DAY_RULE_KINDS:
            self.value = _day_rule(self.value)
        return self

    def matches_target(self, kind: str, value: str) -> bool:
        """A wrong target_id must not delete or replace an unrelated fact (e.g. an allergy).

        remove: same kind, and same value unless the kind has one active row.
        supersede: same kind, or like and dislike of each other.
        """
        if self.op == "remove":
            return kind == self.kind and (self.kind in SINGLE_VALUED_KINDS or value == self.value)
        return kind == self.kind or OPPOSITE_KINDS.get(Kind(kind)) == self.kind


def _budget(value: str) -> str:
    try:
        amount = Decimal(value.removesuffix("sar").strip())
    except InvalidOperation as exc:
        raise ValueError("budget must be a number of SAR") from exc
    if not amount.is_finite():
        raise ValueError("budget must be a number of SAR")
    rounded = amount.quantize(Decimal("0.01"))
    if rounded <= 0 or rounded >= 10_000:
        raise ValueError("budget must be between 0 and 10000 SAR")
    return str(rounded)


def _calories(value: str) -> str:
    digits = value.removesuffix("kcal").removesuffix("calories").strip().replace(",", "")
    if not digits.isdigit() or not CALORIES_MIN <= int(digits) <= CALORIES_MAX:
        raise ValueError(
            f"calories must be a daily goal from {CALORIES_MIN} to {CALORIES_MAX} kcal"
        )
    return str(int(digits))


def _day_rule(value: str) -> str:
    """ "fridays: meat" or "on friday: meat" -> "friday: meat"; the weekday must be real."""
    day, _, food = value.partition(":")
    day = day.removeprefix("on ").strip().removesuffix("s")
    if day not in WEEKDAYS or not food.strip():
        raise ValueError('a day rule must be "<weekday>: <food>", e.g. "friday: fish"')
    rule = f"{day}: {food.strip()}"
    if not re.fullmatch(DAY_RULE_PATTERN, rule):
        raise ValueError("the food in a day rule must be a few plain words")
    return rule
