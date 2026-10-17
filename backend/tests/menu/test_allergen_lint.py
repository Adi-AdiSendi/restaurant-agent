"""A word list check on every menu file: an ingredient or option that names a
known allergen source must list that allergen. It catches a dropped allergen
in hand-written data; it cannot prove an allergen is present."""

import re

import pytest

from app.menu.allergens import Allergen
from scripts.seed_menu import load_restaurants

# Phrases where a trigger word is not that allergen, and what is left to check.
# "milk of your choice" names a required Milk group, whose options carry the allergens.
NOT_ALLERGENS = (
    ("milk of your choice", ""),
    ("coconut milk", "coconut"),
    ("coconut cream", "coconut"),
    ("oat milk", "oat"),
    ("almond milk", "almond"),
    ("soy milk", "soy"),
    ("peanut butter", "peanut"),
    ("cocoa butter", "cocoa"),
    ("vegan cheese", ""),
    ("vegan mayo", ""),
    ("rice noodles", "rice"),
    ("glass noodles", ""),
    ("gluten-free bread", ""),
    ("corn tortillas", "corn"),
    ("glutinous rice flour", "rice"),
    ("rice flour", "rice"),
    ("eggplant", ""),
    ("butternut", "squash"),
    ("nutmeg", ""),
    ("egg-free", ""),
)
SOURCES: dict[Allergen, str] = {
    Allergen.DAIRY: r"milk|cheese|cheddar|mozzarella|parmesan|halloumi|feta|labneh|akkawi"
    r"|butter|cream|yogh?urt|ghee|ice cream|ayran",
    Allergen.GLUTEN: r"bread|buns?|brioche|pita|khubz|saj|flour|wheat|breadcrumbs|panko"
    r"|pastry|croissant|tortillas?|pasta|penne|linguine|couscous|bulgur|soy sauce|batter"
    r"|noodles|sourdough|oats|granola|biscuits?|cake|wrappers?",
    Allergen.EGG: r"eggs?|mayo|mayonnaise|aioli|meringue",
    Allergen.SHELLFISH: r"shrimp|prawns?|crab|lobster|calamari|squid|mussels|clams|oyster",
    Allergen.FISH: r"fish|salmon|tuna|hammour|cod|sea bass|bream|anchov(y|ies)",
    Allergen.SESAME: r"sesame|tahini|za'?atar",
    Allergen.SOY: r"soy|tofu|edamame|miso",
    Allergen.PEANUT: r"peanuts?",
    Allergen.TREE_NUT: r"almonds?|pistachios?|cashews?|walnuts?|pecans?|hazelnuts?"
    r"|pine nuts",
    Allergen.MUSTARD: r"mustard",
}


def named_sources(text: str) -> set[Allergen]:
    text = text.lower()
    for phrase, rest in NOT_ALLERGENS:
        text = text.replace(phrase, f" {rest} ")
    return {a for a, words in SOURCES.items() if re.search(rf"\b({words})\b", text)}


def foods() -> list[tuple[str, list[str], list[Allergen]]]:
    """(label, words to check, listed allergens) for every item and option."""
    found: list[tuple[str, list[str], list[Allergen]]] = []
    for restaurant in load_restaurants():
        for item in restaurant.items:
            found.append((f"{restaurant.slug}: {item.name}", item.ingredients, item.allergens))
            for group in item.option_groups:
                for option in group.options:
                    label = f"{restaurant.slug}: {item.name} / {option.name}"
                    found.append((label, [option.name], option.allergens))
    return found


@pytest.mark.parametrize(("label", "words", "allergens"), foods(), ids=lambda v: str(v)[:60])
def test_named_allergen_sources_are_listed(
    label: str, words: list[str], allergens: list[Allergen]
) -> None:
    missing = set[Allergen]().union(*(named_sources(w) for w in words)) - set(allergens)
    assert not missing, f"{label} names {sorted(missing)} but does not list it"


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("brioche bun", {Allergen.GLUTEN}),
        ("coconut milk", set[Allergen]()),
        ("almond milk", {Allergen.TREE_NUT}),
        ("peanut butter", {Allergen.PEANUT}),
        ("egg noodles", {Allergen.EGG, Allergen.GLUTEN}),
        ("eggplant", set[Allergen]()),
        ("tahini sauce", {Allergen.SESAME}),
        ("light soy sauce", {Allergen.SOY, Allergen.GLUTEN}),
    ],
)
def test_word_list(text: str, expected: set[Allergen]) -> None:
    assert named_sources(text) == expected
