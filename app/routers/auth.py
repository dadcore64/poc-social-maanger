from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
from pydantic import BaseModel
import random

from ..database import get_db
from ..models import User
from ..security import verify_password, get_password_hash, create_access_token, create_reset_token, verify_reset_token, ACCESS_TOKEN_EXPIRE_MINUTES
from ..auth_deps import get_current_user_from_cookie

router = APIRouter(tags=["auth"])

class UserCreate(BaseModel):
    username: str
    email: str
    password: str

class ForgotPasswordRequest(BaseModel):
    email: str

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

@router.post("/forgot-password")
def forgot_password(req: ForgotPasswordRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == req.email).first()
    if not user:
        # We return success anyway to prevent email enumeration
        return {"status": "success", "message": "If that email is registered, a reset link has been sent.", "dev_token": None}
    
    token = create_reset_token(user.email)
    # In a real app, send email here. For prototype, we'll return it so the UI can mock the flow.
    return {"status": "success", "message": "If that email is registered, a reset link has been sent.", "dev_token": token}

@router.post("/reset-password")
def reset_password(req: ResetPasswordRequest, db: Session = Depends(get_db)):
    email = verify_reset_token(req.token)
    if not email:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")
        
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=400, detail="User no longer exists")
        
    user.hashed_password = get_password_hash(req.new_password)
    db.commit()
    
    return {"status": "success", "message": "Password has been reset successfully."}

@router.get("/check-username")
def check_username(username: str, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.username == username).first()
    if existing:
        suggestions = [f"{username}{random.randint(10, 999)}" for _ in range(3)]
        return {"available": False, "suggestions": suggestions}
    return {"available": True}

@router.get("/check-email")
def check_email(email: str, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == email).first()
    return {"available": existing is None}

@router.post("/register")
def register_user(user_data: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter((User.username == user_data.username) | (User.email == user_data.email)).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username or email already registered")
    
    hashed = get_password_hash(user_data.password)
    new_user = User(username=user_data.username, email=user_data.email, hashed_password=hashed)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"status": "success", "user_id": new_user.id}

@router.post("/token")
def login_for_access_token(response: Response, form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        # Using a JSONResponse directly to avoid the default OAuth2 structure masking the error for the frontend
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": "Incorrect username or password"},
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": user.username}, expires_delta=access_token_expires)
    
    response.set_cookie(
        key="access_token", 
        value=f"Bearer {access_token}", 
        httponly=True, 
        max_age=1800,
        samesite="lax"
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/logout")
def logout(response: Response):
    response.delete_cookie("access_token")
    return {"status": "success"}

class UserUpdate(BaseModel):
    username: Optional[str] = None
    password: Optional[str] = None
    ai_provider: Optional[str] = None
    ai_token: Optional[str] = None
    ai_context_prompt: Optional[str] = None
    ai_min_length: Optional[int] = None
    ai_stop_words: Optional[str] = None

@router.put("/api/users/me")
def update_user_settings(user_data: UserUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user_from_cookie)):
    if not user:
        raise HTTPException(status_code=401, detail="User not authenticated")
        
    if user_data.username and user_data.username != user.username:
        existing = db.query(User).filter(User.username == user_data.username).first()
        if existing:
            raise HTTPException(status_code=400, detail="Username already taken")
        user.username = user_data.username
        
    if user_data.password:
        user.hashed_password = get_password_hash(user_data.password)
        
    if user_data.ai_provider:
        user.ai_provider = user_data.ai_provider
        
    if user_data.ai_token and user_data.ai_token != "UNCHANGED":
        from ..security import encrypt_token
        user.encrypted_ai_token = encrypt_token(user_data.ai_token)

    if user_data.ai_context_prompt is not None:
        user.ai_context_prompt = user_data.ai_context_prompt
        
    if user_data.ai_min_length is not None:
        user.ai_min_length = user_data.ai_min_length
        
    if user_data.ai_stop_words is not None:
        user.ai_stop_words = user_data.ai_stop_words
        
    db.commit()
    return {"status": "success"}

@router.delete("/api/users/me")
def delete_user_account(response: Response, db: Session = Depends(get_db), user: User = Depends(get_current_user_from_cookie)):
    if not user:
        raise HTTPException(status_code=401, detail="User not authenticated")
    
    db.delete(user)
    db.commit()
    response.delete_cookie("access_token")
    return {"status": "success"}
