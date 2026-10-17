"""Operation validation: the fixed vocabularies are enforced before the DB."""

import pytest
from pydantic import ValidationError

from app.memory.operations import Operation


def make(**fields: object) -> Operation:
    return Operation.model_validate(fields)


@pytest.mark.parametrize(
    ("kind", "value", "stored"),
    [
        ("allergy", "Peanut", "peanut"),
        ("diet", "vegan", "vegan"),
        ("spice", "hot", "hot"),
        ("budget", "50", "50.00"),
        ("budget", "45.5 SAR", "45.50"),
        ("dislike", "  Mushrooms ", "mushrooms"),
    ],
)
def test_valid_values_are_normalized(kind: str, value: str, stored: str) -> None:
    assert make(op="add", kind=kind, value=value).value == stored


@pytest.mark.parametrize(
    ("kind", "value"),
    [
        ("allergy", "lactose"),
        ("diet", "pescatarian"),
        ("spice", "very"),
        ("budget", "cheap"),
        ("budget", "0"),
        ("budget", "-5"),
        ("budget", "nan"),
        ("budget", "snan"),
        ("budget", "infinity"),
        ("budget", "0.001"),
    ],
)
def test_values_outside_the_vocabulary_are_rejected(kind: str, value: str) -> None:
    with pytest.raises(ValidationError):
        make(op="add", kind=kind, value=value)


@pytest.mark.parametrize("action", ["supersede", "remove"])
def test_supersede_and_remove_need_a_target(action: str) -> None:
    with pytest.raises(ValidationError):
        make(op=action, kind="diet", value="vegan")


def test_remove_skips_the_vocabulary_check() -> None:
    assert make(op="remove", kind="allergy", value="whatever", target_id=3).target_id == 3


@pytest.mark.parametrize(
    ("action", "kind", "value", "target_kind", "target_value", "allowed"),
    [
        ("remove", "allergy", "peanut", "allergy", "peanut", True),
        ("remove", "allergy", "dairy", "allergy", "peanut", False),
        ("remove", "diet", "vegetarian", "allergy", "peanut", False),
        ("remove", "budget", "50", "budget", "40.00", True),
        ("supersede", "diet", "vegan", "diet", "vegetarian", True),
        ("supersede", "like", "mushrooms", "dislike", "mushrooms", True),
        ("supersede", "diet", "vegan", "allergy", "peanut", False),
    ],
)
def test_wrong_target_kind_or_value_does_not_match(
    action: str, kind: str, value: str, target_kind: str, target_value: str, allowed: bool
) -> None:
    operation = make(op=action, kind=kind, value=value, target_id=1)
    assert operation.matches_target(target_kind, target_value) is allowed
