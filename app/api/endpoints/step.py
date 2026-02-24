from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.all_models import ApplicationCache
from pydantic import BaseModel
from typing import Dict, Any, Optional
from sqlalchemy.orm.attributes import flag_modified

router = APIRouter()

class CacheStepDataPayload(BaseModel):
    session_id: str
    user_id: str
    step: str
    data: Dict[str, Any]

@router.post("/{step_name}/")
def save_step(step_name: str, payload: CacheStepDataPayload, db: Session = Depends(get_db)):
    cache = db.query(ApplicationCache).filter(ApplicationCache.session_id == payload.session_id).first()
    if not cache:
        cache = ApplicationCache(session_id=payload.session_id, user_id=payload.user_id, steps={})
        db.add(cache)
        db.commit()
        db.refresh(cache)
    
    steps_data = cache.steps or {}
    steps_data[step_name] = payload.data
    
    cache.steps = steps_data
    flag_modified(cache, "steps")
    db.commit()
    return {"message": "Step cached"}

@router.get("/cache/")
def get_cache(db: Session = Depends(get_db)):
    caches = db.query(ApplicationCache).all()
    cached_applications = []
    for c in caches:
        cached_applications.append({
            "session_id": c.session_id,
            "user_id": c.user_id,
            "steps": c.steps
        })
    return {"cached_applications": cached_applications}
