"""
Interface definition for Department: 04_media_intelligence
PySceneDetect cuts, faster-whisper speech, Demucs stems, TwelveLabs vectors.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from uuid import UUID
from pydantic import BaseModel, Field

class MediaIntelligenceRequest(BaseModel):
    project_id: UUID = Field(..., description="Target project UUID")
    parameters: Dict[str, Any] = Field(default_factory=dict)

class MediaIntelligenceResponse(BaseModel):
    success: bool
    message: str
    data: Dict[str, Any] = Field(default_factory=dict)
    produced_asset_ids: List[UUID] = Field(default_factory=list)

class IMediaIntelligence(ABC):
    """
    Abstract contract for Department 04_media_intelligence: MediaIntelligence
    """
    @abstractmethod
    async def execute(self, request: MediaIntelligenceRequest) -> MediaIntelligenceResponse:
        """Executes the primary task of this department."""
        pass

    @abstractmethod
    def health_check(self) -> bool:
        """Verifies underlying tooling and dependencies are ready."""
        pass
