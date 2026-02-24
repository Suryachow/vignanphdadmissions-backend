import random
import string
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session
from app.models.all_models import OTP
from app.core.config import settings
import aiosmtplib
from email.message import EmailMessage

async def send_otp_email(email_to: str, otp_code: str):
    message = EmailMessage()
    message["From"] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_FROM}>"
    message["To"] = email_to
    message["Subject"] = "Your PhD Admissions Verification Code"
    
    content = f"""
    <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #e2e8f0; rounded-lg: 12px;">
                <h2 style="color: #1e3a8a;">{settings.SMTP_FROM_NAME}</h2>
                <p>Hello,</p>
                <p>You are receiving this email for verification of your Ph.D Admissions account.</p>
                <div style="background-color: #f8fafc; padding: 15px; text-align: center; border-radius: 8px; margin: 20px 0;">
                    <span style="font-size: 32px; font-weight: bold; letter-spacing: 5px; color: #1e3a8a;">{otp_code}</span>
                </div>
                <p>This code will expire in 10 minutes.</p>
                <p>If you did not request this code, please ignore this email.</p>
                <hr style="border: none; border-top: 1px solid #e2e8f0; margin: 20px 0;" />
                <p style="font-size: 12px; color: #64748b;">This is an automated message. Please do not reply.</p>
            </div>
        </body>
    </html>
    """
    message.add_alternative(content, subtype="html")

    if settings.SMTP_HOST and settings.SMTP_USER:
        print(f"Attempting to send OTP email to {email_to} via {settings.SMTP_HOST}:{settings.SMTP_PORT}")
        try:
            # Determine TLS settings based on port
            # Port 465: SSL/TLS (Implicit)
            # Port 587: STARTTLS (Explicit)
            use_ssl = settings.SMTP_PORT == 465
            use_starttls = settings.SMTP_PORT == 587
            
            print(f"Using SSL: {use_ssl}, STARTTLS: {use_starttls}")
            
            await aiosmtplib.send(
                message,
                hostname=settings.SMTP_HOST,
                port=settings.SMTP_PORT,
                username=settings.SMTP_USER,
                password=settings.SMTP_PASSWORD,
                use_tls=use_ssl, 
                start_tls=use_starttls,
            )
            print(f"✅ OTP email sent successfully to {email_to}")
        except Exception as e:
            print(f"❌ Failed to send OTP email to {email_to}: {str(e)}")
            # Log the full error for debugging
            import traceback
            traceback.print_exc()
    else:
        print(f"Skipping email sent (SMTP not configured). OTP for {email_to}: {otp_code}")

class OTPService:
    @staticmethod
    def generate_otp(length: int = 6) -> str:
        return "".join(random.choices(string.digits, k=length))

    @staticmethod
    async def create_otp(db: Session, email: str, phone: str = None, purpose: str = None) -> str:
        code = OTPService.generate_otp()
        expires = datetime.utcnow() + timedelta(minutes=10)
        
        # Deactivate/Remove old OTPs for this target
        db.query(OTP).filter(OTP.email == email, OTP.is_used == False).delete()
        
        db_otp = OTP(email=email, phone=phone, purpose=purpose, code=code, expires_at=expires)
        db.add(db_otp)
        db.commit()
        
        await send_otp_email(email, code)
        return code

    @staticmethod
    def verify_otp(db: Session, code: str, email: str) -> bool:
        db_otp = db.query(OTP).filter(
            OTP.email == email,
            OTP.code == code,
            OTP.expires_at > datetime.utcnow(),
            OTP.is_used == False
        ).first()
        
        if db_otp:
            db_otp.is_used = True
            db.commit()
            return True
        return False

otp_service = OTPService()
