"""
Database ulanish va session boshqaruvi.
SQLAlchemy async engine ishlatiladi PostgreSQL bilan ishlash uchun.
"""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from app.config import get_settings

settings = get_settings()

# Async engine yaratish
# Railway postgresql:// beradi, async_database_url avtomatik postgresql+asyncpg:// ga o'zgartiradi
engine = create_async_engine(
    settings.async_database_url,
    echo=False,  # Production da False bo'lishi kerak
    pool_size=20,
    max_overflow=10,
)

# Session factory
async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """Barcha modellar uchun base class"""
    pass


async def get_db() -> AsyncSession:
    """
    Dependency injection uchun DB session olish.
    Har bir request uchun yangi session ochiladi va yopiladi.
    """
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def create_tables():
    """Barcha jadvallarni yaratish (development uchun)"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
