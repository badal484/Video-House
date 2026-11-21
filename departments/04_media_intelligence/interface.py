"""
Interface definition for Department 04: Media Intelligence.
PySceneDetect cuts, optical flow camera motion, faster-whisper speech,
audio onset/energy intelligence, person/object tracking, OCR detection,
reference video style deconstruction, and hybrid semantic search.
"""
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import UUID
from pydantic import BaseModel, Field

from core.assets.intelligence_models import (
    AnalysisProfile,
    AudioEventRecord,
    CameraMovementRecord,
    DetectedObjectRecord,
    OCRObservation,
    ReferenceProfile,
    ShotRecord,
    TranscriptSegment
)

class MediaIntelligenceRequest(BaseModel):
    project_id: UUID = Field(..., description="Target project UUID")
    asset_id: UUID = Field(..., description="Asset to analyze")
    profile: AnalysisProfile = Field(default=AnalysisProfile.STANDARD)
    parameters: Dict[str, Any] = Field(default_factory=dict)

class MediaIntelligenceResponse(BaseModel):
    success: bool
    message: str
    asset_id: Optional[UUID] = None
    data: Dict[str, Any] = Field(default_factory=dict)

class IMediaIntelligence(ABC):
    """
    Abstract contract for Department 04: Media Intelligence.
    """
    @abstractmethod
    async def analyze_asset(
        self,
        asset_id: UUID,
        profile: AnalysisProfile = AnalysisProfile.STANDARD
    ) -> Dict[str, Any]:
        """Runs end-to-end multi-modal intelligence extraction on an asset."""
        pass

    @abstractmethod
    def health_check(self) -> bool:
        """Verifies underlying CV, ML, and signal processing toolchains are ready."""
        pass
