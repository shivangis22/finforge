"""Date and timestamp helpers."""

from __future__ import annotations

from datetime import date, datetime, time

from dateutil.relativedelta import relativedelta


def parse_date(value: str) -> date:
    """Parse an ISO date string."""
    return date.fromisoformat(value)


def month_start(start: date, offset: int) -> date:
    """Return the first day of a later month."""
    return (start + relativedelta(months=offset)).replace(day=1)


def clamp_day(year: int, month: int, day: int) -> date:
    """Clamp a day-of-month to the actual days available in a month."""
    candidate = date(year, month, 1)
    next_month = candidate + relativedelta(months=1)
    last_day = (next_month - relativedelta(days=1)).day
    return date(year, month, min(day, last_day))


def combine_timestamp(target_date: date, hour: int, minute: int) -> datetime:
    """Combine date with time to produce a timestamp."""
    return datetime.combine(target_date, time(hour=hour, minute=minute))
