# PhD Admissions Backend (FastAPI)

The core API for the Vignan PhD Admissions portal, handling authentication, application data, and payment verification.

## 🚀 Quick Start (Local)

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Environment Setup**:
   Create a `.env` file with your database URL, SMTP credentials, and JWT secret.

3. **Run Server**:
   ```bash
   uvicorn app.main:app --reload
   ```

## ☁️ Production Deployment

This project is configured for deployment on **AWS EC2 (Instance 2)**.

- **Setup Script**: `deployment/setup_backend.sh`
- **DB Setup**: `deployment/setup_db.sh`
- **Production Server**: Gunicorn with Uvicorn workers.

Refer to `PROJECT_HANDOVER.md` for the 3-instance deployment strategy.

## 🛠 Tech Stack
- **Framework**: FastAPI
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Authentication**: JWT & OTP (SMTP/Jio)
- **Validation**: Pydantic v2
