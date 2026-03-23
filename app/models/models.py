"""
Database modellari (ORM).
Barcha jadvallar shu yerda aniqlangan.

Asosiy jadvallar:
- Group: Telegram guruhlar
- User: Foydalanuvchilar (operator yoki oddiy user)
- Message: Xabarlar
- Conversation: Suhbatlar (user xabari + operator javobi)
- AdminUser: Dashboard admin foydalanuvchilari
"""

from datetime import datetime
from sqlalchemy import (
    Column, Integer, BigInteger, String, Text, Boolean,
    DateTime, Float, ForeignKey, Index
)
from sqlalchemy.orm import relationship

from app.database import Base


class Group(Base):
    """Telegram guruhlar jadvali"""
    __tablename__ = "groups"

    id = Column(Integer, primary_key=True, autoincrement=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False, index=True)
    title = Column(String(255), nullable=True)
    custom_title = Column(String(255), nullable=True)
    group_link = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    messages = relationship("Message", back_populates="group")
    conversations = relationship("Conversation", back_populates="group")

    def __repr__(self):
        return f"<Group(id={self.id}, title={self.title})>"


class User(Base):
    """
    Telegram foydalanuvchilar jadvali.
    is_operator: True bo'lsa, bu user operator (admin/support) hisoblanadi
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False, index=True)
    username = Column(String(255), nullable=True)
    first_name = Column(String(255), nullable=True)
    last_name = Column(String(255), nullable=True)
    is_operator = Column(Boolean, default=False, index=True)
    first_seen = Column(DateTime, default=datetime.utcnow)
    last_seen = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    messages = relationship("Message", back_populates="user")
    conversations_as_user = relationship(
        "Conversation", back_populates="user",
        foreign_keys="Conversation.user_id"
    )
    conversations_as_operator = relationship(
        "Conversation", back_populates="operator",
        foreign_keys="Conversation.operator_id"
    )

    @property
    def full_name(self) -> str:
        """To'liq ism"""
        parts = [self.first_name or "", self.last_name or ""]
        return " ".join(p for p in parts if p).strip() or "Unknown"

    @property
    def display_name(self) -> str:
        """Ko'rsatiladigan ism (@username yoki to'liq ism)"""
        if self.username:
            return f"@{self.username}"
        return self.full_name

    def __repr__(self):
        return f"<User(id={self.id}, username={self.username})>"


class Message(Base):
    """
    Telegram xabarlar jadvali.
    Har bir guruhga kelgan xabar shu yerda saqlanadi.
    reply_to_message_id: Agar bu xabar boshqa xabarga javob bo'lsa
    """
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    telegram_message_id = Column(BigInteger, nullable=False)
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    text = Column(Text, nullable=True)
    date = Column(DateTime, nullable=False, index=True)
    reply_to_message_id = Column(BigInteger, nullable=True)
    is_from_operator = Column(Boolean, default=False, index=True)

    # Relationships
    group = relationship("Group", back_populates="messages")
    user = relationship("User", back_populates="messages")

    # Composite index — tez qidiruv uchun
    __table_args__ = (
        Index("idx_msg_group_date", "group_id", "date"),
        Index("idx_msg_group_telegram", "group_id", "telegram_message_id"),
    )

    def __repr__(self):
        return f"<Message(id={self.id}, user_id={self.user_id})>"


class Conversation(Base):
    """
    Suhbat jadvali.
    User xabar yozganda conversation ochiladi.
    Operator reply qilganda is_answered=True bo'ladi va response_time hisoblanadi.

    response_time_seconds: User xabari va operator javobining vaqt farqi (sekundlarda)
    """
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    operator_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    user_message_id = Column(BigInteger, nullable=False)
    operator_reply_id = Column(BigInteger, nullable=True)
    response_time_seconds = Column(Float, nullable=True)
    is_answered = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    answered_at = Column(DateTime, nullable=True)

    # Relationships
    group = relationship("Group", back_populates="conversations")
    user = relationship("User", back_populates="conversations_as_user", foreign_keys=[user_id])
    operator = relationship("User", back_populates="conversations_as_operator", foreign_keys=[operator_id])

    def __repr__(self):
        return f"<Conversation(id={self.id}, answered={self.is_answered})>"


class PredefinedOperator(Base):
    """Oldindan belgilangan operatorlar (username orqali)"""
    __tablename__ = "predefined_operators"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(255), unique=True, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<PredefinedOperator(username={self.username})>"


class AdminUser(Base):
    """Dashboard admin foydalanuvchilari"""
    __tablename__ = "admin_users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<AdminUser(id={self.id}, username={self.username})>"
