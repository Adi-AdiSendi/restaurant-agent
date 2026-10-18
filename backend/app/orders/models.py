"""Carts and orders. A cart holds choices; an order holds a snapshot of what was bought.

Cart lines store only IDs and removals: price, allergens and names are
resolved from the menu on every read, so a cart never shows a stale price.
Order lines copy them at checkout, so later menu changes do not rewrite history.
"""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

QUANTITY_RANGE = "quantity BETWEEN 1 AND 20"


def _now_column() -> Mapped[datetime]:
    return mapped_column(DateTime(timezone=True), server_default=func.now())


class CartLine(Base):
    __tablename__ = "cart_lines"
    __table_args__ = (CheckConstraint(QUANTITY_RANGE, name="cart_quantity_range"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    cart_id: Mapped[int] = mapped_column(ForeignKey("carts.id", ondelete="CASCADE"), index=True)
    item_id: Mapped[int] = mapped_column(ForeignKey("menu_items.id", ondelete="CASCADE"))
    quantity: Mapped[int]
    option_ids: Mapped[list[int]] = mapped_column(ARRAY(Integer))
    removed: Mapped[list[str]] = mapped_column(ARRAY(Text))
    created_at: Mapped[datetime] = _now_column()


class Cart(Base):
    """One open cart per user, at one restaurant."""

    __tablename__ = "carts"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    restaurant_id: Mapped[int] = mapped_column(ForeignKey("restaurants.id", ondelete="RESTRICT"))
    updated_at: Mapped[datetime] = _now_column()
    lines: Mapped[list[CartLine]] = relationship(
        order_by=CartLine.id, lazy="selectin", cascade="all, delete-orphan"
    )


class OrderLine(Base):
    __tablename__ = "order_lines"
    __table_args__ = (CheckConstraint(QUANTITY_RANGE, name="order_quantity_range"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"), index=True)
    item_id: Mapped[int | None] = mapped_column(ForeignKey("menu_items.id", ondelete="SET NULL"))
    item_name: Mapped[str] = mapped_column(String(80))
    category: Mapped[str] = mapped_column(String(40))
    quantity: Mapped[int]
    unit_price_sar: Mapped[Decimal] = mapped_column(Numeric(8, 2))
    option_names: Mapped[list[str]] = mapped_column(ARRAY(Text))
    removed: Mapped[list[str]] = mapped_column(ARRAY(Text))
    allergens: Mapped[list[str]] = mapped_column(ARRAY(Text))
    kcal: Mapped[int | None]
    """Estimated kcal of one, as ordered; summed for the guest's daily total."""


class Order(Base):
    __tablename__ = "orders"
    __table_args__ = (
        CheckConstraint("fulfilment IN ('pickup', 'dine_in')", name="known_fulfilment"),
        CheckConstraint("total_sar > 0", name="total_positive"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    restaurant_id: Mapped[int] = mapped_column(ForeignKey("restaurants.id", ondelete="RESTRICT"))
    fulfilment: Mapped[str] = mapped_column(String(10))
    total_sar: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    placed_at: Mapped[datetime] = _now_column()
    lines: Mapped[list[OrderLine]] = relationship(
        order_by=OrderLine.id, lazy="selectin", cascade="all, delete-orphan"
    )
