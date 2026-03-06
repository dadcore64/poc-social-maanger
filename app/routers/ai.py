from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import User
from ..services.ai import summarize_and_prioritize_messages

from ..auth_deps import get_current_user_from_cookie

router = APIRouter(prefix="/api/ai", tags=["ai"])

@router.post("/summarize")
def trigger_summarization(db: Session = Depends(get_db), user: User = Depends(get_current_user_from_cookie)):
    if not user:
        return {"status": "error", "detail": "No user found"}
        
    processed = summarize_and_prioritize_messages(db, user.id)
    return {"status": "success", "processed_count": processed}
