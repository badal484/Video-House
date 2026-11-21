"""
Interface definition for Department: 06_creative_direction
Natural language brief interpretation, storyboarding, script development.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from uuid import UUID
from pydantic import BaseModel, Field

class CreativeDirectionRequest(BaseModel):
    project_id: UUID = Field(..., description="Target project UUID")
    parameters: Dict[str, Any] = Field(default_factory=dict)

class CreativeDirectionResponse(BaseModel):
    success: bool
    message: str
    data: Dict[str, Any] = Field(default_factory=dict)
    produced_asset_ids: List[UUID] = Field(default_factory=list)

class ICreativeDirection(ABC):
    """
    Abstract contract for Department 06_creative_direction: CreativeDirection
    """
    @abstractmethod
    async def execute(self, request: CreativeDirectionRequest) -> CreativeDirectionResponse:
        """Executes the primary task of this department."""
        pass

    @abstractmethod
    def health_check(self) -> bool:
        """Verifies underlying tooling and dependencies are ready."""
        pass
