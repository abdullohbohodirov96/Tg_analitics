"""
Webhook Router — Telegram update larni qabul qilish.
POST /webhook/telegram endpoint.
"""

from fastapi import APIRouter, Request, HTTPException, status

from app.config import get_settings
from app.database import async_session
from app.services.bot_service import BotService

router = APIRouter(prefix="/webhook", tags=["Webhook"])
settings = get_settings()


@router.post("/telegram")
async def telegram_webhook(request: Request):
    """
    Telegram webhook endpoint.
    Telegram serveridan kelgan update larni qabul qiladi.

    Security: secret_token header orqali tekshiriladi.
    """
    # Webhook secret tekshirish (faqat settingsda mavjud bo'lsa)
    secret = request.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
    if settings.WEBHOOK_SECRET and settings.WEBHOOK_SECRET != "default_secret_change_me":
        if secret != settings.WEBHOOK_SECRET:
            print(f"⚠️ Webhook secret mismatch! Received: {secret[:3]}..., Expected: {settings.WEBHOOK_SECRET[:3]}...")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Webhook secret noto'g'ri",
            )

    # Update ni olish
    try:
        update = await request.json()
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="JSON formatda emas",
        )

    # Update ni qayta ishlash
    async with async_session() as db:
        try:
            bot_service = BotService(db)
            await bot_service.process_update(update)
            await db.commit()
        except Exception as e:
            await db.rollback()
            # Log error but don't expose details
            print(f"Webhook processing error: {e}")

    return {"ok": True}
