from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..auth import current_user, require_admin
from ..db import get_db
from ..models import AuditLog, Student
from ..schemas import StudentIn, StudentOut

router = APIRouter(prefix="/students", tags=["students"])


def _out(s: Student) -> StudentOut:
    return StudentOut(id=s.id, reg_no=s.reg_no, name=s.name,
                      consent_given=s.consent_given, has_embedding=s.embedding is not None)


@router.get("", response_model=list[StudentOut])
def list_students(db: Session = Depends(get_db), _=Depends(current_user)):
    return [_out(s) for s in db.scalars(select(Student).order_by(Student.reg_no))]


@router.post("", response_model=StudentOut, status_code=201)
def register(body: StudentIn, db: Session = Depends(get_db), user=Depends(require_admin)):
    # Consent is a hard gate on enrolment (DPDP Act 2023).
    if not body.consent_given:
        raise HTTPException(422, "Consent is required before enrolment")
    if db.scalar(select(Student).where(Student.reg_no == body.reg_no)):
        raise HTTPException(409, "Registration number already enrolled")
    s = Student(reg_no=body.reg_no, name=body.name, consent_given=True, consent_at=datetime.utcnow())
    db.add(s)
    db.add(AuditLog(user_id=user.id, action="student.enrol", detail=body.reg_no))
    db.commit()
    db.refresh(s)
    return _out(s)


@router.post("/{student_id}/face", response_model=StudentOut)
async def upload_face(student_id: int, files: list[UploadFile],
                      db: Session = Depends(get_db), user=Depends(require_admin)):
    """Compute and store an averaged ArcFace embedding from enrolment photos."""
    s = db.get(Student, student_id)
    if not s or not s.consent_given:
        raise HTTPException(404, "Student not found or no consent on record")
    import cv2
    import numpy as np
    from ..pipeline.faces import embed_faces  # needs insightface installed
    imgs = [cv2.imdecode(np.frombuffer(await f.read(), np.uint8), cv2.IMREAD_COLOR) for f in files]
    emb = embed_faces(imgs)
    if emb is None:
        raise HTTPException(422, "No usable face found in the photos")
    s.embedding = emb.tolist()
    db.add(AuditLog(user_id=user.id, action="student.face", detail=s.reg_no))
    db.commit()
    return _out(s)


@router.delete("/{student_id}", status_code=204)
def withdraw(student_id: int, db: Session = Depends(get_db), user=Depends(require_admin)):
    """Consent withdrawal: erase the student and biometric data."""
    s = db.get(Student, student_id)
    if not s:
        raise HTTPException(404, "Not found")
    db.add(AuditLog(user_id=user.id, action="student.erase", detail=s.reg_no))
    db.delete(s)
    db.commit()
