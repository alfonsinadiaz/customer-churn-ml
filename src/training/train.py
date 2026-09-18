import argparse
from pathlib import Path

import joblib
import pandas as pd
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

from src.data.load_data import load_dataset, split_features_target
from src.evaluation.metrics import classification_metrics
from src.features.preprocessing import build_preprocessor


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATA = PROJECT_ROOT / "data" / "raw" / "customer_churn_historical.csv"
DEFAULT_MODEL = PROJECT_ROOT / "models" / "churn_pipeline.joblib"
DEFAULT_RESULTS = PROJECT_ROOT / "results" / "generated" / "model_metrics.csv"


def model_candidates() -> dict[str, object]:
    return {
        "dummy": DummyClassifier(strategy="prior"),
        "logistic_regression": LogisticRegression(
            random_state=42,
            max_iter=1000,
            class_weight="balanced",
        ),
        "random_forest": RandomForestClassifier(
            random_state=42,
            n_estimators=100,
            max_depth=10,
            class_weight="balanced",
        ),
    }


def train(data_path: Path, model_path: Path, results_path: Path) -> pd.DataFrame:
    data = load_dataset(data_path)
    features, target = split_features_target(data)
    x_train, x_test, y_train, y_test = train_test_split(
        features,
        target,
        test_size=0.2,
        random_state=42,
        stratify=target,
    )

    rows = []
    fitted_pipelines = {}
    for name, estimator in model_candidates().items():
        pipeline = Pipeline(
            [
                ("preprocessor", build_preprocessor(x_train)),
                ("model", estimator),
            ]
        )
        pipeline.fit(x_train, y_train)
        predictions = pipeline.predict(x_test)
        probabilities = pipeline.predict_proba(x_test)[:, 1]
        rows.append({"model": name, **classification_metrics(y_test, predictions, probabilities)})
        fitted_pipelines[name] = pipeline

    results = pd.DataFrame(rows).sort_values(
        by=["recall", "f1", "roc_auc"], ascending=False
    )
    selected_name = str(results.iloc[0]["model"])

    model_path.parent.mkdir(parents=True, exist_ok=True)
    results_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(fitted_pipelines[selected_name], model_path)
    results.to_csv(results_path, index=False)

    print(results.round(3).to_string(index=False))
    print(f"\nModelo guardado: {model_path}")
    print(f"Resultados guardados: {results_path}")
    return results


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Entrena y compara modelos de churn")
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA)
    parser.add_argument("--model", type=Path, default=DEFAULT_MODEL)
    parser.add_argument("--results", type=Path, default=DEFAULT_RESULTS)
    return parser.parse_args()


if __name__ == "__main__":
    arguments = parse_args()
    train(arguments.data, arguments.model, arguments.results)
