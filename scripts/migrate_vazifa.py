import asyncio
import os
import re
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

def get_db_url():
    # .env dan DATABASE_URL ni o'qish
    if os.path.exists(".env"):
        with open(".env", "r") as f:
            for line in f:
                if line.startswith("DATABASE_URL="):
                    url = line.split("=", 1)[1].strip()
                    # asyncpg ga aylantirish if needed
                    if url.startswith("postgresql://"):
                        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
                    return url
    return os.getenv("DATABASE_URL")

async def migrate_db():
    url = get_db_url()
    if not url:
        print("❌ DATABASE_URL topilmadi!")
        return

    print(f"=== Database Migratsiyasi boshlanmoqda... ===")
    engine = create_async_engine(url)
    
    async with engine.begin() as conn:
        try:
            await conn.execute(text("ALTER TABLE tasks ADD COLUMN IF NOT EXISTS source_message_id BIGINT"))
            print("✅ 'source_message_id' ustuni muvaffaqiyatli qo'shildi.")
        except Exception as e:
            print(f"⚠️ Ogohlantirish (source_message_id): {e}")

    await engine.dispose()
    print("=== Migratsiya yakunlandi. ===")

if __name__ == "__main__":
    asyncio.run(migrate_db())
