"""
Repository Layer — Database query lari.
Barcha SQL/ORM query lar shu yerda yoziladi.
Service layer faqat shu repository orqali DB ga murojaat qiladi.
"""

from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy import select, func, case, and_, extract, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.models import Group, User, Message, Conversation, AdminUser


class StatsRepository:
    """Statistika uchun barcha DB query lari"""

    def __init__(self, db: AsyncSession):
        self.db = db

    # =====================================================
    # GROUP OPERATIONS
    # =====================================================

    async def get_or_create_group(self, telegram_id: int, title: Optional[str] = None) -> Group:
        """Guruhni topish yoki yaratish"""
        result = await self.db.execute(
            select(Group).where(Group.telegram_id == telegram_id)
        )
        group = result.scalar_one_or_none()
        if not group:
            group = Group(telegram_id=telegram_id, title=title)
            self.db.add(group)
            await self.db.flush()
        elif title and group.title != title:
            group.title = title
        return group

    # =====================================================
    # GROUP LIST
    # =====================================================

    async def get_groups(self) -> List[Dict]:
        """Barcha guruhlarni ro'yxati"""
        result = await self.db.execute(select(Group).order_by(Group.title))
        groups = result.scalars().all()
        return [{"id": g.id, "telegram_id": g.telegram_id, "title": g.title} for g in groups]

    # =====================================================
    # USER OPERATIONS
    # =====================================================

    async def get_or_create_user(
        self, telegram_id: int, username: Optional[str] = None,
        first_name: Optional[str] = None, last_name: Optional[str] = None
    ) -> User:
        """Foydalanuvchini topish yoki yaratish"""
        result = await self.db.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        user = result.scalar_one_or_none()
        if not user:
            user = User(
                telegram_id=telegram_id,
                username=username,
                first_name=first_name,
                last_name=last_name,
            )
            self.db.add(user)
            await self.db.flush()
        else:
            # Ma'lumotlarni yangilash
            if username:
                user.username = username
            if first_name:
                user.first_name = first_name
            if last_name:
                user.last_name = last_name
            user.last_seen = datetime.utcnow()
        return user

    async def set_user_as_operator(self, user_id: int):
        """Foydalanuvchini operator sifatida belgilash"""
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        if user:
            user.is_operator = True

    async def get_operators(self) -> List[User]:
        """Barcha operatorlarni olish"""
        result = await self.db.execute(
            select(User).where(User.is_operator == True)
        )
        return result.scalars().all()

    # =====================================================
    # MESSAGE OPERATIONS
    # =====================================================

    async def save_message(
        self, telegram_message_id: int, group_id: int, user_id: int,
        text: str, date: datetime, reply_to_message_id: Optional[int] = None,
        is_from_operator: bool = False
    ) -> Message:
        """Xabarni saqlash"""
        msg = Message(
            telegram_message_id=telegram_message_id,
            group_id=group_id,
            user_id=user_id,
            text=text,
            date=date,
            reply_to_message_id=reply_to_message_id,
            is_from_operator=is_from_operator,
        )
        self.db.add(msg)
        await self.db.flush()
        return msg

    async def find_message_by_telegram_id(
        self, group_id: int, telegram_message_id: int
    ) -> Optional[Message]:
        """Telegram message ID bo'yicha xabar topish"""
        result = await self.db.execute(
            select(Message).where(
                and_(
                    Message.group_id == group_id,
                    Message.telegram_message_id == telegram_message_id,
                )
            )
        )
        return result.scalar_one_or_none()

    # =====================================================
    # CONVERSATION OPERATIONS
    # =====================================================

    async def create_conversation(
        self, group_id: int, user_id: int, user_message_id: int
    ) -> Conversation:
        """Yangi suhbat yaratish (user xabar yozganda)"""
        conv = Conversation(
            group_id=group_id,
            user_id=user_id,
            user_message_id=user_message_id,
        )
        self.db.add(conv)
        await self.db.flush()
        return conv

    async def mark_conversation_answered(
        self, conversation_id: int, operator_id: int,
        operator_reply_id: int, response_time: float, answered_at: datetime
    ):
        """Suhbatni javob berilgan deb belgilash"""
        result = await self.db.execute(
            select(Conversation).where(Conversation.id == conversation_id)
        )
        conv = result.scalar_one_or_none()
        if conv:
            conv.is_answered = True
            conv.operator_id = operator_id
            conv.operator_reply_id = operator_reply_id
            conv.response_time_seconds = response_time
            conv.answered_at = answered_at

    async def find_unanswered_conversation_by_message(
        self, group_id: int, user_message_id: int
    ) -> Optional[Conversation]:
        """User message ID bo'yicha javobsiz suhbatni topish"""
        result = await self.db.execute(
            select(Conversation).where(
                and_(
                    Conversation.group_id == group_id,
                    Conversation.user_message_id == user_message_id,
                    Conversation.is_answered == False,
                )
            )
        )
        return result.scalar_one_or_none()

    async def find_unanswered_conversation_by_user(
        self, group_id: int, user_id: int
    ) -> Optional[Conversation]:
        """Ayni foydalanuvchining guruhdagi javobsiz qolgan suhbatini topish"""
        result = await self.db.execute(
            select(Conversation).where(
                and_(
                    Conversation.group_id == group_id,
                    Conversation.user_id == user_id,
                    Conversation.is_answered == False,
                )
            ).order_by(Conversation.created_at.desc())
        )
        return result.scalars().first()

    # =====================================================
    # STATISTICS QUERIES
    # =====================================================

    async def get_overview_stats(
        self, date_from: Optional[datetime] = None, date_to: Optional[datetime] = None, group_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Umumiy statistika"""
        filters = self._date_filters(Message.date, date_from, date_to, group_id=group_id, model=Message)
        conv_filters = self._date_filters(Conversation.created_at, date_from, date_to, group_id=group_id, model=Conversation)

        # Jami xabarlar soni
        total_msg = await self.db.execute(
            select(func.count(Message.id)).where(*filters)
        )
        total_messages = total_msg.scalar() or 0

        # Unique foydalanuvchilar
        unique_q = await self.db.execute(
            select(func.count(func.distinct(Message.user_id))).where(*filters)
        )
        unique_users = unique_q.scalar() or 0

        # Javob berilgan suhbatlar
        answered_q = await self.db.execute(
            select(func.count(Conversation.id)).where(
                Conversation.is_answered == True, *conv_filters
            )
        )
        answered = answered_q.scalar() or 0

        # Jami suhbatlar
        total_conv_q = await self.db.execute(
            select(func.count(Conversation.id)).where(*conv_filters)
        )
        total_conv = total_conv_q.scalar() or 0

        # O'rtacha javob vaqti
        avg_rt_q = await self.db.execute(
            select(func.avg(Conversation.response_time_seconds)).where(
                Conversation.is_answered == True, *conv_filters
            )
        )
        avg_response_time = avg_rt_q.scalar() or 0

        # Javobsiz foydalanuvchilar
        unanswered_q = await self.db.execute(
            select(func.count(func.distinct(Conversation.user_id))).where(
                Conversation.is_answered == False, *conv_filters
            )
        )
        unanswered_users = unanswered_q.scalar() or 0

        # Faol operatorlar
        active_ops = await self.db.execute(
            select(func.count(func.distinct(Message.user_id))).where(
                Message.is_from_operator == True, *filters
            )
        )
        active_operators = active_ops.scalar() or 0

        # Response rate
        response_rate = (answered / total_conv * 100) if total_conv > 0 else 0

        return {
            "total_messages": total_messages,
            "unique_users": unique_users,
            "response_rate": round(response_rate, 1),
            "avg_response_time": round(avg_response_time, 1),
            "unanswered_users": unanswered_users,
            "active_operators": active_operators,
            "total_conversations": total_conv,
            "answered_conversations": answered,
        }

    async def get_daily_messages(
        self, date_from: Optional[datetime] = None, date_to: Optional[datetime] = None, group_id: Optional[int] = None
    ) -> List[Dict]:
        """Kunlik xabar soni"""
        filters = self._date_filters(Message.date, date_from, date_to, group_id=group_id, model=Message)
        result = await self.db.execute(
            select(
                func.date(Message.date).label("day"),
                func.count(Message.id).label("count"),
            )
            .where(*filters)
            .group_by(func.date(Message.date))
            .order_by(func.date(Message.date))
        )
        return [{"date": row.day.isoformat(), "count": row.count} for row in result]

    async def get_hourly_heatmap(
        self, date_from: Optional[datetime] = None, date_to: Optional[datetime] = None, group_id: Optional[int] = None
    ) -> List[Dict]:
        """Soatlik heatmap (qaysi soatda ko'p xabar keladi)"""
        filters = self._date_filters(Message.date, date_from, date_to, group_id=group_id, model=Message)
        result = await self.db.execute(
            select(
                extract("dow", Message.date).label("day_of_week"),
                extract("hour", Message.date).label("hour"),
                func.count(Message.id).label("count"),
            )
            .where(*filters)
            .group_by("day_of_week", "hour")
            .order_by("day_of_week", "hour")
        )
        return [
            {"day": int(row.day_of_week), "hour": int(row.hour), "count": row.count}
            for row in result
        ]

    async def get_operator_stats(
        self, date_from: Optional[datetime] = None, date_to: Optional[datetime] = None, group_id: Optional[int] = None
    ) -> List[Dict]:
        """Operatorlar statistikasi"""
        conv_filters = self._date_filters(Conversation.created_at, date_from, date_to, group_id=group_id, model=Conversation)

        result = await self.db.execute(
            select(
                User.id,
                User.telegram_id,
                User.username,
                User.first_name,
                User.last_name,
                func.count(Conversation.id).label("total_replies"),
                func.avg(Conversation.response_time_seconds).label("avg_response_time"),
                func.count(func.distinct(Conversation.user_id)).label("answered_users"),
            )
            .join(Conversation, Conversation.operator_id == User.id)
            .where(Conversation.is_answered == True, *conv_filters)
            .group_by(User.id)
            .order_by(func.count(Conversation.id).desc())
        )
        operators = []
        for row in result:
            name = row.first_name or ""
            if row.last_name:
                name += f" {row.last_name}"
            operators.append({
                "id": row.id,
                "telegram_id": row.telegram_id,
                "username": row.username,
                "name": name.strip() or "Unknown",
                "total_replies": row.total_replies,
                "avg_response_time": round(row.avg_response_time or 0, 1),
                "answered_users": row.answered_users,
            })
        return operators

    async def get_unanswered_conversations(
        self, date_from: Optional[datetime] = None, date_to: Optional[datetime] = None,
        limit: int = 50, group_id: Optional[int] = None
    ) -> List[Dict]:
        """Javobsiz qolgan suhbatlar to'liq ma'lumoti"""
        conv_filters = self._date_filters(Conversation.created_at, date_from, date_to, group_id=group_id, model=Conversation)
        
        # Subquery orqali textni olish (eng oson usul) - xavfsiz va samarali
        result = await self.db.execute(
            select(
                Conversation.id,
                Conversation.created_at,
                Conversation.user_message_id,
                User.telegram_id,
                User.username,
                User.first_name,
                User.last_name,
                Group.telegram_id.label("group_telegram_id"),
                Group.title.label("group_title"),
                Message.text.label("message_text")
            )
            .join(User, Conversation.user_id == User.id)
            .join(Group, Conversation.group_id == Group.id)
            .outerjoin(Message, and_(Message.telegram_message_id == Conversation.user_message_id, Message.group_id == Conversation.group_id))
            .where(Conversation.is_answered == False, *conv_filters)
            .order_by(Conversation.created_at.desc())
            .limit(limit)
        )
        convs = []
        for row in result:
            name = row.first_name or ""
            if row.last_name:
                name += f" {row.last_name}"
            convs.append({
                "id": row.id,
                "user_telegram_id": row.telegram_id,
                "username": row.username,
                "name": name.strip() or "Unknown",
                "message_id": row.user_message_id,
                "group_telegram_id": str(row.group_telegram_id).replace("-100", "") if str(row.group_telegram_id).startswith("-100") else row.group_telegram_id,
                "group_title": row.group_title,
                "message_text": (row.message_text or "")[:200],
                "created_at": row.created_at.isoformat(),
                "waiting_time": (datetime.utcnow() - row.created_at).total_seconds(),
            })
        return convs

    async def get_answered_conversations(
        self, date_from: Optional[datetime] = None, date_to: Optional[datetime] = None,
        limit: int = 50, group_id: Optional[int] = None
    ) -> List[Dict]:
        """Javob berilgan suhbatlar to'liq ma'lumoti"""
        conv_filters = self._date_filters(Conversation.created_at, date_from, date_to, group_id=group_id, model=Conversation)
        
        result = await self.db.execute(
            select(
                Conversation.id,
                Conversation.created_at,
                Conversation.answered_at,
                Conversation.user_message_id,
                Conversation.response_time_seconds,
                User.telegram_id,
                User.username,
                User.first_name,
                User.last_name,
                Group.telegram_id.label("group_telegram_id"),
                Group.title.label("group_title"),
                Message.text.label("message_text")
            )
            .join(User, Conversation.user_id == User.id)
            .join(Group, Conversation.group_id == Group.id)
            .outerjoin(Message, and_(Message.telegram_message_id == Conversation.user_message_id, Message.group_id == Conversation.group_id))
            .where(Conversation.is_answered == True, *conv_filters)
            .order_by(Conversation.answered_at.desc())
            .limit(limit)
        )
        convs = []
        for row in result:
            name = row.first_name or ""
            if row.last_name:
                name += f" {row.last_name}"
            convs.append({
                "id": row.id,
                "user_telegram_id": row.telegram_id,
                "username": row.username,
                "name": name.strip() or "Unknown",
                "message_id": row.user_message_id,
                "group_telegram_id": str(row.group_telegram_id).replace("-100", "") if str(row.group_telegram_id).startswith("-100") else row.group_telegram_id,
                "group_title": row.group_title,
                "message_text": (row.message_text or "")[:200],
                "created_at": row.created_at.isoformat(),
                "answered_at": row.answered_at.isoformat() if row.answered_at else None,
                "response_time": round(row.response_time_seconds or 0, 1)
            })
        return convs

    async def get_top_users(
        self, date_from: Optional[datetime] = None, date_to: Optional[datetime] = None,
        limit: int = 20, group_id: Optional[int] = None
    ) -> List[Dict]:
        """Eng faol foydalanuvchilar"""
        filters = self._date_filters(Message.date, date_from, date_to, group_id=group_id, model=Message)
        result = await self.db.execute(
            select(
                User.id,
                User.telegram_id,
                User.username,
                User.first_name,
                User.last_name,
                User.first_seen,
                User.last_seen,
                func.count(Message.id).label("message_count"),
            )
            .join(Message, Message.user_id == User.id)
            .where(Message.is_from_operator == False, *filters)
            .group_by(User.id)
            .order_by(func.count(Message.id).desc())
            .limit(limit)
        )
        users = []
        for row in result:
            name = row.first_name or ""
            if row.last_name:
                name += f" {row.last_name}"
            users.append({
                "id": row.id,
                "telegram_id": row.telegram_id,
                "username": row.username,
                "name": name.strip() or "Unknown",
                "message_count": row.message_count,
                "first_seen": row.first_seen.isoformat() if row.first_seen else None,
                "last_seen": row.last_seen.isoformat() if row.last_seen else None,
            })
        return users

    async def get_recent_messages(
        self, limit: int = 50,
        date_from: Optional[datetime] = None, date_to: Optional[datetime] = None, group_id: Optional[int] = None
    ) -> List[Dict]:
        """So'nggi xabarlar"""
        filters = self._date_filters(Message.date, date_from, date_to, group_id=group_id, model=Message)
        result = await self.db.execute(
            select(
                Message.id,
                Message.telegram_message_id,
                Message.text,
                Message.date,
                Message.is_from_operator,
                Message.reply_to_message_id,
                User.username,
                User.first_name,
                User.last_name,
                User.is_operator,
            )
            .join(User, Message.user_id == User.id)
            .where(*filters)
            .order_by(Message.date.desc())
            .limit(limit)
        )
        messages = []
        for row in result:
            name = row.first_name or ""
            if row.last_name:
                name += f" {row.last_name}"
            messages.append({
                "id": row.id,
                "telegram_message_id": row.telegram_message_id,
                "text": (row.text or "")[:200],
                "date": row.date.isoformat(),
                "is_from_operator": row.is_from_operator,
                "is_reply": row.reply_to_message_id is not None,
                "username": row.username,
                "name": name.strip() or "Unknown",
            })
        return messages

    async def get_response_time_trend(
        self, date_from: Optional[datetime] = None, date_to: Optional[datetime] = None, group_id: Optional[int] = None
    ) -> List[Dict]:
        """Kunlik o'rtacha javob vaqti trendi"""
        conv_filters = self._date_filters(Conversation.created_at, date_from, date_to, group_id=group_id, model=Conversation)
        result = await self.db.execute(
            select(
                func.date_trunc("day", Conversation.created_at).label("day"),
                func.avg(Conversation.response_time_seconds).label("avg_time"),
                func.count(Conversation.id).label("count"),
            )
            .where(Conversation.is_answered == True, *conv_filters)
            .group_by("day")
            .order_by("day")
        )
        return [
            {
                "date": str(row.day.date()),
                "avg_response_time": round(row.avg_time or 0, 1),
                "count": row.count,
            }
            for row in result
        ]

    async def get_user_growth(
        self, date_from: Optional[datetime] = None, date_to: Optional[datetime] = None, group_id: Optional[int] = None
    ) -> List[Dict]:
        """Kunlik yangi foydalanuvchilar soni"""
        filters = self._date_filters(User.first_seen, date_from, date_to)
        if group_id:
            # Only users who messaged in this group
            user_ids_subq = select(Message.user_id).where(Message.group_id == group_id).distinct()
            filters.append(User.id.in_(user_ids_subq))

        result = await self.db.execute(
            select(
                func.date_trunc("day", User.first_seen).label("day"),
                func.count(User.id).label("count"),
            )
            .where(User.is_operator == False, *filters)
            .group_by("day")
            .order_by("day")
        )
        return [
            {"date": str(row.day.date()), "count": row.count}
            for row in result
        ]

    async def get_slow_responses(
        self, date_from: Optional[datetime] = None, date_to: Optional[datetime] = None,
        limit: int = 20, group_id: Optional[int] = None
    ) -> List[Dict]:
        """Eng sekin javob berilgan suhbatlar"""
        conv_filters = self._date_filters(Conversation.created_at, date_from, date_to, group_id=group_id, model=Conversation)
        result = await self.db.execute(
            select(Conversation, User)
            .join(User, Conversation.user_id == User.id)
            .where(Conversation.is_answered == True, *conv_filters)
            .order_by(Conversation.response_time_seconds.desc())
            .limit(limit)
        )
        convs = []
        for row in result:
            conv = row[0]
            user = row[1]
            name = user.first_name or ""
            if user.last_name:
                name += f" {user.last_name}"
            convs.append({
                "id": conv.id,
                "username": user.username,
                "name": name.strip() or "Unknown",
                "response_time": round(conv.response_time_seconds or 0, 1),
                "created_at": conv.created_at.isoformat(),
            })
        return convs

    async def get_user_detail(self, user_id: int) -> Optional[Dict]:
        """Bitta foydalanuvchi haqida to'liq ma'lumot"""
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        if not user:
            return None

        # Message count
        msg_count = await self.db.execute(
            select(func.count(Message.id)).where(Message.user_id == user_id)
        )
        messages = msg_count.scalar() or 0

        # Conversation stats
        conv_q = await self.db.execute(
            select(
                func.count(Conversation.id).label("total"),
                func.sum(case((Conversation.is_answered == True, 1), else_=0)).label("answered"),
            ).where(Conversation.user_id == user_id)
        )
        conv_row = conv_q.one()

        # Assigned operator
        op_q = await self.db.execute(
            select(User)
            .join(Conversation, Conversation.operator_id == User.id)
            .where(Conversation.user_id == user_id)
            .order_by(Conversation.created_at.desc())
            .limit(1)
        )
        operator = op_q.scalar_one_or_none()

        return {
            "id": user.id,
            "telegram_id": user.telegram_id,
            "username": user.username,
            "name": user.full_name,
            "first_seen": user.first_seen.isoformat() if user.first_seen else None,
            "last_seen": user.last_seen.isoformat() if user.last_seen else None,
            "message_count": messages,
            "total_conversations": conv_row.total or 0,
            "answered_conversations": conv_row.answered or 0,
            "is_answered": (conv_row.answered or 0) >= (conv_row.total or 1),
            "operator": {
                "id": operator.id,
                "name": operator.full_name,
                "username": operator.username,
            } if operator else None,
        }

    async def get_operator_detail(self, operator_id: int) -> Optional[Dict]:
        """Bitta operator haqida to'liq ma'lumot"""
        result = await self.db.execute(
            select(User).where(User.id == operator_id, User.is_operator == True)
        )
        user = result.scalar_one_or_none()
        if not user:
            return None

        # Stats
        stats_q = await self.db.execute(
            select(
                func.count(Conversation.id).label("total_replies"),
                func.avg(Conversation.response_time_seconds).label("avg_response_time"),
                func.count(func.distinct(Conversation.user_id)).label("answered_users"),
            )
            .where(
                Conversation.operator_id == operator_id,
                Conversation.is_answered == True,
            )
        )
        stats = stats_q.one()

        # Unanswered count (users who messaged in groups where this operator works)
        # Simplified: just count unanswered in system
        unanswered_q = await self.db.execute(
            select(func.count(Conversation.id)).where(
                Conversation.is_answered == False
            )
        )
        unanswered = unanswered_q.scalar() or 0

        return {
            "id": user.id,
            "telegram_id": user.telegram_id,
            "username": user.username,
            "name": user.full_name,
            "total_replies": stats.total_replies or 0,
            "avg_response_time": round(stats.avg_response_time or 0, 1),
            "answered_users": stats.answered_users or 0,
            "unanswered_chats": unanswered,
        }

    # =====================================================
    # ADMIN OPERATIONS
    # =====================================================

    async def get_admin_by_username(self, username: str) -> Optional[AdminUser]:
        """Admin foydalanuvchini username bo'yicha topish"""
        result = await self.db.execute(
            select(AdminUser).where(AdminUser.username == username)
        )
        return result.scalar_one_or_none()

    async def create_admin(self, username: str, password_hash: str) -> AdminUser:
        """Yangi admin yaratish"""
        admin = AdminUser(username=username, password_hash=password_hash)
        self.db.add(admin)
        await self.db.flush()
        return admin

    # =====================================================
    # HELPERS
    # =====================================================

    def _date_filters(
        self, column, date_from: Optional[datetime] = None, date_to: Optional[datetime] = None, 
        group_id: Optional[int] = None, model = None
    ) -> list:
        """Date va guruh filter shartlari yaratish"""
        filters = []
        if date_from:
            filters.append(column >= date_from)
        if date_to:
            filters.append(column <= date_to)
        if group_id and model:
            # Check if model has group_id attribute
            if hasattr(model, 'group_id'):
                filters.append(model.group_id == group_id)
        return filters
