"""
Analytics Service — Biznes logika qatlami.
Repository dan ma'lumotlarni olib, formatlangan natijalarni qaytaradi.
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.stats_repository import StatsRepository


class AnalyticsService:
    """Statistika hisoblash va formatlash xizmati"""

    def __init__(self, db: AsyncSession):
        self.repo = StatsRepository(db)

    # =====================================================
    # GROUPS
    # =====================================================

    async def get_groups(self) -> List[Dict]:
        """Tizimdagi barcha guruhlar ro'yxati"""
        return await self.repo.get_groups()

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
