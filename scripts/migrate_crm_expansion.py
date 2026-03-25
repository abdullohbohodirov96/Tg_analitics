import asyncio
import os
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

    print("=== CRM Expansion Migratsiyasi boshlanmoqda... ===")
    engine = create_async_engine(url)
    
    async with engine.begin() as conn:
        try:
            # Status
            await conn.execute(text("ALTER TABLE conversations ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'new'"))
            # Topic ID
            await conn.execute(text("ALTER TABLE conversations ADD COLUMN IF NOT EXISTS topic_id BIGINT"))
            # Topic Name
            await conn.execute(text("ALTER TABLE conversations ADD COLUMN IF NOT EXISTS topic_name VARCHAR(255)"))
            # Last Activity
            await conn.execute(text("ALTER TABLE conversations ADD COLUMN IF NOT EXISTS last_activity_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP"))
            
            # Indexlar (optional lekin tavsiya etiladi)
            await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_conv_status ON conversations(status)"))
            await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_conv_last_activity ON conversations(last_activity_at)"))
            
            print("✅ 'conversations' jadvali muvaffaqiyatli yangilandi.")
        except Exception as e:
            print(f"⚠️ Ogohlantirish: {e}")

    await engine.dispose()
    print("=== Migratsiya yakunlandi. ===")

if __name__ == "__main__":
    asyncio.run(migrate_db())
