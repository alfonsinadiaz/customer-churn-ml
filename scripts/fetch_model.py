"""Recupera una versión explícita del Registry y sus metadatos de origen."""
import hashlib
import json
import os
from pathlib import Path
import joblib
import mlflow
from mlflow import MlflowClient


def main():
    name = os.getenv("MODEL_NAME", "customer-churn-candidate")
    version = os.getenv("MODEL_VERSION", "4")
    if not version.isdecimal():
        raise ValueError("MODEL_VERSION debe ser una versión numérica explícita")
    uri = os.environ["MLFLOW_TRACKING_URI"]
    mlflow.set_tracking_uri(uri)
    client = MlflowClient()
    registered = client.get_model_version(name, version)
    run = client.get_run(registered.run_id)
    threshold = float(run.data.params["threshold"])
    high = float(os.getenv("RISK_HIGH_THRESHOLD", "0.70"))
    if not 0 < threshold < high < 1:
        raise ValueError("Umbrales de riesgo incompatibles")
    pipeline = mlflow.sklearn.load_model(f"models:/{name}/{version}")
    path = Path(os.getenv("MODEL_PATH", "models/churn_pipeline.joblib"))
    path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipeline, path)
    metadata = {
        "registered_model": name, "registered_version": version,
        "final_run_id": registered.run_id, "git_commit": run.data.tags.get("git_commit"),
        "dataset_sha256": run.data.tags.get("dataset_sha256"),
        "threshold": threshold, "risk_low_threshold": threshold,
        "risk_high_threshold": high,
        "model_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    }
    path.with_suffix(".json").write_text(json.dumps(metadata, indent=2))
    print(f"Modelo {name} versión {version} recuperado en {path}")

if __name__ == "__main__":
    main()
