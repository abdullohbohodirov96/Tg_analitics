"""
Stats Router — Dashboard uchun barcha analytics endpointlar.
Barcha endpointlar JWT token bilan himoyalangan.
Date filter lar: date_from, date_to query parametrlari.
"""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.analytics_service import AnalyticsService
from app.utils.security import get_current_admin

router = APIRouter(prefix="/api/stats", tags=["Statistics"])


def parse_date(date_str: Optional[str]) -> Optional[datetime]:
    """Date stringini datetime ga aylantirish"""
    if not date_str:
        return None
    try:
        return datetime.fromisoformat(date_str)
    except ValueError:
        try:
            return datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            return None

@router.get("/groups")
async def get_groups(
    db: AsyncSession = Depends(get_db),
    _admin: dict = Depends(get_current_admin),
):
    """Tizimdagi barcha guruhlar ro'yxati"""
    service = AnalyticsService(db)
    return await service.get_groups()


# =====================================================
# OVERVIEW ENDPOINTS
# =====================================================

@router.get("/overview")
async def get_overview(
    date_from: Optional[str] = Query(None, description="Boshlanish sanasi (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="Tugash sanasi (YYYY-MM-DD)"),
    group_id: Optional[int] = Query(None, description="Guruh ID (ixtiyoriy)"),
    db: AsyncSession = Depends(get_db),
    _admin: dict = Depends(get_current_admin),
):
    """
    Umumiy statistika.
    Total messages, unique users, response rate,
    average response time, unanswered users, active operators.
    """
    service = AnalyticsService(db)
    return await service.get_overview(parse_date(date_from), parse_date(date_to), group_id=group_id)


@router.get("/today")
async def get_today(
    group_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
    _admin: dict = Depends(get_current_admin),
):
    """Bugungi statistika"""
    service = AnalyticsService(db)
    return await service.get_period_overview("today", group_id=group_id)


@router.get("/week")
async def get_week(
    group_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
    _admin: dict = Depends(get_current_admin),
):
    """Haftalik statistika"""
    service = AnalyticsService(db)
    return await service.get_period_overview("week", group_id=group_id)


@router.get("/month")
async def get_month(
    group_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
    _admin: dict = Depends(get_current_admin),
):
    """Oylik statistika"""
    service = AnalyticsService(db)
    return await service.get_period_overview("month", group_id=group_id)


# =====================================================
# CHARTS DATA
# =====================================================

@router.get("/messages")
async def get_messages(
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    group_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
    _admin: dict = Depends(get_current_admin),
):
    """Kunlik xabarlar grafigi uchun ma'lumot"""
    service = AnalyticsService(db)
    daily = await service.get_daily_messages(parse_date(date_from), parse_date(date_to), group_id=group_id)
    return {"daily_messages": daily}


@router.get("/response-time")
async def get_response_time(
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    group_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
    _admin: dict = Depends(get_current_admin),
):
    """Javob vaqti trendi"""
    service = AnalyticsService(db)
    trend = await service.get_response_time_trend(parse_date(date_from), parse_date(date_to), group_id=group_id)
    return {"response_time_trend": trend}


@router.get("/heatmap")
async def get_heatmap(
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    group_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
    _admin: dict = Depends(get_current_admin),
):
    """Soatlik aktivlik heatmapi"""
    service = AnalyticsService(db)
    heatmap = await service.get_hourly_heatmap(parse_date(date_from), parse_date(date_to), group_id=group_id)
    return {"heatmap": heatmap}


@router.get("/user-growth")
async def get_user_growth(
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    group_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
    _admin: dict = Depends(get_current_admin),
):
    """Foydalanuvchilar o'sish grafigi"""
    service = AnalyticsService(db)
    growth = await service.get_user_growth(parse_date(date_from), parse_date(date_to), group_id=group_id)
    return {"user_growth": growth}


# =====================================================
# OPERATORS
# =====================================================

@router.get("/operators")
async def get_operators(
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    group_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
    _admin: dict = Depends(get_current_admin),
):
    """Operatorlar ro'yxati va statistikasi"""
    service = AnalyticsService(db)
    operators = await service.get_operators(parse_date(date_from), parse_date(date_to), group_id=group_id)
    return {"operators": operators}


@router.get("/operators/{operator_id}")
async def get_operator_detail(
    operator_id: int,
    db: AsyncSession = Depends(get_db),
    _admin: dict = Depends(get_current_admin),
):
    """Bitta operator haqida batafsil ma'lumot"""
    service = AnalyticsService(db)
    detail = await service.get_operator_detail(operator_id)
    if not detail:
        raise HTTPException(status_code=404, detail="Operator topilmadi")
    return detail


# =====================================================
# USERS
# =====================================================

@router.get("/users")
async def get_users(
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    group_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
    _admin: dict = Depends(get_current_admin),
):
    """Eng faol foydalanuvchilar"""
    service = AnalyticsService(db)
    users = await service.get_top_users(parse_date(date_from), parse_date(date_to), group_id=group_id)
    return {"users": users}


@router.get("/users/{user_id}")
async def get_user_detail(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    _admin: dict = Depends(get_current_admin),
):
    """Bitta foydalanuvchi haqida batafsil ma'lumot"""
    service = AnalyticsService(db)
    detail = await service.get_user_detail(user_id)
    if not detail:
        raise HTTPException(status_code=404, detail="Foydalanuvchi topilmadi")
    return detail


# =====================================================
# CONVERSATIONS
# =====================================================

@router.get("/unanswered")
async def get_unanswered(
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    group_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
    _admin: dict = Depends(get_current_admin),
):
    """Javobsiz qolgan suhbatlar"""
    service = AnalyticsService(db)
    unanswered = await service.get_unanswered(parse_date(date_from), parse_date(date_to), group_id=group_id)
    return {"unanswered": unanswered}

@router.get("/answered")
async def get_answered(
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    group_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
    _admin: dict = Depends(get_current_admin),
):
    """Javob berilgan suhbatlar"""
    service = AnalyticsService(db)
    answered = await service.get_answered(parse_date(date_from), parse_date(date_to), group_id=group_id)
    return {"answered": answered}


@router.get("/conversations")
async def get_conversations(
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    group_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
    _admin: dict = Depends(get_current_admin),
):
    """Sekin javob berilgan suhbatlar"""
    service = AnalyticsService(db)
    slow = await service.get_slow_responses(parse_date(date_from), parse_date(date_to), group_id=group_id)
    recent = await service.get_recent_messages(parse_date(date_from), parse_date(date_to), group_id=group_id)
    return {"slow_responses": slow, "recent_messages": recent}
