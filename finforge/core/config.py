"""Configuration models for dataset generation."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field, field_validator

from finforge.core.constants import DEFAULT_MONTHS, DEFAULT_START_DATE, DEFAULT_USER_COUNT
from finforge.core.enums import PersonaType


class GenerationConfig(BaseModel):
    """User-facing configuration for dataset generation."""

    user_count: int = Field(default=DEFAULT_USER_COUNT, ge=1)
    persona: PersonaType = PersonaType.SALARIED
    months: int = Field(default=DEFAULT_MONTHS, ge=1, le=60)
    start_date: str = DEFAULT_START_DATE
    seed: Optional[int] = None
    prevent_negative_balance: bool = True
    allow_overdraft: bool = False
    overdraft_limit: float = Field(default=0.0, ge=0.0)

    @field_validator("start_date")
    @classmethod
    def validate_start_date(cls, value: str) -> str:
        """Ensure the date string uses ISO date format."""
        if len(value.split("-")) != 3:
            raise ValueError("start_date must use ISO format YYYY-MM-DD")
        return value
