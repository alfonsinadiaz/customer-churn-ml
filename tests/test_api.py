import numpy as np
from fastapi.testclient import TestClient
import pytest

import app.api_main as api_main

client = TestClient(api_main.app)


class FakeModel:
    def predict_proba(self, data):
        return np.array([[0.2, 0.8] for _ in range(len(data))])


@pytest.fixture(autouse=True)
def loaded_model(monkeypatch):
    monkeypatch.setattr(api_main, "get_model", lambda: FakeModel())
    monkeypatch.setattr(api_main, "get_model_version", lambda: "test-v1")

VALID_PAYLOAD = {
    "gender": "Female",
    "SeniorCitizen": "No",
    "Partner": "Yes",
    "Dependents": "No",
    "tenure": 12,
    "PhoneService": "Yes",
    "MultipleLines": "No",
    "InternetService": "Fiber optic",
    "OnlineSecurity": "No",
    "OnlineBackup": "Yes",
    "DeviceProtection": "No",
    "TechSupport": "No",
    "StreamingTV": "Yes",
    "StreamingMovies": "Yes",
    "Contract": "Month-to-month",
    "PaperlessBilling": "Yes",
    "PaymentMethod": "Electronic check",
    "MonthlyCharges": 89.5,
    "TotalCharges": 1074.0,
}


def test_health():

    response = client.get("/health")

    assert response.status_code == 200

    data = response.json()

    assert "status" in data
    assert "model_version" in data
    assert "model_status" in data
    assert data["status"] == "healthy"


def test_model_endpoint():

    response = client.get("/model")

    assert response.status_code == 200

    data = response.json()

    assert data["model_version"] == "test-v1"
    assert data["model_source"]


def test_predict():

    response = client.post("/predict", json=VALID_PAYLOAD)

    assert response.status_code == 200
    data = response.json()

    assert data["prediction"] == "CHURN"
    assert data["probability"] == 0.8
    assert data["risk_level"] == "HIGH"
    assert data["model_version"] == "test-v1"
    assert data["request_id"] == response.headers["X-Request-ID"]


def test_predict_invalid_input_returns_422():

    payload = dict(VALID_PAYLOAD)
    payload["tenure"] = -1

    response = client.post("/predict", json=payload)

    assert response.status_code == 422


def test_predict_rejects_unknown_category():
    payload = dict(VALID_PAYLOAD)
    payload["Contract"] = "Weekly"

    response = client.post("/predict", json=payload)

    assert response.status_code == 422


def test_predict_accepts_null_total_charges():
    payload = dict(VALID_PAYLOAD)
    payload["TotalCharges"] = None

    response = client.post("/predict", json=payload)

    assert response.status_code == 200


def test_health_returns_503_without_model(monkeypatch):
    def missing_model():
        raise FileNotFoundError("missing")

    monkeypatch.setattr(api_main, "get_model", missing_model)
    response = client.get("/health")
    assert response.status_code == 503
    assert response.json()["status"] == "degraded"


def test_predict_returns_503_without_model(monkeypatch):
    def missing_model():
        raise FileNotFoundError("missing")

    monkeypatch.setattr(api_main, "get_model", missing_model)
    response = client.post("/predict", json=VALID_PAYLOAD)

    assert response.status_code == 503


def test_request_id_is_propagated():
    response = client.post(
        "/predict", json=VALID_PAYLOAD, headers={"X-Request-ID": "demo-123"}
    )
    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == "demo-123"
    assert response.json()["request_id"] == "demo-123"
