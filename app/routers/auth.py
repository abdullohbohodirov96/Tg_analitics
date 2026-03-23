"""
Auth Router — Admin dashboard login.
POST /api/auth/login endpoint.
"""

from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.repositories.stats_repository import StatsRepository
from app.utils.security import verify_password, create_access_token

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


class LoginRequest(BaseModel):
    """Login so'rov modeli"""
    username: str
    password: str


class LoginResponse(BaseModel):
    """Login javob modeli"""
    access_token: str
    token_type: str = "bearer"


@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest, db: AsyncSession = Depends(get_db)):
    """
    Admin login endpoint.
    Username va password tekshiriladi, JWT token qaytariladi.
    """
    repo = StatsRepository(db)
    admin = await repo.get_admin_by_username(request.username)

    if not admin or not verify_password(request.password, admin.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Username yoki parol noto'g'ri",
        )

    # JWT token yaratish
    token = create_access_token({"sub": admin.username, "admin_id": admin.id})

    return LoginResponse(access_token=token)
