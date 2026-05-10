"""Adaptive spending adjustments based on balance, budget, and lifecycle."""

from __future__ import annotations

from dataclasses import dataclass

from finforge.behavior.budgeting import BudgetingEngine, UserBudgetState
from finforge.core.models import User
from finforge.personas.base import SpendingProfile


@dataclass(frozen=True)
class AdaptiveSpendingSignal:
    """Per-day spending signal derived from balance and memory."""

    state: str
    frequency_multiplier: float
    amount_multiplier: float
    category_multipliers: dict[str, float]
    amount_multipliers: dict[str, float]
    overspend_pressure: float
    lifecycle_phase: str
    max_discretionary_transactions: int | None


class AdaptiveSpendingEngine:
    """Combines balance, month phase, and recent spend memory."""

    def __init__(self, budgeting_engine: BudgetingEngine) -> None:
        self.budgeting_engine = budgeting_engine

    def assess(
        self,
        user: User,
        state: UserBudgetState,
        day_of_month: int,
        days_in_month: int,
        spending_profile: SpendingProfile,
    ) -> AdaptiveSpendingSignal:
        """Compute day-level adaptive spending controls."""
        phase = self._phase(day_of_month, days_in_month)
        overspend = self.budgeting_engine.overspend_pressure(state)
        low_threshold, high_threshold = self._thresholds(user)
        category_multipliers = {category: 1.0 for category in user.category_affinities}
        amount_multipliers = {category: 1.0 for category in user.category_affinities}

        for category, affinity in user.category_affinities.items():
            category_multipliers[category] *= affinity

        if phase == "early":
            category_multipliers["shopping"] = category_multipliers.get("shopping", 1.0) * (1.05 + user.impulse_buying_score * 0.18)
            category_multipliers["entertainment"] = category_multipliers.get("entertainment", 1.0) * (1.03 + user.entertainment_preference * 0.15)
        elif phase == "late":
            for category, multiplier in spending_profile.month_end_category_multipliers.items():
                category_multipliers[category] = category_multipliers.get(category, 1.0) * multiplier

        if state.balance <= low_threshold:
            low_balance_multipliers = {
                "entertainment": 0.10,
                "shopping": 0.15,
                "food": 0.40,
                "coffee": 0.50,
                "travel": 0.80,
                "groceries": 1.20,
            }
            low_balance_amount_multipliers = {
                "entertainment": 0.50,
                "shopping": 0.50,
                "food": 0.65,
                "coffee": 0.75,
                "travel": 0.90,
                "groceries": 1.00,
            }
            for category, multiplier in low_balance_multipliers.items():
                category_multipliers[category] = category_multipliers.get(category, 1.0) * multiplier
            for category, multiplier in low_balance_amount_multipliers.items():
                amount_multipliers[category] = amount_multipliers.get(category, 1.0) * multiplier
            signal_state = "low"
            frequency_multiplier = 0.26 if user.persona.value == "student" else 0.34
            amount_multiplier = 0.46
            max_discretionary_transactions = 1 if user.persona.value == "student" else 2
        elif state.balance >= high_threshold:
            for category, multiplier in spending_profile.high_balance_category_multipliers.items():
                category_multipliers[category] = category_multipliers.get(category, 1.0) * multiplier
            signal_state = "high"
            frequency_multiplier = 1.10
            amount_multiplier = 1.08
            max_discretionary_transactions = None
        else:
            signal_state = "normal"
            frequency_multiplier = 1.0
            amount_multiplier = 1.0
            max_discretionary_transactions = None

        if overspend > 1.0:
            pressure_discount = min((overspend - 1.0) * 0.35, 0.4)
            frequency_multiplier *= 1.0 - pressure_discount
            amount_multiplier *= 1.0 - pressure_discount * 0.8
            category_multipliers["shopping"] = category_multipliers.get("shopping", 1.0) * 0.45
            category_multipliers["entertainment"] = category_multipliers.get("entertainment", 1.0) * 0.55
            category_multipliers["food"] = category_multipliers.get("food", 1.0) * 0.78
            amount_multipliers["shopping"] = amount_multipliers.get("shopping", 1.0) * 0.7
            amount_multipliers["entertainment"] = amount_multipliers.get("entertainment", 1.0) * 0.75
            amount_multipliers["food"] = amount_multipliers.get("food", 1.0) * 0.85

        return AdaptiveSpendingSignal(
            state=signal_state,
            frequency_multiplier=round(frequency_multiplier, 3),
            amount_multiplier=round(amount_multiplier, 3),
            category_multipliers={key: round(value, 3) for key, value in category_multipliers.items()},
            amount_multipliers={key: round(value, 3) for key, value in amount_multipliers.items()},
            overspend_pressure=round(overspend, 3),
            lifecycle_phase=phase,
            max_discretionary_transactions=max_discretionary_transactions,
        )

    def _phase(self, day_of_month: int, days_in_month: int) -> str:
        """Map a day in month into a lifecycle phase."""
        if day_of_month <= 7:
            return "early"
        if day_of_month >= max(days_in_month - 5, 25):
            return "late"
        return "mid"

    def _thresholds(self, user: User) -> tuple[float, float]:
        """Return persona-level low and high balance thresholds."""
        if user.persona.value == "student":
            return 500.0, 5000.0
        return 5000.0, 50000.0
