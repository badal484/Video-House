"""
Interface definitions for Department 06: Creative Direction.
Natural language brief interpretation, storyboarding, script development,
cinematography shot planning, and reference style transfer.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID
from pydantic import BaseModel, Field

class CreativeDirectionRequest(BaseModel):
    project_id: UUID = Field(..., description="Target project UUID")
    action: str = Field(default="parse_brief", description="Action to perform")
    parameters: Dict[str, Any] = Field(default_factory=dict)

class CreativeDirectionResponse(BaseModel):
    success: bool
    message: str
    data: Dict[str, Any] = Field(default_factory=dict)
    produced_asset_ids: List[UUID] = Field(default_factory=list)

class ICreativeDirection(ABC):
    """
    Abstract contract for Department 06: Creative Direction.
    """
    @abstractmethod
    async def execute(self, request: CreativeDirectionRequest) -> CreativeDirectionResponse:
        pass

    @abstractmethod
    def health_check(self) -> bool:
        pass
