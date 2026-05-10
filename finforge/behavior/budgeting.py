"""Budget memory and discretionary spending state."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field

from finforge.core.models import User


@dataclass
class UserBudgetState:
    """Mutable simulation state for a user's cashflow and spending memory."""

    balance: float
    discretionary_budget: float
    discretionary_spent: float = 0.0
    essentials_spent: float = 0.0
    income_received: float = 0.0
    pressure_score: float = 0.0
    recent_discretionary_spend: deque[float] = field(default_factory=lambda: deque(maxlen=10))
    recent_daily_spend: deque[float] = field(default_factory=lambda: deque(maxlen=14))


class BudgetingEngine:
    """Tracks ongoing spending pressure and budget fatigue."""

    DISCRETIONARY_CATEGORIES = {"food", "shopping", "entertainment"}

    def start_user(self, user: User) -> UserBudgetState:
        """Create a budget state for a new user."""
        return UserBudgetState(
            balance=user.initial_balance,
            discretionary_budget=self._monthly_discretionary_budget(user),
        )

    def start_month(self, state: UserBudgetState, user: User) -> None:
        """Reset month-scoped budget counters while keeping recent memory."""
        state.discretionary_budget = self._monthly_discretionary_budget(user)
        state.discretionary_spent = 0.0
        state.essentials_spent = 0.0
        state.income_received = 0.0
        state.pressure_score = 0.0

    def record_transaction(self, state: UserBudgetState, amount: float, category: str) -> None:
        """Update budgeting memory after a transaction is applied."""
        if amount > 0:
            state.income_received += amount
            if category == "income" and state.discretionary_budget < amount * 0.35:
                state.discretionary_budget += amount * 0.08
            return

        spend = abs(amount)
        if category in self.DISCRETIONARY_CATEGORIES:
            state.discretionary_spent += spend
            state.recent_discretionary_spend.append(spend)
            state.recent_daily_spend.append(spend)
        elif category != "income":
            state.essentials_spent += spend
            state.recent_daily_spend.append(spend * 0.35)

        budget_ratio = state.discretionary_spent / max(state.discretionary_budget, 1.0)
        recent_pressure = sum(state.recent_discretionary_spend) / max(state.discretionary_budget * 0.35, 1.0)
        state.pressure_score = round(max(budget_ratio, recent_pressure), 3)

    def overspend_pressure(self, state: UserBudgetState) -> float:
        """Return a smooth overspend indicator."""
        return min(max(state.pressure_score, 0.0), 2.2)

    def _monthly_discretionary_budget(self, user: User) -> float:
        """Derive a discretionary budget from user traits."""
        base_ratio = 0.34 if user.persona.value == "student" else 0.27
        ratio = base_ratio * user.spending_intensity / max(user.savings_tendency, 0.5)
        ratio *= 0.75 + user.lifestyle_score * 0.45
        budget = max(user.monthly_income * ratio, 80.0)
        reserved_subscriptions = sum(user.recurring_subscription_amounts.values())
        budget -= reserved_subscriptions * 0.55
        return round(max(budget, 45.0), 2)
