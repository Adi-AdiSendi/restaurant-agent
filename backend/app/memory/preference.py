"""The preferences table: typed facts with supersession. CHECKs guard the vocabulary."""

from datetime import datetime

from sqlalchemy import CheckConstraint, ForeignKey, Index, String, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.memory.models import created_at_column
from app.memory.vocabulary import (
    CALORIES_PATTERN,
    DAY_DISLIKE_PATTERN,
    HARD_KINDS,
    SINGLE_VALUED_KINDS,
    Diet,
    Kind,
    Spice,
    Status,
)
from app.menu.allergens import Allergen


def _in(values: list[str]) -> str:
    return "(" + ", ".join(f"'{v}'" for v in values) + ")"


def _vocab_check(kind: Kind, values: list[str]) -> CheckConstraint:
    return CheckConstraint(f"kind <> '{kind}' OR value IN {_in(values)}", name=f"pref_{kind}_vocab")


ACTIVE = f"status = '{Status.ACTIVE.value}'"
SINGLE = _in(sorted(k.value for k in SINGLE_VALUED_KINDS))


class Preference(Base):
    __tablename__ = "preferences"
    __table_args__ = (
        CheckConstraint(f"kind IN {_in([k.value for k in Kind])}", name="pref_kind"),
        CheckConstraint(f"status IN {_in([s.value for s in Status])}", name="pref_status"),
        _vocab_check(Kind.ALLERGY, [a.value for a in Allergen]),
        _vocab_check(Kind.DIET, [d.value for d in Diet]),
        _vocab_check(Kind.SPICE, [s.value for s in Spice]),
        CheckConstraint(
            "kind <> 'budget' OR (value ~ '^[0-9]+(\\.[0-9]{1,2})?$' AND value !~ '^[0.]+$')",
            name="pref_budget_number",
        ),
        CheckConstraint(
            f"kind <> 'day_dislike' OR value ~ '{DAY_DISLIKE_PATTERN}'", name="pref_day_format"
        ),
        # 800 to 6000 as a pattern: a cast here could run on other kinds' values.
        CheckConstraint(
            f"kind <> 'calories' OR value ~ '{CALORIES_PATTERN}'", name="pref_calories"
        ),
        Index(
            "one_active_single_valued",
            "user_id",
            "kind",
            unique=True,
            postgresql_where=text(f"{ACTIVE} AND kind IN {SINGLE}"),
        ),
        Index(
            "one_active_per_value",
            "user_id",
            "kind",
            "value",
            unique=True,
            postgresql_where=text(ACTIVE),
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    kind: Mapped[str] = mapped_column(String(20))
    value: Mapped[str] = mapped_column(String(60))
    status: Mapped[str] = mapped_column(String(20), server_default=Status.ACTIVE.value)
    superseded_by: Mapped[int | None] = mapped_column(ForeignKey("preferences.id"))
    source_message_id: Mapped[int | None] = mapped_column(
        ForeignKey("messages.id", ondelete="SET NULL")
    )
    created_at: Mapped[datetime] = created_at_column()

    @property
    def is_hard(self) -> bool:
        return self.kind in HARD_KINDS
