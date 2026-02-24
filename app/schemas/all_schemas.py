from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.models.all_models import ApplicationStatus

# --- OTP ---

class OTPSend(BaseModel):
    type: str  # "email"
    email: EmailStr

class OTPVerify(BaseModel):
    type: str  # "email"
    email: EmailStr
    code: str

# --- Auth & User ---
class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    phone: Optional[str] = None

class UserRegister(UserBase):
    campus: str
    program: str
    specialization: str

class UserLogin(BaseModel):
    email: EmailStr
    otp_code: str

class PasswordChange(BaseModel):
    old_password: Optional[str] = None
    new_password: str

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None

class UserView(UserBase):
    id: int
    is_active: bool
    is_admin: bool
    registration_status: str
    login_status: str
    payment_status: str
    application_status: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserView

# --- Application ---
class PersonalDetails(BaseModel):
    gender: Optional[str] = None
    dob: Optional[str] = None
    category: Optional[str] = None
    father_name: Optional[str] = None
    mother_name: Optional[str] = None
    permanent_address: Optional[str] = None
    correspondence_address: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None

class AcademicDetails(BaseModel):
    ssc_board: Optional[str] = None
    ssc_year: Optional[str] = None
    ssc_percentage: Optional[float] = None
    inter_board: Optional[str] = None
    inter_year: Optional[str] = None
    inter_percentage: Optional[float] = None
    ug_degree: Optional[str] = None
    ug_university: Optional[str] = None
    ug_year: Optional[str] = None
    ug_percentage: Optional[float] = None
    pg_degree: Optional[str] = None
    pg_university: Optional[str] = None
    pg_year: Optional[str] = None
    pg_percentage: Optional[float] = None

class ExperienceDetails(BaseModel):
    total_months: Optional[int] = 0
    research_exp: Optional[str] = None
    teaching_exp: Optional[str] = None
    industry_exp: Optional[str] = None

class ResearchDetails(BaseModel):
    area_of_research: Optional[str] = None
    proposed_topic: Optional[str] = None
    proposal_summary: Optional[str] = None

class ApplicationView(BaseModel):
    id: int
    campus_preference: Optional[str] = None
    program_type: Optional[str] = None
    department: Optional[str] = None
    specialization: Optional[str] = None
    personal_details: Optional[Dict[str, Any]] = None
    academic_details: Optional[Dict[str, Any]] = None
    experience_details: Optional[Dict[str, Any]] = None
    research_details: Optional[Dict[str, Any]] = None
    status: ApplicationStatus
    current_step: int
    
    class Config:
        from_attributes = True

class ApplicationUpdate(BaseModel):
    campus_preference: Optional[str] = None
    program_type: Optional[str] = None
    department: Optional[str] = None
    specialization: Optional[str] = None
    personal_details: Optional[Dict[str, Any]] = None
    academic_details: Optional[Dict[str, Any]] = None
    experience_details: Optional[Dict[str, Any]] = None
    research_details: Optional[Dict[str, Any]] = None
    current_step: Optional[int] = None

# --- Payment ---
class PaymentInit(BaseModel):
    amount: float
    productinfo: str

class PaymentRecord(BaseModel):
    id: int
    transaction_id: str
    amount: float
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True

# --- Document ---
class DocumentView(BaseModel):
    id: int
    document_type: str
    file_name: str
    uploaded_at: datetime
    
    class Config:
        from_attributes = True

# --- Message ---
class MessageView(BaseModel):
    id: int
    subject: str
    content: str
    is_read: bool
    created_at: datetime
    
    class Config:
        from_attributes = True
