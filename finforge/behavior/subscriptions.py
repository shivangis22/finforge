"""Dedicated subscription assignment logic."""

from __future__ import annotations

from dataclasses import dataclass

from finforge.behavior.identity import IdentityProfile
from finforge.utils.randomness import RandomContext


@dataclass(frozen=True)
class SubscriptionPlan:
    """Stable monthly subscription selections and amounts for a user."""

    merchants: list[str]
    amounts: dict[str, float]


class SubscriptionEngine:
    """Assigns stable subscription portfolios per user."""

    _BASE_AMOUNTS = {
        "Netflix": 649.0,
        "Spotify": 119.0,
        "Amazon Prime": 299.0,
        "YouTube Premium": 129.0,
    }

    def __init__(self, random_context: RandomContext) -> None:
        self.random_context = random_context

    def build_plan(self, persona_name: str, identity: IdentityProfile) -> SubscriptionPlan:
        """Create a stable subscription plan for a user."""
        available = list(self._BASE_AMOUNTS.keys())
        ranked = self._rank_candidates(available, persona_name, identity)
        subscription_count = self._subscription_count(persona_name, identity)
        merchants = ranked[:subscription_count]
        amounts = {merchant: self._BASE_AMOUNTS[merchant] for merchant in merchants}
        return SubscriptionPlan(merchants=merchants, amounts=amounts)

    def _subscription_count(self, persona_name: str, identity: IdentityProfile) -> int:
        """Choose how many subscriptions a user maintains."""
        if identity.spending_style == "minimalist":
            return 0 if self.random_context.rng.random() < 0.65 else 1
        if persona_name == "student":
            if identity.spending_style == "impulsive_student":
                return self.random_context.rng.choices([1, 2, 3], weights=[0.3, 0.45, 0.25], k=1)[0]
            return self.random_context.rng.choices([0, 1, 2], weights=[0.25, 0.5, 0.25], k=1)[0]
        if identity.spending_style == "lifestyle_spender":
            return self.random_context.rng.choices([1, 2, 3], weights=[0.15, 0.5, 0.35], k=1)[0]
        if identity.spending_style == "budget_conscious":
            return self.random_context.rng.choices([0, 1, 2], weights=[0.15, 0.6, 0.25], k=1)[0]
        return self.random_context.rng.choices([0, 1], weights=[0.55, 0.45], k=1)[0]

    def _rank_candidates(
        self,
        available: list[str],
        persona_name: str,
        identity: IdentityProfile,
    ) -> list[str]:
        """Rank subscriptions using user identity."""
        ranked = list(available)
        self.random_context.rng.shuffle(ranked)
        if persona_name == "student":
            ranked.sort(key=lambda merchant: merchant not in {"Spotify", "YouTube Premium", "Netflix"})
        if identity.night_activity_score > 0.6:
            ranked.sort(key=lambda merchant: merchant != "Netflix")
        if identity.entertainment_preference < 0.35:
            ranked.sort(key=lambda merchant: merchant in {"Netflix", "YouTube Premium"})
        return ranked
