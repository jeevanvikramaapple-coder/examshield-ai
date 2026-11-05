from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..auth import current_user
from ..db import get_db
from ..models import Alert, AuditLog, ExamSession
from ..pipeline.scoring import score_features
from ..schemas import AlertIn, AlertOut, AlertReview, SessionIn, SessionOut

router = APIRouter(tags=["alerts"])


@router.post("/sessions", response_model=SessionOut, status_code=201)
def start_session(body: SessionIn, db: Session = Depends(get_db), _=Depends(current_user)):
    s = ExamSession(hall=body.hall, course=body.course)
    db.add(s)
    db.commit()
    db.refresh(s)
    return s


@router.get("/sessions", response_model=list[SessionOut])
def list_sessions(db: Session = Depends(get_db), _=Depends(current_user)):
    return db.scalars(select(ExamSession).order_by(ExamSession.id.desc()).limit(50)).all()


@router.post("/alerts", response_model=AlertOut | dict, status_code=201)
def create_alert(body: AlertIn, db: Session = Depends(get_db), _=Depends(current_user)):
    """Called by the inference runner. Scores the features and stores an alert if not 'low'."""
    risk = score_features(body.features)
    if risk.band == "low":
        return {"stored": False, "risk_score": risk.score, "band": risk.band}
    a = Alert(session_id=body.session_id, student_id=body.student_id, seat=body.seat,
              risk_score=risk.score, band=risk.band, reasons="; ".join(risk.reasons),
              evidence_path=body.evidence_path)
    db.add(a)
    db.commit()
    db.refresh(a)
    return a


@router.get("/alerts", response_model=list[AlertOut])
def list_alerts(session_id: int | None = None, status: str | None = None,
                db: Session = Depends(get_db), _=Depends(current_user)):
    q = select(Alert).order_by(Alert.created_at.desc()).limit(200)
    if session_id:
        q = q.where(Alert.session_id == session_id)
    if status:
        q = q.where(Alert.status == status)
    return db.scalars(q).all()


@router.patch("/alerts/{alert_id}", response_model=AlertOut)
def review_alert(alert_id: int, body: AlertReview, db: Session = Depends(get_db), user=Depends(current_user)):
    if body.status not in ("confirmed", "dismissed"):
        raise HTTPException(422, "status must be confirmed or dismissed")
    a = db.get(Alert, alert_id)
    if not a:
        raise HTTPException(404, "Alert not found")
    a.status, a.reviewed_by = body.status, user.id
    db.add(AuditLog(user_id=user.id, action=f"alert.{body.status}", detail=str(alert_id)))
    db.commit()
    db.refresh(a)
    return a


@router.get("/alerts/{alert_id}/evidence")
def evidence(alert_id: int, db: Session = Depends(get_db), _=Depends(current_user)):
    a = db.get(Alert, alert_id)
    if not a or not a.evidence_path:
        raise HTTPException(404, "No evidence")
    return FileResponse(a.evidence_path)


@router.get("/stats")
def stats(db: Session = Depends(get_db), _=Depends(current_user)):
    by_band = dict(db.execute(select(Alert.band, func.count()).group_by(Alert.band)).all())
    by_status = dict(db.execute(select(Alert.status, func.count()).group_by(Alert.status)).all())
    confirmed, dismissed = by_status.get("confirmed", 0), by_status.get("dismissed", 0)
    reviewed = confirmed + dismissed
    return {"by_band": by_band, "by_status": by_status,
            "precision_of_reviewed": round(confirmed / reviewed, 3) if reviewed else None}
