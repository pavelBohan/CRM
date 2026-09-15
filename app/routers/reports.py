from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, extract
from datetime import datetime, timedelta
from typing import Optional

from app.database import get_db
from app.models import Lead, LeadStatus, User, UserRole
from app.schemas import ConversionReport, ManagersReport, ManagerStats, DynamicsReport, DynamicsItem
from app.middleware.auth import get_current_admin_user

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.get("/conversion", response_model=ConversionReport)
async def get_conversion_report(
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Get conversion statistics for leads.
    Shows total leads, won leads, lost leads, and conversion rate.
    Admin only.
    """
    # Set default date range (last 30 days) if not provided
    if not date_to:
        date_to = datetime.utcnow()
    if not date_from:
        date_from = date_to - timedelta(days=30)
    
    query = select(Lead).where(
        Lead.created_at >= date_from,
        Lead.created_at <= date_to
    )
    
    result = await db.execute(query)
    leads = result.scalars().all()
    
    total_leads = len(leads)
    won_leads = sum(1 for lead in leads if lead.status == LeadStatus.WON)
    lost_leads = sum(1 for lead in leads if lead.status == LeadStatus.LOST)
    
    conversion_rate = (won_leads / total_leads * 100) if total_leads > 0 else 0.0
    
    return ConversionReport(
        total_leads=total_leads,
        won_leads=won_leads,
        lost_leads=lost_leads,
        conversion_rate=round(conversion_rate, 2),
        period_from=date_from,
        period_to=date_to
    )


@router.get("/managers", response_model=ManagersReport)
async def get_managers_report(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Get performance statistics for each manager.
    Shows total leads, won leads, and conversion rate per manager.
    Admin only.
    """
    # Get all managers
    managers_query = select(User).where(User.role == UserRole.MANAGER)
    result = await db.execute(managers_query)
    managers = result.scalars().all()
    
    manager_stats = []
    
    for manager in managers:
        # Get leads for this manager
        leads_query = select(Lead).where(Lead.manager_id == manager.id)
        leads_result = await db.execute(leads_query)
        leads = leads_result.scalars().all()
        
        total_leads = len(leads)
        won_leads = sum(1 for lead in leads if lead.status == LeadStatus.WON)
        conversion_rate = (won_leads / total_leads * 100) if total_leads > 0 else 0.0
        
        manager_stats.append(ManagerStats(
            manager_id=manager.id,
            manager_email=manager.email,
            total_leads=total_leads,
            won_leads=won_leads,
            conversion_rate=round(conversion_rate, 2)
        ))
    
    return ManagersReport(managers=manager_stats)


@router.get("/dynamics", response_model=DynamicsReport)
async def get_dynamics_report(
    period: str = Query("daily", regex="^(daily|weekly)$"),
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Get dynamics of new leads over time.
    Can be daily or weekly aggregation.
    Admin only.
    """
    date_to = datetime.utcnow()
    date_from = date_to - timedelta(days=days)
    
    dynamics_data = []
    
    if period == "daily":
        # Group by day
        current_date = date_from.date()
        while current_date <= date_to.date():
            next_date = current_date + timedelta(days=1)
            
            count_query = select(func.count(Lead.id)).where(
                Lead.created_at >= datetime.combine(current_date, datetime.min.time()),
                Lead.created_at < datetime.combine(next_date, datetime.min.time())
            )
            
            result = await db.execute(count_query)
            count = result.scalar() or 0
            
            dynamics_data.append(DynamicsItem(
                date=datetime.combine(current_date, datetime.min.time()),
                count=count
            ))
            
            current_date = next_date
    else:
        # Group by week
        current_date = date_from.date()
        while current_date <= date_to.date():
            next_date = current_date + timedelta(weeks=1)
            
            count_query = select(func.count(Lead.id)).where(
                Lead.created_at >= datetime.combine(current_date, datetime.min.time()),
                Lead.created_at < datetime.combine(next_date, datetime.min.time())
            )
            
            result = await db.execute(count_query)
            count = result.scalar() or 0
            
            dynamics_data.append(DynamicsItem(
                date=datetime.combine(current_date, datetime.min.time()),
                count=count
            ))
            
            current_date = next_date
    
    return DynamicsReport(period=period, data=dynamics_data)
