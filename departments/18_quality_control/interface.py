"""
Interface definition for Department: 18_quality_control
Automated detection of black frames, freeze frames, audio clipping.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from uuid import UUID
from pydantic import BaseModel, Field

class QualityControlRequest(BaseModel):
    project_id: UUID = Field(..., description="Target project UUID")
    parameters: Dict[str, Any] = Field(default_factory=dict)

class QualityControlResponse(BaseModel):
    success: bool
    message: str
    data: Dict[str, Any] = Field(default_factory=dict)
    produced_asset_ids: List[UUID] = Field(default_factory=list)

class IQualityControl(ABC):
    """
    Abstract contract for Department 18_quality_control: QualityControl
    """
    @abstractmethod
    async def execute(self, request: QualityControlRequest) -> QualityControlResponse:
        """Executes the primary task of this department."""
        pass

    @abstractmethod
    def health_check(self) -> bool:
        """Verifies underlying tooling and dependencies are ready."""
        pass
