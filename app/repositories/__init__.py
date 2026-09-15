from typing import Optional
from uuid import UUID
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User, Lead, LeadStatusHistory, LeadStatus, UserRole
from app.services.auth import hash_password


class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_email(self, email: str) -> Optional[User]:
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_by_id(self, user_id: UUID) -> Optional[User]:
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def create(
        self,
        email: str,
        password: str,
        role: UserRole = UserRole.MANAGER
    ) -> User:
        user = User(
            email=email,
            password_hash=hash_password(password),
            role=role
        )
        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)
        return user

    async def get_all(self, skip: int = 0, limit: int = 100) -> list[User]:
        result = await self.db.execute(select(User).offset(skip).limit(limit))
        return list(result.scalars().all())


class LeadRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, lead_id: UUID) -> Optional[Lead]:
        result = await self.db.execute(
            select(Lead).where(Lead.id == lead_id)
        )
        return result.scalar_one_or_none()

    async def create(
        self,
        title: str,
        description: str,
        company_name: str,
        contact_email: str,
        manager_id: Optional[UUID] = None
    ) -> Lead:
        lead = Lead(
            title=title,
            description=description,
            company_name=company_name,
            contact_email=contact_email,
            manager_id=manager_id
        )
        self.db.add(lead)
        await self.db.flush()
        await self.db.refresh(lead)
        return lead

    async def update(self, lead: Lead, **kwargs) -> Lead:
        for key, value in kwargs.items():
            if value is not None:
                setattr(lead, key, value)
        lead.updated_at = func.now()
        await self.db.flush()
        await self.db.refresh(lead)
        return lead

    async def delete(self, lead: Lead) -> None:
        await self.db.delete(lead)

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        status: Optional[LeadStatus] = None,
        manager_id: Optional[UUID] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None
    ) -> tuple[list[Lead], int]:
        query = select(Lead)
        count_query = select(func.count(Lead.id))

        if status:
            query = query.where(Lead.status == status)
            count_query = count_query.where(Lead.status == status)

        if manager_id:
            query = query.where(Lead.manager_id == manager_id)
            count_query = count_query.where(Lead.manager_id == manager_id)

        if date_from:
            query = query.where(Lead.created_at >= date_from)
            count_query = count_query.where(Lead.created_at >= date_from)

        if date_to:
            query = query.where(Lead.created_at <= date_to)
            count_query = count_query.where(Lead.created_at <= date_to)

        query = query.order_by(Lead.created_at.desc()).offset(skip).limit(limit)

        result = await self.db.execute(query)
        leads = list(result.scalars().all())

        count_result = await self.db.execute(count_query)
        total = count_result.scalar() or 0

        return leads, total

    async def get_leads_for_manager(self, manager_id: UUID, skip: int = 0, limit: int = 100) -> tuple[list[Lead], int]:
        return await self.get_all(skip=skip, limit=limit, manager_id=manager_id)

    async def get_all_leads(self, skip: int = 0, limit: int = 100) -> tuple[list[Lead], int]:
        return await self.get_all(skip=skip, limit=limit)


class LeadStatusHistoryRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        lead_id: UUID,
        old_status: LeadStatus,
        new_status: LeadStatus,
        changed_by: UUID
    ) -> LeadStatusHistory:
        history = LeadStatusHistory(
            lead_id=lead_id,
            old_status=old_status,
            new_status=new_status,
            changed_by=changed_by
        )
        self.db.add(history)
        await self.db.flush()
        await self.db.refresh(history)
        return history

    async def get_history_for_lead(self, lead_id: UUID) -> list[LeadStatusHistory]:
        result = await self.db.execute(
            select(LeadStatusHistory)
            .where(LeadStatusHistory.lead_id == lead_id)
            .order_by(LeadStatusHistory.changed_at.desc())
        )
        return list(result.scalars().all())
