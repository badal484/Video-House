"""
Interface definition for Department: 17_subtitles_dubbing
WhisperX timed subtitles and ElevenLabs/Kokoro voice dubbing.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from uuid import UUID
from pydantic import BaseModel, Field

class SubtitlesDubbingRequest(BaseModel):
    project_id: UUID = Field(..., description="Target project UUID")
    parameters: Dict[str, Any] = Field(default_factory=dict)

class SubtitlesDubbingResponse(BaseModel):
    success: bool
    message: str
    data: Dict[str, Any] = Field(default_factory=dict)
    produced_asset_ids: List[UUID] = Field(default_factory=list)

class ISubtitlesDubbing(ABC):
    """
    Abstract contract for Department 17_subtitles_dubbing: SubtitlesDubbing
    """
    @abstractmethod
    async def execute(self, request: SubtitlesDubbingRequest) -> SubtitlesDubbingResponse:
        """Executes the primary task of this department."""
        pass

    @abstractmethod
    def health_check(self) -> bool:
        """Verifies underlying tooling and dependencies are ready."""
        pass
