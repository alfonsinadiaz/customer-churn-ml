from fastapi import FastAPI, HTTPException
import pandas as pd

from app.predictor import get_model, get_model_version
from app.schemas import CustomerInput

app = FastAPI()


@app.get("/")
def root():
    return {"message": "Customer Churn API"}


@app.get("/health")
def health():
    try:
        get_model()
        model_status = "loaded"
    except FileNotFoundError:
        model_status = "not_loaded"
    return {
        "status": "healthy",
        "model_version": get_model_version(),
        "model_status": model_status,
    }


@app.get("/model")
def model_info():
    return {
        "model_version": get_model_version(),
        "model_path": str(Path(__file__).resolve().parents[1] / "models" / "churn_pipeline.joblib"),
    }


@app.post("/predict")
def predict(customer: CustomerInput):
    try:
        model = get_model()
    except FileNotFoundError:
        raise HTTPException(
            status_code=503,
            detail="Modelo no disponible. Entrene el modelo primero con scripts/train_api_model.py",
        )

    data = pd.DataFrame([customer.model_dump()])

    probability = float(model.predict_proba(data)[0][1])

    prediction = "CHURN" if probability >= 0.35 else "NO_CHURN"

    if probability < 0.40:
        risk_level = "LOW"
    elif probability < 0.70:
        risk_level = "MEDIUM"
    else:
        risk_level = "HIGH"

    return {
        "prediction": prediction,
        "probability": round(probability, 4),
        "risk_level": risk_level,
        "model_version": get_model_version(),
    }
