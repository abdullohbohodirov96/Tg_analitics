"""
Bot Service — Telegram bot command handler lari.
Webhook orqali kelgan update larni qayta ishlash.
"""

from datetime import datetime
from typing import Optional, Dict, Any
import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.repositories.stats_repository import StatsRepository
from app.services.analytics_service import AnalyticsService

settings = get_settings()


class BotService:
    """Telegram bot xabarlarini qayta ishlash xizmati"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = StatsRepository(db)
        self.analytics = AnalyticsService(db)

    # =====================================================
    # TELEGRAM API
    # =====================================================

    async def send_message(self, chat_id: int, text: str, parse_mode: str = "HTML"):
        """Telegram API orqali xabar yuborish"""
        url = f"https://api.telegram.org/bot{settings.BOT_TOKEN}/sendMessage"
        async with httpx.AsyncClient() as client:
            await client.post(url, json={
                "chat_id": chat_id,
                "text": text,
                "parse_mode": parse_mode,
            })

    # =====================================================
    # UPDATE PROCESSING
    # =====================================================

    async def process_update(self, update: Dict[str, Any]):
        """
        Telegram update ni qayta ishlash.
        1. Faqat group xabarlarni qayta ishlash
        2. User va group ni saqlash
        3. Xabarni saqlash
        4. Agar reply bo'lsa, conversation ni yangilash
        5. Bot commandlarni tekshirish
        """
        message = update.get("message")
        if not message:
            return

        chat = message.get("chat", {})
        chat_type = chat.get("type", "")

        # Faqat group va supergroup xabarlarni qayta ishlash
        if chat_type not in ("group", "supergroup"):
            # Private chatda command qabul qilish
            if chat_type == "private":
                await self._handle_private_command(message)
            return

        from_user = message.get("from", {})
        if not from_user or from_user.get("is_bot", False):
            return

        # Group va User ni saqlash
        group = await self.repo.get_or_create_group(
            telegram_id=chat["id"],
            title=chat.get("title"),
        )

        user = await self.repo.get_or_create_user(
            telegram_id=from_user["id"],
            username=from_user.get("username"),
            first_name=from_user.get("first_name"),
            last_name=from_user.get("last_name"),
        )

        # Bot command tekshirish
        text = message.get("text", "") or ""
        if text.startswith("/"):
            await self._handle_command(chat["id"], text, user)
            return

        # Reply tekshirish — operator javobi ekanligini aniqlash
        reply_to = message.get("reply_to_message")
        reply_to_msg_id = None
        is_from_operator = user.is_operator

        if reply_to:
            reply_to_msg_id = reply_to.get("message_id")

            # Agar operator boshqa user xabariga reply qilsa
            if is_from_operator and reply_to_msg_id:
                await self._handle_operator_reply(
                    group_id=group.id,
                    operator=user,
                    reply_to_message_id=reply_to_msg_id,
                    reply_date=datetime.utcfromtimestamp(message["date"]),
                    reply_telegram_id=message["message_id"],
                )

        # Xabarni saqlash
        msg_date = datetime.utcfromtimestamp(message["date"])
        saved_msg = await self.repo.save_message(
            telegram_message_id=message["message_id"],
            group_id=group.id,
            user_id=user.id,
            text=text,
            date=msg_date,
            reply_to_message_id=reply_to_msg_id,
            is_from_operator=is_from_operator,
        )

        # Agar oddiy user xabar yozsa — yangi conversation ochish
        if not is_from_operator and not reply_to_msg_id:
            await self.repo.create_conversation(
                group_id=group.id,
                user_id=user.id,
                user_message_id=message["message_id"],
            )

    async def _handle_operator_reply(
        self, group_id: int, operator, reply_to_message_id: int,
        reply_date: datetime, reply_telegram_id: int
    ):
        """
        Operator reply qilgandagi logika:
        1. Reply qilingan xabarni topish
        2. Usha xabar uchun ochilgan conversation ni topish
        3. Conversation ni answered deb belgilash
        4. Response time ni hisoblash
        """
        # Reply qilingan xabar bilan bog'langan conversation ni topish
        conv = await self.repo.find_unanswered_conversation_by_message(
            group_id=group_id,
            user_message_id=reply_to_message_id,
        )

        if conv:
            # Response time hisoblash
            response_time = (reply_date - conv.created_at).total_seconds()

            await self.repo.mark_conversation_answered(
                conversation_id=conv.id,
                operator_id=operator.id,
                operator_reply_id=reply_telegram_id,
                response_time=max(0, response_time),
                answered_at=reply_date,
            )

            # Agar operator hali belgilanmagan bo'lsa
            if not operator.is_operator:
                await self.repo.set_user_as_operator(operator.id)

    # =====================================================
    # COMMAND HANDLERS
    # =====================================================

    async def _handle_command(self, chat_id: int, text: str, user):
        """Group ichida bot commandlarni qayta ishlash"""
        command = text.split()[0].lower().split("@")[0]

        handlers = {
            "/stats": self._cmd_stats,
            "/today": self._cmd_today,
            "/week": self._cmd_week,
            "/month": self._cmd_month,
            "/operators": self._cmd_operators,
            "/unanswered": self._cmd_unanswered,
            "/help": self._cmd_help,
        }

        handler = handlers.get(command)
        if handler:
            response = await handler()
            await self.send_message(chat_id, response)

    async def _handle_private_command(self, message: Dict):
        """Private chatda commandlarni qayta ishlash"""
        text = message.get("text", "") or ""
        chat_id = message["chat"]["id"]

        if text.startswith("/start") or text.startswith("/help"):
            await self.send_message(chat_id, self._help_text())

    async def _cmd_stats(self) -> str:
        return await self.analytics.format_stats_for_bot()

    async def _cmd_today(self) -> str:
        return await self.analytics.format_stats_for_bot("today")

    async def _cmd_week(self) -> str:
        return await self.analytics.format_stats_for_bot("week")

    async def _cmd_month(self) -> str:
        return await self.analytics.format_stats_for_bot("month")

    async def _cmd_operators(self) -> str:
        return await self.analytics.format_operators_for_bot()

    async def _cmd_unanswered(self) -> str:
        return await self.analytics.format_unanswered_for_bot()

    async def _cmd_help(self) -> str:
        return self._help_text()

    @staticmethod
    def _help_text() -> str:
        return (
            "🤖 <b>Telegram Analytics Bot</b>\n\n"
            "Mavjud buyruqlar:\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "/stats — Umumiy statistika\n"
            "/today — Bugungi statistika\n"
            "/week — Haftalik statistika\n"
            "/month — Oylik statistika\n"
            "/operators — Operatorlar natijasi\n"
            "/unanswered — Javobsiz foydalanuvchilar\n"
            "/help — Yordam\n"
            "━━━━━━━━━━━━━━━━━━"
        )
