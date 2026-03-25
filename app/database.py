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
    """Barcha jadvallarni yaratish (development uchun) va jadvallarni kengaytirish"""
    import app.models.models as models
    print(f"📊 Jadvallar Metadata-da: {list(Base.metadata.tables.keys())}")
    
    # 1. Barcha asosiy jadvallarni yaratish
    async with engine.begin() as conn:
        print("🛠 Jadvallarni yaratish (create_all)...")
        await conn.run_sync(Base.metadata.create_all)
    
    # 2. Migratsiyalar (Har birini alohida blockda qilish kerak, xato bo'lsa rollback bo'lmasligi uchun)
    async def safe_execute_alt(sql):
        try:
            async with engine.begin() as conn:
                await conn.execute(text(sql))
        except Exception:
            pass # Allaqachon mavjud yoki boshqa xato

    await safe_execute_alt("ALTER TABLE messages ADD COLUMN text TEXT")
    await safe_execute_alt("ALTER TABLE conversations ADD COLUMN response_time_seconds DOUBLE PRECISION")
    await safe_execute_alt("ALTER TABLE groups ADD COLUMN custom_title VARCHAR(255)")
    await safe_execute_alt("ALTER TABLE groups ADD COLUMN group_link VARCHAR(255)")
    await safe_execute_alt("ALTER TABLE users ADD COLUMN is_operator BOOLEAN DEFAULT FALSE")

    # CRM Expansion Migrations
    await safe_execute_alt("ALTER TABLE conversations ADD COLUMN status VARCHAR(50) DEFAULT 'new'")
    await safe_execute_alt("ALTER TABLE conversations ADD COLUMN topic_id BIGINT")
    await safe_execute_alt("ALTER TABLE conversations ADD COLUMN topic_name VARCHAR(255)")
    await safe_execute_alt("ALTER TABLE conversations ADD COLUMN last_activity_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
    
    # Task Expansion Migrations
    await safe_execute_alt("ALTER TABLE tasks ADD COLUMN source_message_id BIGINT")

    print(f"✅ Jadvallar va migratsiyalar yakunlandi.")
