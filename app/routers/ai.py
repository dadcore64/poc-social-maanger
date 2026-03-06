from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional

from ..database import get_db
from ..models import User, AILog
from ..services.ai import summarize_and_prioritize_messages

from ..auth_deps import get_current_user_from_cookie

router = APIRouter(prefix="/api/ai", tags=["ai"])

@router.post("/summarize")
def trigger_summarization(
    hours: int = Query(1),
    platform: str = Query("ALL"),
    search: str = Query(""),
    db: Session = Depends(get_db), 
    user: User = Depends(get_current_user_from_cookie)
):
    if not user:
        return {"status": "error", "detail": "No user found"}
        
    result = summarize_and_prioritize_messages(db, user.id, hours, platform, search)
    return {"status": "success", "processed_count": result.get("processed_count", 0), "overall_summary": result.get("overall_summary", "")}

@router.get("/history")
def get_ai_history(db: Session = Depends(get_db), user: User = Depends(get_current_user_from_cookie)):
    if not user:
        return {"status": "error", "detail": "No user found"}
    
    logs = db.query(AILog).filter(AILog.user_id == user.id).order_by(AILog.timestamp.desc()).limit(50).all()
    
    return [
        {
            "id": log.id,
            "timestamp": log.timestamp.isoformat(),
            "overall_summary": log.overall_summary,
            "processed_count": log.processed_count,
            "filter_criteria": log.filter_criteria
        }
        for log in logs
    ]
