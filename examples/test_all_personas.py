"""Test FinForge behavior across all supported personas."""

import pandas as pd
from finforge import DatasetGenerator


PERSONAS = ["student", "salaried"]


def summarize_dataset(df: pd.DataFrame, persona: str) -> None:
    print("\n" + "=" * 80)
    print(f"PERSONA: {persona.upper()}")
    print("=" * 80)

    print("\nBasic Summary")
    print("Rows:", len(df))
    print("Users:", df["user_id"].nunique())
    print("Date range:", df["timestamp"].min(), "to", df["timestamp"].max())

    print("\nTransactions by User")
    print(df.groupby(["user_id", "spending_style"]).size())

    print("\nCategory Distribution")
    print(df["category"].value_counts())

    print("\nTransaction Type Distribution")
    print(df["transaction_type"].value_counts())

    print("\nDiscretionary Rate by Balance State")
    if "balance_state" in df.columns:
        print(df.groupby("balance_state")["is_discretionary"].mean())

    print("\nSession Rate")
    if "session_id" in df.columns:
        session_rate = df["session_id"].notna().mean()
        print(round(session_rate, 3))

    print("\nSession Rate by Spending Style")
    if "session_id" in df.columns:
        print(df.groupby("spending_style")["session_id"].apply(lambda s: s.notna().mean()))

    print("\nRecurring Transactions")
    if "recurrence_type" in df.columns:
        print(df["recurrence_type"].value_counts())

    print("\nSubscription Summary")
    if "is_subscription" in df.columns:
        sub_df = df[df["is_subscription"] == True].copy()
        if not sub_df.empty:
            sub_df["month"] = pd.to_datetime(sub_df["timestamp"]).dt.to_period("M")
            print(sub_df.groupby(["user_id", "merchant", "month"]).size())
        else:
            print("No subscriptions found.")

    print("\nNegative Balances")
    print((df["balance_after"] < 0).sum())

    print("\nBalance Integrity Check")
    mismatch = (
        df["balance_after"].round(2)
        != (df["balance_before"] + df["amount"]).round(2)
    )
    print("Balance mismatches:", mismatch.sum())

    print("\nSample Rows")
    columns = [
        "user_id",
        "persona",
        "spending_style",
        "timestamp",
        "merchant",
        "category",
        "amount",
        "balance_before",
        "balance_after",
        "is_recurring",
        "is_discretionary",
        "balance_state",
        "session_id",
    ]

    available_columns = [col for col in columns if col in df.columns]
    print(df[available_columns].head(20).to_string(index=False))


def main() -> None:
    for persona in PERSONAS:
        df = (
            DatasetGenerator(seed=101)
            .with_users(10)
            .with_persona(persona)
            .for_months(3)
            .generate()
        )

        output_path = f"{persona}_behavior_v1.csv"
        df.to_csv(output_path, index=False)

        summarize_dataset(df, persona)

        print(f"\nSaved CSV: {output_path}")


if __name__ == "__main__":
    main()