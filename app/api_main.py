from contextlib import asynccontextmanager
import logging
import pandas as pd
from fastapi import FastAPI, HTTPException, Request
from app.predictor import load_predictor
from app.schemas import CustomerInput, PredictionOutput, HealthOutput

logger = logging.getLogger("uvicorn.error")

@asynccontextmanager
async def lifespan(app):
    app.state.predictor = load_predictor()
    logger.info("Modelo cargado: %s", app.state.predictor.version)
    yield

app = FastAPI(title="Customer Churn API", lifespan=lifespan)

@app.get("/")
def root():
    return {"message": "Customer Churn API"}

@app.get("/health", response_model=HealthOutput)
def health(request: Request):
    predictor = getattr(request.app.state, "predictor", None)
    if predictor is None:
        raise HTTPException(503, "Modelo no disponible")
    return {"status": "healthy", "model_version": predictor.version}

@app.post("/predict", response_model=PredictionOutput)
def predict(customer: CustomerInput, request: Request):
    predictor = getattr(request.app.state, "predictor", None)
    if predictor is None:
        raise HTTPException(503, "Modelo no disponible")
    try:
        return predictor.predict(pd.DataFrame([customer.model_dump()]))
    except Exception:
        logger.exception("Error de inferencia")
        raise HTTPException(500, "No se pudo generar la predicción") from None
