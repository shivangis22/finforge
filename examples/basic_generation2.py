from finforge import DatasetGenerator

generator = (
    DatasetGenerator(seed=42)
    .with_users(5)
    .with_persona("student")
    .for_months(1)
)

dataset = generator.generate()
generator.export_csv("transactions.csv")
