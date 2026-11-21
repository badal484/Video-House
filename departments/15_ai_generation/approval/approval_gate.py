"""
Human Approval & Creative Control Gate
Department 15: 15_ai_generation
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel, Field

from ..core.generation_models import GenerationRequest


class ApprovalStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class ApprovalTicket(BaseModel):
    ticket_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    request_id: str
    project_id: str
    reason: str
    estimated_cost_usd: float = 0.0
    status: ApprovalStatus = ApprovalStatus.PENDING
    reviewer_notes: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    resolved_at: Optional[str] = None


class ApprovalGateManager:
    """Manages human-in-the-loop approval gates for sensitive or high-cost generation operations."""

    def __init__(self, high_cost_threshold_usd: float = 1.00):
        self.high_cost_threshold_usd = high_cost_threshold_usd
        self._tickets: Dict[str, ApprovalTicket] = {}

    def requires_approval(self, request: GenerationRequest) -> Tuple[bool, Optional[str]]:
        """Determines if a request must be held for human review."""
        if request.estimated_cost_usd >= self.high_cost_threshold_usd:
            return True, f"Estimated cost ${request.estimated_cost_usd:.2f} exceeds high-cost threshold (${self.high_cost_threshold_usd:.2f})."

        # Check for external raw media upload without pre-cleared consent
        if request.reference_assets:
            for ref in request.reference_assets:
                if ref.notes and "unapproved_external_upload" in ref.notes.lower():
                    return True, "External asset upload requires human privacy clearance."

        return False, None

    def create_ticket(self, request: GenerationRequest, reason: str) -> ApprovalTicket:
        ticket = ApprovalTicket(
            request_id=request.request_id,
            project_id=request.project_id,
            reason=reason,
            estimated_cost_usd=request.estimated_cost_usd,
        )
        self._tickets[ticket.ticket_id] = ticket
        return ticket

    def get_ticket(self, ticket_id: str) -> Optional[ApprovalTicket]:
        return self._tickets.get(ticket_id)

    def list_pending_tickets(self, project_id: Optional[str] = None) -> List[ApprovalTicket]:
        tickets = [t for t in self._tickets.values() if t.status == ApprovalStatus.PENDING]
        if project_id:
            tickets = [t for t in tickets if t.project_id == project_id]
        return tickets

    def approve_ticket(self, ticket_id: str, reviewer_notes: str = "Approved by director") -> Optional[ApprovalTicket]:
        t = self._tickets.get(ticket_id)
        if t:
            t.status = ApprovalStatus.APPROVED
            t.reviewer_notes = reviewer_notes
            t.resolved_at = datetime.now(timezone.utc).isoformat()
            return t
        return None

    def reject_ticket(self, ticket_id: str, reviewer_notes: str = "Rejected by director") -> Optional[ApprovalTicket]:
        t = self._tickets.get(ticket_id)
        if t:
            t.status = ApprovalStatus.REJECTED
            t.reviewer_notes = reviewer_notes
            t.resolved_at = datetime.now(timezone.utc).isoformat()
            return t
        return None
