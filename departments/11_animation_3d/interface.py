"""
Interface definition for Department: 11_animation_3d
Headless Blender 4.x and OpenUSD 3D scene rendering.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from uuid import UUID
from pydantic import BaseModel, Field

class Animation3DRequest(BaseModel):
    project_id: UUID = Field(..., description="Target project UUID")
    parameters: Dict[str, Any] = Field(default_factory=dict)

class Animation3DResponse(BaseModel):
    success: bool
    message: str
    data: Dict[str, Any] = Field(default_factory=dict)
    produced_asset_ids: List[UUID] = Field(default_factory=list)

class IAnimation3D(ABC):
    """
    Abstract contract for Department 11_animation_3d: Animation3D
    """
    @abstractmethod
    async def execute(self, request: Animation3DRequest) -> Animation3DResponse:
        """Executes the primary task of this department."""
        pass

    @abstractmethod
    def health_check(self) -> bool:
        """Verifies underlying tooling and dependencies are ready."""
        pass
