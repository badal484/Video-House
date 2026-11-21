"""
Interface definition for Department: 01_studio_application
User interface, director prompts, streaming viewport.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from uuid import UUID
from pydantic import BaseModel, Field

class StudioApplicationRequest(BaseModel):
    project_id: UUID = Field(..., description="Target project UUID")
    parameters: Dict[str, Any] = Field(default_factory=dict)

class StudioApplicationResponse(BaseModel):
    success: bool
    message: str
    data: Dict[str, Any] = Field(default_factory=dict)
    produced_asset_ids: List[UUID] = Field(default_factory=list)

class IStudioApplication(ABC):
    """
    Abstract contract for Department 01_studio_application: StudioApplication
    """
    @abstractmethod
    async def execute(self, request: StudioApplicationRequest) -> StudioApplicationResponse:
        """Executes the primary task of this department."""
        pass

    @abstractmethod
    def health_check(self) -> bool:
        """Verifies underlying tooling and dependencies are ready."""
        pass
