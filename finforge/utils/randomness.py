"""Randomness helpers with deterministic seed handling."""

from __future__ import annotations

import random
from typing import Optional

import numpy as np
from faker import Faker


class RandomContext:
    """Owns seeded randomness sources used across the package."""

    def __init__(self, seed: Optional[int] = None) -> None:
        self.seed = seed
        self.rng = random.Random(seed)
        self.numpy_rng = np.random.default_rng(seed)
        self.faker = Faker()
        if seed is not None:
            random.seed(seed)
            np.random.seed(seed)
            Faker.seed(seed)
            self.faker.seed_instance(seed)
