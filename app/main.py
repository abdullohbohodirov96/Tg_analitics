"""
FastAPI asosiy fayl — Ilova uchun kirish nuqtasi.
Barcha router lar shu yerda ulanadi.
Dashboard static fayllar ham shu yerdan xizmat ko'rsatiladi.
"""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from app.config import get_settings
from app.models.base import Base
from app.database import create_tables, async_session
print(f"📊 MODELLAR YUKLANMOQDA: AdminUser va boshqalar...")
from app.repositories.stats_repository import StatsRepository
from app.utils.security import hash_password

# Routerlar
from app.routers import webhook, stats, auth

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Ilova hayot sikli.
    Startup: jadvallar yaratish, default admin yaratish.
    Shutdown: resurslarni tozalash.
    """
    import asyncio
    
    # Jadvallarni yaratish
    try:
        print(f"📡 DB URL: {settings.async_database_url[:20]}***")
        await create_tables()
        print("✅ Database jadvallar tayyor")
    except Exception as e:
        print(f"❌ Jadvallar yaratishda xato: {e}")
        raise

    # Biroz kutish — jadvallar to'liq yaratilganini ta'minlash
    await asyncio.sleep(1)

    # Default admin yaratish (agar mavjud bo'lmasa)
    try:
        async with async_session() as db:
            repo = StatsRepository(db)
            admin = await repo.get_admin_by_username(settings.ADMIN_USERNAME)
            if not admin:
                await repo.create_admin(
                    username=settings.ADMIN_USERNAME,
                    password_hash=hash_password(settings.ADMIN_PASSWORD),
                )
                await db.commit()
                print(f"✅ Admin yaratildi: {settings.ADMIN_USERNAME}")
            else:
                print(f"ℹ️ Admin mavjud: {settings.ADMIN_USERNAME}")
    except Exception as e:
        print(f"⚠️ Admin yaratishda xato (keyinroq qayta urinib ko'riladi): {e}")
        # Admin yaratish crash qilsa ham, ilova ishlashni davom ettirsin
        try:
            await asyncio.sleep(2)
            async with async_session() as db:
                repo = StatsRepository(db)
                admin = await repo.get_admin_by_username(settings.ADMIN_USERNAME)
                if not admin:
                    await repo.create_admin(
                        username=settings.ADMIN_USERNAME,
                        password_hash=hash_password(settings.ADMIN_PASSWORD),
                    )
                    await db.commit()
                    print(f"✅ Admin yaratildi (2-urinish): {settings.ADMIN_USERNAME}")
        except Exception as e2:
            print(f"❌ Admin yaratish 2-urinish ham xato: {e2}")

    print("✅ Ilova tayyor!")
    yield
    # Shutdown
    print("🛑 Ilova to'xtatilmoqda...")


# FastAPI ilova yaratish
app = FastAPI(
    title="Telegram Analytics",
    description="Telegram guruhlar uchun analytics tizimi",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS sozlamalari
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routerlarni ulash
app.include_router(webhook.router)
app.include_router(stats.router)
app.include_router(auth.router)

# Dashboard static fayllar
dashboard_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "dashboard")
if os.path.exists(dashboard_dir):
    app.mount("/static", StaticFiles(directory=dashboard_dir), name="dashboard")


@app.get("/")
async def root():
    """Dashboard bosh sahifa"""
    index_path = os.path.join(dashboard_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "Telegram Analytics API", "docs": "/docs"}


@app.get("/login")
async def login_page():
    """Login sahifa"""
    login_path = os.path.join(dashboard_dir, "login.html")
    if os.path.exists(login_path):
        return FileResponse(login_path)
    return {"message": "Login page not found"}


@app.get("/health")
async def health():
    """Health check endpoint with DB verification"""
    db_status = "unknown"
    tables_count = 0
    registered_tables = list(Base.metadata.tables.keys())
    admin_exists = False
    
    try:
        from sqlalchemy import text
        async with async_session() as db:
            result = await db.execute(text("SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public'"))
            tables_count = result.scalar()
            db_status = "connected"
            
            # Check for admin
            from app.repositories.stats_repository import StatsRepository
            repo = StatsRepository(db)
            admin = await repo.get_admin_by_username(settings.ADMIN_USERNAME)
            admin_exists = admin is not None
    except Exception as e:
        db_status = f"error: {str(e)}"

    return {
        "status": "ok",
        "database": db_status,
        "tables_in_db": tables_count,
        "tables_in_metadata": registered_tables,
        "admin_exists": admin_exists,
        "webhook_secret_prefix": settings.WEBHOOK_SECRET[:3] + "...",
        "environment": os.getenv("RENDER", "local")
    }
