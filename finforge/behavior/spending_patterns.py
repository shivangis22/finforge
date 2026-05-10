"""Behavioral daily spending plan generation."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import date

from finforge.behavior.balance_awareness import BalanceAdjustment
from finforge.core.models import User
from finforge.personas.base import SpendingProfile
from finforge.utils.randomness import RandomContext


@dataclass(frozen=True)
class ClusterRequest:
    """A requested behavioral cluster template for a specific day."""

    template_name: str


class SpendingPatternEngine:
    """Converts user profile, day context, and balance state into activity plans."""

    def __init__(self, random_context: RandomContext) -> None:
        self.random_context = random_context

    def plan_day(
        self,
        user: User,
        spending_profile: SpendingProfile,
        target_date: date,
        adjustment: BalanceAdjustment,
    ) -> list[ClusterRequest]:
        """Return cluster requests for a single day."""
        is_weekend = target_date.weekday() >= 5
        avg_weekly_transactions = sum(spending_profile.weekly_transaction_range) / 2
        base_transactions = avg_weekly_transactions / 7
        day_multiplier = 1.25 if is_weekend else 0.95
        expected_transactions = (
            base_transactions
            * spending_profile.base_active_day_probability
            * user.spending_intensity
            * adjustment.frequency_multiplier
            * day_multiplier
        )

        if target_date.day <= 5 and user.persona.value == "salaried":
            expected_transactions *= 0.82
        elif 12 <= target_date.day <= 22:
            expected_transactions *= 1.08

        if target_date.day >= 26:
            expected_transactions *= 0.88

        expected_sessions = max(expected_transactions / (1.45 + spending_profile.cluster_propensity), 0.05)
        session_count = int(self.random_context.numpy_rng.poisson(expected_sessions))
        if session_count == 0 and self.random_context.rng.random() < min(expected_sessions, 0.8):
            session_count = 1
        session_count = min(session_count, 3)

        templates = []
        template_weights = self._template_weights(user, spending_profile, target_date, adjustment)
        template_names = list(template_weights.keys())
        weights = list(template_weights.values())
        for _ in range(session_count):
            template_name = self.random_context.rng.choices(template_names, weights=weights, k=1)[0]
            templates.append(ClusterRequest(template_name=template_name))
        return templates

    def _template_weights(
        self,
        user: User,
        spending_profile: SpendingProfile,
        target_date: date,
        adjustment: BalanceAdjustment,
    ) -> dict[str, float]:
        """Build template weights for the day."""
        is_weekend = target_date.weekday() >= 5
        if user.persona.value == "student":
            weights = {
                "campus_commute": 1.1,
                "food_run": 0.9,
                "grocery_stop": 0.55,
                "weekend_hangout": 1.8,
                "shopping_trip": 0.5,
                "cinema_night": 1.25,
                "commute_coffee": 0.85,
                "late_streaming": 1.15,
            }
        else:
            weights = {
                "commute_coffee": 1.35,
                "lunch_run": 0.95,
                "grocery_stop": 0.8,
                "weekend_hangout": 1.25,
                "shopping_trip": 0.7,
                "cinema_night": 0.8,
                "food_run": 0.6,
                "late_streaming": 0.35,
            }

        if is_weekend:
            for name in ("weekend_hangout", "shopping_trip", "cinema_night", "food_run", "late_streaming"):
                weights[name] = weights.get(name, 0.0) * 1.45
            for name in ("commute_coffee", "campus_commute", "lunch_run"):
                weights[name] = weights.get(name, 0.0) * 0.45
        else:
            for name in ("commute_coffee", "campus_commute", "lunch_run", "grocery_stop"):
                weights[name] = weights.get(name, 0.0) * 1.2
            for name in ("weekend_hangout", "cinema_night"):
                weights[name] = weights.get(name, 0.0) * 0.55

        category_counter = Counter(self._template_categories(name) for name in weights)
        for name, groups in category_counter.items():
            _ = groups
        adjusted_weights: dict[str, float] = {}
        for template_name, base_weight in weights.items():
            category_multiplier = self._template_category_multiplier(
                template_name=template_name,
                category_multipliers=adjustment.category_multipliers,
            )
            adjusted_weights[template_name] = max(base_weight * category_multiplier, 0.05)

        return adjusted_weights

    def _template_category_multiplier(
        self,
        template_name: str,
        category_multipliers: dict[str, float],
    ) -> float:
        """Average category multiplier for a template."""
        categories = self._template_categories(template_name)
        total = 0.0
        for category in categories:
            total += category_multipliers.get(category, 1.0)
        return total / max(len(categories), 1)

    def _template_categories(self, template_name: str) -> tuple[str, ...]:
        """Map a template name to its category sequence."""
        mapping = {
            "commute_coffee": ("travel", "coffee"),
            "lunch_run": ("food",),
            "grocery_stop": ("groceries",),
            "weekend_hangout": ("food", "entertainment"),
            "shopping_trip": ("shopping", "food"),
            "cinema_night": ("entertainment", "food"),
            "food_run": ("food",),
            "campus_commute": ("coffee", "food", "travel"),
            "late_streaming": ("entertainment",),
        }
        return mapping[template_name]
