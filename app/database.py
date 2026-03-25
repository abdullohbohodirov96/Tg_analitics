from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.config import get_settings
from app.models.base import Base

settings = get_settings()

# Async engine yaratish
engine = create_async_engine(
    settings.async_database_url,
    echo=False,
    pool_size=20,
    max_overflow=10,
)

# Session factory
async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

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


from sqlalchemy import text

async def create_tables():
    """Barcha jadvallarni yaratish (development uchun) va yangi columnlarni qo'shish"""
    # Modellarni import qilish create_all dan oldin
    import app.models.models as models
    print(f"📊 Jadvallar Metadata-da: {list(Base.metadata.tables.keys())}")
    
    async with engine.begin() as conn:
        print("🛠 Jadvallarni yaratish boshlanmoqda...")
        await conn.run_sync(Base.metadata.create_all)
        print(f"✅ Jadvallar yaratildi. Jami: {len(Base.metadata.tables)}")
        
        # Migrations (Add missing columns if they don't exist)
        try:
            await conn.execute(text("ALTER TABLE messages ADD COLUMN text TEXT"))
        except Exception:
            pass  # Already exists

        try:
            await conn.execute(text("ALTER TABLE conversations ADD COLUMN response_time_seconds DOUBLE PRECISION"))
        except Exception:
            pass  # Already exists

        # Group table migrations
        try:
            await conn.execute(text("ALTER TABLE groups ADD COLUMN custom_title VARCHAR(255)"))
        except Exception:
            pass

        try:
            await conn.execute(text("ALTER TABLE groups ADD COLUMN group_link VARCHAR(255)"))
        except Exception:
            pass

        try:
            await conn.execute(text("ALTER TABLE users ADD COLUMN is_operator BOOLEAN DEFAULT FALSE"))
        except Exception:
            pass
