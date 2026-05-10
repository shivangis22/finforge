"""Student persona implementation."""

from __future__ import annotations

from finforge.core.models import User
from finforge.personas.base import BasePersona, RecurringEvent, SpendingProfile


class StudentPersona(BasePersona):
    """Lower-income persona with smaller discretionary spends and irregular inflows."""

    name = "student"

    def recurring_events(self, user: User) -> list[RecurringEvent]:
        stipend = round(max(user.monthly_income * 0.55, 100.0), 2)
        events = [
            RecurringEvent(
                name="family_support",
                merchant="Family Transfer",
                category="income",
                day_of_month=5,
                amount=stipend,
                recurrence_type="income",
            ),
        ]
        for merchant in user.recurring_subscription_merchants:
            amount = -float(user.recurring_subscription_amounts[merchant])
            events.append(
                RecurringEvent(
                    name=f"subscription_{merchant.lower().replace(' ', '_')}",
                    merchant=merchant,
                    category="subscription",
                    day_of_month=6,
                    amount=amount,
                    recurrence_type="subscription",
                    is_subscription=True,
                )
            )
        return events

    def spending_profile(self) -> SpendingProfile:
        return SpendingProfile(
            weekly_transaction_range=(7, 13),
            category_weights_weekday={
                "food": 0.25,
                "coffee": 0.15,
                "travel": 0.13,
                "entertainment": 0.28,
                "shopping": 0.07,
                "groceries": 0.12,
            },
            category_weights_weekend={
                "food": 0.30,
                "entertainment": 0.38,
                "travel": 0.08,
                "shopping": 0.10,
                "groceries": 0.07,
                "coffee": 0.10,
            },
            month_end_category_multipliers={
                "entertainment": 0.60,
                "shopping": 0.65,
                "food": 0.92,
                "travel": 0.95,
                "coffee": 0.85,
                "groceries": 1.0,
            },
            low_balance_category_multipliers={
                "entertainment": 0.45,
                "shopping": 0.40,
                "food": 0.82,
                "travel": 0.88,
                "coffee": 0.7,
                "groceries": 0.95,
            },
            high_balance_category_multipliers={
                "entertainment": 1.30,
                "shopping": 1.10,
                "food": 1.08,
                "travel": 1.02,
                "coffee": 1.05,
                "groceries": 1.0,
            },
            base_active_day_probability=0.78,
            cluster_propensity=0.76,
        )
