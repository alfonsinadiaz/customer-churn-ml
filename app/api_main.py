from contextlib import asynccontextmanager
import logging
import os
from time import perf_counter
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
import pandas as pd

from app.logging_config import configure_logging
from app.predictor import get_model, get_model_source, get_model_version
from app.schemas import CustomerInput, HealthResponse, PredictionResponse

configure_logging()
logger = logging.getLogger("churn_api")
APP_VERSION = os.getenv("APP_VERSION", "dev")


@asynccontextmanager
async def lifespan(_: FastAPI):
    logger.info(
        "api_started",
        extra={"event": "api_started", "model_version": get_model_version()},
    )
    yield


app = FastAPI(title="Customer Churn API", version=APP_VERSION, lifespan=lifespan)


@app.middleware("http")
async def request_observability(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or str(uuid4())
    request.state.request_id = request_id
    started = perf_counter()
    try:
        response = await call_next(request)
    except Exception:
        logger.exception(
            "request_failed",
            extra={
                "event": "request_failed",
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "duration_ms": round((perf_counter() - started) * 1000, 2),
                "model_version": get_model_version(),
            },
        )
        raise

    duration_ms = round((perf_counter() - started) * 1000, 2)
    response.headers["X-Request-ID"] = request_id
    logger.info(
        "request_completed",
        extra={
            "event": "request_completed",
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_ms": duration_ms,
            "model_version": get_model_version(),
        },
    )
    return response


@app.get("/")
def root():
    return {"message": "Customer Churn API"}


@app.get("/health", response_model=HealthResponse)
def health():
    try:
        get_model()
    except Exception as exc:
        logger.warning(
            "model_unavailable",
            extra={"event": "model_unavailable", "model_version": get_model_version()},
        )
        return JSONResponse(
            status_code=503,
            content={
                "status": "degraded",
                "model_version": get_model_version(),
                "model_status": type(exc).__name__,
                "app_version": APP_VERSION,
            },
        )
    return HealthResponse(
        status="healthy",
        model_version=get_model_version(),
        model_status="loaded",
        app_version=APP_VERSION,
    )


@app.get("/model")
def model_info():
    return {
        "model_version": get_model_version(),
        "model_source": get_model_source(),
    }


@app.post("/predict", response_model=PredictionResponse)
def predict(customer: CustomerInput, request: Request):
    try:
        model = get_model()
    except Exception as exc:
        logger.exception(
            "prediction_model_unavailable",
            extra={
                "event": "prediction_model_unavailable",
                "request_id": request.state.request_id,
                "model_version": get_model_version(),
            },
        )
        raise HTTPException(
            status_code=503,
            detail="Modelo no disponible. Revise MODEL_URI o MODEL_PATH.",
        ) from exc

    data = pd.DataFrame([customer.model_dump()])

    probability = float(model.predict_proba(data)[0][1])

    prediction = "CHURN" if probability >= 0.35 else "NO_CHURN"

    if probability < 0.40:
        risk_level = "LOW"
    elif probability < 0.70:
        risk_level = "MEDIUM"
    else:
        risk_level = "HIGH"

    return PredictionResponse(
        prediction=prediction,
        probability=round(probability, 4),
        risk_level=risk_level,
        model_version=get_model_version(),
        request_id=request.state.request_id,
    )
