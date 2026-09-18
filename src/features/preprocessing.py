import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


NUMERIC_COLUMNS = ["tenure", "MonthlyCharges", "TotalCharges"]


def build_preprocessor(features: pd.DataFrame) -> ColumnTransformer:
    """Construye el mismo preprocesamiento utilizado en el notebook."""
    categorical_columns = [
        column for column in features.columns if column not in NUMERIC_COLUMNS
    ]

    numeric_pipeline = Pipeline(
        [
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )
    categorical_pipeline = Pipeline(
        [("one_hot", OneHotEncoder(handle_unknown="ignore"))]
    )

    return ColumnTransformer(
        [
            ("numeric", numeric_pipeline, NUMERIC_COLUMNS),
            ("categorical", categorical_pipeline, categorical_columns),
        ]
    )
