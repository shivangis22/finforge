"""Category-safe merchant catalog utilities."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import random


@dataclass(frozen=True)
class MerchantSpec:
    """Merchant metadata used for realistic sampling and ticket sizes."""

    name: str
    category: str
    amount_range: tuple[float, float]
    fixed_amount: Optional[float] = None
    tags: tuple[str, ...] = ()


@dataclass(frozen=True)
class MerchantCatalog:
    """Merchant lookup and category-safe sampling."""

    merchants_by_category: dict[str, tuple[str, ...]]
    specs_by_merchant: dict[str, MerchantSpec]

    def pick(self, category: str, rng: random.Random) -> str:
        """Pick a merchant that belongs to the provided category."""
        merchants = self.merchants_by_category.get(category)
        if not merchants:
            raise KeyError(f"Unknown category: {category}")
        return rng.choice(list(merchants))

    def pick_weighted(
        self,
        category: str,
        merchant_weights: dict[str, float],
        rng: random.Random,
    ) -> str:
        """Pick a merchant using per-user affinity weights."""
        merchants = self.merchants_by_category.get(category)
        if not merchants:
            raise KeyError(f"Unknown category: {category}")
        weights = [merchant_weights.get(merchant, 0.01) for merchant in merchants]
        return rng.choices(list(merchants), weights=weights, k=1)[0]

    def categories(self) -> tuple[str, ...]:
        """Return known transaction categories."""
        return tuple(self.merchants_by_category.keys())

    def amount_for(self, merchant: str, rng: random.Random, amount_multiplier: float = 1.0) -> float:
        """Return a realistic positive ticket size for the merchant."""
        spec = self.specs_by_merchant[merchant]
        if spec.fixed_amount is not None:
            return round(spec.fixed_amount, 2)
        low, high = spec.amount_range
        midpoint = (low + high) / 2
        spread = (high - low) / 6 if high > low else 0.1
        sampled = rng.gauss(midpoint, spread)
        adjusted = min(max(sampled * amount_multiplier, low * 0.7), high * 1.35)
        return round(max(adjusted, 0.5), 2)

    def category_for(self, merchant: str) -> str:
        """Return the canonical category for a merchant."""
        return self.specs_by_merchant[merchant].category

    def merchants_for_tag(self, tag: str) -> tuple[str, ...]:
        """Return merchants that expose a given behavior tag."""
        return tuple(
            spec.name
            for spec in self.specs_by_merchant.values()
            if tag in spec.tags
        )


_MERCHANT_SPECS = (
    MerchantSpec("Swiggy", "food", (14.0, 34.0), tags=("delivery", "meal")),
    MerchantSpec("Zomato", "food", (12.0, 30.0), tags=("delivery", "meal")),
    MerchantSpec("Dominos", "food", (16.0, 32.0), tags=("delivery", "meal")),
    MerchantSpec("McDonalds", "food", (8.0, 18.0), tags=("meal",)),
    MerchantSpec("Uber", "travel", (7.0, 28.0), tags=("commute",)),
    MerchantSpec("Ola", "travel", (7.0, 24.0), tags=("commute",)),
    MerchantSpec("Metro Card", "travel", (4.0, 12.0), tags=("commute",)),
    MerchantSpec("Amazon", "shopping", (18.0, 220.0), tags=("variable",)),
    MerchantSpec("Flipkart", "shopping", (15.0, 180.0), tags=("variable",)),
    MerchantSpec("Myntra", "shopping", (20.0, 150.0), tags=("variable",)),
    MerchantSpec("Netflix", "subscription", (649.0, 649.0), fixed_amount=649.0, tags=("subscription",)),
    MerchantSpec("Spotify", "subscription", (119.0, 119.0), fixed_amount=119.0, tags=("subscription",)),
    MerchantSpec("Amazon Prime", "subscription", (299.0, 299.0), fixed_amount=299.0, tags=("subscription",)),
    MerchantSpec("YouTube Premium", "subscription", (129.0, 129.0), fixed_amount=129.0, tags=("subscription",)),
    MerchantSpec("PVR Cinemas", "entertainment", (180.0, 520.0), tags=("leisure",)),
    MerchantSpec("BookMyShow", "entertainment", (150.0, 440.0), tags=("leisure",)),
    MerchantSpec("Gaming Cafe", "entertainment", (80.0, 220.0), tags=("leisure",)),
    MerchantSpec("Bowling Alley", "entertainment", (140.0, 360.0), tags=("leisure",)),
    MerchantSpec("Concert Tickets", "entertainment", (400.0, 1800.0), tags=("leisure",)),
    MerchantSpec("BigBasket", "groceries", (24.0, 90.0), tags=("essentials",)),
    MerchantSpec("Blinkit", "groceries", (10.0, 42.0), tags=("essentials",)),
    MerchantSpec("Nature's Basket", "groceries", (18.0, 70.0), tags=("essentials",)),
    MerchantSpec("Starbucks", "coffee", (4.5, 9.0), tags=("coffee",)),
    MerchantSpec("Blue Tokai", "coffee", (3.5, 8.0), tags=("coffee",)),
    MerchantSpec("Third Wave Coffee", "coffee", (4.0, 8.5), tags=("coffee",)),
    MerchantSpec("Acme Payroll", "income", (0.0, 0.0), tags=("income",)),
    MerchantSpec("Family Transfer", "income", (0.0, 0.0), tags=("income",)),
    MerchantSpec("Freelance Client", "income", (0.0, 0.0), tags=("income",)),
    MerchantSpec("Green Residency", "housing", (0.0, 0.0), tags=("bill",)),
    MerchantSpec("Urban Rentals", "housing", (0.0, 0.0), tags=("bill",)),
    MerchantSpec("City Power", "utilities", (55.0, 160.0), tags=("bill",)),
    MerchantSpec("Aqua Utility", "utilities", (18.0, 50.0), tags=("bill",)),
)

_MERCHANTS_BY_CATEGORY = {}
for _spec in _MERCHANT_SPECS:
    _MERCHANTS_BY_CATEGORY.setdefault(_spec.category, []).append(_spec.name)

DEFAULT_MERCHANT_CATALOG = MerchantCatalog(
    merchants_by_category={key: tuple(value) for key, value in _MERCHANTS_BY_CATEGORY.items()},
    specs_by_merchant={spec.name: spec for spec in _MERCHANT_SPECS},
)
