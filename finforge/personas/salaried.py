"""Salaried persona implementation."""

from __future__ import annotations

from finforge.core.models import User
from finforge.personas.base import BasePersona, RecurringEvent, SpendingProfile


class SalariedPersona(BasePersona):
    """Stable-income persona with predictable recurring outflows."""

    name = "salaried"

    def recurring_events(self, user: User) -> list[RecurringEvent]:
        rent_amount = round(min(user.monthly_income * 0.28, 2400.0), 2)
        utility_amount = round(min(max(user.monthly_income * 0.035, 65.0), 180.0), 2)
        events = [
            RecurringEvent(
                name="salary",
                merchant="Acme Payroll",
                category="income",
                day_of_month=1,
                amount=round(user.monthly_income, 2),
                recurrence_type="income",
            ),
            RecurringEvent(
                name="rent",
                merchant="Green Residency",
                category="housing",
                day_of_month=3,
                amount=round(-rent_amount, 2),
                recurrence_type="bill",
            ),
            RecurringEvent(
                name="utilities",
                merchant="City Power",
                category="utilities",
                day_of_month=4,
                amount=round(-utility_amount, 2),
                recurrence_type="bill",
            ),
        ]
        for index, merchant in enumerate(user.recurring_subscription_merchants, start=5):
            amount = -float(user.recurring_subscription_amounts[merchant])
            events.append(
                RecurringEvent(
                    name=f"subscription_{merchant.lower().replace(' ', '_')}",
                    merchant=merchant,
                    category="subscription",
                    day_of_month=index,
                    amount=amount,
                    recurrence_type="subscription",
                    is_subscription=True,
                )
            )
        return events

    def spending_profile(self) -> SpendingProfile:
        return SpendingProfile(
            weekly_transaction_range=(6, 11),
            category_weights_weekday={
                "travel": 0.28,
                "coffee": 0.14,
                "food": 0.20,
                "shopping": 0.12,
                "entertainment": 0.08,
                "groceries": 0.18,
            },
            category_weights_weekend={
                "food": 0.28,
                "shopping": 0.22,
                "entertainment": 0.24,
                "groceries": 0.14,
                "travel": 0.06,
                "coffee": 0.06,
            },
            month_end_category_multipliers={
                "entertainment": 0.45,
                "shopping": 0.55,
                "food": 0.9,
                "travel": 0.95,
                "coffee": 0.9,
                "groceries": 1.0,
            },
            low_balance_category_multipliers={
                "entertainment": 0.30,
                "shopping": 0.35,
                "food": 0.8,
                "travel": 0.85,
                "coffee": 0.7,
                "groceries": 0.95,
            },
            high_balance_category_multipliers={
                "entertainment": 1.25,
                "shopping": 1.20,
                "food": 1.05,
                "travel": 1.05,
                "coffee": 1.0,
                "groceries": 1.0,
            },
            base_active_day_probability=0.72,
            cluster_propensity=0.68,
        )
