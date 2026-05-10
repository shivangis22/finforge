"""Basic FinForge usage example."""

from finforge import DatasetGenerator


def main() -> None:
    dataset = (
        DatasetGenerator(seed=42)
        .with_users(10)
        .with_persona("salaried")
        .for_months(3)
        .generate()
    )
    print(dataset.head(10).to_string(index=False))
    print("\nMonthly merchant reuse snapshot:")
    print(dataset.groupby(["user_id", "merchant"]).size().sort_values(ascending=False).head(10).to_string())


if __name__ == "__main__":
    main()
