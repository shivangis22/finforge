"""Public fluent dataset generation API."""

from __future__ import annotations

from pathlib import Path
from typing import Optional, Union

import pandas as pd

from finforge.behavior.adaptive_spending import AdaptiveSpendingEngine
from finforge.behavior.budgeting import BudgetingEngine
from finforge.behavior.identity import IdentityEngine
from finforge.behavior.lifecycle import FinancialLifecycleEngine
from finforge.behavior.merchant_affinity import MerchantAffinityModel
from finforge.behavior.overdraft import OverdraftPolicy
from finforge.behavior.subscriptions import SubscriptionEngine
from finforge.behavior.sessions import TransactionSessionEngine
from finforge.core.config import GenerationConfig
from finforge.core.enums import PersonaType
from finforge.exporters.csv_exporter import CsvExporter
from finforge.generators.scheduler import TransactionScheduler
from finforge.generators.transaction_generator import TransactionGenerator
from finforge.merchants.catalog import DEFAULT_MERCHANT_CATALOG
from finforge.generators.user_generator import UserGenerator
from finforge.personas.base import BasePersona
from finforge.personas.salaried import SalariedPersona
from finforge.personas.student import StudentPersona
from finforge.utils.dates import parse_date
from finforge.utils.randomness import RandomContext


class DatasetGenerator:
    """Fluent API for generating synthetic financial transaction datasets."""

    def __init__(self, seed: Optional[int] = None, start_date: str = "2026-01-01") -> None:
        self.config = GenerationConfig(seed=seed, start_date=start_date)
        self.random_context = RandomContext(seed=seed)
        self.merchant_catalog = DEFAULT_MERCHANT_CATALOG
        self.identity_engine = IdentityEngine(self.random_context)
        self.subscription_engine = SubscriptionEngine(self.random_context)
        self.merchant_affinity_model = MerchantAffinityModel(
            self.random_context,
            self.merchant_catalog,
            self.subscription_engine,
        )
        self.user_generator = UserGenerator(
            self.random_context,
            self.identity_engine,
            self.merchant_affinity_model,
        )
        self.scheduler = TransactionScheduler(self.random_context)
        self.budgeting_engine = BudgetingEngine()
        self.adaptive_spending_engine = AdaptiveSpendingEngine(self.budgeting_engine)
        self.lifecycle_engine = FinancialLifecycleEngine(self.random_context)
        self.session_engine = TransactionSessionEngine(self.random_context)
        self.overdraft_policy = OverdraftPolicy(
            prevent_negative_balance=self.config.prevent_negative_balance,
            allow_overdraft=self.config.allow_overdraft,
            overdraft_limit=self.config.overdraft_limit,
        )
        self.transaction_generator = TransactionGenerator(
            random_context=self.random_context,
            scheduler=self.scheduler,
            budgeting_engine=self.budgeting_engine,
            adaptive_spending_engine=self.adaptive_spending_engine,
            lifecycle_engine=self.lifecycle_engine,
            session_engine=self.session_engine,
            overdraft_policy=self.overdraft_policy,
            merchant_catalog=self.merchant_catalog,
        )
        self.csv_exporter = CsvExporter()
        self._dataframe: Optional[pd.DataFrame] = None

    def with_users(self, count: int) -> "DatasetGenerator":
        """Configure the number of synthetic users."""
        self.config.user_count = count
        return self

    def with_persona(self, persona: str) -> "DatasetGenerator":
        """Configure the persona used for user behavior."""
        self.config.persona = PersonaType(persona)
        return self

    def for_months(self, months: int) -> "DatasetGenerator":
        """Configure how many months of transactions to simulate."""
        self.config.months = months
        return self

    def starting(self, start_date: str) -> "DatasetGenerator":
        """Configure the starting month for simulation."""
        self.config.start_date = start_date
        return self

    def prevent_negative_balance(self, enabled: bool = True) -> "DatasetGenerator":
        """Toggle prevention of negative balances."""
        self.config.prevent_negative_balance = enabled
        self.overdraft_policy.prevent_negative_balance = enabled
        return self

    def with_overdraft(self, overdraft_limit: float) -> "DatasetGenerator":
        """Allow overdrafts up to a configured limit."""
        self.config.allow_overdraft = overdraft_limit > 0
        self.config.overdraft_limit = max(overdraft_limit, 0.0)
        self.overdraft_policy.allow_overdraft = self.config.allow_overdraft
        self.overdraft_policy.overdraft_limit = self.config.overdraft_limit
        return self

    def generate(self) -> pd.DataFrame:
        """Generate a pandas dataframe of synthetic transactions."""
        persona = self._persona_for(self.config.persona)
        users = self.user_generator.generate(
            count=self.config.user_count,
            persona=self.config.persona,
            persona_definition=persona,
        )
        transactions = self.transaction_generator.generate_for_users(
            users=users,
            persona=persona,
            months=self.config.months,
            start_date=parse_date(self.config.start_date),
        )
        self._dataframe = pd.DataFrame([transaction.model_dump() for transaction in transactions])
        if not self._dataframe.empty:
            self._dataframe = self._dataframe.sort_values(
                by=["user_id", "timestamp", "transaction_id"]
            ).reset_index(drop=True)
        return self._dataframe

    def export_csv(self, path: Union[str, Path]) -> Path:
        """Export the most recently generated dataset to CSV."""
        if self._dataframe is None:
            self.generate()
        assert self._dataframe is not None
        return self.csv_exporter.export(self._dataframe, path)

    def _persona_for(self, persona_type: PersonaType) -> BasePersona:
        """Map persona enum to implementation."""
        if persona_type == PersonaType.SALARIED:
            return SalariedPersona()
        if persona_type == PersonaType.STUDENT:
            return StudentPersona()
        raise ValueError(f"Unsupported persona: {persona_type}")
