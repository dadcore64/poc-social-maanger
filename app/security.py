from passlib.context import CryptContext
from jose import JWTError, jwt
from cryptography.fernet import Fernet
from datetime import datetime, timedelta
from typing import Optional

SECRET_KEY = "super-secret-development-key-please-change"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
FERNET_KEY = b'Wv1nJkK9vGkR_5_0hK4k5O8n7V3x2-5H4b1c3n4d5e8=' 

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
f_cipher = Fernet(FERNET_KEY)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def encrypt_token(token: str) -> str:
    return f_cipher.encrypt(token.encode()).decode()

def decrypt_token(encrypted_token: str) -> str:
    return f_cipher.decrypt(encrypted_token.encode()).decode()

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def create_reset_token(email: str) -> str:
    expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode = {"sub": email, "exp": expire, "type": "reset"}
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_reset_token(token: str) -> Optional[str]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "reset":
            return None
        return payload.get("sub")
    except JWTError:
        return None
