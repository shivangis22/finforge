"""Scheduling utilities for recurring and discretionary events."""

from __future__ import annotations

from datetime import date, datetime

from finforge.personas.base import RecurringEvent
from finforge.utils.dates import clamp_day, combine_timestamp
from finforge.utils.randomness import RandomContext


class TransactionScheduler:
    """Generates realistic timestamps for synthetic transactions."""

    def __init__(self, random_context: RandomContext) -> None:
        self.random_context = random_context

    def recurring_timestamp(self, month_date: date, event: RecurringEvent) -> datetime:
        """Create a timestamp for a recurring event."""
        target_date = clamp_day(month_date.year, month_date.month, event.day_of_month)
        if event.category == "income":
            hour = self.random_context.rng.randint(8, 11)
        elif event.category == "housing":
            hour = self.random_context.rng.randint(9, 18)
        elif event.category == "utilities":
            hour = self.random_context.rng.randint(10, 18)
        else:
            hour = self.random_context.rng.randint(18, 22)
        minute = self.random_context.rng.randint(0, 59)
        return combine_timestamp(target_date, hour, minute)

    def random_time(self, target_date: date, hour: int, minute: int) -> datetime:
        """Return a concrete timestamp from explicit components."""
        return combine_timestamp(target_date, hour, minute)
