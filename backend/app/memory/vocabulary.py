"""Fixed values for stored preferences. The DB CHECKs and extraction use these."""

from enum import StrEnum


class Kind(StrEnum):
    ALLERGY = "allergy"
    DIET = "diet"
    DISLIKE = "dislike"
    LIKE = "like"
    BUDGET = "budget"
    SPICE = "spice"


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

SINGLE_VALUED_KINDS = frozenset({Kind.DIET, Kind.BUDGET, Kind.SPICE})
"""A user has at most one active row of each of these kinds."""

OPPOSITE_KINDS = {Kind.LIKE: Kind.DISLIKE, Kind.DISLIKE: Kind.LIKE}
