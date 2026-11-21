"""
Interface definition for Department: 05_multimodal_providers
Unified provider adapters for Gemini 2.0/1.5, TwelveLabs, Qwen2.5-VL.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from uuid import UUID
from pydantic import BaseModel, Field

class MultimodalProvidersRequest(BaseModel):
    project_id: UUID = Field(..., description="Target project UUID")
    parameters: Dict[str, Any] = Field(default_factory=dict)

class MultimodalProvidersResponse(BaseModel):
    success: bool
    message: str
    data: Dict[str, Any] = Field(default_factory=dict)
    produced_asset_ids: List[UUID] = Field(default_factory=list)

class IMultimodalProviders(ABC):
    """
    Abstract contract for Department 05_multimodal_providers: MultimodalProviders
    """
    @abstractmethod
    async def execute(self, request: MultimodalProvidersRequest) -> MultimodalProvidersResponse:
        """Executes the primary task of this department."""
        pass

    @abstractmethod
    def health_check(self) -> bool:
        """Verifies underlying tooling and dependencies are ready."""
        pass
