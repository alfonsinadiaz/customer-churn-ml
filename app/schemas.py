from typing import Literal

from pydantic import BaseModel, Field


YesNo = Literal["Yes", "No"]
InternetAddon = Literal["Yes", "No", "No internet service"]


class CustomerInput(BaseModel):
    gender: Literal["Female", "Male"]
    SeniorCitizen: YesNo
    Partner: YesNo
    Dependents: YesNo
    tenure: int = Field(ge=0, le=100)
    PhoneService: YesNo
    MultipleLines: Literal["Yes", "No", "No phone service"]
    InternetService: Literal["DSL", "Fiber optic", "No"]
    OnlineSecurity: InternetAddon
    OnlineBackup: InternetAddon
    DeviceProtection: InternetAddon
    TechSupport: InternetAddon
    StreamingTV: InternetAddon
    StreamingMovies: InternetAddon
    Contract: Literal["Month-to-month", "One year", "Two year"]
    PaperlessBilling: YesNo
    PaymentMethod: Literal[
        "Bank transfer (automatic)",
        "Credit card (automatic)",
        "Electronic check",
        "Mailed check",
    ]
    MonthlyCharges: float = Field(ge=0)
    TotalCharges: float | None = Field(default=None, ge=0)


class PredictionResponse(BaseModel):
    prediction: Literal["CHURN", "NO_CHURN"]
    probability: float
    risk_level: Literal["LOW", "MEDIUM", "HIGH"]
    model_version: str
    request_id: str


class HealthResponse(BaseModel):
    status: Literal["healthy", "degraded"]
    model_status: str
    model_version: str
    app_version: str


class ModelResponse(BaseModel):
    model_version: str
    model_source: str
