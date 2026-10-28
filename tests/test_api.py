from fastapi.testclient import TestClient

from app.api_main import app

client = TestClient(app)

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


def test_model_endpoint():

    response = client.get("/model")

    assert response.status_code == 200

    data = response.json()

    assert "model_version" in data


def test_predict():

    response = client.post("/predict", json=VALID_PAYLOAD)

    assert response.status_code in (200, 503)

    if response.status_code == 200:
        data = response.json()

        assert "prediction" in data
        assert "probability" in data
        assert "risk_level" in data
        assert "model_version" in data

        assert data["prediction"] in ("CHURN", "NO_CHURN")
        assert isinstance(data["probability"], float)
        assert data["risk_level"] in ("LOW", "MEDIUM", "HIGH")


def test_predict_invalid_input_returns_422():

    payload = dict(VALID_PAYLOAD)
    payload["tenure"] = -1

    response = client.post("/predict", json=payload)

    assert response.status_code == 422
