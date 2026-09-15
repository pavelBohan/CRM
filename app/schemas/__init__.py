from pydantic import BaseModel, EmailStr, Field, UUID4
from typing import Optional
from datetime import datetime
from enum import Enum


class UserRole(str, Enum):
    ADMIN = "admin"
    MANAGER = "manager"


class LeadStatus(str, Enum):
    NEW = "new"
    IN_PROGRESS = "in_progress"
    NEGOTIATION = "negotiation"
    WON = "won"
    LOST = "lost"


# Auth schemas
class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    user_id: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None


class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)
    role: UserRole = UserRole.MANAGER


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: UUID4
    email: str
    role: UserRole
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# Lead schemas
class LeadCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: str = ""
    company_name: str = Field(..., min_length=1, max_length=255)
    contact_email: EmailStr
    manager_id: Optional[UUID4] = None


class LeadUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    company_name: Optional[str] = Field(None, min_length=1, max_length=255)
    contact_email: Optional[EmailStr] = None
    status: Optional[LeadStatus] = None
    manager_id: Optional[UUID4] = None


class LeadResponse(BaseModel):
    id: UUID4
    title: str
    description: str
    company_name: str
    contact_email: str
    status: LeadStatus
    manager_id: Optional[UUID4]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class LeadListResponse(BaseModel):
    items: list[LeadResponse]
    total: int
    page: int
    per_page: int
    pages: int


# Status history schema
class StatusHistoryResponse(BaseModel):
    id: UUID4
    lead_id: UUID4
    old_status: LeadStatus
    new_status: LeadStatus
    changed_by: UUID4
    changed_at: datetime

    class Config:
        from_attributes = True


# Report schemas
class ConversionReport(BaseModel):
    total_leads: int
    won_leads: int
    lost_leads: int
    conversion_rate: float
    period_from: datetime
    period_to: datetime


class ManagerStats(BaseModel):
    manager_id: UUID4
    manager_email: str
    total_leads: int
    won_leads: int
    conversion_rate: float


class ManagersReport(BaseModel):
    managers: list[ManagerStats]


class DynamicsItem(BaseModel):
    date: datetime
    count: int


class DynamicsReport(BaseModel):
    period: str  # "daily" or "weekly"
    data: list[DynamicsItem]
