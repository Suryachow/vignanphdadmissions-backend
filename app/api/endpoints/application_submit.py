from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.all_models import User, Application, ApplicationStatus
from pydantic import BaseModel
from typing import Dict, Any, Optional
from datetime import datetime

router = APIRouter()

class ApplicationSubmitPayload(BaseModel):
    email: str
    phone: str
    personal: Optional[Dict[str, Any]] = None
    address: Optional[Dict[str, Any]] = None
    education: Optional[Dict[str, Any]] = None
    ugEducation: Optional[Dict[str, Any]] = None
    pgEducation: Optional[Dict[str, Any]] = None
    documents: Optional[Dict[str, Any]] = None
    examSchedule: Optional[Dict[str, Any]] = None

@router.post("/submit")
def submit_new_application(
    payload: ApplicationSubmitPayload,
    db: Session = Depends(get_db)
):
    query = db.query(User)
    if payload.email:
        user = query.filter(User.email == payload.email).first()
    elif payload.phone:
        user = query.filter(User.phone == payload.phone).first()
    else:
        user = None

    if not user:
        raise HTTPException(status_code=404, detail="User not found for submission")

    if user.payment_status != "success":
        raise HTTPException(status_code=400, detail="Payment must be completed before submission")

    app = user.application
    if not app:
        app = Application(user_id=user.id)
        db.add(app)
        db.commit()
        db.refresh(app)
        
    app.personal_details = {"personal": payload.personal, "address": payload.address}
    app.academic_details = {"education": payload.education, "ugEducation": payload.ugEducation, "pgEducation": payload.pgEducation}
    app.status = ApplicationStatus.SUBMITTED
    app.submission_date = datetime.utcnow()
    user.application_status = "completed"
    
    db.commit()
    
    return {"message": "Application submitted successfully", "status": app.status}
