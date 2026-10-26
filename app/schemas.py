from typing import Literal
from pydantic import BaseModel, ConfigDict, Field

YesNo = Literal["Yes", "No"]
Service = Literal["Yes", "No", "No internet service"]

class CustomerInput(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    gender: Literal["Female", "Male"]
    SeniorCitizen: YesNo
    Partner: YesNo
    Dependents: YesNo
    tenure: int = Field(ge=0, strict=True)
    PhoneService: YesNo
    MultipleLines: Literal["Yes", "No", "No phone service"]
    InternetService: Literal["DSL", "Fiber optic", "No"]
    OnlineSecurity: Service
    OnlineBackup: Service
    DeviceProtection: Service
    TechSupport: Service
    StreamingTV: Service
    StreamingMovies: Service
    Contract: Literal["Month-to-month", "One year", "Two year"]
    PaperlessBilling: YesNo
    PaymentMethod: Literal["Electronic check", "Mailed check", "Bank transfer (automatic)", "Credit card (automatic)"]
    MonthlyCharges: float = Field(ge=0)
    TotalCharges: float = Field(ge=0)

class PredictionOutput(BaseModel):
    model_config = ConfigDict(allow_inf_nan=False, protected_namespaces=())
    prediction: Literal["CHURN", "NO_CHURN"]
    probability: float = Field(ge=0, le=1)
    risk_level: Literal["LOW", "MEDIUM", "HIGH"]
    model_version: str

class HealthOutput(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    status: Literal["healthy"]
    model_version: str
