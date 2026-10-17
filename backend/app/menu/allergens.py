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
