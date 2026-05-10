# FinForge v1.0

FinForge is a synthetic financial transaction data generation framework for developers, QA teams, and analytics engineers who need realistic transaction datasets without using production customer records.

Unlike basic fake data libraries, FinForge focuses on behavioral simulation: persona-driven users, persistent financial identities, recurring cash flows, spending memory, merchant loyalty, monthly stress cycles, chronological balance updates, and deterministic reproducibility for testing and benchmarking.

## Why FinForge v1.0 Is Different

FinForge v1.0 simulates persistent financial lives instead of generating isolated fake rows.

- Persistent user identity: each user carries a stable spending style, merchant loyalty profile, night activity score, and savings tendency.
- Temporal financial rhythm: salaries, transfers, bills, and subscriptions follow a repeatable monthly cadence.
- Realistic behavioral adaptation: low-balance users pull back discretionary spending, while stronger spenders show more weekend and late-night activity.
- Reproducible synthetic data: the same seed and config produce the same dataset, which makes FinForge practical for testing and benchmarking.

## Problem Statement

Financial applications often need transaction histories that are:

- realistic enough to exercise business logic
- reproducible enough for automated testing
- structured enough for analytics experiments
- safe enough to share across teams

Most generic fake data tools generate isolated rows. Real financial systems need temporally consistent histories where balances evolve over time, transactions follow plausible cadence, and spending patterns reflect customer behavior.

FinForge addresses that gap.

## Features

- Synthetic user generation with configurable personas
- Persona-driven transaction generation with persistent user habits
- Persistent user identity traits such as spending style, merchant loyalty, and commute pattern
- Chronologically ordered event simulation
- Deterministic seed support for reproducible datasets
- Realistic recurring events like salary, rent, and subscriptions
- Merchant/category consistency with merchant affinity reuse
- Weekend vs weekday spending behavior
- Balance-aware suppression of discretionary spending
- Spending memory and overspend suppression
- Dedicated subscription engine with once-per-month recurrence
- Explicit overdraft metadata and configurable negative-balance handling
- Month-end spending compression and salary-cycle effects
- Clustered daily transaction bursts that feel session-like
- Spending-style frequency calibration for `minimalist`, `budget_conscious`, `lifestyle_spender`, and `impulsive_student`
- Running balance tracking
- Pandas DataFrame output
- CSV export utilities

## Installation

```bash
pip install -e .
```

Or install dependencies manually:

```bash
pip install -r requirements.txt
```

## Quickstart

```python
from finforge import DatasetGenerator

dataset = (
    DatasetGenerator(seed=42)
    .with_users(100)
    .with_persona("salaried")
    .for_months(6)
    .generate()
)

print(dataset.head())
```

Export to CSV:

```python
from finforge import DatasetGenerator

generator = (
    DatasetGenerator(seed=42)
    .with_users(25)
    .with_persona("student")
    .for_months(3)
)

dataset = generator.generate()
generator.export_csv("student_transactions.csv")
```

The public API remains fluent and backward-compatible:

```python
from finforge import DatasetGenerator

dataset = (
    DatasetGenerator(seed=101)
    .with_users(3)
    .with_persona("student")
    .for_months(2)
    .generate()
)

dataset.to_csv("transactionsBehaviour.csv", index=False)
```

Overdraft controls are configurable without changing the public API shape:

```python
dataset = (
    DatasetGenerator(seed=7)
    .with_users(10)
    .with_persona("student")
    .for_months(2)
    .prevent_negative_balance(True)
    .with_overdraft(0.0)
    .generate()
)
```

## Architecture Overview

FinForge is organized into small, composable modules:

- `finforge.core`: shared models, enums, constants, and configuration
- `finforge.personas`: persona definitions and behavioral profiles
- `finforge.generators`: user generation, scheduling, and transaction generation
- `finforge.merchants`: category-safe merchant catalog
- `finforge.utils`: randomness, dates, and balance helpers
- `finforge.exporters`: output adapters such as CSV
- `finforge.dataset`: fluent public API surface

The v1.0 architecture keeps future local-model extensions possible while keeping all LLM-related functionality out of the runtime path for now.

Behavioral simulation components live under `finforge.behavior`:

- `identity.py`: long-lived user behavioral identities
- `merchant_affinity.py`: persistent merchant preferences and reuse weights
- `adaptive_spending.py`: liquidity and overspend-aware daily spending controls
- `subscriptions.py`: dedicated subscription assignment and stable monthly pricing
- `overdraft.py`: explicit negative-balance policy decisions
- `budgeting.py`: rolling budget memory and spending pressure
- `lifecycle.py`: monthly cashflow rhythm and student irregular inflows
- `sessions.py`: grouped temporal spending sessions

## Example Output

Example generated schema:

| transaction_id | user_id | timestamp | merchant | category | amount | spending_style | is_subscription | recurrence_type | balance_state | session_id |
| --- | --- | --- | --- | --- | ---: | --- | --- | --- | --- | --- |
| txn_000001 | user_000001 | 2026-01-01 09:14:00 | Acme Payroll | income | 5840.00 | budget_conscious | False | income | normal |  |
| txn_000002 | user_000001 | 2026-01-03 10:05:00 | Green Residency | housing | -1450.00 | budget_conscious | False | bill | normal |  |
| txn_000003 | user_000001 | 2026-01-05 20:11:00 | Netflix | subscription | -649.00 | budget_conscious | True | subscription | normal |  |

Typical generated behavior now includes:

- recurring salary and bill cadence near the beginning of each month
- subscriptions generated only by the recurring engine, never by random entertainment spending
- exactly one subscription row per assigned merchant per simulated month
- repeated use of a user’s preferred merchants
- persistent user styles such as `budget_conscious`, `lifestyle_spender`, and `impulsive_student`
- stronger commute and coffee activity on weekdays
- more entertainment and food delivery on weekends
- student late-night activity and irregular top-up inflows
- smaller discretionary tickets when balances run low
- behavioral pullback after recent overspending
- overdrafts either prevented or explicitly marked with `is_overdraft` and `overdraft_amount`
- clustered bursts such as `Uber -> Coffee -> Lunch`

## Metadata Columns

Generated transaction rows include behavioral metadata that is useful for testing and downstream modeling:

- `persona`
- `spending_style`
- `savings_tendency`
- `merchant_loyalty`
- `impulse_buying_score`
- `lifestyle_score`
- `night_activity_score`
- `is_recurring`
- `is_subscription`
- `is_discretionary`
- `recurrence_type`
- `session_id`
- `day_type`
- `balance_state`
- `is_overdraft`
- `overdraft_amount`

## Testing Guarantees

The v1.0 test suite verifies:

- balance integrity on every row
- chronological ordering per user
- seed reproducibility
- subscription recurrence and amount stability
- low-balance discretionary suppression
- reasonable session-linked rates
- merchant-category consistency
- required behavioral metadata columns
- explicit overdraft marking whenever balances go negative

## Roadmap

- Additional personas for freelancers, retirees, and small business owners
- More nuanced cash flow events and seasonal behavior
- Local Ollama-backed narrative and explanation modules
- Richer export formats and scenario presets
- Extended validation and benchmarking datasets

## Contributing

Contributions are welcome. Good first contributions include:

- new persona modules
- expanded merchant catalogs
- improved temporal rules
- additional exporters
- stronger test coverage

To contribute:

1. Fork the repository
2. Create a feature branch
3. Add tests for behavior changes
4. Run `pytest`
5. Open a pull request with a clear description of the use case

## Development

```bash
pip install -e .[dev]
pytest
```

## License

MIT
