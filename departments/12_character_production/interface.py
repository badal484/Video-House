"""
Interface definition for Department: 12_character_production
Character consistency, facial blendshapes, voice profiles, LoRA weights.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from uuid import UUID
from pydantic import BaseModel, Field

class CharacterProductionRequest(BaseModel):
    project_id: UUID = Field(..., description="Target project UUID")
    parameters: Dict[str, Any] = Field(default_factory=dict)

class CharacterProductionResponse(BaseModel):
    success: bool
    message: str
    data: Dict[str, Any] = Field(default_factory=dict)
    produced_asset_ids: List[UUID] = Field(default_factory=list)

class ICharacterProduction(ABC):
    """
    Abstract contract for Department 12_character_production: CharacterProduction
    """
    @abstractmethod
    async def execute(self, request: CharacterProductionRequest) -> CharacterProductionResponse:
        """Executes the primary task of this department."""
        pass

    @abstractmethod
    def health_check(self) -> bool:
        """Verifies underlying tooling and dependencies are ready."""
        pass
