from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import User
from ..services.ai import summarize_and_prioritize_messages

router = APIRouter(prefix="/api/ai", tags=["ai"])

@router.post("/summarize")
def trigger_summarization(db: Session = Depends(get_db)):
    # In a real app we'd get the user_id from the token dependency. 
    # For now, grabbing the demo admin user
    user = db.query(User).filter(User.username == "discgolf_admin").first()
    if not user:
        # Fallback for testing
        user = db.query(User).first()
        
    if not user:
        return {"status": "error", "detail": "No user found"}
        
    processed = summarize_and_prioritize_messages(db, user.id)
    return {"status": "success", "processed_count": processed}
