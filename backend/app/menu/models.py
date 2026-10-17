"""The menu_items table. CHECK constraints keep bad data out of the database itself."""

from decimal import Decimal

from sqlalchemy import CheckConstraint, Numeric, String, Text
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.menu.allergens import Allergen
from app.menu.categories import Category


def _sql_array(values: list[str]) -> str:
    return "ARRAY[" + ", ".join(f"'{v}'" for v in values) + "]::text[]"


ALLERGENS_SQL = _sql_array([a.value for a in Allergen])
CATEGORIES_SQL = _sql_array([c.value for c in Category])


class MenuItem(Base):
    __tablename__ = "menu_items"
    __table_args__ = (
        CheckConstraint("price_sar > 0", name="price_positive"),
        CheckConstraint("spice_level BETWEEN 0 AND 3", name="spice_range"),
        CheckConstraint("NOT is_vegan OR is_vegetarian", name="vegan_is_vegetarian"),
        CheckConstraint(f"category = ANY({CATEGORIES_SQL})", name="known_category"),
        CheckConstraint(f"allergens <@ {ALLERGENS_SQL}", name="known_allergens"),
        CheckConstraint(f"may_contain <@ {ALLERGENS_SQL}", name="known_may_contain"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(80), unique=True)
    category: Mapped[str] = mapped_column(String(40))
    description: Mapped[str] = mapped_column(Text)
    price_sar: Mapped[Decimal] = mapped_column(Numeric(8, 2))
    is_vegetarian: Mapped[bool]
    is_vegan: Mapped[bool]
    spice_level: Mapped[int]
    ingredients: Mapped[list[str]] = mapped_column(ARRAY(Text))
    allergens: Mapped[list[str]] = mapped_column(ARRAY(Text))
    may_contain: Mapped[list[str]] = mapped_column(ARRAY(Text))
