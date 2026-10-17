"""Menu categories, in the order the menu shows them."""

from enum import StrEnum


class Category(StrEnum):
    STARTERS = "starters"
    BURGERS_AND_MAINS = "burgers_and_mains"
    BOWLS_AND_PASTA = "bowls_and_pasta"
    DESSERTS_AND_DRINKS = "desserts_and_drinks"
