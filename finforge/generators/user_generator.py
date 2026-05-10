"""Synthetic user generation."""

from __future__ import annotations

from finforge.behavior.identity import IdentityEngine
from finforge.behavior.merchant_affinity import MerchantAffinityModel
from finforge.core.constants import DEFAULT_CITY, DEFAULT_INCOME_RANGE, DEFAULT_INITIAL_BALANCE_RANGE
from finforge.core.enums import PersonaType
from finforge.core.models import User
from finforge.personas.base import BasePersona
from finforge.utils.randomness import RandomContext


class UserGenerator:
    """Builds synthetic users for a selected persona."""

    def __init__(
        self,
        random_context: RandomContext,
        identity_engine: IdentityEngine,
        merchant_affinity_model: MerchantAffinityModel,
    ) -> None:
        self.random_context = random_context
        self.identity_engine = identity_engine
        self.merchant_affinity_model = merchant_affinity_model

    def generate(self, count: int, persona: PersonaType, persona_definition: BasePersona) -> list[User]:
        """Generate a list of synthetic users."""
        income_min, income_max = DEFAULT_INCOME_RANGE[persona.value]
        balance_min, balance_max = DEFAULT_INITIAL_BALANCE_RANGE
        users: list[User] = []

        for index in range(1, count + 1):
            monthly_income = round(self.random_context.rng.uniform(income_min, income_max), 2)
            if persona == PersonaType.STUDENT:
                age = self.random_context.rng.randint(18, 27)
                base_balance = round(self.random_context.rng.uniform(120.0, 1200.0), 2)
            else:
                age = self.random_context.rng.randint(24, 58)
                base_balance = round(self.random_context.rng.uniform(balance_min * 1.3, balance_max * 1.9), 2)

            base_user = User(
                user_id=f"user_{index:06d}",
                name=self.random_context.faker.name(),
                age=age,
                city=DEFAULT_CITY,
                persona=persona,
                monthly_income=monthly_income,
                initial_balance=base_balance,
            )
            identity = self.identity_engine.build_for_user(base_user)
            affinity = self.merchant_affinity_model.build_for_user(base_user, identity, persona_definition.name)
            users.append(
                base_user.model_copy(
                    update={
                        "spending_style": identity.spending_style,
                        "savings_tendency": identity.savings_tendency,
                        "merchant_loyalty": identity.merchant_loyalty,
                        "lifestyle_score": identity.lifestyle_score,
                        "impulse_buying_score": identity.impulse_buying_score,
                        "entertainment_preference": identity.entertainment_preference,
                        "preferred_categories": identity.preferred_categories,
                        "category_affinities": identity.category_affinities,
                        "preferred_merchants": affinity.preferred_merchants,
                        "merchant_weights": affinity.merchant_weights,
                        "recurring_subscription_merchants": affinity.recurring_subscription_merchants,
                        "recurring_subscription_amounts": affinity.recurring_subscription_amounts,
                        "commute_pattern": identity.commute_pattern,
                        "night_activity_score": identity.night_activity_score,
                        "spending_intensity": identity.spending_intensity,
                        "savings_preference": identity.savings_preference,
                    }
                )
            )

        return users
