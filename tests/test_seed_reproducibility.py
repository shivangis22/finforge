from finforge import DatasetGenerator


def test_same_seed_produces_identical_dataset() -> None:
    first = DatasetGenerator(seed=42).with_users(10).with_persona("salaried").for_months(3).generate()
    second = DatasetGenerator(seed=42).with_users(10).with_persona("salaried").for_months(3).generate()
    assert first.equals(second)
