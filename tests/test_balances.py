from finforge import DatasetGenerator


def test_balance_integrity() -> None:
    dataset = DatasetGenerator(seed=42).with_users(5).with_persona("salaried").for_months(2).generate()
    computed = (dataset["balance_before"] + dataset["amount"]).round(2)
    actual = dataset["balance_after"].round(2)
    assert computed.equals(actual)
