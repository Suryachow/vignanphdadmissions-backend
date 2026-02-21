from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.endpoints import auth, application, payment
from app.core.config import settings
from app.db.session import engine
from app.models import all_models

# Init DB
all_models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Vignan PhD API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Unified Router for all /api calls
app.include_router(auth.router, prefix="/api", tags=["Admissions API"])

# Special PayU sub-router if needed, or we can move it to auth too
app.include_router(payment.router, prefix="/api/payu", tags=["PayU"])

# Internal student management
app.include_router(application.router, prefix="/api/student/internal", tags=["Internal"])

@app.get("/")
def home(): return {"status": "Vignan API Operational"}
