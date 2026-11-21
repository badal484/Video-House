"""
Interface definition for Department: 19_rendering_delivery
Master export with EBU R128 loudness conformance.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from uuid import UUID
from pydantic import BaseModel, Field

class RenderingDeliveryRequest(BaseModel):
    project_id: UUID = Field(..., description="Target project UUID")
    parameters: Dict[str, Any] = Field(default_factory=dict)

class RenderingDeliveryResponse(BaseModel):
    success: bool
    message: str
    data: Dict[str, Any] = Field(default_factory=dict)
    produced_asset_ids: List[UUID] = Field(default_factory=list)

class IRenderingDelivery(ABC):
    """
    Abstract contract for Department 19_rendering_delivery: RenderingDelivery
    """
    @abstractmethod
    async def execute(self, request: RenderingDeliveryRequest) -> RenderingDeliveryResponse:
        """Executes the primary task of this department."""
        pass

    @abstractmethod
    def health_check(self) -> bool:
        """Verifies underlying tooling and dependencies are ready."""
        pass
