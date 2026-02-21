from fastapi import APIRouter, Depends, HTTPException, Request, Response, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.all_models import User, Payment
from app.schemas.all_schemas import PaymentInit
from app.api.deps import get_current_user
from app.core.config import settings
import hashlib
import uuid

router = APIRouter()

@router.post("/init")
def initiate_payu(
    data: PaymentInit, 
    db: Session = Depends(get_db)
):
    # In a real app we'd use current_user. For demo, we'll take last user if not provided.
    user = db.query(User).order_by(User.id.desc()).first()
    
    txnid = f"VIG{uuid.uuid4().hex[:12].upper()}"
    
    params = {
        "key": settings.PAYU_MERCHANT_KEY,
        "txnid": txnid,
        "amount": f"{data.amount:.2f}",
        "productinfo": data.productinfo,
        "firstname": user.full_name if user else "Student",
        "email": user.email if user else "student@example.com",
        "phone": user.phone if user else "9999999999",
        "surl": f"http://localhost:8000/api/payu/success",
        "furl": f"http://localhost:8000/api/payu/failure",
    }
    
    # Simple hash for demo
    hash_str = f"{params['key']}|{params['txnid']}|{params['amount']}|{params['productinfo']}|{params['firstname']}|{params['email']}||||||{settings.PAYU_MERCHANT_SALT}"
    params["hash"] = hashlib.sha512(hash_str.encode()).hexdigest().lower()
    params["payment_url"] = settings.PAYU_URL
    
    # Store pending
    if user:
        db.add(Payment(user_id=user.id, transaction_id=txnid, amount=data.amount, status="pending"))
        db.commit()

    return params

@router.get("/payments/", response_model=dict)
def check_payment_status(transactionId: str = Query(...), db: Session = Depends(get_db)):
    payment = db.query(Payment).filter(Payment.transaction_id == transactionId).first()
    if not payment:
        return {"records": []}
        
    return {
        "records": [{
            "status": payment.status,
            "payment_data": {
                "transactionId": payment.transaction_id,
                "paymentAmount": payment.amount,
                "paymentMethod": payment.payment_mode or "PayU"
            }
        }]
    }

@router.post("/student/coupon/validate")
def validate_coupon(data: dict):
    code = data.get("code", "").upper()
    # Simple logic for demo
    valid_coupons = ["SAVE7X3", "FLARE2025", "VIG100"]
    if code in valid_coupons:
        return {"valid": True, "discount": 150}
    return {"valid": False, "message": "Invalid coupon"}

@router.post("/success")
async def success(request: Request, db: Session = Depends(get_db)):
    form = await request.form()
    txnid = form.get("txnid")
    payment = db.query(Payment).filter(Payment.transaction_id == txnid).first()
    if payment:
        payment.status = "success"
        user = payment.user
        user.payment_status = "success"
        user.application_status = "current"
        db.commit()
    return RedirectResponse(url="http://localhost:5173/dashboard?payment=success", status_code=303)

@router.post("/failure")
async def failure(request: Request, db: Session = Depends(get_db)):
    return RedirectResponse(url="http://localhost:5173/application?payment=failed", status_code=303)
