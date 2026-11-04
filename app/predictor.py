from pathlib import Path
import joblib

PROJECT_ROOT = Path(__file__).resolve().parents[1]
MODEL_PATH = PROJECT_ROOT / "models" / "churn_pipeline.joblib"
VERSION_PATH = PROJECT_ROOT / "models" / "version.txt"

_model = None
_model_version = None


def get_model():
    global _model
    if _model is None:
        if not MODEL_PATH.exists():
            raise FileNotFoundError(f"Modelo no encontrado: {MODEL_PATH}")
        _model = joblib.load(MODEL_PATH)
    return _model


def get_model_version():
    global _model_version
    if _model_version is None:
        if VERSION_PATH.exists():
            _model_version = VERSION_PATH.read_text(encoding="utf-8").strip()
        else:
            _model_version = "unknown"
    return _model_version
