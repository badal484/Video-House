"""
Interface definition for Department: 13_vfx_compositing
SAM 2.1 rotoscoping, E2FGVI inpainting, OpenColorIO ACEScg composites.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from uuid import UUID
from pydantic import BaseModel, Field

class VFXCompositingRequest(BaseModel):
    project_id: UUID = Field(..., description="Target project UUID")
    parameters: Dict[str, Any] = Field(default_factory=dict)

class VFXCompositingResponse(BaseModel):
    success: bool
    message: str
    data: Dict[str, Any] = Field(default_factory=dict)
    produced_asset_ids: List[UUID] = Field(default_factory=list)

class IVFXCompositing(ABC):
    """
    Abstract contract for Department 13_vfx_compositing: VFXCompositing
    """
    @abstractmethod
    async def execute(self, request: VFXCompositingRequest) -> VFXCompositingResponse:
        """Executes the primary task of this department."""
        pass

    @abstractmethod
    def health_check(self) -> bool:
        """Verifies underlying tooling and dependencies are ready."""
        pass
