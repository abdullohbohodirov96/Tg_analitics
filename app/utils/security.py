"""
Xavfsizlik utilitlari.
JWT token yaratish/tekshirish va parol hash qilish funksiyalari.
"""

from datetime import datetime, timedelta
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.config import get_settings

settings = get_settings()

# Parol hash qilish uchun
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Bearer token olish uchun
security = HTTPBearer()


def hash_password(password: str) -> str:
    """Parolni hash qilish"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Parolni tekshirish"""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """JWT access token yaratish"""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.JWT_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def verify_token(token: str) -> dict:
    """JWT tokenni tekshirish va decode qilish"""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token yaroqsiz yoki muddati o'tgan",
        )


async def get_current_admin(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    """
    Dependency: joriy admin foydalanuvchini olish.
    Har bir himoyalangan endpointda ishlatiladi.
    """
    return verify_token(credentials.credentials)
