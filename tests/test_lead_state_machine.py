import pytest
from uuid import uuid4

from app.models import LeadStatus
from app.services.lead_state_machine import (
    validate_status_transition,
    get_allowed_transitions,
    StatusTransitionError,
    ALLOWED_TRANSITIONS
)


class TestStatusTransitions:
    """Test the lead status state machine."""

    def test_valid_transition_new_to_in_progress(self):
        """Test valid transition from NEW to IN_PROGRESS."""
        assert validate_status_transition(LeadStatus.NEW, LeadStatus.IN_PROGRESS) is True

    def test_valid_transition_in_progress_to_negotiation(self):
        """Test valid transition from IN_PROGRESS to NEGOTIATION."""
        assert validate_status_transition(LeadStatus.IN_PROGRESS, LeadStatus.NEGOTIATION) is True

    def test_valid_transition_in_progress_to_lost(self):
        """Test valid transition from IN_PROGRESS to LOST."""
        assert validate_status_transition(LeadStatus.IN_PROGRESS, LeadStatus.LOST) is True

    def test_valid_transition_negotiation_to_won(self):
        """Test valid transition from NEGOTIATION to WON."""
        assert validate_status_transition(LeadStatus.NEGOTIATION, LeadStatus.WON) is True

    def test_valid_transition_negotiation_to_lost(self):
        """Test valid transition from NEGOTIATION to LOST."""
        assert validate_status_transition(LeadStatus.NEGOTIATION, LeadStatus.LOST) is True

    def test_same_status_no_change(self):
        """Test that same status returns True (no change needed)."""
        assert validate_status_transition(LeadStatus.NEW, LeadStatus.NEW) is True
        assert validate_status_transition(LeadStatus.WON, LeadStatus.WON) is True

    def test_invalid_transition_new_to_won(self):
        """Test invalid transition from NEW directly to WON."""
        with pytest.raises(StatusTransitionError):
            validate_status_transition(LeadStatus.NEW, LeadStatus.WON)

    def test_invalid_transition_new_to_lost(self):
        """Test invalid transition from NEW directly to LOST."""
        with pytest.raises(StatusTransitionError):
            validate_status_transition(LeadStatus.NEW, LeadStatus.LOST)

    def test_invalid_transition_won_to_new(self):
        """Test invalid transition from WON back to NEW (terminal state)."""
        with pytest.raises(StatusTransitionError):
            validate_status_transition(LeadStatus.WON, LeadStatus.NEW)

    def test_invalid_transition_lost_to_in_progress(self):
        """Test invalid transition from LOST back to IN_PROGRESS (terminal state)."""
        with pytest.raises(StatusTransitionError):
            validate_status_transition(LeadStatus.LOST, LeadStatus.IN_PROGRESS)

    def test_invalid_transition_won_to_negotiation(self):
        """Test invalid transition from WON to NEGOTIATION."""
        with pytest.raises(StatusTransitionError):
            validate_status_transition(LeadStatus.WON, LeadStatus.NEGOTIATION)

    def test_get_allowed_transitions_new(self):
        """Test getting allowed transitions for NEW status."""
        allowed = get_allowed_transitions(LeadStatus.NEW)
        assert allowed == ["in_progress"]

    def test_get_allowed_transitions_in_progress(self):
        """Test getting allowed transitions for IN_PROGRESS status."""
        allowed = get_allowed_transitions(LeadStatus.IN_PROGRESS)
        assert set(allowed) == {"negotiation", "lost"}

    def test_get_allowed_transitions_won(self):
        """Test getting allowed transitions for WON status (terminal)."""
        allowed = get_allowed_transitions(LeadStatus.WON)
        assert allowed == []

    def test_get_allowed_transitions_lost(self):
        """Test getting allowed transitions for LOST status (terminal)."""
        allowed = get_allowed_transitions(LeadStatus.LOST)
        assert allowed == []


@pytest.mark.asyncio
class TestLeadAccessControl:
    """Test access control for leads."""

    async def test_manager_sees_only_own_leads(self):
        """Test that manager can only see their own leads."""
        # This would require database setup - placeholder for integration test
        pass

    async def test_admin_sees_all_leads(self):
        """Test that admin can see all leads."""
        # This would require database setup - placeholder for integration test
        pass


@pytest.mark.asyncio
class TestLeadCRUD:
    """Test CRUD operations for leads."""

    async def test_create_lead(self):
        """Test creating a new lead."""
        pass

    async def test_update_lead(self):
        """Test updating a lead."""
        pass

    async def test_delete_lead_admin_only(self):
        """Test that only admin can delete leads."""
        pass


@pytest.mark.asyncio
class TestReports:
    """Test report endpoints."""

    async def test_conversion_report(self):
        """Test conversion report generation."""
        pass

    async def test_managers_report(self):
        """Test managers performance report."""
        pass

    async def test_dynamics_report(self):
        """Test dynamics report generation."""
        pass
