"""
Loyiha konfiguratsiyasi.
Barcha muhim sozlamalar .env faylidan yoki environment variablesdan o'qiladi.
Railway.app avtomatik DATABASE_URL beradi.
"""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Asosiy sozlamalar - .env faylidan o'qiladi"""

    # Telegram Bot
    BOT_TOKEN: str = ""
    WEBHOOK_SECRET: str = "default_secret_change_me"

    # Database — Railway avtomatik beradi
    # Railway format: postgresql://user:pass@host:port/db
    # Biz asyncpg ishlatamiz: postgresql+asyncpg://user:pass@host:port/db
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@db:5432/telegram_analytics"

    # JWT Auth (Admin panel uchun)
    JWT_SECRET: str = "change_this_secret_key"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 1440  # 24 soat

    # Admin (birinchi ishga tushirishda yaratiladi)
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = "admin123"

    # Server — Railway PORT ni avtomatik beradi
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    PORT: int = 8000  # Railway shu nomda beradi

    @property
    def async_database_url(self) -> str:
        """
        Railway postgresql:// beradi, lekin bizga postgresql+asyncpg:// kerak.
        Bu property avtomatik o'zgartiradi.
        """
        url = self.DATABASE_URL
        if url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        return url

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """Sozlamalarni cache qilib qaytaradi"""
    return Settings()
