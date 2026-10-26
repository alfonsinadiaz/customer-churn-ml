from pathlib import Path

from src.data.load_data import load_dataset


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = PROJECT_ROOT / "data" / "raw" / "customer_churn_historical.csv"


def main() -> None:
    data = load_dataset(DATA_PATH)
    print(f"Dimensiones: {data.shape[0]} filas, {data.shape[1]} columnas")
    print(f"Filas duplicadas: {data.duplicated().sum()}")
    print("\nValores faltantes:")
    print(data.isna().sum()[lambda values: values > 0])
    print("\nDistribución de Churn:")
    print((data["Churn"].value_counts(normalize=True) * 100).round(2))
    print("\nTasa de churn por contrato:")
    print((data.groupby("Contract")["Churn"].apply(lambda values: values.eq("Yes").mean()) * 100).round(2))
    print("\nTasa de churn por servicio de Internet:")
    print((data.groupby("InternetService")["Churn"].apply(lambda values: values.eq("Yes").mean()) * 100).round(2))


if __name__ == "__main__":
    main()
