# Project Handover: PhD Admissions Portal (Vignan University)

This document provides a comprehensive overview of the current state of the PhD Admissions Portal for hand-off to ChatGPT or other AI assistants.

## 🚀 Project Overview
A full-stack application for PhD student admissions featuring automated OTP verification, payment gateway integration (PayU), and a multi-step application form.

### 🛠 Technology Stack
- **Frontend**: React 19 (Vite), Tailwind CSS 4, Framer Motion, Lucide Icons.
- **Backend**: FastAPI (Python), PostgreSQL, SQLAlchemy.
- **Email/Auth**: Gmail SMTP (App Password) for OTP delivery.
- **Payment**: PayU Integration.
- **Deployment**: AWS (EC2, RDS, S3).

---

## 📂 Project Structure
```text
/phd-admissions (Root)
├── backend/                # FastAPI Application
│   ├── app/                # Main logic, models, schemas, and API routes
│   │   ├── api/            # Route endpoints (/auth, /payment, /student)
│   │   ├── core/           # Security, Config, and DB connection
│   │   ├── models/         # SQLAlchemy DB Models (User, Payment, etc.)
│   │   ├── schemas/        # Pydantic Schemas for validation
│   │   └── services/       # OTP and Email services
│   ├── requirements.txt    # Python dependencies
│   └── .env                # Local secrets (Database, SMTP)
│
├── phdadmissions/          # React Student Frontend (Vite)
│   ├── src/
│   │   ├── pages/          # Pages: Registration, Dashboard, ApplicationForm
│   │   ├── store/          # StepContext for workflow state
│   │   ├── components/     # UI elements (Buttons, Cards, Guards)
│   │   └── services/       # API calling logic (Verification, OTP)
│   ├── dist/               # PRODUCTION BUILD (Generated for deployment)
│   └── package.json        # Frontend config and dependencies
│
└── deployment/             # AWS Production Setup Scripts
    ├── setup_db.sh         # PostgreSQL installer for Instance 3
    ├── setup_backend.sh    # Python & Gunicorn setup for Instance 2
    ├── setup_frontend.sh   # Nginx setup for Instance 1
    ├── nginx.conf          # Reverse Proxy settings for Gateway
    ├── backend.env.prod    # Production environment template
    └── frontend.env.prod   # Frontend API URL config for production
```

---

## ☁️ AWS Deployment - Help Needed
The project is ready for a **3-Instance Production Setup**. The AI Assistant should guide the user through these specific cloud steps:

### **Phase 1: Database (Instance 3)**
- Launch standard Ubuntu EC2 or use RDS.
- Run `setup_db.sh`.
- **Action**: Explain how to configure the **AWS Security Group** to allow Port 5432 ONLY from the Backend's private IP.

### **Phase 2: Backend Logic (Instance 2)**
- Launch EC2.
- Run `setup_backend.sh`.
- **Action**: Help the user git clone the repo and manually create the production `.env`.
- **Action**: Map the Database Private IP into the `DATABASE_URL`.

### **Phase 3: Gateway & Frontend (Instance 1)**
- Launch EC2.
- Run `setup_frontend.sh`.
- **Action**: Configure `nginx.conf` with the Backend's Private IP.
- **Action**: Explain how to map a **Domain Name** or use the **Elastic IP** for the public-facing URL.

### **Phase 4: Verification**
- Test the signup flow.
- Ensure the PayU redirect triggers successfully.
- Confirm SMTP emails are sent through the AWS network.

---

## 📋 Current To-Do List (Next Steps)
1. **AWS Accounts**: Propose the instance types (t3.micro is usually enough for start).
2. **IP Mapping**: Guide the user on where to find the "Private IP" and "Public IP" in the AWS Console.
3. **SSL Setup**: Help with Port 443 opening and Certbot installation.


---

## 🔑 Key Credentials (Local)
- **SMTP**: `patibandlasurya9989@gmail.com`
- **DB (Local)**: User: `postgres`, Pass: `9989`, DB: `phd_admissions`
- **Frontend API**: `http://localhost:8000` (Dev)

---
*Created by Antigravity AI Assistant.*
