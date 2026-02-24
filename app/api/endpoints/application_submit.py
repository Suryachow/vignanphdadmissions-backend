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
    user = None
    if payload.email:
        user = query.filter(User.email == payload.email).first()
    
    if not user and payload.phone:
        # Robust phone matching: try direct and then partial match
        clean_phone = "".join(filter(str.isdigit, payload.phone))
        if len(clean_phone) >= 10:
            last_10 = clean_phone[-10:]
            user = query.filter(User.phone.like(f"%{last_10}")).first()
        else:
            user = query.filter(User.phone == payload.phone).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found for submission")

    if user.payment_status != "success":
        # Allow bypass if transaction exists for demo purposes? 
        # No, better to stick to the fix in bypass endpoint.
        raise HTTPException(status_code=400, detail="Payment must be completed before submission")

    app = user.application
    if not app:
        app = Application(user_id=user.id)
        db.add(app)
        db.commit()
        db.refresh(app)
        
    # 1. Update Core Application Searchable Fields
    # These might come from the 'personal' object or represent changed preferences
    personal = payload.personal or {}
    app.campus_preference = personal.get("campus") or app.campus_preference
    app.program_type = personal.get("program_type") or app.program_type or "Full-time"
    app.department = personal.get("department") or app.department
    app.specialization = personal.get("specialization") or app.specialization

    # 2. Normalize and Save Detailed Data
    # Store complete objects to prevent data loss, but maintain structured keys
    app.personal_details = {
        "personal": payload.personal, 
        "address": payload.address
    }
    app.academic_details = {
        "education": payload.education, 
        "ugEducation": payload.ugEducation, 
        "pgEducation": payload.pgEducation
    }
    
    # Store document metadata and exam schedule
    app.experience_details = {"documents": payload.documents}
    app.research_details = {"examSchedule": payload.examSchedule}
    
    # 3. Handle Document Table Sync
    # If document metadata contains file paths, ensure they are reflected if possible
    # (Note: Files are uploaded separately, but we can verify links here)
    if payload.documents and "files" in payload.documents:
        from app.models.all_models import Document
        for doc_type, file_info in payload.documents["files"].items():
            if isinstance(file_info, dict) and file_info.get("path"):
                existing_doc = db.query(Document).filter(
                    Document.user_id == user.id, 
                    Document.document_type == doc_type
                ).first()
                if not existing_doc:
                    new_doc = Document(
                        user_id=user.id,
                        document_type=doc_type,
                        file_name=file_info.get("name", "uploaded_file"),
                        file_path=file_info.get("path"),
                        mime_type=file_info.get("type", "application/octet-stream")
                    )
                    db.add(new_doc)

    # 4. Status and Housekeeping
    app.status = ApplicationStatus.SUBMITTED
    app.submission_date = datetime.utcnow()
    app.current_step = 5 # Final step
    
    user.application_status = "completed"
    
    # Explicitly flag JSON fields as modified for SQLAlchemy
    from sqlalchemy.orm.attributes import flag_modified
    for field in ["personal_details", "academic_details", "experience_details", "research_details"]:
        flag_modified(app, field)
    
    db.commit()

    # 5. Clear Application Cache
    try:
        from app.models.all_models import ApplicationCache
        # Clear cache by session_id (pending-phone or pending-email)
        clean_phone = "".join(filter(str.isdigit, payload.phone))
        last_10 = clean_phone[-10:] if len(clean_phone) >= 10 else clean_phone
        
        db.query(ApplicationCache).filter(
            (ApplicationCache.session_id == f"pending-{last_10}") |
            (ApplicationCache.session_id == f"pending-{payload.email}") |
            (ApplicationCache.user_id == last_10) |
            (ApplicationCache.user_id == payload.phone)
        ).delete(synchronize_session=False)
        db.commit()
    except Exception as e:
        print(f"Failed to clear cache: {e}")
        # Don't fail the whole submission if cache clearing fails
    
    return {
        "message": "Application submitted successfully", 
        "status": app.status,
        "application_id": app.id
    }
