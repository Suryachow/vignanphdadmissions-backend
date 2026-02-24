from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.db.session import get_db
from app.models.all_models import User, Application, Payment, Document, ApplicationCache, ApplicationStatus
from app.core.security import create_access_token
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

router = APIRouter()

class AdminLogin(BaseModel):
    email: str
    password: str

@router.post("/login")
async def admin_login(data: AdminLogin):
    if data.email == "admin@vignan.ac.in" and data.password == "admin123":
        # Using a special sub for admin, or we can use a fixed ID like 0 if we want
        access_token = create_access_token(subject="admin_user")
        return {"access_token": access_token, "token_type": "bearer"}
    raise HTTPException(status_code=401, detail="Invalid credentials")

@router.get("/stats")
async def get_stats(db: Session = Depends(get_db)):
    registered_students = db.query(User).count()
    payments_completed = db.query(Payment).filter(Payment.status == "success").count()
    applications_filled = db.query(Application).filter(Application.status != ApplicationStatus.DRAFT).count()
    applications_pending = db.query(ApplicationCache).count()
    
    # Get registration trend (last 7 days or all)
    registration_trend = db.query(
        func.date(User.created_at).label('date'),
        func.count(User.id).label('count')
    ).group_by(func.date(User.created_at)).order_by(func.date(User.created_at)).all()
    
    trend_data = [{"date": str(r.date), "count": r.count} for r in registration_trend]

    return {
        "registered_students": registered_students,
        "payments_completed": payments_completed,
        "applications_filled": applications_filled,
        "applications_pending": applications_pending,
        "registration_trend": trend_data
    }

@router.get("/users")
async def get_users(db: Session = Depends(get_db)):
    users = db.query(User).all()
    return users

@router.get("/payments")
async def get_payments(db: Session = Depends(get_db)):
    payments = db.query(Payment).all()
    # Include user email for better context
    result = []
    for p in payments:
        user = db.query(User).filter(User.id == p.user_id).first()
        result.append({
            "id": p.id,
            "user_email": user.email if user else "Unknown",
            "transaction_id": p.transaction_id or "N/A",
            "amount": float(p.amount) if p.amount is not None else 0.0,
            "status": str(p.status).lower() if p.status else "pending",
            "created_at": p.created_at.isoformat() if p.created_at else None
        })
    return result

@router.get("/applications-pending")
async def get_applications_pending(db: Session = Depends(get_db)):
    pending = db.query(ApplicationCache).all()
    return pending

@router.get("/applications")
async def get_applications(db: Session = Depends(get_db)):
    apps = db.query(Application).all()
    result = []
    for app in apps:
        user = db.query(User).filter(User.id == app.user_id).first()
        result.append({
            "id": app.id,
            "user_email": user.email if user else "Unknown",
            "campus": app.campus_preference,
            "department": app.department,
            "status": app.status,
            "updated_at": app.updated_at
        })
    return result

@router.get("/documents")
async def get_documents_grouped(db: Session = Depends(get_db)):
    # Group documents by user email
    # Use an outer join to see all users with documents, or just query documents and group manually
    docs = db.query(Document).all()
    
    # Simple manual grouping to be 100% sure of data structure
    grouped = {}
    for d in docs:
        user = db.query(User).filter(User.id == d.user_id).first()
        if not user:
            continue
            
        email = user.email
        if email not in grouped:
            grouped[email] = {
                "email": email,
                "full_name": user.full_name,
                "documents": []
            }
        
        grouped[email]["documents"].append({
            "id": d.id,
            "document_type": d.document_type,
            "file_name": d.file_name,
            "file_path": d.file_path,
            "uploaded_at": d.uploaded_at.isoformat() if d.uploaded_at else None
        })
    
    return list(grouped.values())
