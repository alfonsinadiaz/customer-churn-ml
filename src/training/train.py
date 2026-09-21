from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
from typing import Any

import joblib
import mlflow
import mlflow.sklearn
import pandas as pd
from mlflow.models import infer_signature
from sklearn.base import clone
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
DEFAULT_RESULTS = PROJECT_ROOT / "results" / "generated" / "experiment_results.csv"
MODEL_NAME = "customer-churn-candidate"
RANDOM_STATE = 42


def model_candidates() -> list[dict[str, Any]]:
    """Seis alternativas razonadas: baseline, lineales, umbral y árboles."""
    return [
        {
            "run_name": "dummy_prior",
            "family": "baseline",
            "threshold": 0.50,
            "model": DummyClassifier(strategy="prior"),
        },
        {
            "run_name": "logreg_c0.5",
            "family": "linear",
            "threshold": 0.50,
            "model": LogisticRegression(
                C=0.5, max_iter=1500, class_weight="balanced", random_state=RANDOM_STATE
            ),
        },
        {
            "run_name": "logreg_c1",
            "family": "linear",
            "threshold": 0.50,
            "model": LogisticRegression(
                C=1.0, max_iter=1500, class_weight="balanced", random_state=RANDOM_STATE
            ),
        },
        {
            "run_name": "logreg_c1_threshold035",
            "family": "linear_threshold",
            "threshold": 0.35,
            "model": LogisticRegression(
                C=1.0, max_iter=1500, class_weight="balanced", random_state=RANDOM_STATE
            ),
        },
        {
            "run_name": "random_forest_depth5",
            "family": "tree",
            "threshold": 0.50,
            "model": RandomForestClassifier(
                n_estimators=200,
                max_depth=5,
                class_weight="balanced",
                random_state=RANDOM_STATE,
                n_jobs=-1,
            ),
        },
        {
            "run_name": "random_forest_depth10",
            "family": "tree",
            "threshold": 0.50,
            "model": RandomForestClassifier(
                n_estimators=200,
                max_depth=10,
                class_weight="balanced",
                random_state=RANDOM_STATE,
                n_jobs=-1,
            ),
        },
    ]


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git_commit() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], text=True, stderr=subprocess.DEVNULL
        ).strip()
    except (FileNotFoundError, subprocess.CalledProcessError):
        return "unknown"


def pipeline_for(features: pd.DataFrame, estimator: object) -> Pipeline:
    return Pipeline(
        [
            ("preprocessor", build_preprocessor(features)),
            ("model", estimator),
        ]
    )


def evaluate(
    pipeline: Pipeline,
    features: pd.DataFrame,
    target: pd.Series,
    threshold: float,
) -> dict:
    probabilities = pipeline.predict_proba(features)[:, 1]
    predictions = (probabilities >= threshold).astype(int)
    return classification_metrics(target, predictions, probabilities)


def log_pipeline(pipeline: Pipeline, features: pd.DataFrame) -> Any:
    input_example = features.head(3).copy()
    predictions = pipeline.predict(input_example)
    return mlflow.sklearn.log_model(
        sk_model=pipeline,
        name="model",
        input_example=input_example,
        signature=infer_signature(input_example, predictions),
    )


def run_experiments(
    data_path: Path,
    model_path: Path,
    results_path: Path,
    experiment: str,
    register_best: bool,
) -> pd.DataFrame:
    tracking_uri = os.getenv("MLFLOW_TRACKING_URI", "sqlite:///mlflow.db")
    mlflow.set_tracking_uri(tracking_uri)
    mlflow.set_experiment(experiment)

    data = load_dataset(data_path)
    features, target = split_features_target(data)
    x_train_val, x_test, y_train_val, y_test = train_test_split(
        features,
        target,
        test_size=0.20,
        random_state=RANDOM_STATE,
        stratify=target,
    )
    x_train, x_validation, y_train, y_validation = train_test_split(
        x_train_val,
        y_train_val,
        test_size=0.25,
        random_state=RANDOM_STATE,
        stratify=y_train_val,
    )

    dataset_hash = file_sha256(data_path)
    commit = git_commit()
    rows: list[dict[str, Any]] = []

    for config in model_candidates():
        pipeline = pipeline_for(x_train, config["model"])
        with mlflow.start_run(run_name=config["run_name"]) as run:
            pipeline.fit(x_train, y_train)
            metrics = evaluate(
                pipeline, x_validation, y_validation, float(config["threshold"])
            )
            model_params = {
                f"model__{key}": value
                for key, value in config["model"].get_params(deep=False).items()
                if isinstance(value, (str, int, float, bool)) or value is None
            }
            mlflow.log_params(
                {
                    "family": config["family"],
                    "threshold": config["threshold"],
                    "random_state": RANDOM_STATE,
                    "test_size": 0.20,
                    "validation_size_within_train": 0.25,
                    **model_params,
                }
            )
            mlflow.log_metrics({f"val_{key}": value for key, value in metrics.items()})
            mlflow.set_tags(
                {
                    "dataset": data_path.name,
                    "dataset_sha256": dataset_hash,
                    "git_commit": commit,
                    "target": "Churn",
                    "evaluation_split": "validation",
                }
            )
            mlflow.log_dict(metrics, "validation_metrics.json")
            log_pipeline(pipeline, x_train)
            rows.append(
                {
                    "run_name": config["run_name"],
                    "run_id": run.info.run_id,
                    "threshold": config["threshold"],
                    **metrics,
                }
            )

    results = pd.DataFrame(rows)
    eligible = results[results["run_name"] != "dummy_prior"].copy()
    eligible["selection_score"] = (
        0.50 * eligible["recall"]
        + 0.30 * eligible["f1"]
        + 0.20 * eligible["roc_auc"]
    )
    selected = eligible.sort_values(
        ["selection_score", "roc_auc"], ascending=False
    ).iloc[0]
    selected_config = next(
        item for item in model_candidates() if item["run_name"] == selected["run_name"]
    )

    final_pipeline = pipeline_for(x_train_val, clone(selected_config["model"]))
    with mlflow.start_run(run_name=f"final_{selected['run_name']}") as final_run:
        final_pipeline.fit(x_train_val, y_train_val)
        test_metrics = evaluate(
            final_pipeline, x_test, y_test, float(selected_config["threshold"])
        )
        mlflow.log_params(
            {
                "selected_candidate": selected["run_name"],
                "threshold": selected_config["threshold"],
                "selection_criterion": "0.50*recall + 0.30*f1 + 0.20*roc_auc",
                "random_state": RANDOM_STATE,
            }
        )
        mlflow.log_metrics({f"test_{key}": value for key, value in test_metrics.items()})
        mlflow.set_tags(
            {
                "stage": "final_candidate",
                "dataset": data_path.name,
                "dataset_sha256": dataset_hash,
                "git_commit": commit,
                "evaluation_split": "isolated_test",
            }
        )
        mlflow.log_dict(test_metrics, "test_metrics.json")
        model_info = log_pipeline(final_pipeline, x_train_val)
        final_run_id = final_run.info.run_id

    registered_version = None
    if register_best:
        registered = mlflow.register_model(model_uri=model_info.model_uri, name=MODEL_NAME)
        registered_version = registered.version

    model_path.parent.mkdir(parents=True, exist_ok=True)
    results_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(final_pipeline, model_path)
    results.to_csv(results_path, index=False)
    evidence = {
        "tracking_uri": tracking_uri,
        "experiment": experiment,
        "registered_model": MODEL_NAME if register_best else None,
        "registered_version": registered_version,
        "selected_candidate": selected["run_name"],
        "final_run_id": final_run_id,
        "threshold": float(selected_config["threshold"]),
        "dataset_sha256": dataset_hash,
        "git_commit": commit,
        "test_metrics": test_metrics,
    }
    with (results_path.parent / "selected_model.json").open("w", encoding="utf-8") as file:
        json.dump(evidence, file, indent=2)

    print("Resultados de validación:")
    print(results.sort_values("recall", ascending=False).round(3).to_string(index=False))
    print("\nEvaluación final sobre test aislado:")
    print(pd.Series(test_metrics).round(3).to_string())
    print(f"\nCandidato: {selected['run_name']} | run_id: {final_run_id}")
    if registered_version is not None:
        print(f"Modelo registrado: {MODEL_NAME} | versión: {registered_version}")
    return results


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Entrena, compara y registra modelos de churn")
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA)
    parser.add_argument("--model", type=Path, default=DEFAULT_MODEL)
    parser.add_argument("--results", type=Path, default=DEFAULT_RESULTS)
    parser.add_argument("--experiment", default="customer-churn-entrega-1")
    parser.add_argument("--register-best", action="store_true")
    return parser.parse_args()


if __name__ == "__main__":
    arguments = parse_args()
    run_experiments(
        arguments.data,
        arguments.model,
        arguments.results,
        arguments.experiment,
        arguments.register_best,
    )
