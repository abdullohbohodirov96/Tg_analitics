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
        """
        # 0. Bot guruhga qo'shilganda yoki huquqlari o'zgarganda
        if "my_chat_member" in update:
            await self._handle_my_chat_member(update["my_chat_member"])
            return

        message = update.get("message")
        if not message:
            return

        chat = message.get("chat", {})
        chat_type = chat.get("type", "")

        # Faqat group va supergroup xabarlarni qayta ishlash
        if chat_type not in ("group", "supergroup"):
            if chat_type == "private":
                await self._handle_private_command(message)
            return

        from_user = message.get("from", {})
        if not from_user or from_user.get("is_bot", False):
            return

        # Group va User ni saqlash
        username = from_user.get("username", "") or ""
        group = await self.repo.get_or_create_group(
            telegram_id=chat["id"],
            title=chat.get("title"),
        )
        user = await self.repo.get_or_create_user(
            telegram_id=from_user["id"],
            username=username,
            first_name=from_user.get("first_name"),
            last_name=from_user.get("last_name"),
        )

        # Topic ma'lumotlari
        topic_id = message.get("message_thread_id")
        topic_name = None
        if "forum_topic_created" in message:
            topic_name = message["forum_topic_created"].get("name")

        # Bot command tekshirish
        text = message.get("text", "") or ""
        if text.startswith("/"):
            await self._handle_command(chat["id"], text, user)
            return

        # Javob (Answer) logikasi
        reply_to = message.get("reply_to_message")
        answered_someone = False

        if reply_to:
            # 1. Kimgadir reply qilinganda (agar u boshqa odam bo'lsa)
            reply_to_user = reply_to.get("from", {})
            if reply_to_user and reply_to_user.get("id") != from_user.get("id"):
                # Boshqa odamga javob berildi
                # O'sha userning bu guruhdagi barcha javobsiz xabarlarini yopamiz
                target_user = await self.repo.get_user_by_telegram_id(reply_to_user["id"])
                if target_user:
                    await self.repo.mark_user_conversations_answered(
                        user_id=target_user.id,
                        group_id=group.id,
                        operator_id=user.id,
                        operator_reply_id=message["message_id"],
                        answered_at=datetime.utcfromtimestamp(message["date"]),
                    )
                    # Javob bergan odamni "operator" (staff) deb belgilab qo'yamiz
                    if not user.is_operator:
                        await self.repo.set_user_as_operator(user.id)
                    answered_someone = True

        # 2. Hech qanday replysiz xabar yozilganda (agar bu odam operator bo'lsa)
        if not answered_someone and user.is_operator:
            # Eng eski javobsiz suhbatni topib yopamiz
            oldest_conv = await self.repo.get_oldest_unanswered_conversation(group.id)
            if oldest_conv and oldest_conv.user_id != user.id:
                await self.repo.mark_user_conversations_answered(
                    user_id=oldest_conv.user_id,
                    group_id=group.id,
                    operator_id=user.id,
                    operator_reply_id=message["message_id"],
                    answered_at=datetime.utcfromtimestamp(message["date"]),
                )
                answered_someone = True

        # 3. Stateful Conversation Logic (Phase 7)
        if not user.is_operator and not answered_someone:
            # Root message bolsa conversation ochamiz
            if not reply_to:
                await self.repo.create_conversation(
                    group_id=group.id,
                    user_id=user.id,
                    user_message_id=message["message_id"],
                    topic_id=topic_id,
                    topic_name=topic_name
                )

        # Xabarni saqlash
        msg_date = datetime.utcfromtimestamp(message["date"])
        saved_msg = await self.repo.save_message(
            telegram_message_id=message["message_id"],
            group_id=group.id,
            user_id=user.id,
            text=text,
            date=msg_date,
            reply_to_message_id=reply_to.get("message_id") if reply_to else None,
            is_from_operator=user.is_operator or answered_someone,
        )

        # 3. SMART TASK DETECTION (Yaxshilangan tahlil)
        from app.services.task_classifier import TaskClassifier
        from app.repositories.task_repository import TaskRepository
        
        classifier = TaskClassifier()
        task_repo = TaskRepository(self.db)
        
        # A) Avtomatik aniqlash (User so'rovlari)
        is_task, normalized = classifier.classify(text)
        if is_task and not user.is_operator:
            # Takrorlanmasligi uchun tekshirish (ixtiyoriy, lekin maqsadga muvofiq)
            await task_repo.create_task(
                title=normalized,
                description=text,
                group_id=group.id,
                user_id=user.id,
                created_by_id=None,
                source_message_id=message["message_id"]
            )
            print(f"✅ Auto-task created: {normalized}")

        # B) Operator tasdig'i orqali (Affinmation)
        # "ok", "hop", "qilamiz", "bajaraman", "tashadim", "vazifaga qo'shdim"
        affirmation_keywords = ["ok", "hop", "qilamiz", "bajaraman", "tashadim", "vazifaga qo'shdim", "добавьте", "сделаем"]
        is_affirmation = any(kw in text.lower() for kw in affirmation_keywords) and user.is_operator
        
        if is_affirmation:
            # Qaysi userga javob beryapti?
            target_user_id = None
            if reply_to:
                rep_user_tg_id = reply_to.get("from", {}).get("id")
                rep_user = await self.repo.get_user_by_telegram_id(rep_user_tg_id)
                if rep_user:
                    target_user_id = rep_user.id
            
            # Oxirgi xabarni topish
            last_msg = await task_repo.find_last_user_message_in_group(group.id, target_user_id)
            if last_msg and last_msg.text:
                # Xabarni vazifa sifatida saqlash
                # (Agar u avtomatik tushmagan bo'lsa ham tushadi)
                alt_title = classifier.normalize_task_text(last_msg.text)
                await task_repo.create_task(
                    title=alt_title,
                    description=last_msg.text,
                    group_id=group.id,
                    user_id=last_msg.user_id,
                    created_by_id=user.id, # Operator yaratdi
                    source_message_id=last_msg.telegram_message_id
                )
                print(f"📌 Task created via affirmation: {alt_title}")

        # 4. Conversation ochish yoki davom ettirish
        if not answered_someone and not user.is_operator:
            # O'zi uchun yangi suhbat ochish (agar hali ochilmagan bo'lsa)
            unanswered_conv = await self.repo.find_unanswered_conversation_by_user(
                group_id=group.id,
                user_id=user.id
            )
            if not unanswered_conv:
                await self.repo.create_conversation(
                    group_id=group.id,
                    user_id=user.id,
                    user_message_id=message["message_id"],
                )


    async def _handle_my_chat_member(self, chat_member_update: Dict[str, Any]):
        """Bot guruhga qo'shilganda yoki huquqlari o'zgarganda guruhni ro'yxatdan o'tkazish"""
        chat = chat_member_update.get("chat", {})
        if chat.get("type") in ("group", "supergroup"):
            await self.repo.get_or_create_group(
                telegram_id=chat["id"],
                title=chat.get("title")
            )

    async def _handle_operator_reply(
        self, group_id: int, operator, reply_to_message_id: int,
        reply_date: datetime, reply_telegram_id: int
    ) -> bool:
        """
        Operator reply qilgandagi logika. 
        Javob berilganini tasdiqlasa True qaytaradi.
        """
        conv = await self.repo.find_unanswered_conversation_by_message(
            group_id=group_id,
            user_message_id=reply_to_message_id,
        )

        if conv:
            # Foydalanuvchining o'sha guruhdagi barcha javobsiz suhbatlarini yopamiz
            await self.repo.mark_user_conversations_answered(
                user_id=conv.user_id,
                group_id=group_id,
                operator_id=operator.id,
                operator_reply_id=reply_telegram_id,
                answered_at=reply_date,
            )
            return True
        return False

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
            "🤖 <b>Telegram Analytics & CRM Bot</b>\n\n"
            "Mavjud buyruqlar:\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "/stats — Umumiy statistika\n"
            "/today — Bugungi statistika\n"
            "/week — Haftalik statistika\n"
            "/month — Oylik statistika\n"
            "/operators — Operatorlar natijasi\n"
            "/unanswered — Javobsiz foydalanuvchilar\n"
            "/help — Yordam\n\n"
            "<b>CRM Yangiliklari:</b>\n"
            "✅ <b>Smart Tasks</b>: Bot xabarlardan vazifalarni aniqlaydi.\n"
            "✅ <b>Multi-Group</b>: Har bir guruh uchun alohida analiz.\n"
            "✅ <b>Conversation History</b>: Dashboardda to'liq tarix.\n"
            "━━━━━━━━━━━━━━━━━━"
        )
