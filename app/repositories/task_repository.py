"""
Task Repository — Vazifalar bilan ishlash uchun DB query lari.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import select, func, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.models import Task, User, Group, Conversation


class TaskRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_task(
        self, title: str, description: str, group_id: int, user_id: int,
        created_by_id: int, conversation_id: Optional[int] = None,
        priority: str = "medium", due_date: Optional[datetime] = None
    ) -> Task:
        """Yangi vazifa yaratish"""
        task = Task(
            title=title,
            description=description,
            group_id=group_id,
            user_id=user_id,
            conversation_id=conversation_id,
            created_by_id=created_by_id,
            priority=priority,
            due_date=due_date,
            status="new"
        )
        self.db.add(task)
        await self.db.flush()
        return task

    async def get_tasks(
        self, group_id: Optional[int] = None, status: Optional[str] = None,
        limit: int = 50
    ) -> List[Task]:
        """Vazifalar ro'yxatini olish"""
        query = select(Task).options(
            joinedload(Task.user),
            joinedload(Task.group),
            joinedload(Task.assigned_operator)
        ).order_by(desc(Task.created_at))

        if group_id:
            query = query.where(Task.group_id == group_id)
        if status:
            query = query.where(Task.status == status)
            
        result = await self.db.execute(query.limit(limit))
        return result.scalars().all()

    async def get_task_by_id(self, task_id: int) -> Optional[Task]:
        """ID bo'yicha vazifani topish"""
        result = await self.db.execute(
            select(Task).options(
                joinedload(Task.user),
                joinedload(Task.group),
                joinedload(Task.assigned_operator),
                joinedload(Task.creator)
            ).where(Task.id == task_id)
        )
        return result.scalar_one_or_none()

    async def update_task(self, task_id: int, **kwargs) -> Optional[Task]:
        """Vazifani yangilash"""
        task = await self.get_task_by_id(task_id)
        if not task:
            return None
            
        for key, value in kwargs.items():
            if hasattr(task, key):
                setattr(task, key, value)
        
        if kwargs.get("status") == "done" and not task.completed_at:
            task.completed_at = datetime.utcnow()
            
        await self.db.flush()
        return task
