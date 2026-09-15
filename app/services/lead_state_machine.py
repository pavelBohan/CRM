from typing import Optional, Dict, Set
from uuid import UUID

from app.models import LeadStatus


class StatusTransitionError(Exception):
    """Raised when an invalid status transition is attempted."""
    pass


# Define allowed transitions for the lead state machine
ALLOWED_TRANSITIONS: Dict[LeadStatus, Set[LeadStatus]] = {
    LeadStatus.NEW: {LeadStatus.IN_PROGRESS},
    LeadStatus.IN_PROGRESS: {LeadStatus.NEGOTIATION, LeadStatus.LOST},
    LeadStatus.NEGOTIATION: {LeadStatus.WON, LeadStatus.LOST},
    LeadStatus.WON: set(),  # Terminal state - no transitions allowed
    LeadStatus.LOST: set(),  # Terminal state - no transitions allowed
}


def validate_status_transition(old_status: LeadStatus, new_status: LeadStatus) -> bool:
    """
    Validate if a status transition is allowed.
    
    Args:
        old_status: Current status of the lead
        new_status: Desired new status
        
    Returns:
        True if transition is valid
        
    Raises:
        StatusTransitionError: If transition is not allowed
    """
    if old_status == new_status:
        return True  # No change needed
    
    allowed = ALLOWED_TRANSITIONS.get(old_status, set())
    
    if new_status not in allowed:
        raise StatusTransitionError(
            f"Invalid status transition from '{old_status.value}' to '{new_status.value}'. "
            f"Allowed transitions from '{old_status.value}': {[s.value for s in allowed] or 'none (terminal state)'}"
        )
    
    return True


def get_allowed_transitions(status: LeadStatus) -> list[str]:
    """Get list of allowed next statuses for a given status."""
    allowed = ALLOWED_TRANSITIONS.get(status, set())
    return [s.value for s in allowed]
