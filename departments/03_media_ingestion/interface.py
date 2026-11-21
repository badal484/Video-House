"""
Interface definition for Department: 03_media_ingestion
FFmpeg/FFprobe demuxing, conformance, proxy transcode, keyframe indexing.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from uuid import UUID
from pydantic import BaseModel, Field

class MediaIngestionRequest(BaseModel):
    project_id: UUID = Field(..., description="Target project UUID")
    parameters: Dict[str, Any] = Field(default_factory=dict)

class MediaIngestionResponse(BaseModel):
    success: bool
    message: str
    data: Dict[str, Any] = Field(default_factory=dict)
    produced_asset_ids: List[UUID] = Field(default_factory=list)

class IMediaIngestion(ABC):
    """
    Abstract contract for Department 03_media_ingestion: MediaIngestion
    """
    @abstractmethod
    async def execute(self, request: MediaIngestionRequest) -> MediaIngestionResponse:
        """Executes the primary task of this department."""
        pass

    @abstractmethod
    def health_check(self) -> bool:
        """Verifies underlying tooling and dependencies are ready."""
        pass
