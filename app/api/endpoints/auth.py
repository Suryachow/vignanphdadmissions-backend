from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.all_models import User, Application, Document, Payment, ApplicationStatus
from app.schemas.all_schemas import UserRegister, OTPSend, OTPVerify, Token, UserView, ApplicationUpdate, PasswordChange
from pydantic import BaseModel
from app.services.otp_service import otp_service
from app.core.security import create_access_token
from app.api.deps import get_current_user
from app.core.config import settings
from typing import Any, Optional, List
import os
import shutil
from datetime import datetime
import uuid
import hashlib

router = APIRouter()

# --- OTP ---

@router.post("/otp/send")
async def send_otp(data: OTPSend, db: Session = Depends(get_db)):
    await otp_service.create_otp(db, email=data.email)
    return {"message": "OTP sent"}

@router.post("/otp/verify")
async def verify_otp(data: OTPVerify, db: Session = Depends(get_db)):
    print(f"Verifying OTP for {data.email}: {data.code}")
    if not otp_service.verify_otp(db, code=data.code, email=data.email):
        print(f"Verification failed for {data.email}")
        raise HTTPException(status_code=400, detail="Invalid OTP")
    
    print(f"Verification success for {data.email}")
    user = db.query(User).filter(User.email == data.email).first()

    if user:
        access_token = create_access_token(user.id)
        return {"access_token": access_token, "user": user, "success": True}
    return {"success": True}

# --- REGISTRATION ---

@router.post("/student/register", response_model=UserView)
async def register(user_in: UserRegister, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == user_in.email).first():
        raise HTTPException(status_code=400, detail="Already registered")
    
    user = User(full_name=user_in.full_name, email=user_in.email, phone=user_in.phone, registration_status="completed")
    db.add(user)
    db.commit()
    db.refresh(user)
    
    app = Application(user_id=user.id, campus_preference=user_in.campus, department=user_in.program, specialization=user_in.specialization)
    db.add(app)
    db.commit()
    return user

@router.get("/register/details/")
def details(email: Optional[str] = None, phone: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(User)
    user = None
    
    if email:
        user = query.filter(User.email == email).first()
    elif phone:
        # Robust phone matching: try direct and then partial match
        clean_phone = "".join(filter(str.isdigit, phone))
        if len(clean_phone) >= 10:
            last_10 = clean_phone[-10:]
            user = query.filter(User.phone.like(f"%{last_10}")).first()
        else:
            user = query.filter(User.phone == phone).first()
            
    if not user: 
        raise HTTPException(status_code=404, detail="User not found")
        
    return {
        "user": {
            "name": user.full_name, 
            "email": user.email, 
            "phone": user.phone, 
            "payment_status": user.payment_status, 
            "application_status": user.application_status, 
            "program": user.application.department if user.application else ""
        }
    }

@router.post("/student/change-password")
async def change_password(data: PasswordChange, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.hashed_password:
        # If user has a password, they must provide the correct old one
        # For simplicity in this demo, we use plantext comparison or a simple hash
        # In production, use pwd_context.verify
        if current_user.hashed_password != data.old_password:
            raise HTTPException(status_code=400, detail="Incorrect old password")
    
    current_user.hashed_password = data.new_password
    db.commit()
    return {"message": "Password updated successfully"}

# --- PAYMENTS ---

@router.get("/payments/")
def get_payment(transactionId: str, db: Session = Depends(get_db)):
    p = db.query(Payment).filter(Payment.transaction_id == transactionId).first()
    if not p: return {"records": []}
    return {
        "records": [{
            "status": p.status, 
            "payment_data": {
                "transactionId": p.transaction_id, 
                "paymentAmount": p.amount,
                "errorMessage": p.error_message
            }
        }]
    }

@router.post("/student/coupon/validate")
def validate_coupon(data: dict):
    return {"valid": True, "discount": 100} if data.get("code") in ["VIG100", "SAVE7X3"] else {"valid": False}

# --- DOCUMENTS ---

@router.post("/upload_single_document")
async def upload(file_key: str, file: UploadFile = File(...), db: Session = Depends(get_db)):
    # In a real app, use get_current_user. For now, matching existing logic of last user.
    user = db.query(User).order_by(User.id.desc()).first()
    if not user: raise HTTPException(status_code=404, detail="User not found")
    
    # Check if S3 is configured
    if not settings.AWS_ACCESS_KEY_ID or not settings.AWS_S3_BUCKET:
        raise HTTPException(
            status_code=500, 
            detail="Cloud storage (S3) is not configured. Please check environment variables."
        )

    from app.services.s3_service import s3_service
    
    # Prepare unique object name for S3
    ext = os.path.splitext(file.filename)[1]
    object_name = f"documents/{user.id}/{file_key}_{uuid.uuid4().hex}{ext}"
    
    # Upload to S3
    file_url = s3_service.upload_file(file.file, object_name)
    
    if not file_url:
        raise HTTPException(status_code=500, detail="Failed to upload file to S3")
    
    # Save the S3 URL in the database
    doc = Document(
        user_id=user.id, 
        document_type=file_key, 
        file_name=file.filename, 
        file_path=file_url
    )
    db.add(doc)
    db.commit()
    
    return {"id": doc.id, "url": file_url}

# --- APPLICATIONS ---

@router.get("/applications/")
def get_apps(email: Optional[str] = None, phone: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(User)
    user = None
    
    if email:
        user = query.filter(User.email == email).first()
    elif phone:
        # Robust phone matching
        clean_phone = "".join(filter(str.isdigit, phone))
        if len(clean_phone) >= 10:
            last_10 = clean_phone[-10:]
            user = query.filter(User.phone.like(f"%{last_10}")).first()
        else:
            user = query.filter(User.phone == phone).first()

    if not user: 
        raise HTTPException(status_code=404, detail="User not found")
    
    app = user.application
    if not app:
        return {
            "id": user.id,
            "name": user.full_name,
            "email": user.email,
            "status": "draft",
            "personal_info": {},
            "academic_details": {},
            "address_info": {}
        }

    return {
        "id": user.id,
        "name": user.full_name,
        "email": user.email,
        "campus": app.campus_preference,
        "department": app.department,
        "specialization": app.specialization,
        "status": app.status,
        "application_status": {
            "status": app.status,
            "submission_date": app.submission_date
        },
        "personal": app.personal_details.get("personal", {}),
        "address": app.personal_details.get("address", {}),
        "education": app.academic_details.get("education", {}),
        "btechEducation": app.academic_details.get("ugEducation", {}),
        "mtechEducation": app.academic_details.get("pgEducation", {}),
        "documents": app.experience_details.get("documents", {}),
        "examSchedule": app.research_details.get("examSchedule", {})
    }

class PhaseData(BaseModel):
    email: Optional[str] = None
    phone: Optional[str] = None
    phase: str

@router.post("/student/phase")
def record_phase(data: PhaseData, db: Session = Depends(get_db)):
    # Best effort phase logging based on frontend design
    return {"status": "success"}

@router.get("/student/payment-status/")
def get_payment_status(email: Optional[str] = None, phone: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(User)
    if email:
        user = query.filter(User.email == email).first()
    elif phone:
        user = query.filter(User.phone == phone).first()
    else:
        user = None

    if not user:
        return {"hasCompletedPayment": False}

    payment = db.query(Payment).filter(Payment.user_id == user.id, Payment.status == "success").order_by(Payment.id.desc()).first()
    if payment:
        return {"hasCompletedPayment": True, "transactionId": payment.transaction_id}
    return {"hasCompletedPayment": False}
