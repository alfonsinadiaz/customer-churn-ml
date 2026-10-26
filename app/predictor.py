import hashlib
import json
import os
from pathlib import Path
import joblib

PROJECT_ROOT = Path(__file__).resolve().parents[1]

class Predictor:
    def __init__(self, model, metadata):
        self.model = model
        self.metadata = metadata
        self.version = str(metadata.get("registered_version") or "local-" + metadata["model_sha256"][:12])
        self.threshold = float(metadata["threshold"])
        self.low = float(metadata["risk_low_threshold"])
        self.high = float(metadata["risk_high_threshold"])
        if not 0 < self.threshold < 1 or not 0 < self.low < self.high < 1:
            raise ValueError("Umbrales fuera de rango")
        if self.low != self.threshold:
            raise ValueError("El límite LOW debe coincidir con el umbral de clasificación")
        if list(model.classes_) != [0, 1]:
            raise ValueError("Se esperan clases [0, 1], con 1 = churn")

    def predict(self, data):
        probability = float(self.model.predict_proba(data)[0][1])
        if not 0 <= probability <= 1:
            raise ValueError("Probabilidad no válida")
        return {
            "prediction": "CHURN" if probability >= self.threshold else "NO_CHURN",
            "probability": probability,
            "risk_level": "LOW" if probability < self.low else "MEDIUM" if probability < self.high else "HIGH",
            "model_version": self.version,
        }

def load_predictor():
    path = Path(os.getenv("MODEL_PATH", str(PROJECT_ROOT / "models/churn_pipeline.joblib")))
    metadata_path = path.with_suffix(".json")
    if not path.is_file() or not metadata_path.is_file():
        raise RuntimeError("Falta el modelo o sus metadatos. Ejecute python -m scripts.fetch_model o entrene según README.")
    metadata = json.loads(metadata_path.read_text())
    actual = hashlib.sha256(path.read_bytes()).hexdigest()
    if actual != metadata["model_sha256"]:
        raise ValueError("El hash del modelo no coincide con sus metadatos")
    return Predictor(joblib.load(path), metadata)
