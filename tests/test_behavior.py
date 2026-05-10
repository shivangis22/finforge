from finforge import DatasetGenerator


def test_low_balance_discretionary_suppression() -> None:
    dataset = DatasetGenerator(seed=41).with_users(18).with_persona("student").for_months(5).generate()
    low = dataset[dataset["balance_state"] == "low"]
    normal = dataset[dataset["balance_state"] == "normal"]
    assert low["is_discretionary"].mean() < normal["is_discretionary"].mean()
    assert low["is_discretionary"].mean() < 0.70
    assert (low["category"] == "entertainment").mean() < (normal["category"] == "entertainment").mean()
    assert (low["category"] == "shopping").mean() < (normal["category"] == "shopping").mean()


def test_no_unmarked_negative_balances() -> None:
    dataset = (
        DatasetGenerator(seed=52)
        .with_users(12)
        .with_persona("student")
        .for_months(4)
        .with_overdraft(500.0)
        .generate()
    )
    negative = dataset[dataset["balance_after"] < 0]
    if not negative.empty:
        assert negative["is_overdraft"].all()
        assert (negative["overdraft_amount"].round(2) == negative["balance_after"].abs().round(2)).all()
    non_negative = dataset[dataset["balance_after"] >= 0]
    assert (~non_negative["is_overdraft"]).all()
    assert (non_negative["overdraft_amount"] == 0.0).all()


def test_prevent_negative_balance_mode() -> None:
    dataset = (
        DatasetGenerator(seed=63)
        .with_users(10)
        .with_persona("student")
        .for_months(4)
        .prevent_negative_balance(True)
        .with_overdraft(0.0)
        .generate()
    )
    violating = dataset[(dataset["is_discretionary"]) & (dataset["balance_after"] < 0)]
    assert violating.empty


def test_transaction_clusters_exist_within_short_windows() -> None:
    dataset = DatasetGenerator(seed=95).with_users(5).with_persona("salaried").for_months(2).generate()
    dataset["date"] = dataset["timestamp"].dt.date
    clustered = False
    for _, group in dataset.groupby(["user_id", "date"]):
        timestamps = list(group["timestamp"].sort_values())
        for index in range(1, len(timestamps)):
            if (timestamps[index] - timestamps[index - 1]).total_seconds() <= 2.5 * 3600:
                clustered = True
                break
        if clustered:
            break
    assert clustered


def test_session_rate_is_reasonable() -> None:
    dataset = DatasetGenerator(seed=88).with_users(20).with_persona("student").for_months(4).generate()
    recurring = dataset[dataset["is_recurring"]]
    assert recurring["session_id"].isna().all()
    overall_session_rate = dataset["session_id"].notna().mean()
    discretionary_session_rate = dataset[dataset["is_discretionary"]]["session_id"].notna().mean()
    assert overall_session_rate <= 0.75
    assert discretionary_session_rate <= 0.90
    per_user = (
        dataset.assign(session_linked=dataset["session_id"].notna())
        .groupby(["user_id", "spending_style"])["session_linked"]
        .mean()
        .reset_index()
    )
    style_rates = per_user.groupby("spending_style")["session_linked"].mean().to_dict()
    if "minimalist" in style_rates and "impulsive_student" in style_rates:
        assert style_rates["minimalist"] < style_rates["impulsive_student"]
