"""Balance computation helpers."""

from __future__ import annotations


def apply_balance(balance: float, amount: float) -> tuple[float, float]:
    """Return balance_before and balance_after for a transaction."""
    balance_before = round(balance, 2)
    balance_after = round(balance_before + amount, 2)
    return balance_before, balance_after
