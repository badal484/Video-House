"""
Interface definition for Department: 09_motion_graphics
Motion Canvas declarative 2D kinetic typography and graphics.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from uuid import UUID
from pydantic import BaseModel, Field

class MotionGraphicsRequest(BaseModel):
    project_id: UUID = Field(..., description="Target project UUID")
    parameters: Dict[str, Any] = Field(default_factory=dict)

class MotionGraphicsResponse(BaseModel):
    success: bool
    message: str
    data: Dict[str, Any] = Field(default_factory=dict)
    produced_asset_ids: List[UUID] = Field(default_factory=list)

class IMotionGraphics(ABC):
    """
    Abstract contract for Department 09_motion_graphics: MotionGraphics
    """
    @abstractmethod
    async def execute(self, request: MotionGraphicsRequest) -> MotionGraphicsResponse:
        """Executes the primary task of this department."""
        pass

    @abstractmethod
    def health_check(self) -> bool:
        """Verifies underlying tooling and dependencies are ready."""
        pass
