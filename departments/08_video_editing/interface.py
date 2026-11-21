"""
Interface definition for Department: 08_video_editing
OpenTimelineIO programmatic multi-track editorial assembly.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from uuid import UUID
from pydantic import BaseModel, Field

class VideoEditingRequest(BaseModel):
    project_id: UUID = Field(..., description="Target project UUID")
    parameters: Dict[str, Any] = Field(default_factory=dict)

class VideoEditingResponse(BaseModel):
    success: bool
    message: str
    data: Dict[str, Any] = Field(default_factory=dict)
    produced_asset_ids: List[UUID] = Field(default_factory=list)

class IVideoEditing(ABC):
    """
    Abstract contract for Department 08_video_editing: VideoEditing
    """
    @abstractmethod
    async def execute(self, request: VideoEditingRequest) -> VideoEditingResponse:
        """Executes the primary task of this department."""
        pass

    @abstractmethod
    def health_check(self) -> bool:
        """Verifies underlying tooling and dependencies are ready."""
        pass
