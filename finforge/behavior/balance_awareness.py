"""Balance-aware spending adjustments."""

from __future__ import annotations

from dataclasses import dataclass

from finforge.personas.base import SpendingProfile


@dataclass(frozen=True)
class BalanceAdjustment:
    """Spending modifiers derived from current financial headroom."""

    state: str
    frequency_multiplier: float
    amount_multiplier: float
    category_multipliers: dict[str, float]


class BalanceAwarenessEngine:
    """Adjusts spending based on current liquidity and month timing."""

    def assess(
        self,
        current_balance: float,
        monthly_income: float,
        day_of_month: int,
        days_in_month: int,
        spending_profile: SpendingProfile,
        savings_preference: float,
    ) -> BalanceAdjustment:
        """Return spending modifiers for the user's current financial state."""
        low_threshold = max(monthly_income * 0.18 * savings_preference, 120.0)
        high_threshold = max(monthly_income * 0.85, 900.0)
        month_end = day_of_month >= max(days_in_month - 4, 24)

        if current_balance <= low_threshold:
            category_multipliers = dict(spending_profile.low_balance_category_multipliers)
            if month_end:
                category_multipliers = self._merge_category_multipliers(
                    category_multipliers,
                    spending_profile.month_end_category_multipliers,
                )
            return BalanceAdjustment(
                state="low",
                frequency_multiplier=0.50,
                amount_multiplier=0.72,
                category_multipliers=category_multipliers,
            )

        if current_balance >= high_threshold:
            category_multipliers = dict(spending_profile.high_balance_category_multipliers)
            if month_end:
                category_multipliers = self._merge_category_multipliers(
                    category_multipliers,
                    spending_profile.month_end_category_multipliers,
                )
            return BalanceAdjustment(
                state="high",
                frequency_multiplier=1.15,
                amount_multiplier=1.10,
                category_multipliers=category_multipliers,
            )

        category_multipliers = {category: 1.0 for category in spending_profile.category_weights_weekday}
        if month_end:
            category_multipliers = self._merge_category_multipliers(
                category_multipliers,
                spending_profile.month_end_category_multipliers,
            )
            return BalanceAdjustment(
                state="normal",
                frequency_multiplier=0.88,
                amount_multiplier=0.92,
                category_multipliers=category_multipliers,
            )

        return BalanceAdjustment(
            state="normal",
            frequency_multiplier=1.0,
            amount_multiplier=1.0,
            category_multipliers=category_multipliers,
        )

    def _merge_category_multipliers(
        self,
        base: dict[str, float],
        overlay: dict[str, float],
    ) -> dict[str, float]:
        """Multiply an existing category map by another one."""
        merged = dict(base)
        for category, multiplier in overlay.items():
            merged[category] = round(merged.get(category, 1.0) * multiplier, 4)
        return merged
