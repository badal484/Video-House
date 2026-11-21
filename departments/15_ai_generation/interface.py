"""
Interface definition for Department: 15_ai_generation
Multi-provider router for Runway Gen-3, Kling 1.5, Wan2.1, Flux.1.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from uuid import UUID
from pydantic import BaseModel, Field

class AIGenerationRequest(BaseModel):
    project_id: UUID = Field(..., description="Target project UUID")
    parameters: Dict[str, Any] = Field(default_factory=dict)

class AIGenerationResponse(BaseModel):
    success: bool
    message: str
    data: Dict[str, Any] = Field(default_factory=dict)
    produced_asset_ids: List[UUID] = Field(default_factory=list)

class IAIGeneration(ABC):
    """
    Abstract contract for Department 15_ai_generation: AIGeneration
    """
    @abstractmethod
    async def execute(self, request: AIGenerationRequest) -> AIGenerationResponse:
        """Executes the primary task of this department."""
        pass

    @abstractmethod
    def health_check(self) -> bool:
        """Verifies underlying tooling and dependencies are ready."""
        pass
