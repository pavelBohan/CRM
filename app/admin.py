from sqladmin import Admin, ModelView

from app.config import settings
from app.models import User, Lead, LeadStatusHistory


class UserAdmin(ModelView, model=User):
    column_list = [User.id, User.email, User.role, User.is_active, User.created_at]
    column_searchable_list = [User.email]
    column_filters = [User.role, User.is_active]
    column_default_sort = [(User.created_at, True)]
    can_create = False  # Disable creation via admin, use API instead
    can_edit = True
    can_delete = True
    export_max_rows = 1000


class LeadAdmin(ModelView, model=Lead):
    column_list = [
        Lead.id, Lead.title, Lead.company_name, Lead.status,
        Lead.manager_id, Lead.created_at, Lead.updated_at
    ]
    column_searchable_list = [Lead.title, Lead.company_name, Lead.contact_email]
    column_filters = [Lead.status, Lead.manager_id, Lead.created_at]
    column_default_sort = [(Lead.created_at, True)]
    can_create = False
    can_edit = True
    can_delete = True
    export_max_rows = 1000
    
    # Add CSV export
    column_export_list = [
        Lead.id, Lead.title, Lead.description, Lead.company_name,
        Lead.contact_email, Lead.status, Lead.manager_id,
        Lead.created_at, Lead.updated_at
    ]


class LeadStatusHistoryAdmin(ModelView, model=LeadStatusHistory):
    column_list = [
        LeadStatusHistory.id, LeadStatusHistory.lead_id,
        LeadStatusHistory.old_status, LeadStatusHistory.new_status,
        LeadStatusHistory.changed_by, LeadStatusHistory.changed_at
    ]
    column_filters = [LeadStatusHistory.old_status, LeadStatusHistory.new_status, LeadStatusHistory.changed_at]
    column_default_sort = [(LeadStatusHistory.changed_at, True)]
    can_create = False
    can_edit = False
    can_delete = False


def create_admin(engine):
    """Create and return admin instance."""
    admin_instance = Admin(engine, title="CRM Admin Panel")
    admin_instance.add_view(UserAdmin)
    admin_instance.add_view(LeadAdmin)
    admin_instance.add_view(LeadStatusHistoryAdmin)
    return admin_instance
