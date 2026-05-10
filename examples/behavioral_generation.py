"""Example focused on behavioral simulation outputs."""

from finforge import DatasetGenerator


def main() -> None:
    generator = (
        DatasetGenerator(seed=101)
        .with_users(3)
        .with_persona("student")
        .for_months(2)
    )

    columns = [
        "user_id",
        "timestamp",
        "merchant",
        "category",
        "amount",
        "balance_before",
        "balance_after",
        "spending_style",
        "balance_state",
        "is_subscription",
        "session_id",
    ]
    dataset = generator.generate()

    generator.export_csv("transactionsBehaviour3.csv")

    print("Sample transactions")
    print(dataset[columns].head(25).to_string(index=False))
    print("\nNight activity snapshot")
    print(
        dataset[dataset["timestamp"].dt.hour >= 21][["user_id", "timestamp", "merchant", "category"]]
        .head(10)
        .to_string(index=False)
    )
    print("\nSubscription summary")
    subscriptions = dataset[dataset["is_subscription"]][["user_id", "merchant", "amount", "timestamp"]].copy()
    subscriptions["month"] = subscriptions["timestamp"].dt.to_period("M")
    print(subscriptions[["user_id", "month", "merchant", "amount"]].to_string(index=False))
    print("\nSession rate summary")
    print(f"Overall session-linked rate: {dataset['session_id'].notna().mean():.2%}")
    print(f"Discretionary session-linked rate: {dataset[dataset['is_discretionary']]['session_id'].notna().mean():.2%}")
    print("\nLow balance spending summary")
    low_balance = dataset[dataset["balance_state"] == "low"]
    normal_balance = dataset[dataset["balance_state"] == "normal"]
    print(f"Low balance discretionary rate: {low_balance['is_discretionary'].mean():.2%}")
    print(f"Normal balance discretionary rate: {normal_balance['is_discretionary'].mean():.2%}")
    print("\nSpending style summary")
    print(
        dataset.groupby(["user_id", "spending_style"])
        .size()
        .reset_index(name="transaction_count")
        .groupby("spending_style")["transaction_count"]
        .mean()
        .round(2)
        .to_string()
    )


if __name__ == "__main__":
    main()
