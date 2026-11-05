from datetime import datetime

from pydantic import BaseModel


class LoginIn(BaseModel):
    email: str
    password: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str


class StudentIn(BaseModel):
    reg_no: str
    name: str
    consent_given: bool


class StudentOut(BaseModel):
    id: int
    reg_no: str
    name: str
    consent_given: bool
    has_embedding: bool = False

    model_config = {"from_attributes": True}


class SessionIn(BaseModel):
    hall: str
    course: str


class SessionOut(BaseModel):
    id: int
    hall: str
    course: str
    started_at: datetime
    ended_at: datetime | None = None

    model_config = {"from_attributes": True}


class AlertIn(BaseModel):
    session_id: int
    student_id: int | None = None
    seat: str | None = None
    features: dict[str, float]
    evidence_path: str | None = None


class AlertOut(BaseModel):
    id: int
    session_id: int
    student_id: int | None
    seat: str | None
    risk_score: float
    band: str
    reasons: str
    evidence_path: str | None
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class AlertReview(BaseModel):
    status: str  # confirmed | dismissed
