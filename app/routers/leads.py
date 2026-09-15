from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from uuid import UUID
from datetime import datetime

from app.database import get_db
from app.repositories import LeadRepository, UserRepository, LeadStatusHistoryRepository
from app.services.lead_state_machine import validate_status_transition, StatusTransitionError
from app.schemas import (
    LeadCreate, LeadUpdate, LeadResponse, LeadListResponse,
    LeadStatus, StatusHistoryResponse
)
from app.models import User, UserRole, LeadStatus as ModelLeadStatus
from app.middleware.auth import get_current_user, get_current_admin_user

router = APIRouter(prefix="/leads", tags=["Leads"])


@router.post("", response_model=LeadResponse, status_code=status.HTTP_201_CREATED)
async def create_lead(
    lead_data: LeadCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new lead.
    Both admins and managers can create leads.
    """
    lead_repo = LeadRepository(db)
    
    # Validate manager_id if provided
    if lead_data.manager_id:
        user_repo = UserRepository(db)
        manager = await user_repo.get_by_id(lead_data.manager_id)
        if not manager or manager.role != UserRole.MANAGER:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid manager_id"
            )
    
    lead = await lead_repo.create(
        title=lead_data.title,
        description=lead_data.description,
        company_name=lead_data.company_name,
        contact_email=lead_data.contact_email,
        manager_id=lead_data.manager_id
    )
    
    # Record initial status in history
    history_repo = LeadStatusHistoryRepository(db)
    await history_repo.create(
        lead_id=lead.id,
        old_status=ModelLeadStatus.NEW,
        new_status=ModelLeadStatus.NEW,
        changed_by=current_user.id
    )
    
    return lead


@router.get("", response_model=LeadListResponse)
async def get_leads(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    status_filter: Optional[LeadStatus] = Query(None, alias="status"),
    manager_id: Optional[UUID] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get list of leads with pagination and filters.
    Admin sees all leads, manager sees only their own.
    """
    lead_repo = LeadRepository(db)
    
    skip = (page - 1) * per_page
    
    # Managers can only see their own leads
    if current_user.role == UserRole.MANAGER:
        leads, total = await lead_repo.get_leads_for_manager(
            manager_id=current_user.id,
            skip=skip,
            limit=per_page
        )
    else:
        # Admin can filter by manager_id
        leads, total = await lead_repo.get_all(
            skip=skip,
            limit=per_page,
            status=status_filter,
            manager_id=manager_id,
            date_from=date_from.isoformat() if date_from else None,
            date_to=date_to.isoformat() if date_to else None
        )
    
    pages = (total + per_page - 1) // per_page
    
    return LeadListResponse(
        items=leads,
        total=total,
        page=page,
        per_page=per_page,
        pages=pages
    )


@router.get("/{lead_id}", response_model=LeadResponse)
async def get_lead(
    lead_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get lead details by ID.
    Manager can only view their own leads.
    """
    lead_repo = LeadRepository(db)
    lead = await lead_repo.get_by_id(lead_id)
    
    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found"
        )
    
    # Check permissions
    if current_user.role == UserRole.MANAGER and lead.manager_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: You can only view your own leads"
        )
    
    return lead


@router.patch("/{lead_id}", response_model=LeadResponse)
async def update_lead(
    lead_id: UUID,
    lead_data: LeadUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update lead information.
    Manager can update their own leads, admin can update any lead.
    Status transitions are validated according to state machine rules.
    """
    lead_repo = LeadRepository(db)
    user_repo = UserRepository(db)
    history_repo = LeadStatusHistoryRepository(db)
    
    lead = await lead_repo.get_by_id(lead_id)
    
    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found"
        )
    
    # Check permissions
    if current_user.role == UserRole.MANAGER and lead.manager_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: You can only update your own leads"
        )
    
    # Validate status transition if status is being changed
    update_data = lead_data.model_dump(exclude_unset=True)
    
    if "status" in update_data:
        new_status = update_data["status"]
        old_status = lead.status
        
        try:
            validate_status_transition(old_status, new_status)
        except StatusTransitionError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        
        # Record status change in history
        await history_repo.create(
            lead_id=lead.id,
            old_status=old_status,
            new_status=new_status,
            changed_by=current_user.id
        )
    
    # Validate manager_id if being changed
    if "manager_id" in update_data and update_data["manager_id"] is not None:
        manager = await user_repo.get_by_id(update_data["manager_id"])
        if not manager or manager.role != UserRole.MANAGER:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid manager_id"
            )
    
    lead = await lead_repo.update(lead, **update_data)
    return lead


@router.delete("/{lead_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_lead(
    lead_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Delete a lead. Admin only.
    """
    lead_repo = LeadRepository(db)
    lead = await lead_repo.get_by_id(lead_id)
    
    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found"
        )
    
    await lead_repo.delete(lead)
    return None


@router.get("/{lead_id}/history", response_model=list[StatusHistoryResponse])
async def get_lead_history(
    lead_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get status change history for a lead.
    Manager can only view history for their own leads.
    """
    lead_repo = LeadRepository(db)
    lead = await lead_repo.get_by_id(lead_id)
    
    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found"
        )
    
    # Check permissions
    if current_user.role == UserRole.MANAGER and lead.manager_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: You can only view history for your own leads"
        )
    
    history_repo = LeadStatusHistoryRepository(db)
    history = await history_repo.get_history_for_lead(lead_id)
    
    return history
