from pathlib import Path

import pandas as pd


TARGET = "Churn"
IDENTIFIER = "customerID"


def load_dataset(path: str | Path) -> pd.DataFrame:
    """Carga el CSV y transforma SeniorCitizen en una categoría."""
    data = pd.read_csv(path)
    data["SeniorCitizen"] = data["SeniorCitizen"].map({0: "No", 1: "Yes"})
    return data


def split_features_target(data: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    """Separa predictores y objetivo, excluyendo el identificador."""
    features = data.drop(columns=[TARGET, IDENTIFIER])
    target = data[TARGET].map({"No": 0, "Yes": 1})
    return features, target
