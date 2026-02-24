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
def details(email: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == email).first()
    if not user: raise HTTPException(status_code=404)
    return {"user": {"name": user.full_name, "email": user.email, "phone": user.phone, "payment_status": user.payment_status, "application_status": user.application_status, "program": user.application.department if user.application else ""}}

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
    return {"records": [{"status": p.status, "payment_data": {"transactionId": p.transaction_id, "paymentAmount": p.amount}}]}

@router.post("/student/coupon/validate")
def validate_coupon(data: dict):
    return {"valid": True, "discount": 100} if data.get("code") in ["VIG100", "SAVE7X3"] else {"valid": False}

# --- DOCUMENTS ---

@router.post("/upload_single_document")
async def upload(file_key: str, file: UploadFile = File(...), db: Session = Depends(get_db)):
    user = db.query(User).order_by(User.id.desc()).first()
    if not user: raise HTTPException(status_code=404)
    
    path = os.path.join(settings.UPLOAD_DIR, f"{user.id}_{file_key}_{file.filename}")
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    with open(path, "wb") as b: shutil.copyfileobj(file.file, b)
    
    doc = Document(user_id=user.id, document_type=file_key, file_name=file.filename, file_path=path)
    db.add(doc)
    db.commit()
    return {"id": doc.id}

# --- APPLICATIONS ---

@router.get("/applications/")
def get_apps(email: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == email).first()
    if not user: raise HTTPException(status_code=404)
    return {"id": user.id, "name": user.full_name, "email": user.email, "personal_info": user.application.personal_details if user.application else {}}

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
