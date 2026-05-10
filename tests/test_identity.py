from finforge.behavior.identity import IdentityEngine
from finforge.core.enums import PersonaType
from finforge.core.models import User
from finforge.utils.randomness import RandomContext


def test_identity_engine_populates_required_behavioral_traits() -> None:
    engine = IdentityEngine(RandomContext(seed=42))
    user = User(
        user_id="user_000001",
        name="Test User",
        age=28,
        city="Bengaluru",
        persona=PersonaType.SALARIED,
        monthly_income=5000.0,
        initial_balance=1200.0,
    )
    identity = engine.build_for_user(user)

    assert identity.spending_style
    assert identity.preferred_categories
    assert identity.commute_pattern in {"public_transit", "mixed", "ride_hailing"}
    assert 0.0 <= identity.night_activity_score <= 1.0
    assert "entertainment" in identity.category_affinities
