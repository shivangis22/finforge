"""Temporal clustering for human-like transaction bursts."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta

from finforge.utils.dates import combine_timestamp
from finforge.utils.randomness import RandomContext


@dataclass(frozen=True)
class SessionTemplate:
    """A reusable daily spending cluster pattern."""

    name: str
    category_sequence: tuple[str, ...]
    hour_range: tuple[int, int]
    minute_offsets: tuple[int, ...]


@dataclass(frozen=True)
class ClusteredEvent:
    """A planned transaction event inside a behavioral cluster."""

    timestamp: datetime
    category: str


class ClusteringEngine:
    """Generates grouped transaction bursts instead of isolated events."""

    def __init__(self, random_context: RandomContext) -> None:
        self.random_context = random_context
        self.templates = {
            "commute_coffee": SessionTemplate(
                name="commute_coffee",
                category_sequence=("travel", "coffee"),
                hour_range=(7, 9),
                minute_offsets=(0, 35),
            ),
            "lunch_run": SessionTemplate(
                name="lunch_run",
                category_sequence=("food",),
                hour_range=(12, 14),
                minute_offsets=(0,),
            ),
            "grocery_stop": SessionTemplate(
                name="grocery_stop",
                category_sequence=("groceries",),
                hour_range=(18, 21),
                minute_offsets=(0,),
            ),
            "weekend_hangout": SessionTemplate(
                name="weekend_hangout",
                category_sequence=("food", "entertainment"),
                hour_range=(13, 20),
                minute_offsets=(0, 110),
            ),
            "shopping_trip": SessionTemplate(
                name="shopping_trip",
                category_sequence=("shopping", "food"),
                hour_range=(12, 18),
                minute_offsets=(0, 95),
            ),
            "cinema_night": SessionTemplate(
                name="cinema_night",
                category_sequence=("entertainment", "food"),
                hour_range=(18, 21),
                minute_offsets=(0, 140),
            ),
            "food_run": SessionTemplate(
                name="food_run",
                category_sequence=("food",),
                hour_range=(18, 22),
                minute_offsets=(0,),
            ),
            "campus_commute": SessionTemplate(
                name="campus_commute",
                category_sequence=("coffee", "food", "travel"),
                hour_range=(8, 11),
                minute_offsets=(0, 190, 430),
            ),
            "late_streaming": SessionTemplate(
                name="late_streaming",
                category_sequence=("entertainment",),
                hour_range=(21, 23),
                minute_offsets=(0,),
            ),
        }

    def build_session(self, target_date: date, template_name: str) -> list[ClusteredEvent]:
        """Generate clustered events for a daily session template."""
        template = self.templates[template_name]
        base_hour = self.random_context.rng.randint(template.hour_range[0], template.hour_range[1])
        base_minute = self.random_context.rng.randint(0, 45)
        base_timestamp = combine_timestamp(target_date, base_hour, base_minute)
        events: list[ClusteredEvent] = []
        for category, offset in zip(template.category_sequence, template.minute_offsets):
            timestamp = base_timestamp + timedelta(minutes=offset)
            events.append(ClusteredEvent(timestamp=timestamp, category=category))
        return events
