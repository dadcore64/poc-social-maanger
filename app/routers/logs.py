from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
from datetime import datetime, timedelta
from ..auth_deps import get_current_user_from_cookie
from ..models import User
import os
import glob
import re

router = APIRouter(prefix="/api/logs", tags=["logs"])

# Format: [2026-03-05 00:00:00,000]
LOG_TIME_PATTERN = re.compile(r"^\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}),\d{3}\]")

@router.get("")
def get_dev_logs(
    hours: Optional[str] = Query("1"), 
    user: User = Depends(get_current_user_from_cookie)
):
    if not user:
        raise HTTPException(status_code=401, detail="User not authenticated")
    
    log_dir = "logs"
    if not os.path.exists(log_dir):
        return {"logs": []}

    # Find all log files (like app.log, app.log.1, other.log)
    log_files = glob.glob(os.path.join(log_dir, "*.log*"))
    
    # Sort files by modification time so oldest files are first, newest last
    log_files.sort(key=os.path.getmtime)

    all_lines = []
    for log_file in log_files:
        try:
            with open(log_file, "r", encoding="utf-8") as f:
                all_lines.extend(f.readlines())
        except Exception:
            continue

    if hours == "all" or hours is None:
        return {"logs": all_lines[-2000:]} # Limit to last 2000 to prevent huge payloads
    
    try:
        hours_int = int(hours)
    except ValueError:
        return {"logs": all_lines[-2000:]}
        
    cutoff_time = datetime.now() - timedelta(hours=hours_int)
    
    filtered_lines = []
    last_valid_time = None
    for line in all_lines:
        match = LOG_TIME_PATTERN.match(line)
        if match:
            time_str = match.group(1)
            try:
                last_valid_time = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                pass
        
        # Exclude lines if their block is older than the cutoff
        if last_valid_time and last_valid_time < cutoff_time:
            continue
            
        filtered_lines.append(line)
        
    return {"logs": filtered_lines[-2000:]}