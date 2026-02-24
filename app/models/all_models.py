from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, JSON, Float, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.db.session import Base

class ApplicationStatus(str, enum.Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    PAYMENT_PENDING = "payment_pending"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    phone = Column(String(20), index=True, nullable=True)
    hashed_password = Column(String(255), nullable=True) # Optional if only using OTP
    is_active = Column(Boolean(), default=True)
    is_admin = Column(Boolean(), default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Progress trackers
    registration_status = Column(String(50), default="completed")
    login_status = Column(String(50), default="pending")
    payment_status = Column(String(50), default="pending")
    application_status = Column(String(50), default="locked")
    
    # Relationships
    application = relationship("Application", back_populates="user", uselist=False)
    payments = relationship("Payment", back_populates="user")
    documents = relationship("Document", back_populates="user")
    messages = relationship("Message", back_populates="user")

class Application(Base):
    __tablename__ = "applications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    
    # Form Sections (Stored as JSON for flexibility, but can be split if needed for querying)
    campus_preference = Column(String(100)) # Visakhapatnam, Guntur, Hyderabad
    program_type = Column(String(50)) # Full-time, Part-time
    department = Column(String(100))
    specialization = Column(String(255))
    
    # Detailed Data Objects
    personal_details = Column(JSON, default={}) # gender, dob, category, address, etc.
    academic_details = Column(JSON, default={}) # 10th, 12th, UG, PG details
    experience_details = Column(JSON, default={}) # Work/Research experience
    research_details = Column(JSON, default={}) # Research proposal, area of interest
    
    current_step = Column(Integer, default=1)
    status = Column(Enum(ApplicationStatus), default=ApplicationStatus.DRAFT)
    
    submission_date = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship("User", back_populates="application")

class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    transaction_id = Column(String(100), unique=True, index=True)
    payu_id = Column(String(100), nullable=True)
    amount = Column(Float)
    status = Column(String(50)) # success, failure, pending
    payment_mode = Column(String(50))
    error_message = Column(String(255), nullable=True)
    raw_response = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="payments")

class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    document_type = Column(String(100)) # ssc_memo, ug_degree, etc.
    file_name = Column(String(255))
    file_path = Column(String(500))
    file_size = Column(Integer)
    mime_type = Column(String(100))
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="documents")

class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    subject = Column(String(255))
    content = Column(Text)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="messages")

class OTP(Base):
    __tablename__ = "otps"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), index=True, nullable=True)
    phone = Column(String(20), index=True, nullable=True)
    code = Column(String(6))
    purpose = Column(String(50)) # login, verify_email
    is_used = Column(Boolean, default=False)
    expires_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

class CampusInfo(Base):
    __tablename__ = "campus_info"
    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    is_active = Column(Boolean, default=True)

class ProgramInfo(Base):
    __tablename__ = "program_info"
    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    is_full_time = Column(Boolean, default=True)
    is_part_time = Column(Boolean, default=True)
    is_active = Column(Boolean, default=True)

class ApplicationCache(Base):
    __tablename__ = "application_cache"
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(255), unique=True, index=True)
    user_id = Column(String(50), index=True)
    steps = Column(JSON, default={})
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
