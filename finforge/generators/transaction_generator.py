"""Persona-driven transaction generation engine."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import date
from typing import Any

from finforge.behavior.adaptive_spending import AdaptiveSpendingEngine
from finforge.behavior.budgeting import BudgetingEngine, UserBudgetState
from finforge.behavior.lifecycle import FinancialLifecycleEngine
from finforge.behavior.overdraft import OverdraftPolicy
from finforge.behavior.sessions import TransactionSessionEngine
from finforge.core.enums import TransactionType
from finforge.core.models import Transaction, User
from finforge.generators.scheduler import TransactionScheduler
from finforge.merchants.catalog import DEFAULT_MERCHANT_CATALOG, MerchantCatalog
from finforge.personas.base import BasePersona, SpendingProfile
from finforge.utils.balances import apply_balance
from finforge.utils.dates import month_start
from finforge.utils.randomness import RandomContext


class TransactionGenerator:
    """Generates temporally consistent transactions for users."""

    def __init__(
        self,
        random_context: RandomContext,
        scheduler: TransactionScheduler,
        budgeting_engine: BudgetingEngine,
        adaptive_spending_engine: AdaptiveSpendingEngine,
        lifecycle_engine: FinancialLifecycleEngine,
        session_engine: TransactionSessionEngine,
        overdraft_policy: OverdraftPolicy,
        merchant_catalog: MerchantCatalog = DEFAULT_MERCHANT_CATALOG,
    ) -> None:
        self.random_context = random_context
        self.scheduler = scheduler
        self.budgeting_engine = budgeting_engine
        self.adaptive_spending_engine = adaptive_spending_engine
        self.lifecycle_engine = lifecycle_engine
        self.session_engine = session_engine
        self.overdraft_policy = overdraft_policy
        self.merchant_catalog = merchant_catalog
        self.transaction_counter = 0
        self.session_counter = 0

    def generate_for_users(
        self,
        users: Iterable[User],
        persona: BasePersona,
        months: int,
        start_date: date,
    ) -> list[Transaction]:
        """Generate transactions for a group of users."""
        transactions: list[Transaction] = []
        for user in users:
            transactions.extend(self.generate_for_user(user=user, persona=persona, months=months, start_date=start_date))
        return sorted(transactions, key=lambda item: (item.user_id, item.timestamp, item.transaction_id))

    def generate_for_user(
        self,
        user: User,
        persona: BasePersona,
        months: int,
        start_date: date,
    ) -> list[Transaction]:
        """Generate transactions for a single user."""
        state = self.budgeting_engine.start_user(user)
        transactions: list[Transaction] = []
        spending_profile = persona.spending_profile()

        for offset in range(months):
            current_month = month_start(start_date, offset)
            self.budgeting_engine.start_month(state, user)
            month_transactions, balance = self._simulate_month(
                user=user,
                persona=persona,
                current_month=current_month,
                spending_profile=spending_profile,
                state=state,
            )
            state.balance = balance
            transactions.extend(month_transactions)

        return transactions

    def _simulate_month(
        self,
        user: User,
        persona: BasePersona,
        current_month: date,
        spending_profile: SpendingProfile,
        state: UserBudgetState,
    ) -> tuple[list[Transaction], float]:
        """Simulate a full month in chronological order."""
        recurring_events_by_day: dict[int, list[dict[str, Any]]] = {}
        for event in persona.recurring_events(user):
            timestamp = self.scheduler.recurring_timestamp(current_month, event)
            recurring_events_by_day.setdefault(timestamp.day, []).append(
                {
                    "timestamp": timestamp,
                    "merchant": event.merchant,
                    "category": event.category,
                    "amount": round(event.amount, 2),
                    "is_recurring": True,
                    "is_subscription": event.is_subscription,
                    "is_discretionary": False,
                    "recurrence_type": event.recurrence_type,
                    "session_id": None,
                }
            )

        balance = state.balance
        transactions: list[Transaction] = []
        next_month = month_start(current_month, 1)
        days_in_month = (next_month - current_month).days

        for day in range(1, days_in_month + 1):
            daily_entries = sorted(recurring_events_by_day.get(day, []), key=lambda item: item["timestamp"])
            for raw_transaction in daily_entries:
                if not self._can_apply(raw_transaction, balance):
                    continue
                transaction, balance = self._materialize_transaction(user, raw_transaction, balance)
                self.budgeting_engine.record_transaction(state, transaction.amount, transaction.category)
                state.balance = balance
                transactions.append(transaction)

            target_date = current_month.replace(day=day)
            lifecycle = self.lifecycle_engine.context_for_day(
                user=user,
                target_date=target_date,
                state=state,
                days_in_month=days_in_month,
            )
            signal = self.adaptive_spending_engine.assess(
                user=user,
                state=state,
                day_of_month=day,
                days_in_month=days_in_month,
                spending_profile=spending_profile,
            )
            cluster_requests = self.session_engine.plan_sessions(
                user=user,
                target_date=target_date,
                lifecycle=lifecycle,
                signal=signal,
                weekly_transaction_range=spending_profile.weekly_transaction_range,
                cluster_propensity=spending_profile.cluster_propensity,
                base_active_day_probability=spending_profile.base_active_day_probability,
            )
            remaining_commitments = self._remaining_recurring_commitments(
                recurring_events_by_day=recurring_events_by_day,
                current_day=day,
            )

            raw_spends: list[dict[str, Any]] = []
            for cluster_request in cluster_requests:
                session_events = self.session_engine.build_session(target_date, cluster_request.template_name)
                session_id = self._next_session_id() if len(session_events) > 1 else None
                raw_spends.extend(
                    self._build_cluster_spend(
                        user=user,
                        template_name=cluster_request.template_name,
                        amount_multiplier=signal.amount_multiplier,
                        category_multipliers=signal.category_multipliers,
                        category_amount_multipliers=signal.amount_multipliers,
                        state=state,
                        monthly_income=user.monthly_income,
                        balance_state=signal.state,
                        session_id=session_id,
                        session_events=session_events,
                        remaining_commitments=remaining_commitments,
                    )
                )

            raw_spends.extend(
                self._materialize_lifecycle_inflows(
                    user=user,
                    target_date=target_date,
                    state=state,
                )
            )
            raw_spends = self._apply_low_balance_daily_cap(
                raw_spends=raw_spends,
                max_discretionary_transactions=signal.max_discretionary_transactions,
            )

            raw_spends.sort(key=lambda item: item["timestamp"])
            for raw_transaction in raw_spends:
                if not self._can_apply(raw_transaction, balance):
                    continue
                transaction, balance = self._materialize_transaction(user, raw_transaction, balance)
                self.budgeting_engine.record_transaction(state, transaction.amount, transaction.category)
                state.balance = balance
                transactions.append(transaction)

        return transactions, balance

    def _build_cluster_spend(
        self,
        user: User,
        template_name: str,
        amount_multiplier: float,
        category_multipliers: dict[str, float],
        category_amount_multipliers: dict[str, float],
        state: UserBudgetState,
        monthly_income: float,
        balance_state: str,
        session_id: str | None,
        session_events: list[Any],
        remaining_commitments: float,
    ) -> list[dict[str, Any]]:
        """Build spend events for a cluster template."""
        transactions: list[dict[str, Any]] = []
        projected_balance = state.balance
        for event in session_events:
            category = event.category
            category_multiplier = category_multipliers.get(category, 1.0)
            if projected_balance <= 0 and category in {"shopping", "entertainment"}:
                continue
            affinity_multiplier = user.category_affinities.get(category, 1.0)
            amount_limit_multiplier = (
                amount_multiplier
                * category_multiplier
                * category_amount_multipliers.get(category, 1.0)
                * affinity_multiplier
                * user.spending_intensity
            )
            merchant_weights = user.merchant_weights.get(category, {})
            merchant = self.merchant_catalog.pick_weighted(category, merchant_weights, self.random_context.rng)
            amount = self.merchant_catalog.amount_for(
                merchant,
                self.random_context.rng,
                amount_multiplier=amount_limit_multiplier,
            )
            affordability_cap = max(projected_balance * 0.22 + monthly_income * 0.08, amount * 0.72, 4.0)
            reserve_adjusted_cap = max(projected_balance - remaining_commitments, 0.0)
            affordability_cap = min(affordability_cap, max(reserve_adjusted_cap, amount * 0.35))
            if user.spending_style == "Minimalist" and category in {"shopping", "entertainment"}:
                affordability_cap *= 0.7
            if user.impulse_buying_score > 0.75 and category == "shopping":
                affordability_cap *= 1.15
            amount = min(amount, affordability_cap)
            if amount < 1.0:
                continue
            debit_amount = round(-amount, 2)
            decision = self.overdraft_policy.evaluate(
                balance_before=projected_balance,
                amount=debit_amount,
                is_discretionary=True,
            )
            if not decision.allowed:
                continue
            transactions.append(
                {
                    "timestamp": event.timestamp,
                    "merchant": merchant,
                    "category": category,
                    "amount": debit_amount,
                    "is_recurring": False,
                    "is_subscription": False,
                    "is_discretionary": True,
                    "recurrence_type": "none",
                    "session_id": session_id,
                    "balance_state": balance_state,
                }
            )
            projected_balance += debit_amount
        return transactions

    def _materialize_lifecycle_inflows(
        self,
        user: User,
        target_date: date,
        state: UserBudgetState,
    ) -> list[dict[str, Any]]:
        """Convert lifecycle inflow descriptors into timestamped transactions."""
        inflows = self.lifecycle_engine.irregular_income_for_day(user, target_date, state)
        results: list[dict[str, Any]] = []
        for inflow in inflows:
            if inflow["time_bucket"] == "afternoon":
                hour = self.random_context.rng.randint(13, 17)
            else:
                hour = self.random_context.rng.randint(10, 16)
            minute = self.random_context.rng.randint(0, 59)
            results.append(
                {
                    "timestamp": self.scheduler.random_time(target_date, hour, minute),
                    "merchant": inflow["merchant"],
                    "category": inflow["category"],
                    "amount": inflow["amount"],
                    "is_recurring": inflow["merchant"] == "Family Transfer",
                    "is_subscription": False,
                    "is_discretionary": False,
                    "recurrence_type": "income",
                    "session_id": None,
                }
            )
        return results

    def _materialize_transaction(
        self,
        user: User,
        raw_transaction: dict[str, Any],
        balance: float,
    ) -> tuple[Transaction, float]:
        """Turn a raw transaction payload into a validated transaction model."""
        amount = float(raw_transaction["amount"])
        is_discretionary = bool(raw_transaction.get("is_discretionary", False))
        decision = self.overdraft_policy.evaluate(
            balance_before=balance,
            amount=amount,
            is_discretionary=is_discretionary,
        )
        if not decision.allowed:
            raise ValueError("Attempted to materialize a disallowed transaction")
        balance_before, balance_after = apply_balance(balance, amount)
        day_type = "weekend" if raw_transaction["timestamp"].weekday() >= 5 else "weekday"
        balance_state = str(raw_transaction.get("balance_state") or self._balance_state_for_user(user, balance_before))
        transaction = Transaction(
            transaction_id=self._next_transaction_id(),
            user_id=user.user_id,
            timestamp=raw_transaction["timestamp"],
            merchant=str(raw_transaction["merchant"]),
            category=str(raw_transaction["category"]),
            amount=round(amount, 2),
            transaction_type=TransactionType.CREDIT if amount > 0 else TransactionType.DEBIT,
            balance_before=balance_before,
            balance_after=balance_after,
            persona=user.persona.value,
            spending_style=user.spending_style,
            savings_tendency=user.savings_tendency,
            merchant_loyalty=user.merchant_loyalty,
            impulse_buying_score=user.impulse_buying_score,
            lifestyle_score=user.lifestyle_score,
            night_activity_score=user.night_activity_score,
            is_recurring=bool(raw_transaction.get("is_recurring", False)),
            is_subscription=bool(raw_transaction.get("is_subscription", False)),
            is_discretionary=is_discretionary,
            recurrence_type=str(raw_transaction.get("recurrence_type", "none")),
            session_id=raw_transaction.get("session_id"),
            day_type=day_type,
            balance_state=balance_state,
            is_overdraft=decision.is_overdraft,
            overdraft_amount=decision.overdraft_amount,
        )
        return transaction, balance_after

    def _next_transaction_id(self) -> str:
        """Return a monotonically increasing transaction identifier."""
        self.transaction_counter += 1
        return f"txn_{self.transaction_counter:06d}"

    def _next_session_id(self) -> str:
        """Return a session identifier for clustered spending."""
        self.session_counter += 1
        return f"session_{self.session_counter:06d}"

    def _balance_state_for_user(self, user: User, balance: float) -> str:
        """Classify current balance state using persona-aware thresholds."""
        if user.persona.value == "student":
            if balance < 500:
                return "low"
            if balance > 5000:
                return "high"
            return "normal"
        if balance < 5000:
            return "low"
        if balance > 50000:
            return "high"
        return "normal"

    def _apply_low_balance_daily_cap(
        self,
        raw_spends: list[dict[str, Any]],
        max_discretionary_transactions: int | None,
    ) -> list[dict[str, Any]]:
        """Limit discretionary activity on low-balance days."""
        if max_discretionary_transactions is None:
            return raw_spends
        discretionary_count = 0
        filtered: list[dict[str, Any]] = []
        for spend in sorted(raw_spends, key=lambda item: item["timestamp"]):
            if not bool(spend.get("is_discretionary", False)):
                filtered.append(spend)
                continue
            if discretionary_count >= max_discretionary_transactions:
                continue
            filtered.append(spend)
            discretionary_count += 1
        return filtered

    def _can_apply(self, raw_transaction: dict[str, Any], balance: float) -> bool:
        """Check whether a transaction is allowed under overdraft rules."""
        decision = self.overdraft_policy.evaluate(
            balance_before=balance,
            amount=float(raw_transaction["amount"]),
            is_discretionary=bool(raw_transaction.get("is_discretionary", False)),
        )
        return decision.allowed

    def _remaining_recurring_commitments(
        self,
        recurring_events_by_day: dict[int, list[dict[str, Any]]],
        current_day: int,
    ) -> float:
        """Compute remaining negative recurring commitments after the current day."""
        remaining = 0.0
        for day, events in recurring_events_by_day.items():
            if day <= current_day:
                continue
            for event in events:
                if event["amount"] < 0 and event.get("recurrence_type") in {"subscription", "bill"}:
                    remaining += abs(float(event["amount"]))
        return round(remaining, 2)
