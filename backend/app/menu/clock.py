"""The restaurants' local time (Riyadh, UTC+3 all year), for day rules and "today"."""

from datetime import UTC, datetime, timedelta, timezone

RIYADH = timezone(timedelta(hours=3), "Asia/Riyadh")


def now() -> datetime:
    return datetime.now(RIYADH)


def weekday(at: datetime | None = None) -> str:
    """Lowercase English weekday, as day rules store it: "friday"."""
    return (at or now()).astimezone(RIYADH).strftime("%A").lower()


def start_of_day(at: datetime | None = None) -> datetime:
    """Midnight in Riyadh at the start of this day, in UTC."""
    local = (at or now()).astimezone(RIYADH)
    return local.replace(hour=0, minute=0, second=0, microsecond=0).astimezone(UTC)
