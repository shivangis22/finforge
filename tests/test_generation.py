from finforge import DatasetGenerator
from finforge.merchants.catalog import DEFAULT_MERCHANT_CATALOG


SUBSCRIPTION_MERCHANTS = {"Netflix", "Spotify", "Amazon Prime", "YouTube Premium"}


def test_transactions_are_chronological_per_user() -> None:
    dataset = DatasetGenerator(seed=7).with_users(4).with_persona("student").for_months(2).generate()
    for _, group in dataset.groupby("user_id"):
        timestamps = list(group["timestamp"])
        assert timestamps == sorted(timestamps)


def test_merchant_category_consistency() -> None:
    dataset = DatasetGenerator(seed=99).with_users(3).with_persona("salaried").for_months(1).generate()
    entertainment_merchants = set(DEFAULT_MERCHANT_CATALOG.merchants_by_category["entertainment"])
    for row in dataset.itertuples(index=False):
        assert DEFAULT_MERCHANT_CATALOG.category_for(row.merchant) == row.category
        if row.category == "entertainment":
            assert row.merchant in entertainment_merchants
            assert row.merchant not in SUBSCRIPTION_MERCHANTS


def test_subscription_once_per_month() -> None:
    dataset = DatasetGenerator(seed=13).with_users(8).with_persona("salaried").for_months(4).generate()
    subscriptions = dataset[dataset["merchant"].isin(SUBSCRIPTION_MERCHANTS)].copy()
    subscriptions["year_month"] = subscriptions["timestamp"].dt.to_period("M")
    counts = subscriptions.groupby(["user_id", "merchant", "year_month"]).size()
    assert (counts == 1).all()
    assert subscriptions["is_subscription"].all()
    assert subscriptions["is_recurring"].all()
    assert (subscriptions["recurrence_type"] == "subscription").all()
    assert (~subscriptions["is_discretionary"]).all()
    assert subscriptions["session_id"].isna().all()


def test_subscription_amount_stability() -> None:
    dataset = DatasetGenerator(seed=17).with_users(8).with_persona("student").for_months(4).generate()
    subscriptions = dataset[dataset["merchant"].isin(SUBSCRIPTION_MERCHANTS)]
    variation = subscriptions.groupby(["user_id", "merchant"])["amount"].nunique()
    assert (variation == 1).all()


def test_required_metadata_columns_exist() -> None:
    dataset = DatasetGenerator(seed=23).with_users(3).with_persona("student").for_months(1).generate()
    expected = {
        "persona",
        "spending_style",
        "savings_tendency",
        "merchant_loyalty",
        "impulse_buying_score",
        "lifestyle_score",
        "night_activity_score",
        "is_recurring",
        "is_subscription",
        "is_discretionary",
        "recurrence_type",
        "session_id",
        "day_type",
        "balance_state",
        "is_overdraft",
        "overdraft_amount",
    }
    assert expected.issubset(set(dataset.columns))


def test_large_positive_amounts_are_income_events() -> None:
    dataset = DatasetGenerator(seed=29).with_users(8).with_persona("salaried").for_months(2).generate()
    large_credits = dataset[dataset["amount"] > 250]
    assert not large_credits.empty
    assert set(large_credits["category"]) == {"income"}
