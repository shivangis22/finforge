"""Overdraft policy decisions."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class OverdraftDecision:
    """Outcome of evaluating whether a transaction may be applied."""

    allowed: bool
    resulting_balance: float
    is_overdraft: bool
    overdraft_amount: float


class OverdraftPolicy:
    """Applies configurable negative-balance rules."""

    def __init__(
        self,
        prevent_negative_balance: bool = True,
        allow_overdraft: bool = False,
        overdraft_limit: float = 0.0,
    ) -> None:
        self.prevent_negative_balance = prevent_negative_balance
        self.allow_overdraft = allow_overdraft
        self.overdraft_limit = overdraft_limit

    def evaluate(
        self,
        balance_before: float,
        amount: float,
        is_discretionary: bool,
    ) -> OverdraftDecision:
        """Decide whether a transaction can be applied."""
        resulting_balance = round(balance_before + amount, 2)
        if resulting_balance >= 0:
            return OverdraftDecision(True, resulting_balance, False, 0.0)

        overdraft_amount = round(abs(resulting_balance), 2)
        if is_discretionary and self.prevent_negative_balance:
            return OverdraftDecision(False, balance_before, False, 0.0)

        if self.allow_overdraft and overdraft_amount <= self.overdraft_limit:
            return OverdraftDecision(True, resulting_balance, True, overdraft_amount)

        return OverdraftDecision(False, balance_before, False, 0.0)
