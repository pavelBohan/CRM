"""
Seed script to create admin user and test data.
Run this after migrations with: python seed.py
"""
import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select

from app.database import Base
from app.models import User, Lead, LeadStatus, UserRole, LeadStatusHistory
from app.services.auth import hash_password
from app.config import settings


async def seed():
    engine = create_async_engine(settings.DATABASE_URL)
    async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session_maker() as session:
        # Check if admin already exists
        result = await session.execute(select(User).where(User.email == settings.ADMIN_EMAIL))
        admin = result.scalar_one_or_none()
        
        if not admin:
            # Create admin user
            admin = User(
                email=settings.ADMIN_EMAIL,
                password_hash=hash_password(settings.ADMIN_PASSWORD),
                role=UserRole.ADMIN,
                is_active=True
            )
            session.add(admin)
            await session.flush()
            print(f"Created admin user: {settings.ADMIN_EMAIL}")
        else:
            print(f"Admin user already exists: {settings.ADMIN_EMAIL}")
        
        # Create test managers
        managers_data = [
            {"email": "manager1@crm.local", "password": "manager123"},
            {"email": "manager2@crm.local", "password": "manager123"},
        ]
        
        managers = []
        for manager_data in managers_data:
            result = await session.execute(
                select(User).where(User.email == manager_data["email"])
            )
            manager = result.scalar_one_or_none()
            
            if not manager:
                manager = User(
                    email=manager_data["email"],
                    password_hash=hash_password(manager_data["password"]),
                    role=UserRole.MANAGER,
                    is_active=True
                )
                session.add(manager)
                await session.flush()
                print(f"Created manager: {manager_data['email']}")
            
            managers.append(manager)
        
        # Create test leads
        leads_data = [
            {
                "title": "Website Redesign Project",
                "description": "Complete website redesign for tech startup",
                "company_name": "TechCorp Inc.",
                "contact_email": "contact@techcorp.com",
                "status": LeadStatus.NEW,
                "manager_id": managers[0].id if managers else None
            },
            {
                "title": "CRM Integration",
                "description": "Integration of CRM system with existing tools",
                "company_name": "SalesPro Ltd.",
                "contact_email": "info@salespro.com",
                "status": LeadStatus.IN_PROGRESS,
                "manager_id": managers[0].id if managers else None
            },
            {
                "title": "Mobile App Development",
                "description": "Native mobile app for iOS and Android",
                "company_name": "AppMakers Co.",
                "contact_email": "hello@appmakers.io",
                "status": LeadStatus.NEGOTIATION,
                "manager_id": managers[1].id if len(managers) > 1 else None
            },
            {
                "title": "Data Analytics Platform",
                "description": "Custom analytics dashboard for e-commerce",
                "company_name": "DataViz Solutions",
                "contact_email": "support@dataviz.com",
                "status": LeadStatus.WON,
                "manager_id": managers[1].id if len(managers) > 1 else None
            },
            {
                "title": "Cloud Migration",
                "description": "Migration of legacy systems to cloud infrastructure",
                "company_name": "CloudFirst Inc.",
                "contact_email": "cloud@cloudfirst.net",
                "status": LeadStatus.LOST,
                "manager_id": None
            },
        ]
        
        for lead_data in leads_data:
            result = await session.execute(
                select(Lead).where(Lead.title == lead_data["title"])
            )
            lead = result.scalar_one_or_none()
            
            if not lead:
                lead = Lead(**lead_data)
                session.add(lead)
                await session.flush()
                
                # Add status history
                history = LeadStatusHistory(
                    lead_id=lead.id,
                    old_status=LeadStatus.NEW,
                    new_status=lead_data["status"],
                    changed_by=admin.id
                )
                session.add(history)
                print(f"Created lead: {lead_data['title']}")
        
        await session.commit()
        print("\nSeed completed successfully!")
        print(f"\nTest credentials:")
        print(f"  Admin: {settings.ADMIN_EMAIL} / {settings.ADMIN_PASSWORD}")
        print(f"  Manager 1: {managers_data[0]['email']} / {managers_data[0]['password']}")
        print(f"  Manager 2: {managers_data[1]['email']} / {managers_data[1]['password']}")


if __name__ == "__main__":
    asyncio.run(seed())
