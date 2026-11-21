"""
Interface definition for Department: 10_animation_2d
Headless Blender Grease Pencil 3.0 vector animation.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from uuid import UUID
from pydantic import BaseModel, Field

class Animation2DRequest(BaseModel):
    project_id: UUID = Field(..., description="Target project UUID")
    parameters: Dict[str, Any] = Field(default_factory=dict)

class Animation2DResponse(BaseModel):
    success: bool
    message: str
    data: Dict[str, Any] = Field(default_factory=dict)
    produced_asset_ids: List[UUID] = Field(default_factory=list)

class IAnimation2D(ABC):
    """
    Abstract contract for Department 10_animation_2d: Animation2D
    """
    @abstractmethod
    async def execute(self, request: Animation2DRequest) -> Animation2DResponse:
        """Executes the primary task of this department."""
        pass

    @abstractmethod
    def health_check(self) -> bool:
        """Verifies underlying tooling and dependencies are ready."""
        pass
