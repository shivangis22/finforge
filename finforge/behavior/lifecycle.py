"""Monthly lifecycle and cashflow helpers."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from finforge.behavior.budgeting import UserBudgetState
from finforge.core.models import User
from finforge.utils.randomness import RandomContext


@dataclass(frozen=True)
class LifecycleContext:
    """Lightweight lifecycle classification for a given day."""

    phase: str
    is_weekend: bool
    financial_stress: bool


class FinancialLifecycleEngine:
    """Encodes persona-specific monthly financial rhythm."""

    def __init__(self, random_context: RandomContext) -> None:
        self.random_context = random_context

    def context_for_day(self, user: User, target_date: date, state: UserBudgetState, days_in_month: int) -> LifecycleContext:
        """Return lifecycle context for a user on a day."""
        if target_date.day <= 7:
            phase = "early"
        elif target_date.day >= max(days_in_month - 5, 25):
            phase = "late"
        else:
            phase = "mid"
        financial_stress = phase == "late" or state.balance < max(user.monthly_income * 0.14, 120.0)
        return LifecycleContext(
            phase=phase,
            is_weekend=target_date.weekday() >= 5,
            financial_stress=financial_stress,
        )

    def irregular_income_for_day(self, user: User, target_date: date, state: UserBudgetState) -> list[dict[str, object]]:
        """Create persona-specific irregular inflows."""
        if user.persona.value != "student":
            return []
        inflows: list[dict[str, object]] = []
        chance = 0.05
        if state.balance < 120:
            chance = 0.12
        if target_date.day in {17, 24}:
            chance += 0.03
        if self.random_context.rng.random() < chance:
            merchant = "Family Transfer" if state.balance < 90 else "Freelance Client"
            amount = self.random_context.rng.uniform(35.0, 140.0) if merchant == "Freelance Client" else self.random_context.rng.uniform(60.0, 180.0)
            inflows.append(
                {
                    "merchant": merchant,
                    "category": "income",
                    "amount": round(amount, 2),
                    "time_bucket": "afternoon",
                }
            )
        return inflows
