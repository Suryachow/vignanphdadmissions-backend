from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.all_models import User, Application, Document, ApplicationStatus, Message
from app.schemas.all_schemas import ApplicationUpdate, ApplicationView, MessageView, DocumentView
from app.api.deps import get_current_user
from app.core.config import settings
import os
import shutil
from typing import List, Any
from datetime import datetime

router = APIRouter()

@router.get("/me", response_model=ApplicationView)
def get_my_application(
    current_user: User = Depends(get_current_user)
):
    if not current_user.application:
        raise HTTPException(status_code=404, detail="Application profile not found")
    return current_user.application

@router.put("/update", response_model=ApplicationView)
def update_application_data(
    data: ApplicationUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    app = current_user.application
    if not app:
        raise HTTPException(status_code=404, detail="Application record not found")
        
    # Update fields if provided
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(app, field, value)
            
    db.commit()
    db.refresh(app)
    return app

@router.post("/submit")
def submit_application(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    app = current_user.application
    if not app:
        raise HTTPException(status_code=400, detail="Incomplete profile")
    
    # Check if payment is successful before submit (optional depending on business logic)
    if current_user.payment_status != "success":
        # Some unis allow submit before pay, others don't. 
        # Here we'll require payment or at least mark it as payment pending
        pass
        
    app.status = ApplicationStatus.SUBMITTED
    app.submission_date = datetime.utcnow()
    current_user.application_status = "completed"
    
    db.commit()
    return {"message": "Application submitted successfully", "status": app.status}

@router.get("/documents", response_model=List[DocumentView])
def get_user_documents(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return db.query(Document).filter(Document.user_id == current_user.id).all()

@router.post("/upload_document", response_model=DocumentView)
async def upload_student_document(
    document_type: str,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Security: limit file types
    ext = file.filename.split(".")[-1].lower()
    if ext not in ["pdf", "jpg", "jpeg", "png"]:
        raise HTTPException(status_code=400, detail="Unsupported file format")

    # Create storage path
    user_storage = os.path.join(settings.UPLOAD_DIR, str(current_user.id))
    os.makedirs(user_storage, exist_ok=True)
    
    # Unique file name to prevent caching/overwriting issues
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    safe_name = f"{document_type}_{timestamp}.{ext}"
    dest_path = os.path.join(user_storage, safe_name)
    
    # Save file
    file_size = 0
    with open(dest_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        file_size = os.path.getsize(dest_path)
        
    # Check Max Size
    if file_size > 5 * 1024 * 1024: # 5MB
        os.remove(dest_path)
        raise HTTPException(status_code=400, detail="File too large (Max 5MB)")

    # Update metadata in DB
    db_doc = db.query(Document).filter(
        Document.user_id == current_user.id, 
        Document.document_type == document_type
    ).first()
    
    if db_doc:
        # Remove old file if exists
        try:
            if os.path.exists(db_doc.file_path):
                os.remove(db_doc.file_path)
        except:
            pass
        db_doc.file_name = file.filename
        db_doc.file_path = dest_path
        db_doc.file_size = file_size
        db_doc.mime_type = file.content_type
        db_doc.uploaded_at = datetime.utcnow()
    else:
        db_doc = Document(
            user_id=current_user.id,
            document_type=document_type,
            file_name=file.filename,
            file_path=dest_path,
            file_size=file_size,
            mime_type=file.content_type
        )
        db.add(db_doc)
        
    db.commit()
    db.refresh(db_doc)
    
    return db_doc

@router.get("/messages", response_model=List[MessageView])
def get_user_messages(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return db.query(Message).filter(Message.user_id == current_user.id).order_by(Message.created_at.desc()).all()
