import os
from pathlib import Path

import joblib

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MODEL_PATH = PROJECT_ROOT / "models" / "churn_pipeline.joblib"
DEFAULT_VERSION_PATH = PROJECT_ROOT / "models" / "version.txt"

_model = None
_model_version = None


def get_model():
    global _model
    if _model is None:
        model_uri = os.getenv("MODEL_URI", "").strip()
        if model_uri:
            import mlflow.sklearn

            _model = mlflow.sklearn.load_model(model_uri)
        else:
            model_path = Path(os.getenv("MODEL_PATH", str(DEFAULT_MODEL_PATH)))
            if not model_path.exists():
                raise FileNotFoundError(f"Modelo no encontrado: {model_path}")
            _model = joblib.load(model_path)
    return _model


def get_model_version():
    global _model_version
    if _model_version is None:
        configured_version = os.getenv("MODEL_VERSION", "").strip()
        version_path = Path(os.getenv("MODEL_VERSION_PATH", str(DEFAULT_VERSION_PATH)))
        if configured_version:
            _model_version = configured_version
        elif version_path.exists():
            _model_version = version_path.read_text(encoding="utf-8").strip()
        elif os.getenv("MODEL_URI", "").strip():
            _model_version = os.environ["MODEL_URI"].strip()
        else:
            _model_version = "unknown"
    return _model_version


def get_model_source() -> str:
    """Devuelve una referencia auditable sin exponer credenciales."""
    model_uri = os.getenv("MODEL_URI", "").strip()
    if model_uri:
        return model_uri
    return str(Path(os.getenv("MODEL_PATH", str(DEFAULT_MODEL_PATH))))


def reset_model_cache() -> None:
    """Limpia el cache; se usa en pruebas y al cambiar la configuración."""
    global _model, _model_version
    _model = None
    _model_version = None
