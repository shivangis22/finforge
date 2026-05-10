"""User-level merchant habit generation."""

from __future__ import annotations

from dataclasses import dataclass

from finforge.behavior.identity import IdentityProfile
from finforge.behavior.subscriptions import SubscriptionEngine
from finforge.core.models import User
from finforge.merchants.catalog import MerchantCatalog
from finforge.utils.randomness import RandomContext


@dataclass(frozen=True)
class MerchantAffinityProfile:
    """Persistent user merchant preferences."""

    preferred_merchants: dict[str, list[str]]
    merchant_weights: dict[str, dict[str, float]]
    recurring_subscription_merchants: list[str]
    recurring_subscription_amounts: dict[str, float]


class MerchantAffinityModel:
    """Builds per-user merchant habits that persist across the simulation."""

    def __init__(
        self,
        random_context: RandomContext,
        catalog: MerchantCatalog,
        subscription_engine: SubscriptionEngine,
    ) -> None:
        self.random_context = random_context
        self.catalog = catalog
        self.subscription_engine = subscription_engine

    def build_for_user(self, user: User, identity: IdentityProfile, persona_name: str) -> MerchantAffinityProfile:
        """Create preferred merchants and affinity weights for a user."""
        preferred_merchants: dict[str, list[str]] = {}
        merchant_weights: dict[str, dict[str, float]] = {}
        tracked_categories = ("food", "travel", "shopping", "entertainment", "groceries", "coffee")

        for category in tracked_categories:
            merchants = list(self.catalog.merchants_by_category[category])
            merchants = self._ordered_merchants(category, merchants, identity, user)
            preferred_count = 2 if len(merchants) > 2 and identity.merchant_loyalty < 0.82 else 1
            preferred = merchants[:preferred_count]
            weights: dict[str, float] = {}
            if preferred_count == 1:
                primary = preferred[0]
                dominant_weight = 0.62 + identity.merchant_loyalty * 0.26
                weights[primary] = round(dominant_weight, 4)
                for merchant in merchants[1:]:
                    weights[merchant] = round((1.0 - weights[primary]) / max(len(merchants) - 1, 1), 4)
            else:
                primary_weight = 0.42 + identity.merchant_loyalty * 0.2
                secondary_weight = 0.2 + (1.0 - identity.merchant_loyalty) * 0.16
                weights[preferred[0]] = round(primary_weight, 4)
                weights[preferred[1]] = round(secondary_weight, 4)
                remainder = (1.0 - weights[preferred[0]] - weights[preferred[1]]) / max(len(merchants) - 2, 1)
                for merchant in merchants[2:]:
                    weights[merchant] = round(remainder, 4)
            preferred_merchants[category] = preferred
            merchant_weights[category] = weights

        subscription_plan = self.subscription_engine.build_plan(persona_name, identity)
        recurring_subscription_merchants, recurring_subscription_amounts = self._affordable_subscriptions(
            user=user,
            merchants=subscription_plan.merchants,
            amounts=subscription_plan.amounts,
        )

        return MerchantAffinityProfile(
            preferred_merchants=preferred_merchants,
            merchant_weights=merchant_weights,
            recurring_subscription_merchants=recurring_subscription_merchants,
            recurring_subscription_amounts=recurring_subscription_amounts,
        )

    def _ordered_merchants(
        self,
        category: str,
        merchants: list[str],
        identity: IdentityProfile,
        user: User,
    ) -> list[str]:
        """Order merchants according to identity-specific biases."""
        ranked = list(merchants)
        self.random_context.rng.shuffle(ranked)
        if category == "travel":
            if identity.commute_pattern == "public_transit":
                ranked.sort(key=lambda merchant: merchant != "Metro Card")
            elif identity.commute_pattern == "ride_hailing":
                ranked.sort(key=lambda merchant: merchant == "Metro Card")
        elif category == "coffee" and identity.night_activity_score < 0.25:
            ranked.sort(key=lambda merchant: merchant == "Third Wave Coffee")
        elif category == "food" and "food" in identity.preferred_categories:
            ranked.sort(key=lambda merchant: merchant not in {"Swiggy", "Zomato"})
        elif category == "entertainment" and user.persona.value == "student":
            ranked.sort(key=lambda merchant: merchant == "PVR Cinemas")
        return ranked

    def _affordable_subscriptions(
        self,
        user: User,
        merchants: list[str],
        amounts: dict[str, float],
    ) -> tuple[list[str], dict[str, float]]:
        """Trim subscriptions so recurring commitments stay affordable."""
        if user.persona.value == "student":
            budget_limit = max(user.monthly_income * 0.32, 129.0)
        else:
            budget_limit = max(user.monthly_income * 0.18, 299.0)
        affordable_candidates = [merchant for merchant in merchants if amounts[merchant] <= budget_limit]
        if not affordable_candidates:
            return [], {}
        selected: list[str] = []
        selected_amounts: dict[str, float] = {}
        running_total = 0.0
        for merchant in affordable_candidates:
            amount = amounts[merchant]
            if running_total + amount <= budget_limit:
                selected.append(merchant)
                selected_amounts[merchant] = amount
                running_total += amount
        return selected, selected_amounts
