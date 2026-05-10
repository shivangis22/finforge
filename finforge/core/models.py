"""Pydantic domain models for users and transactions."""

from __future__ import annotations

from datetime import datetime
from typing import Dict, List

from pydantic import BaseModel, Field

from finforge.core.enums import PersonaType, TransactionType


class User(BaseModel):
    """Synthetic user definition."""

    user_id: str
    name: str
    age: int = Field(ge=18, le=90)
    city: str
    persona: PersonaType
    monthly_income: float = Field(ge=0)
    initial_balance: float = Field(ge=0)
    spending_style: str = "budget_conscious"
    savings_tendency: float = Field(default=1.0, ge=0.2, le=1.8)
    merchant_loyalty: float = Field(default=0.6, ge=0.1, le=1.0)
    lifestyle_score: float = Field(default=0.5, ge=0.0, le=1.0)
    impulse_buying_score: float = Field(default=0.5, ge=0.0, le=1.0)
    entertainment_preference: float = Field(default=0.5, ge=0.0, le=1.0)
    preferred_categories: List[str] = Field(default_factory=list)
    category_affinities: Dict[str, float] = Field(default_factory=dict)
    preferred_merchants: Dict[str, List[str]] = Field(default_factory=dict)
    merchant_weights: Dict[str, Dict[str, float]] = Field(default_factory=dict)
    recurring_subscription_merchants: List[str] = Field(default_factory=list)
    recurring_subscription_amounts: Dict[str, float] = Field(default_factory=dict)
    commute_pattern: str = "mixed"
    night_activity_score: float = Field(default=0.4, ge=0.0, le=1.0)
    spending_intensity: float = Field(default=1.0, ge=0.4, le=1.8)
    savings_preference: float = Field(default=1.0, ge=0.4, le=1.8)


class Transaction(BaseModel):
    """Synthetic transaction record."""

    transaction_id: str
    user_id: str
    timestamp: datetime
    merchant: str
    category: str
    amount: float
    transaction_type: TransactionType
    balance_before: float
    balance_after: float
    persona: str
    spending_style: str
    savings_tendency: float
    merchant_loyalty: float
    impulse_buying_score: float
    lifestyle_score: float
    night_activity_score: float
    is_recurring: bool
    is_subscription: bool
    is_discretionary: bool
    recurrence_type: str
    session_id: str | None = None
    day_type: str
    balance_state: str
    is_overdraft: bool
    overdraft_amount: float
