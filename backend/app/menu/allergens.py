"""Fixed allergen vocabulary. User wording is mapped to these values at extraction."""

from enum import StrEnum


class Allergen(StrEnum):
    GLUTEN = "gluten"
    DAIRY = "dairy"
    EGG = "egg"
    PEANUT = "peanut"
    TREE_NUT = "tree_nut"
    SOY = "soy"
    SESAME = "sesame"
    FISH = "fish"
    SHELLFISH = "shellfish"
    MUSTARD = "mustard"


def sql_text_array(values: list[str]) -> str:
    """A literal text[] for CHECK constraints, e.g. ARRAY['gluten', 'dairy']::text[]."""
    return "ARRAY[" + ", ".join(f"'{v}'" for v in values) + "]::text[]"


ALLERGENS_SQL = sql_text_array([a.value for a in Allergen])
