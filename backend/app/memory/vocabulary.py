"""Fixed values for stored preferences. The DB CHECKs and extraction use these."""

from enum import StrEnum


class Kind(StrEnum):
    ALLERGY = "allergy"
    DIET = "diet"
    DISLIKE = "dislike"
    LIKE = "like"
    BUDGET = "budget"
    SPICE = "spice"
    DAY_DISLIKE = "day_dislike"
    """A food avoided on one weekday: "friday: meat"."""
    DAY_LIKE = "day_like"
    """A food wanted on one weekday: "friday: fish"."""
    CALORIES = "calories"
    """A daily calorie goal in kcal, e.g. "1800" (soft, from estimates)."""


WEEKDAYS = ("monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday")
DAY_RULE_PATTERN = rf"^({'|'.join(WEEKDAYS)}): [a-z][a-z ,-]{{0,48}}$"
CALORIES_PATTERN = r"^([89][0-9]{2}|[1-5][0-9]{3}|6000)$"
"""A daily goal from CALORIES_MIN to CALORIES_MAX kcal."""
CALORIES_MIN, CALORIES_MAX = 800, 6000


class Diet(StrEnum):
    VEGETARIAN = "vegetarian"
    VEGAN = "vegan"


class Spice(StrEnum):
    """How much heat the user enjoys."""

    NONE = "none"
    MILD = "mild"
    MEDIUM = "medium"
    HOT = "hot"


class Status(StrEnum):
    ACTIVE = "active"
    SUPERSEDED = "superseded"
    REMOVED = "removed"


HARD_KINDS = frozenset({Kind.ALLERGY, Kind.DIET})
"""Enforced in code by `safety/` (phase 4). Everything else is soft."""

SINGLE_VALUED_KINDS = frozenset({Kind.DIET, Kind.BUDGET, Kind.SPICE, Kind.CALORIES})
"""A user has at most one active row of each of these kinds."""

OPPOSITE_KINDS = {
    Kind.LIKE: Kind.DISLIKE,
    Kind.DISLIKE: Kind.LIKE,
    Kind.DAY_LIKE: Kind.DAY_DISLIKE,
    Kind.DAY_DISLIKE: Kind.DAY_LIKE,
}
DAY_RULE_KINDS = frozenset({Kind.DAY_DISLIKE, Kind.DAY_LIKE})
"""Stored as "<weekday>: <food>"."""
