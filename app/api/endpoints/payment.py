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
    # Try to find user by email first, then fallback to last user
    user = None
    if data.email:
        user = db.query(User).filter(User.email == data.email).first()
    
    if not user:
        user = db.query(User).order_by(User.id.desc()).first()
    
    txnid = f"VIG{uuid.uuid4().hex[:12].upper()}"
    
    params = {
        "key": settings.PAYU_MERCHANT_KEY,
        "txnid": txnid,
        "amount": f"{data.amount:.2f}",
        "productinfo": data.productinfo,
        "firstname": data.firstname or (user.full_name if user else "Student"),
        "email": data.email or (user.email if user else "student@example.com"),
        "phone": data.phone or (user.phone if user else "9999999999"),
        "surl": f"{settings.BACKEND_URL}/api/payu/success",
        "furl": f"{settings.BACKEND_URL}/api/payu/failure",
    }
    
    # PayU Biz Hash Formula:
    # sha512(key|txnid|amount|productinfo|firstname|email|udf1|udf2|udf3|udf4|udf5|udf6|udf7|udf8|udf9|udf10|salt)
    # We must include 10 pipes for the 10 UDFs even if they are empty
    hash_sequence = [
        params["key"],
        params["txnid"],
        params["amount"],
        params["productinfo"],
        params["firstname"],
        params["email"],
        "", "", "", "", "", "", "", "", "", "", # 10 UDF slots
        settings.PAYU_MERCHANT_SALT
    ]
    hash_str = "|".join(hash_sequence)
    params["hash"] = hashlib.sha512(hash_str.encode()).hexdigest().lower()
    params["payment_url"] = settings.PAYU_URL
    
    # Store pending
    if user:
        payment = Payment(user_id=user.id, transaction_id=txnid, amount=data.amount, status="pending")
        db.add(payment)
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
    # Production coupons - update as needed
    valid_coupons = {}  # e.g. {"VIGNAN2026": 150}
    if code in valid_coupons:
        return {"valid": True, "discount": valid_coupons[code]}
    return {"valid": False, "message": "Invalid coupon"}

@router.post("/success")
async def success(request: Request, db: Session = Depends(get_db)):
    try:
        form = await request.form()
        form_data = dict(form)
        print("PAYU SUCCESS CALLBACK - DATA:", form_data)
        
        txnid = form_data.get("txnid")
        status = form_data.get("status")
        
        payment = db.query(Payment).filter(Payment.transaction_id == txnid).first()
        if payment:
            payment.status = "success"
            payment.payu_id = form_data.get("mihpayid")
            payment.payment_mode = form_data.get("mode")
            payment.raw_response = form_data
            
            user = payment.user
            if user:
                user.payment_status = "success"
                user.application_status = "current"
                
            db.commit()
            print(f"Payment {txnid} marked as SUCCESS for user {user.email if user else 'unknown'}")
        else:
            print(f"Payment record not found for txnid: {txnid}")
            
    except Exception as e:
        print(f"Error in PayU success callback: {str(e)}")
        
    return RedirectResponse(url=f"{settings.FRONTEND_URL}/dashboard?payment=success", status_code=303)

@router.post("/failure")
async def failure(request: Request, db: Session = Depends(get_db)):
    try:
        form = await request.form()
        form_data = dict(form)
        print("PAYU FAILURE CALLBACK - DATA:", form_data)
        
        txnid = form_data.get("txnid")
        payment = db.query(Payment).filter(Payment.transaction_id == txnid).first()
        if payment:
            payment.status = "failure"
            payment.error_message = form_data.get("field9") or form_data.get("error_Message") or "Transaction failed"
            payment.raw_response = form_data
            
            user = payment.user
            if user:
                user.payment_status = "failed"
            
            db.commit()
            print(f"Payment {txnid} marked as FAILURE for user {user.email if user else 'unknown'}. Reason: {payment.error_message}")
            
    except Exception as e:
        print(f"Error in PayU failure callback: {str(e)}")
        
    return RedirectResponse(url=f"{settings.FRONTEND_URL}/application?payment=failed", status_code=303)


