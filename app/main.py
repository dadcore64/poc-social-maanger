from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.staticfiles import StaticFiles
import time

from .database import engine, Base, SessionLocal
from .models import User, PlatformConnection, IncomingMessage, MuteRule
from .routers import auth, messages, views, webhooks, ai, platforms, logs
from .logger import logger

# Create tables in the database
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Socialease API")

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# ==========================================
# MIDDLEWARE & EXCEPTION HANDLING
# ==========================================
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    
    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        logger.info(f"Method: {request.method} Path: {request.url.path} Status: {response.status_code} Process Time: {process_time:.4f}s")
        return response
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(f"Failed Request: Method: {request.method} Path: {request.url.path} Process Time: {process_time:.4f}s")
        raise e

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled Exception on {request.method} {request.url.path}: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal server error occurred. Please review the application logs."},
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.warning(f"Validation Error on {request.method} {request.url.path}: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors()},
    )

app.include_router(auth.router)
app.include_router(messages.router)
app.include_router(views.router)
app.include_router(webhooks.router)
app.include_router(ai.router)
app.include_router(platforms.router)
app.include_router(logs.router)

@app.on_event("startup")
def startup_event():
    db = SessionLocal()
    user = db.query(User).filter(User.username == "discgolf_admin").first()
    if not user:
        from .security import get_password_hash
        hashed = get_password_hash("hashed")
        new_user = User(username="discgolf_admin", email="admin@socialease.local", hashed_password=hashed)
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        ig_conn = PlatformConnection(user_id=new_user.id, platform_name="INSTAGRAM", account_id="ig_123", encrypted_token="xyz")
        yt_conn = PlatformConnection(user_id=new_user.id, platform_name="YOUTUBE", account_id="yt_123", encrypted_token="xyz")
        db.add_all([ig_conn, yt_conn])
        db.commit()
        
        msg1 = IncomingMessage(connection_id=ig_conn.id, external_message_id="ext_1", sender_name="DiscLover99", content="Hey! Are you guys getting the new Simon Lizotte discs in stock this week?")
        msg2 = IncomingMessage(connection_id=yt_conn.id, external_message_id="ext_2", sender_name="ProTourFan", content="Great podcast today! Really agree with your take on the PDGA rules change.")
        db.add_all([msg1, msg2])
        db.commit()
    db.close()
