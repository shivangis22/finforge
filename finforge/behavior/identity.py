"""Persistent user identity generation."""

from __future__ import annotations

from dataclasses import dataclass

from finforge.core.models import User
from finforge.utils.randomness import RandomContext


@dataclass(frozen=True)
class IdentityProfile:
    """Stable long-term behavioral traits for a user."""

    spending_style: str
    savings_tendency: float
    merchant_loyalty: float
    lifestyle_score: float
    impulse_buying_score: float
    entertainment_preference: float
    preferred_categories: list[str]
    category_affinities: dict[str, float]
    commute_pattern: str
    night_activity_score: float
    spending_intensity: float
    savings_preference: float


class IdentityEngine:
    """Creates persistent financial personalities."""

    _STYLE_LIBRARY = {
        "salaried": (
            {
                "name": "budget_conscious",
                "weight": 0.35,
                "savings_tendency": (1.15, 1.45),
                "merchant_loyalty": (0.65, 0.9),
                "lifestyle_score": (0.25, 0.45),
                "impulse_buying_score": (0.15, 0.35),
                "entertainment_preference": (0.2, 0.4),
                "preferred_categories": ("groceries", "travel", "coffee"),
                "commute_patterns": ("public_transit", "mixed"),
                "night_activity_score": (0.15, 0.35),
                "spending_intensity": (0.72, 0.95),
            },
            {
                "name": "lifestyle_spender",
                "weight": 0.40,
                "savings_tendency": (0.7, 0.95),
                "merchant_loyalty": (0.55, 0.8),
                "lifestyle_score": (0.65, 0.95),
                "impulse_buying_score": (0.45, 0.7),
                "entertainment_preference": (0.65, 0.9),
                "preferred_categories": ("food", "entertainment", "shopping"),
                "commute_patterns": ("ride_hailing", "mixed"),
                "night_activity_score": (0.45, 0.75),
                "spending_intensity": (1.05, 1.3),
            },
            {
                "name": "minimalist",
                "weight": 0.25,
                "savings_tendency": (1.2, 1.55),
                "merchant_loyalty": (0.75, 0.95),
                "lifestyle_score": (0.15, 0.35),
                "impulse_buying_score": (0.1, 0.25),
                "entertainment_preference": (0.12, 0.25),
                "preferred_categories": ("groceries", "coffee", "travel"),
                "commute_patterns": ("public_transit",),
                "night_activity_score": (0.08, 0.25),
                "spending_intensity": (0.55, 0.82),
            },
        ),
        "student": (
            {
                "name": "impulsive_student",
                "weight": 0.45,
                "savings_tendency": (0.45, 0.75),
                "merchant_loyalty": (0.45, 0.7),
                "lifestyle_score": (0.55, 0.85),
                "impulse_buying_score": (0.7, 0.95),
                "entertainment_preference": (0.7, 0.95),
                "preferred_categories": ("entertainment", "food", "coffee"),
                "commute_patterns": ("ride_hailing", "mixed"),
                "night_activity_score": (0.65, 0.95),
                "spending_intensity": (1.1, 1.4),
            },
            {
                "name": "budget_conscious",
                "weight": 0.35,
                "savings_tendency": (0.95, 1.2),
                "merchant_loyalty": (0.6, 0.85),
                "lifestyle_score": (0.25, 0.45),
                "impulse_buying_score": (0.2, 0.4),
                "entertainment_preference": (0.3, 0.55),
                "preferred_categories": ("food", "groceries", "travel"),
                "commute_patterns": ("public_transit", "mixed"),
                "night_activity_score": (0.25, 0.5),
                "spending_intensity": (0.75, 0.98),
            },
            {
                "name": "minimalist",
                "weight": 0.20,
                "savings_tendency": (1.05, 1.35),
                "merchant_loyalty": (0.72, 0.92),
                "lifestyle_score": (0.15, 0.3),
                "impulse_buying_score": (0.12, 0.25),
                "entertainment_preference": (0.15, 0.3),
                "preferred_categories": ("groceries", "coffee", "food"),
                "commute_patterns": ("public_transit",),
                "night_activity_score": (0.05, 0.2),
                "spending_intensity": (0.55, 0.8),
            },
        ),
    }

    _CATEGORY_BIASES = {
        "budget_conscious": {"groceries": 1.2, "coffee": 0.9, "travel": 1.0, "food": 0.9, "shopping": 0.55, "entertainment": 0.6},
        "lifestyle_spender": {"groceries": 0.85, "coffee": 1.0, "travel": 1.0, "food": 1.25, "shopping": 1.15, "entertainment": 1.3},
        "minimalist": {"groceries": 1.15, "coffee": 0.9, "travel": 0.95, "food": 0.8, "shopping": 0.45, "entertainment": 0.45},
        "impulsive_student": {"groceries": 0.7, "coffee": 1.05, "travel": 0.85, "food": 1.15, "shopping": 0.95, "entertainment": 1.4},
    }

    def __init__(self, random_context: RandomContext) -> None:
        self.random_context = random_context

    def build_for_user(self, user: User) -> IdentityProfile:
        """Create a persistent identity profile for a user."""
        templates = self._STYLE_LIBRARY[user.persona.value]
        selected = self.random_context.rng.choices(
            population=list(templates),
            weights=[template["weight"] for template in templates],
            k=1,
        )[0]
        style_name = str(selected["name"])
        preferred_categories = list(selected["preferred_categories"])
        self.random_context.rng.shuffle(preferred_categories)
        preferred_categories = preferred_categories[:2]
        commute_pattern = self.random_context.rng.choice(list(selected["commute_patterns"]))

        category_affinities = self._build_category_affinities(style_name)
        return IdentityProfile(
            spending_style=style_name,
            savings_tendency=round(self._sample_range(selected["savings_tendency"]), 2),
            merchant_loyalty=round(self._sample_range(selected["merchant_loyalty"]), 2),
            lifestyle_score=round(self._sample_range(selected["lifestyle_score"]), 2),
            impulse_buying_score=round(self._sample_range(selected["impulse_buying_score"]), 2),
            entertainment_preference=round(self._sample_range(selected["entertainment_preference"]), 2),
            preferred_categories=preferred_categories,
            category_affinities=category_affinities,
            commute_pattern=commute_pattern,
            night_activity_score=round(self._sample_range(selected["night_activity_score"]), 2),
            spending_intensity=round(self._sample_range(selected["spending_intensity"]), 2),
            savings_preference=round(self._sample_range(selected["savings_tendency"]), 2),
        )

    def _build_category_affinities(self, style_name: str) -> dict[str, float]:
        """Build stable user category affinities."""
        base_bias = self._CATEGORY_BIASES[style_name]
        affinities = {}
        for category, bias in base_bias.items():
            noise = self.random_context.rng.uniform(0.92, 1.08)
            affinities[category] = round(bias * noise, 3)
        return affinities

    def _sample_range(self, value_range: tuple[float, float]) -> float:
        """Sample a random value from a range."""
        return self.random_context.rng.uniform(value_range[0], value_range[1])
