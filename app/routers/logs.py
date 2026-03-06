from fastapi import APIRouter, Depends, HTTPException
from ..auth_deps import get_current_user_from_cookie
from ..models import User
import os

router = APIRouter(prefix="/api/logs", tags=["logs"])

@router.get("")
def get_dev_logs(user: User = Depends(get_current_user_from_cookie)):
    if not user:
        raise HTTPException(status_code=401, detail="User not authenticated")
    
    log_file = "logs/app.log"
    if not os.path.exists(log_file):
        return {"logs": []}
    
    with open(log_file, "r", encoding="utf-8") as f:
        # Get the last 1000 lines
        lines = f.readlines()
    
    return {"logs": lines[-1000:]}
