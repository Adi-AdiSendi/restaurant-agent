"""The restaurants table. Every menu item and conversation belongs to one restaurant."""

from sqlalchemy import CheckConstraint, String, Text
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

SLUG_PATTERN = r"^[a-z0-9]+(-[a-z0-9]+)*$"
ACCENT_PATTERN = r"^#[0-9a-f]{6}$"
CATEGORY_PATTERN = r"^[a-z]+(_[a-z]+)*$"
PHOTO_PATTERN = r"^[a-z0-9]+(-[a-z0-9]+)*/[a-z0-9]+(-[a-z0-9]+)*$"
"""`<restaurant>/<photo>`: the UI loads `/menu/<restaurant>/<photo>-{320,640}.webp` (ADR 0024)."""


class Restaurant(Base):
    __tablename__ = "restaurants"
    __table_args__ = (
        CheckConstraint(f"slug ~ '{SLUG_PATTERN}'", name="slug_format"),
        CheckConstraint(f"accent_color ~ '{ACCENT_PATTERN}'", name="accent_hex"),
        CheckConstraint("cardinality(categories) > 0", name="has_categories"),
        CheckConstraint(f"photo ~ '{PHOTO_PATTERN}'", name="photo_format"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(40), unique=True)
    name: Mapped[str] = mapped_column(String(60), unique=True)
    cuisine: Mapped[str] = mapped_column(String(40))
    tagline: Mapped[str] = mapped_column(Text)
    accent_color: Mapped[str] = mapped_column(String(7))
    categories: Mapped[list[str]] = mapped_column(ARRAY(Text))
    position: Mapped[int]
    photo: Mapped[str | None] = mapped_column(String(100))
