"""Transaction session planning and timestamp clustering."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta

from finforge.behavior.adaptive_spending import AdaptiveSpendingSignal
from finforge.behavior.lifecycle import LifecycleContext
from finforge.core.models import User
from finforge.utils.dates import combine_timestamp
from finforge.utils.randomness import RandomContext


@dataclass(frozen=True)
class SessionTemplate:
    """A reusable transaction session blueprint."""

    name: str
    categories: tuple[str, ...]
    hour_range: tuple[int, int]
    minute_offsets: tuple[int, ...]


@dataclass(frozen=True)
class SessionRequest:
    """A selected session template for a day."""

    template_name: str


@dataclass(frozen=True)
class SessionEvent:
    """A planned event within a session."""

    timestamp: datetime
    category: str


class TransactionSessionEngine:
    """Creates session-like transaction bursts from user identity and day context."""

    STYLE_FREQUENCY_MULTIPLIER = {
        "minimalist": 0.45,
        "budget_conscious": 0.65,
        "lifestyle_spender": 1.20,
        "impulsive_student": 1.35,
    }

    SESSION_PROBABILITY_BY_STYLE = {
        "minimalist": 0.25,
        "budget_conscious": 0.35,
        "lifestyle_spender": 0.60,
        "impulsive_student": 0.70,
    }

    def __init__(self, random_context: RandomContext) -> None:
        self.random_context = random_context
        self.templates = {
            "morning_commute": SessionTemplate("morning_commute", ("travel", "coffee"), (7, 9), (0, 28)),
            "office_lunch": SessionTemplate("office_lunch", ("food",), (12, 14), (0,)),
            "grocery_stop": SessionTemplate("grocery_stop", ("groceries",), (18, 21), (0,)),
            "weekend_outing": SessionTemplate("weekend_outing", ("travel", "food", "entertainment"), (13, 19), (0, 70, 170)),
            "shopping_cluster": SessionTemplate("shopping_cluster", ("shopping", "food"), (12, 18), (0, 95)),
            "late_night_delivery": SessionTemplate("late_night_delivery", ("food", "entertainment"), (21, 23), (0, 75)),
            "student_hangout": SessionTemplate("student_hangout", ("coffee", "food", "entertainment"), (15, 21), (0, 95, 200)),
            "campus_day": SessionTemplate("campus_day", ("coffee", "food", "travel"), (8, 11), (0, 175, 430)),
            "standalone_food": SessionTemplate("standalone_food", ("food",), (12, 22), (0,)),
            "standalone_shopping": SessionTemplate("standalone_shopping", ("shopping",), (12, 20), (0,)),
            "standalone_entertainment": SessionTemplate("standalone_entertainment", ("entertainment",), (18, 22), (0,)),
        }

    def plan_sessions(
        self,
        user: User,
        target_date: date,
        lifecycle: LifecycleContext,
        signal: AdaptiveSpendingSignal,
        weekly_transaction_range: tuple[int, int],
        cluster_propensity: float,
        base_active_day_probability: float,
    ) -> list[SessionRequest]:
        """Select session templates for a day."""
        avg_weekly = sum(weekly_transaction_range) / 2
        style_multiplier = self.STYLE_FREQUENCY_MULTIPLIER.get(user.spending_style, 1.0)
        baseline = (avg_weekly / 7.0) * base_active_day_probability * user.spending_intensity * style_multiplier
        weekend_bonus = 1.22 if lifecycle.is_weekend else 0.95
        early_bonus = 1.12 if lifecycle.phase == "early" else 1.0
        late_penalty = 0.78 if lifecycle.phase == "late" else 1.0
        expected_sessions = baseline * signal.frequency_multiplier * weekend_bonus * early_bonus * late_penalty
        expected_sessions = max(expected_sessions / (1.7 + cluster_propensity), 0.02)
        session_probability = self.SESSION_PROBABILITY_BY_STYLE.get(user.spending_style, 0.4)
        if signal.state == "low":
            session_probability *= 0.55
            expected_sessions *= 0.6
        elif signal.state == "high":
            session_probability *= 1.05
        if self.random_context.rng.random() > min(session_probability, 0.95):
            return []

        session_count = int(self.random_context.numpy_rng.poisson(expected_sessions))
        if session_count == 0 and self.random_context.rng.random() < min(expected_sessions, 0.85):
            session_count = 1
        if user.spending_style == "minimalist":
            session_count = min(session_count, 1)
        else:
            session_count = min(session_count, 2 if signal.state == "low" else 3)

        template_weights = self._template_weights(user, lifecycle, signal)
        names = list(template_weights.keys())
        weights = list(template_weights.values())
        return [
            SessionRequest(template_name=self.random_context.rng.choices(names, weights=weights, k=1)[0])
            for _ in range(session_count)
        ]

    def build_session(self, target_date: date, template_name: str) -> list[SessionEvent]:
        """Materialize timestamps for a session template."""
        template = self.templates[template_name]
        base_hour = self.random_context.rng.randint(template.hour_range[0], template.hour_range[1])
        base_minute = self.random_context.rng.randint(0, 45)
        start = combine_timestamp(target_date, base_hour, base_minute)
        return [
            SessionEvent(timestamp=start + timedelta(minutes=offset), category=category)
            for category, offset in zip(template.categories, template.minute_offsets)
        ]

    def _template_weights(
        self,
        user: User,
        lifecycle: LifecycleContext,
        signal: AdaptiveSpendingSignal,
    ) -> dict[str, float]:
        """Score session templates for a user and day."""
        weights = {
            "morning_commute": 0.9,
            "office_lunch": 0.8,
            "grocery_stop": 0.65,
            "weekend_outing": 1.0,
            "shopping_cluster": 0.7,
            "late_night_delivery": 0.45,
            "student_hangout": 0.6,
            "campus_day": 0.55,
            "standalone_food": 0.75,
            "standalone_shopping": 0.45,
            "standalone_entertainment": 0.4,
        }

        if user.commute_pattern == "public_transit":
            weights["morning_commute"] *= 1.25
        elif user.commute_pattern == "ride_hailing":
            weights["weekend_outing"] *= 1.15
            weights["morning_commute"] *= 1.1

        if lifecycle.is_weekend:
            weights["weekend_outing"] *= 1.5
            weights["shopping_cluster"] *= 1.25
            weights["late_night_delivery"] *= 1.35
            weights["morning_commute"] *= 0.35
            weights["office_lunch"] *= 0.55
            weights["campus_day"] *= 0.55
            weights["standalone_food"] *= 1.15
            weights["standalone_entertainment"] *= 1.1
        else:
            weights["morning_commute"] *= 1.3
            weights["office_lunch"] *= 1.15
            weights["weekend_outing"] *= 0.45
            weights["standalone_food"] *= 0.9

        if user.persona.value == "student":
            weights["student_hangout"] *= 1.55
            weights["campus_day"] *= 1.25
            weights["late_night_delivery"] *= 1.15 + user.night_activity_score * 0.95
            weights["standalone_entertainment"] *= 1.1
        else:
            weights["campus_day"] *= 0.35
            weights["student_hangout"] *= 0.25
            weights["office_lunch"] *= 1.15
            weights["late_night_delivery"] *= 0.65

        weights["late_night_delivery"] *= 0.75 + user.night_activity_score * 1.1
        if user.spending_style in {"lifestyle_spender", "impulsive_student"}:
            weights["shopping_cluster"] *= 1.15 + user.impulse_buying_score * 0.25
            weights["weekend_outing"] *= 1.05 + user.entertainment_preference * 0.25
        if user.spending_style == "minimalist":
            weights["shopping_cluster"] *= 0.55
            weights["late_night_delivery"] *= 0.65

        if lifecycle.financial_stress:
            weights["shopping_cluster"] *= 0.55
            weights["weekend_outing"] *= 0.72
            weights["late_night_delivery"] *= 0.7
            weights["standalone_shopping"] *= 0.65
            weights["standalone_food"] *= 0.85
            weights["standalone_entertainment"] *= 0.55

        if signal.state == "low":
            weights["shopping_cluster"] *= 0.05
            weights["standalone_shopping"] *= 0.03
            weights["weekend_outing"] *= 0.45
            weights["student_hangout"] *= 0.55
            weights["late_night_delivery"] *= 0.6
            weights["standalone_food"] *= 0.72
            weights["grocery_stop"] *= 1.2
            weights["morning_commute"] *= 1.05

        for template_name in list(weights):
            affinity = self._template_affinity(user, template_name)
            category_multiplier = self._template_category_multiplier(signal.category_multipliers, template_name)
            weights[template_name] = max(weights[template_name] * affinity * category_multiplier, 0.05)

        return weights

    def _template_affinity(self, user: User, template_name: str) -> float:
        """Measure how well a template matches the user's persistent preferences."""
        categories = self.templates[template_name].categories
        score = 0.0
        for category in categories:
            score += user.category_affinities.get(category, 1.0)
            if category in user.preferred_categories:
                score += 0.22
        return score / max(len(categories), 1)

    def _template_category_multiplier(self, category_multipliers: dict[str, float], template_name: str) -> float:
        """Average adaptive multiplier for the session's categories."""
        categories = self.templates[template_name].categories
        total = 0.0
        for category in categories:
            total += category_multipliers.get(category, 1.0)
        return total / max(len(categories), 1)
