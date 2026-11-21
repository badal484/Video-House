"""
Generation Cost Estimator & Budget Firewall
Department 15: 15_ai_generation
"""
from __future__ import annotations

from typing import Any, Dict, Tuple


class GenerationBudgetManager:
    """Tracks project budgets and prevents accidental expenditure overruns."""

    DEFAULT_PROJECT_BUDGET_USD = 100.0
    DEFAULT_PER_SHOT_BUDGET_USD = 5.0
    HIGH_COST_THRESHOLD_USD = 1.00

    def __init__(self):
        # project_id -> {"ceiling_usd": float, "spent_usd": float}
        self._budgets: Dict[str, Dict[str, float]] = {}

    def set_project_budget(self, project_id: str, ceiling_usd: float) -> None:
        if project_id not in self._budgets:
            self._budgets[project_id] = {"ceiling_usd": ceiling_usd, "spent_usd": 0.0}
        else:
            self._budgets[project_id]["ceiling_usd"] = ceiling_usd

    def get_budget_status(self, project_id: str) -> Dict[str, Any]:
        info = self._budgets.get(project_id, {
            "ceiling_usd": self.DEFAULT_PROJECT_BUDGET_USD,
            "spent_usd": 0.0,
        })
        remaining = max(0.0, info["ceiling_usd"] - info["spent_usd"])
        return {
            "project_id": project_id,
            "ceiling_usd": info["ceiling_usd"],
            "spent_usd": round(info["spent_usd"], 4),
            "remaining_usd": round(remaining, 4),
        }

    def check_budget(self, project_id: str, cost_usd: float) -> Tuple[bool, str]:
        """Verifies if spending cost_usd is permissible."""
        status = self.get_budget_status(project_id)
        if status["remaining_usd"] < cost_usd:
            return False, f"Generation cost ${cost_usd:.2f} exceeds remaining project budget of ${status['remaining_usd']:.2f}."
        return True, "Budget cleared."

    def record_spend(self, project_id: str, actual_cost_usd: float) -> None:
        """Commits actual expense to the project ledger."""
        if project_id not in self._budgets:
            self._budgets[project_id] = {
                "ceiling_usd": self.DEFAULT_PROJECT_BUDGET_USD,
                "spent_usd": actual_cost_usd,
            }
        else:
            self._budgets[project_id]["spent_usd"] += actual_cost_usd

    @classmethod
    def requires_high_cost_approval(cls, cost_usd: float) -> bool:
        """Identifies expensive operations requiring explicit user confirmation."""
        return cost_usd >= cls.HIGH_COST_THRESHOLD_USD
