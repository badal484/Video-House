"""
Interface definition for Department 07: Production Planning.
Job dependency DAG compilation, compute estimations, feasibility review,
and canonical production blueprint management.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from uuid import UUID
from pydantic import BaseModel, Field

class ProductionPlanningRequest(BaseModel):
    project_id: UUID = Field(..., description="Target project UUID")
    action: str = Field(default="build_breakdown", description="Action to perform")
    parameters: Dict[str, Any] = Field(default_factory=dict)

class ProductionPlanningResponse(BaseModel):
    success: bool
    message: str
    data: Dict[str, Any] = Field(default_factory=dict)
    produced_asset_ids: List[UUID] = Field(default_factory=list)

class IProductionPlanning(ABC):
    """
    Abstract contract for Department 07: Production Planning.
    """
    @abstractmethod
    async def execute(self, request: ProductionPlanningRequest) -> ProductionPlanningResponse:
        pass

    @abstractmethod
    def health_check(self) -> bool:
        pass
