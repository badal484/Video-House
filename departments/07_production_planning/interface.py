"""
Interface definition for Department: 07_production_planning
Job dependency DAG compilation, compute and budget estimations.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from uuid import UUID
from pydantic import BaseModel, Field

class ProductionPlanningRequest(BaseModel):
    project_id: UUID = Field(..., description="Target project UUID")
    parameters: Dict[str, Any] = Field(default_factory=dict)

class ProductionPlanningResponse(BaseModel):
    success: bool
    message: str
    data: Dict[str, Any] = Field(default_factory=dict)
    produced_asset_ids: List[UUID] = Field(default_factory=list)

class IProductionPlanning(ABC):
    """
    Abstract contract for Department 07_production_planning: ProductionPlanning
    """
    @abstractmethod
    async def execute(self, request: ProductionPlanningRequest) -> ProductionPlanningResponse:
        """Executes the primary task of this department."""
        pass

    @abstractmethod
    def health_check(self) -> bool:
        """Verifies underlying tooling and dependencies are ready."""
        pass
