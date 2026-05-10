"""Enumeration types used across the package."""

from enum import Enum


class PersonaType(str, Enum):
    """Supported persona names."""

    SALARIED = "salaried"
    STUDENT = "student"


class TransactionType(str, Enum):
    """Financial transaction direction."""

    CREDIT = "credit"
    DEBIT = "debit"
