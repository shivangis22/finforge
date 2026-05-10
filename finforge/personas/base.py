"""Persona abstractions and shared event models."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from finforge.core.models import User


@dataclass(frozen=True)
class RecurringEvent:
    """Definition for a scheduled recurring transaction."""

    name: str
    merchant: str
    category: str
    day_of_month: int
    amount: float
    recurrence_type: str = "none"
    is_subscription: bool = False


@dataclass(frozen=True)
class SpendingProfile:
    """Behavioral profile for discretionary transaction generation."""

    weekly_transaction_range: tuple[int, int]
    category_weights_weekday: dict[str, float]
    category_weights_weekend: dict[str, float]
    month_end_category_multipliers: dict[str, float]
    low_balance_category_multipliers: dict[str, float]
    high_balance_category_multipliers: dict[str, float]
    base_active_day_probability: float
    cluster_propensity: float


class Persona(Protocol):
    """Protocol implemented by all personas."""

    name: str

    def recurring_events(self, user: User) -> list[RecurringEvent]:
        """Return recurring monthly events."""

    def spending_profile(self) -> SpendingProfile:
        """Return discretionary spending preferences."""


class BasePersona:
    """Base class for persona implementations."""

    name: str = "base"

    def recurring_events(self, user: User) -> list[RecurringEvent]:
        """Return recurring monthly events for a user."""
        raise NotImplementedError

    def spending_profile(self) -> SpendingProfile:
        """Return discretionary spending profile."""
        raise NotImplementedError
