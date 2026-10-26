import hashlib
import json
import joblib
import pandas as pd
import pytest
from fastapi.testclient import TestClient
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from app.api_main import app
from app.predictor import load_predictor
from src.features.preprocessing import build_preprocessor

PAYLOAD = dict(gender="Female", SeniorCitizen="No", Partner="Yes", Dependents="No", tenure=12,
    PhoneService="Yes", MultipleLines="No", InternetService="Fiber optic", OnlineSecurity="No",
    OnlineBackup="Yes", DeviceProtection="No", TechSupport="No", StreamingTV="Yes", StreamingMovies="Yes",
    Contract="Month-to-month", PaperlessBilling="Yes", PaymentMethod="Electronic check", MonthlyCharges=89.5, TotalCharges=1074.0)

@pytest.fixture
def artifact(tmp_path, monkeypatch):
    # Artefacto sintético: comprueba el servicio, no la calidad del modelo de negocio.
    x = pd.DataFrame([dict(PAYLOAD, tenure=i, MonthlyCharges=20+i) for i in range(12)])
    model = Pipeline([("preprocessor", build_preprocessor(x)), ("model", LogisticRegression())])
    model.fit(x, [0]*6 + [1]*6)
    path = tmp_path / "pipeline.joblib"
    joblib.dump(model, path)
    path.with_suffix('.json').write_text(json.dumps(dict(registered_version=None,
        model_sha256=hashlib.sha256(path.read_bytes()).hexdigest(), threshold=.35,
        risk_low_threshold=.35, risk_high_threshold=.70)))
    monkeypatch.setenv("MODEL_PATH", str(path))
    return path

@pytest.fixture
def client(artifact):
    with TestClient(app) as client:
        yield client


def test_health(client):
    result = client.get('/health')
    assert result.status_code == 200
    assert result.json()['status'] == 'healthy'
    assert result.json()['model_version'].startswith('local-')


def test_predict(client):
    response = client.post('/predict', json=PAYLOAD)
    assert response.status_code == 200
    data = response.json()
    assert set(data) == {'prediction','probability','risk_level','model_version'}
    assert isinstance(data['probability'], float)
    assert 0 <= data['probability'] <= 1
    assert data['prediction'] in ('CHURN','NO_CHURN')
    assert data['risk_level'] in ('LOW','MEDIUM','HIGH')
    assert data['model_version'] == client.get('/health').json()['model_version']

@pytest.mark.parametrize('changes', [{'tenure':-1}, {'tenure':1.5}, {'MonthlyCharges':-1},
    {'TotalCharges':-1}, {'Contract':'inventado'}, {'SeniorCitizen':'0'}, {'extra':1}, {'tenure':None}])
def test_invalid(client, changes):
    assert client.post('/predict', json={**PAYLOAD, **changes}).status_code == 422


def test_missing_field(client):
    payload = dict(PAYLOAD)
    del payload['Contract']
    assert client.post('/predict', json=payload).status_code == 422


def test_model_load(artifact):
    predictor = load_predictor()
    assert predictor.model.predict_proba(pd.DataFrame([PAYLOAD])).shape == (1, 2)


def test_hash_mismatch(artifact):
    artifact.write_bytes(b'changed')
    with pytest.raises(ValueError, match='hash'):
        load_predictor()


def test_missing_model(artifact):
    artifact.unlink()
    with pytest.raises(RuntimeError, match='Falta'):
        load_predictor()


def test_prediction_failure(client, monkeypatch):
    def fail(data):
        raise RuntimeError('detalle interno')
    monkeypatch.setattr(app.state.predictor, 'predict', fail)
    response = client.post('/predict', json=PAYLOAD)
    assert response.status_code == 500
    assert 'detalle interno' not in response.text

@pytest.mark.parametrize('probability, prediction, risk', [(.349,'NO_CHURN','LOW'),(.35,'CHURN','MEDIUM'),(.699,'CHURN','MEDIUM'),(.70,'CHURN','HIGH')])
def test_boundaries(client, monkeypatch, probability, prediction, risk):
    monkeypatch.setattr(app.state.predictor.model, 'predict_proba', lambda data: [[1-probability,probability]])
    result = client.post('/predict', json=PAYLOAD).json()
    assert result['prediction'] == prediction
    assert result['risk_level'] == risk


def test_swagger(client):
    assert client.get('/docs').status_code == 200
    schema = client.get('/openapi.json').json()
    assert 'PredictionOutput' in schema['components']['schemas']
