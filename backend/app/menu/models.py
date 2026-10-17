"""Menu items and their options. CHECK constraints keep bad data out of the database itself.

Options and groups load with their item (`selectin`), so an item read in async
code always carries everything the fit rules and the resolver need.
"""

from decimal import Decimal

from sqlalchemy import CheckConstraint, ForeignKey, Numeric, String, Text, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.menu.allergens import ALLERGENS_SQL


class Option(Base):
    __tablename__ = "options"
    __table_args__ = (
        UniqueConstraint("group_id", "name", name="options_group_name_key"),
        CheckConstraint("price_delta_sar >= 0", name="option_price_not_negative"),
        CheckConstraint("spice_level BETWEEN 0 AND 3", name="option_spice_range"),
        CheckConstraint("NOT is_vegan OR is_vegetarian", name="option_vegan_is_vegetarian"),
        CheckConstraint(f"allergens <@ {ALLERGENS_SQL}", name="option_known_allergens"),
        CheckConstraint(f"may_contain <@ {ALLERGENS_SQL}", name="option_known_may_contain"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    group_id: Mapped[int] = mapped_column(
        ForeignKey("option_groups.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(60))
    price_delta_sar: Mapped[Decimal] = mapped_column(Numeric(8, 2))
    allergens: Mapped[list[str]] = mapped_column(ARRAY(Text))
    may_contain: Mapped[list[str]] = mapped_column(ARRAY(Text))
    is_vegetarian: Mapped[bool]
    is_vegan: Mapped[bool]
    spice_level: Mapped[int]
    position: Mapped[int]


class OptionGroup(Base):
    __tablename__ = "option_groups"
    __table_args__ = (
        UniqueConstraint("item_id", "name", name="option_groups_item_name_key"),
        CheckConstraint("min_choices >= 0 AND max_choices >= 1", name="choices_positive"),
        CheckConstraint("min_choices <= max_choices", name="min_not_above_max"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    item_id: Mapped[int] = mapped_column(
        ForeignKey("menu_items.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(60))
    min_choices: Mapped[int]
    max_choices: Mapped[int]
    position: Mapped[int]
    options: Mapped[list[Option]] = relationship(order_by=Option.position, lazy="selectin")


class MenuItem(Base):
    __tablename__ = "menu_items"
    __table_args__ = (
        UniqueConstraint("restaurant_id", "name", name="menu_items_restaurant_name_key"),
        CheckConstraint("price_sar > 0", name="price_positive"),
        CheckConstraint("spice_level BETWEEN 0 AND 3", name="spice_range"),
        CheckConstraint("NOT is_vegan OR is_vegetarian", name="vegan_is_vegetarian"),
        CheckConstraint(f"allergens <@ {ALLERGENS_SQL}", name="known_allergens"),
        CheckConstraint(f"may_contain <@ {ALLERGENS_SQL}", name="known_may_contain"),
        CheckConstraint("removable <@ ingredients", name="removable_are_ingredients"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    restaurant_id: Mapped[int] = mapped_column(
        ForeignKey("restaurants.id", ondelete="RESTRICT"), index=True
    )
    name: Mapped[str] = mapped_column(String(80))
    category: Mapped[str] = mapped_column(String(40))
    description: Mapped[str] = mapped_column(Text)
    price_sar: Mapped[Decimal] = mapped_column(Numeric(8, 2))
    is_vegetarian: Mapped[bool]
    is_vegan: Mapped[bool]
    spice_level: Mapped[int]
    ingredients: Mapped[list[str]] = mapped_column(ARRAY(Text))
    allergens: Mapped[list[str]] = mapped_column(ARRAY(Text))
    may_contain: Mapped[list[str]] = mapped_column(ARRAY(Text))
    removable: Mapped[list[str]] = mapped_column(ARRAY(Text), server_default=text("'{}'"))
    option_groups: Mapped[list[OptionGroup]] = relationship(
        order_by=OptionGroup.position, lazy="selectin"
    )
