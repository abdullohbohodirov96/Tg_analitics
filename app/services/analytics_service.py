"""
Analytics Service — Biznes logika qatlami.
Repository dan ma'lumotlarni olib, formatlangan natijalarni qaytaradi.
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.stats_repository import StatsRepository
from app.repositories.task_repository import TaskRepository
from app.models.models import Conversation, Message


class AnalyticsService:
    """Statistika hisoblash va formatlash xizmati"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = StatsRepository(db)
        self.task_repo = TaskRepository(db)

    # =====================================================
    # GROUPS
    # =====================================================

    async def get_groups(self) -> List[Dict]:
        """Tizimdagi barcha guruhlar ro'yxati"""
        return await self.repo.get_groups()

    async def update_group(self, group_id: int, custom_title: Optional[str] = None, group_link: Optional[str] = None) -> Optional[Dict]:
        """Guruh ma'lumotlarini yangilash"""
        group = await self.repo.update_group(group_id, custom_title, group_link)
        if group:
            return {
                "id": group.id,
                "telegram_id": group.telegram_id,
                "title": group.title,
                "custom_title": group.custom_title,
                "group_link": group.group_link
            }
        return None

    # =====================================================
    # OPERATORS
    # =====================================================

    async def get_all_operators(
        self, date_from: Optional[datetime] = None, date_to: Optional[datetime] = None, group_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Barcha operatorlar (aktiv va oldindan belgilangan)"""
        active = await self.repo.get_operator_stats(date_from, date_to, group_id=group_id)
        predefined = await self.repo.get_predefined_operators()
        return {
            "active": active,
            "predefined": predefined
        }

    async def add_predefined_operator(self, username: str) -> Dict:
        """Username orqali operator qo'shish"""
        op = await self.repo.add_predefined_operator(username)
        return {"id": op.id, "username": op.username}

    async def remove_predefined_operator(self, op_id: int):
        """Operatorni o'chirish"""
        return await self.repo.remove_predefined_operator(op_id)

    # =====================================================
    # DATE RANGE HELPERS
    # =====================================================

    @staticmethod
    def get_date_range(period: str) -> tuple:
        """
        Period nomi bo'yicha sana oralig'ini qaytarish.
        today, yesterday, week, month
        """
        now = datetime.utcnow()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

        if period == "today":
            return today_start, now
        elif period == "yesterday":
            yesterday = today_start - timedelta(days=1)
            return yesterday, today_start
        elif period == "week":
            week_ago = today_start - timedelta(days=7)
            return week_ago, now
        elif period == "month":
            month_ago = today_start - timedelta(days=30)
            return month_ago, now
        else:
            return None, None

    # =====================================================
    # OVERVIEW
    # =====================================================

    async def get_overview(
        self, date_from: Optional[datetime] = None, date_to: Optional[datetime] = None, group_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Umumiy ko'rsatkichlar"""
        return await self.repo.get_overview_stats(date_from, date_to, group_id=group_id)

    async def get_period_overview(self, period: str, group_id: Optional[int] = None) -> Dict[str, Any]:
        """Period bo'yicha umumiy ko'rsatkichlar"""
        date_from, date_to = self.get_date_range(period)
        return await self.repo.get_overview_stats(date_from, date_to, group_id=group_id)

    # =====================================================
    # CHARTS DATA
    # =====================================================

    async def get_daily_messages(
        self, date_from: Optional[datetime] = None, date_to: Optional[datetime] = None, group_id: Optional[int] = None
    ) -> List[Dict]:
        """Kunlik xabarlar grafigi uchun ma'lumot"""
        return await self.repo.get_daily_messages(date_from, date_to, group_id=group_id)

    async def get_response_time_trend(
        self, date_from: Optional[datetime] = None, date_to: Optional[datetime] = None, group_id: Optional[int] = None
    ) -> List[Dict]:
        """Javob vaqti trendi"""
        return await self.repo.get_response_time_trend(date_from, date_to, group_id=group_id)

    async def get_hourly_heatmap(
        self, date_from: Optional[datetime] = None, date_to: Optional[datetime] = None, group_id: Optional[int] = None
    ) -> List[Dict]:
        """Soatlik aktivlik heatmapi"""
        return await self.repo.get_hourly_heatmap(date_from, date_to, group_id=group_id)

    async def get_user_growth(
        self, date_from: Optional[datetime] = None, date_to: Optional[datetime] = None, group_id: Optional[int] = None
    ) -> List[Dict]:
        """Foydalanuvchilar o'sish grafigi"""
        return await self.repo.get_user_growth(date_from, date_to, group_id=group_id)

    # =====================================================
    # OPERATORS
    # =====================================================

    async def get_operators(
        self, date_from: Optional[datetime] = None, date_to: Optional[datetime] = None, group_id: Optional[int] = None
    ) -> List[Dict]:
        """Operatorlar ro'yxati va statistikasi"""
        operators = await self.repo.get_operator_stats(date_from, date_to, group_id=group_id)
        # Rank qo'shish
        for i, op in enumerate(operators, 1):
            op["rank"] = i
        return operators

    async def get_operator_detail(self, operator_id: int) -> Optional[Dict]:
        """Bitta operator haqida batafsil"""
        return await self.repo.get_operator_detail(operator_id)

    # =====================================================
    # USERS
    # =====================================================

    async def get_top_users(
        self, date_from: Optional[datetime] = None, date_to: Optional[datetime] = None, group_id: Optional[int] = None
    ) -> List[Dict]:
        """Eng faol foydalanuvchilar"""
        return await self.repo.get_top_users(date_from, date_to, group_id=group_id)

    async def get_user_detail(self, user_id: int) -> Optional[Dict]:
        """Bitta foydalanuvchi haqida batafsil"""
        return await self.repo.get_user_detail(user_id)

    # =====================================================
    # CONVERSATIONS
    # =====================================================

    async def get_unanswered(
        self, date_from: Optional[datetime] = None, date_to: Optional[datetime] = None, group_id: Optional[int] = None
    ) -> List[Dict]:
        """Javobsiz qolgan suhbatlar"""
        return await self.repo.get_unanswered_conversations(date_from, date_to, group_id=group_id)

    async def get_answered(
        self, date_from: Optional[datetime] = None, date_to: Optional[datetime] = None, group_id: Optional[int] = None
    ) -> List[Dict]:
        """Javob berilgan suhbatlar"""
        return await self.repo.get_answered_conversations(date_from, date_to, group_id=group_id)

    async def get_slow_responses(
        self, date_from: Optional[datetime] = None, date_to: Optional[datetime] = None, group_id: Optional[int] = None
    ) -> List[Dict]:
        """Sekin javob berilgan suhbatlar"""
        return await self.repo.get_slow_responses(date_from, date_to, group_id=group_id)

    # =====================================================
    # MESSAGES
    # =====================================================

    async def get_recent_messages(
        self, date_from: Optional[datetime] = None, date_to: Optional[datetime] = None, group_id: Optional[int] = None
    ) -> List[Dict]:
        """So'nggi xabarlar"""
        return await self.repo.get_recent_messages(
            date_from=date_from, date_to=date_to, group_id=group_id
        )

    # =====================================================
    # BOT UCHUN FORMATLANGAN NATIJALAR
    # =====================================================

    async def format_stats_for_bot(self, period: Optional[str] = None) -> str:
        """Telegram bot uchun formatlangan statistika"""
        date_from, date_to = (None, None)
        if period:
            date_from, date_to = self.get_date_range(period)

        stats = await self.repo.get_overview_stats(date_from, date_to)

        period_key = period or "total"
        period_name = {
            "today": "📅 Bugun",
            "yesterday": "📅 Kecha",
            "week": "📅 Oxirgi 7 kun",
            "month": "📅 Oxirgi 30 kun",
            "total": "📊 Umumiy",
        }.get(period_key, "📊 Umumiy")

        # Javob vaqtini formatlash
        rt = stats["avg_response_time"]
        if rt > 3600:
            rt_text = f"{rt / 3600:.1f} soat"
        elif rt > 60:
            rt_text = f"{rt / 60:.1f} daqiqa"
        else:
            rt_text = f"{rt:.0f} soniya"

        return (
            f"{period_name} statistika:\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"📨 Xabarlar: {stats['total_messages']}\n"
            f"👥 Foydalanuvchilar: {stats['unique_users']}\n"
            f"✅ Javob darajasi: {stats['response_rate']}%\n"
            f"⏱ O'rtacha javob: {rt_text}\n"
            f"❌ Javobsiz: {stats['unanswered_users']}\n"
            f"👨‍💼 Faol operatorlar: {stats['active_operators']}\n"
            f"━━━━━━━━━━━━━━━━━━"
        )

    async def format_operators_for_bot(self) -> str:
        """Operatorlar natijasi bot uchun"""
        operators = await self.repo.get_operator_stats()
        if not operators:
            return "👨‍💼 Hozircha operator statistikasi yo'q."

        text = "👨‍💼 Operatorlar natijasi:\n━━━━━━━━━━━━━━━━━━\n"
        for i, op in enumerate(operators, 1):
            rt = op["avg_response_time"]
            if rt > 3600:
                rt_text = f"{rt / 3600:.1f} soat"
            elif rt > 60:
                rt_text = f"{rt / 60:.1f} daq"
            else:
                rt_text = f"{rt:.0f} son"

            text += (
                f"\n{'🥇🥈🥉'[i-1] if i <= 3 else f'{i}.'} "
                f"{op['name']}\n"
                f"   💬 {op['total_replies']} javob | "
                f"⏱ {rt_text} | "
                f"👥 {op['answered_users']} user\n"
            )
        return text + "━━━━━━━━━━━━━━━━━━"

    async def format_unanswered_for_bot(self) -> str:
        """Javobsiz foydalanuvchilar ro'yxati bot uchun"""
        unanswered = await self.repo.get_unanswered_conversations(limit=20)
        if not unanswered:
            return "✅ Barcha foydalanuvchilarga javob berilgan!"

        text = "❌ Javobsiz foydalanuvchilar:\n━━━━━━━━━━━━━━━━━━\n"
        for conv in unanswered:
            waiting = conv["waiting_time"]
            if waiting > 3600:
                wait_text = f"{waiting / 3600:.1f} soat"
            elif waiting > 60:
                wait_text = f"{waiting / 60:.0f} daqiqa"
            else:
                wait_text = f"{waiting:.0f} soniya"

            name = conv["username"] or conv["name"]
            if conv["username"]:
                name = f"@{name}"
            text += f"• {name} — {wait_text} kutmoqda\n"

        return text + "━━━━━━━━━━━━━━━━━━"

    # =====================================================
    # CRM & TASKS (NEW)
    # =====================================================

    async def get_conversation_history(self, conversation_id: int) -> List[Dict]:
        """Suhbatning to'liq tarixi (user + operator xabarlari)"""
        from sqlalchemy import select
        from sqlalchemy.orm import joinedload
        
        # Suhbatni topamiz
        result = await self.db.execute(
            select(Conversation).options(joinedload(Conversation.group)).where(Conversation.id == conversation_id)
        )
        conv = result.scalar_one_or_none()
        if not conv:
            return []

        # Suhbat diapazonidagi xabarlarni olamiz
        end_time = conv.answered_at or datetime.utcnow()
        start_time = conv.created_at - timedelta(hours=1)
        
        query = select(Message).options(joinedload(Message.user)).where(
            Message.group_id == conv.group_id,
            Message.date >= start_time,
            Message.date <= end_time + timedelta(minutes=5)
        ).order_by(Message.date.asc())
        
        msg_result = await self.db.execute(query)
        messages = msg_result.scalars().all()
        
        return [
            {
                "id": m.id,
                "text": m.text,
                "date": m.date.isoformat(),
                "is_from_operator": m.is_from_operator,
                "user_name": m.user.full_name,
                "user_id": m.user_id,
                "telegram_message_id": m.telegram_message_id,
                "group_telegram_id": str(conv.group.telegram_id).replace("-100", "") if str(conv.group.telegram_id).startswith("-100") else conv.group.telegram_id
            } for m in messages
        ]

    async def get_tasks(self, group_id: Optional[int] = None, status: Optional[str] = None) -> List[Dict]:
        """Vazifalar ro'yxati"""
        try:
            tasks = await self.task_repo.get_tasks(group_id=group_id, status=status)
            result = []
            for t in tasks:
                try:
                    result.append({
                        "id": t.id,
                        "title": t.title or "Nomi yo'q",
                        "description": t.description or "",
                        "status": t.status or "new",
                        "priority": t.priority or "medium",
                        "user_name": (t.user.full_name if t.user else "Unknown"),
                        "group_title": (t.group.title if t.group else "Unknown"),
                        "operator_name": t.assigned_operator.full_name if (t.assigned_operator and t.assigned_operator.full_name) else None,
                        "created_at": t.created_at.isoformat() if t.created_at else datetime.utcnow().isoformat(),
                        "due_date": t.due_date.isoformat() if t.due_date else None
                    })
                except Exception as e:
                    print(f"Error processing task {t.id}: {e}")
                    continue
            return result
        except Exception as e:
            print(f"Error in get_tasks: {e}")
            return []

    async def get_history_feed(self, date_from, date_to, group_id: Optional[int] = None):
        """Barcha harakatlar tarixi"""
        try:
            feed = await self.repo.get_history_feed(date_from, date_to, group_id=group_id)
            if not feed:
                return []
            # Validate each item
            validated = []
            for item in feed:
                try:
                    validated.append({
                        "id": item.get("id", 0),
                        "title": item.get("title", "No title"),
                        "date": item.get("event_date") or item.get("date", datetime.utcnow().isoformat()),
                        "type": item.get("type", "unknown"),
                        "user_name": item.get("user_name", "Unknown"),
                        "group_title": item.get("group_title", "Unknown"),
                    })
                except Exception as e:
                    print(f"Error processing history item: {e}")
                    continue
            return validated
        except Exception as e:
            print(f"Error in get_history_feed: {e}")
            return []

    async def create_task(self, data: Dict[str, Any], created_by_id: int) -> Dict:
        """Yangi vazifa yaratish"""
        task = await self.task_repo.create_task(
            title=data["title"],
            description=data.get("description", ""),
            group_id=data["group_id"],
            user_id=data["user_id"],
            conversation_id=data.get("conversation_id"),
            created_by_id=created_by_id,
            priority=data.get("priority", "medium"),
            due_date=datetime.fromisoformat(data["due_date"]) if data.get("due_date") else None
        )
        return {"id": task.id, "status": "ok"}

    async def update_task(self, task_id: int, **kwargs) -> bool:
        """Vazifani tahrirlash"""
        task = await self.task_repo.update_task(task_id, **kwargs)
        return task is not None
