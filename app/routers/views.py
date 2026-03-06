from fastapi import APIRouter, Request, Depends, status
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
import os

from ..database import get_db
from ..models import User
from ..auth_deps import get_current_user_from_cookie

router = APIRouter(tags=["views"])

# Setup templates directory
current_dir = os.path.dirname(os.path.abspath(__file__))
templates_dir = os.path.join(os.path.dirname(current_dir), "templates")
templates = Jinja2Templates(directory=templates_dir)

@router.get("/", response_class=HTMLResponse)
def get_dashboard(request: Request, user: User = Depends(get_current_user_from_cookie)):
    if not user:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    
    # Access platforms to ensure they are loaded into the user object 
    # before the database session is closed by the dependency.
    _ = user.platforms

    return templates.TemplateResponse("dashboard.html", {"request": request, "user": user})

@router.get("/login", response_class=HTMLResponse)
def get_login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})
