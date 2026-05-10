from finforge import DatasetGenerator


def test_salaried_persona_includes_salary_rent_and_utilities() -> None:
    dataset = DatasetGenerator(seed=3).with_users(1).with_persona("salaried").for_months(1).generate()
    merchants = set(dataset["merchant"])
    assert "Acme Payroll" in merchants
    assert "Green Residency" in merchants
    assert "City Power" in merchants


def test_student_persona_has_lower_income_and_more_entertainment_share() -> None:
    salaried = DatasetGenerator(seed=11).with_users(8).with_persona("salaried").for_months(2).generate()
    student = DatasetGenerator(seed=11).with_users(8).with_persona("student").for_months(2).generate()

    salaried_income = salaried[salaried["category"] == "income"]["amount"].mean()
    student_income = student[student["category"] == "income"]["amount"].mean()
    salaried_entertainment_share = (salaried["category"] == "entertainment").mean()
    student_entertainment_share = (student["category"] == "entertainment").mean()

    assert student_income < salaried_income
    assert student_entertainment_share > salaried_entertainment_share


def test_salaried_balances_are_more_stable_than_student_balances() -> None:
    salaried = DatasetGenerator(seed=51).with_users(10).with_persona("salaried").for_months(2).generate()
    student = DatasetGenerator(seed=51).with_users(10).with_persona("student").for_months(2).generate()

    salaried_negative_ratio = (salaried["balance_after"] < 300).mean()
    student_negative_ratio = (student["balance_after"] < 300).mean()

    assert salaried_negative_ratio < student_negative_ratio


def test_students_have_more_night_activity_than_salaried_users() -> None:
    salaried = DatasetGenerator(seed=19).with_users(8).with_persona("salaried").for_months(2).generate()
    student = DatasetGenerator(seed=19).with_users(8).with_persona("student").for_months(2).generate()
    salaried_night = (salaried["timestamp"].dt.hour >= 21).mean()
    student_night = (student["timestamp"].dt.hour >= 21).mean()
    assert student_night > salaried_night


def test_behavioral_identity_affects_generation() -> None:
    dataset = DatasetGenerator(seed=77).with_users(40).with_persona("student").for_months(3).generate()
    user_styles = dataset.groupby("user_id")["spending_style"].nunique()
    assert (user_styles == 1).all()
    transaction_counts = dataset.groupby(["user_id", "spending_style"]).size().reset_index(name="transaction_count")
    style_means = transaction_counts.groupby("spending_style")["transaction_count"].mean().to_dict()
    if "minimalist" in style_means and "budget_conscious" in style_means:
        assert style_means["minimalist"] < style_means["budget_conscious"]
    if "budget_conscious" in style_means and "impulsive_student" in style_means:
        assert style_means["budget_conscious"] < style_means["impulsive_student"]
    late_night = dataset.assign(late_night=dataset["timestamp"].dt.hour >= 21)
    late_night_rates = late_night.groupby("spending_style")["late_night"].mean().to_dict()
    if "impulsive_student" in late_night_rates and "budget_conscious" in late_night_rates:
        assert late_night_rates["impulsive_student"] > late_night_rates["budget_conscious"]
