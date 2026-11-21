"""
Render Cost Manager for Department 19.
Tracks local compute time, cloud worker charges, enforces project budget ceilings,
and requires human approval for expensive jobs (> $1.00).
"""
from __future__ import annotations

from typing import Dict, Optional
from uuid import UUID


class BudgetExceededException(Exception):
    """Raised when a render job exceeds the project budget ceiling."""
    pass


class RenderCostManager:
    """Monitors compute charges and budget ceilings."""

    DEFAULT_PROJECT_BUDGET_USD = 25.0
    EXPENSIVE_JOB_THRESHOLD_USD = 1.00

    def __init__(self):
        self._project_budgets: Dict[UUID, float] = {}
        self._project_spend: Dict[UUID, float] = {}

    def set_budget(self, project_id: UUID, budget_usd: float) -> None:
        """Sets project budget ceiling."""
        self._project_budgets[project_id] = budget_usd

    def record_cost(self, project_id: UUID, cost_usd: float) -> None:
        """Records realized compute charge."""
        current = self._project_spend.get(project_id, 0.0)
        self._project_spend[project_id] = round(current + cost_usd, 4)

    def verify_budget(self, project_id: UUID, estimated_cost_usd: float) -> tuple[bool, Optional[str]]:
        """
        Verifies that estimated_cost_usd does not violate project budget ceiling.
        Returns:
            can_proceed (bool)
            reason (Optional[str])
        """
        budget = self._project_budgets.get(project_id, self.DEFAULT_PROJECT_BUDGET_USD)
        spend = self._project_spend.get(project_id, 0.0)

        if spend + estimated_cost_usd > budget:
            return (
                False,
                f"Project budget exceeded: current spend ${spend:.2f} + job ${estimated_cost_usd:.2f} > ceiling ${budget:.2f}.",
            )

        # Check if job requires human sign-off
        if estimated_cost_usd > self.EXPENSIVE_JOB_THRESHOLD_USD:
            return (
                True,
                f"Job cost (${estimated_cost_usd:.2f}) exceeds ${self.EXPENSIVE_JOB_THRESHOLD_USD:.2f} threshold; human approval required.",
            )

        return True, None

