from pathlib import Path
import joblib

PROJECT_ROOT = Path(__file__).resolve().parents[1]

MODEL_PATH = PROJECT_ROOT / "models" / "churn_pipeline.joblib"

model = joblib.load(MODEL_PATH)
