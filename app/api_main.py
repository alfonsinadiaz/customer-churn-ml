from fastapi import FastAPI
import pandas as pd

from app.predictor import model
from app.schemas import CustomerInput

app = FastAPI()


@app.get("/")
def root():
    return {"message": "Customer Churn API"}


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "model_version": "4"
    }


@app.post("/predict")
def predict(customer: CustomerInput):

    data = pd.DataFrame([customer.model_dump()])

    probability = float(
        model.predict_proba(data)[0][1]
    )

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
        "model_version": "4"
    }