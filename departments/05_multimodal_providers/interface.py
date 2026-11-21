"""
Interface definitions for Department 05: Multimodal Providers.
Unified provider adapters for Google Gemini, TwelveLabs, Qwen2.5-VL,
and Local Intelligence fallback pipelines.
"""
from abc import ABC, abstractmethod
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import UUID
from pydantic import BaseModel, Field

class ProviderRoutingMode(str, Enum):
    LOCAL_FIRST = "LOCAL_FIRST"
    LOCAL_ONLY = "LOCAL_ONLY"
    CLOUD_ONLY = "CLOUD_ONLY"
    COST_OPTIMIZED = "COST_OPTIMIZED"
    ACCURACY_OPTIMIZED = "ACCURACY_OPTIMIZED"

class VideoAnalysisResult(BaseModel):
    provider: str
    model: str
    summary: str
    events: List[Dict[str, Any]] = Field(default_factory=list)
    tokens_used: int = 0
    estimated_cost_usd: float = 0.0
    raw_response: Dict[str, Any] = Field(default_factory=dict)

class IVideoUnderstandingProvider(ABC):
    """
    Contract for video-language foundation models (Gemini, TwelveLabs, Qwen-VL).
    """
    @abstractmethod
    async def analyze_video(
        self,
        video_path: Path,
        prompt: str,
        fps: Optional[float] = None
    ) -> VideoAnalysisResult:
        """Analyzes video content with a specific prompt, returning structured temporal insights."""
        pass

    @abstractmethod
    async def compare_videos(
        self,
        video_a_path: Path,
        video_b_path: Path,
        comparison_prompt: str
    ) -> Dict[str, Any]:
        """Compares two videos (e.g. source footage vs reference style)."""
        pass

    @abstractmethod
    def health_check(self) -> bool:
        """Verifies API credentials or local inference runtime."""
        pass

class ISpeechProvider(ABC):
    """
    Contract for speech-to-text and diarization providers.
    """
    @abstractmethod
    async def transcribe(
        self,
        audio_path: Path,
        language: Optional[str] = None
    ) -> Dict[str, Any]:
        """Transcribes audio with word-level timestamps and speaker tags."""
        pass

    @abstractmethod
    def health_check(self) -> bool:
        pass

class IEmbeddingProvider(ABC):
    """
    Contract for multimodal semantic embeddings.
    """
    @abstractmethod
    async def embed_text(self, text: str) -> List[float]:
        pass

    @abstractmethod
    async def embed_video(self, video_path: Path) -> List[float]:
        pass

    @abstractmethod
    def health_check(self) -> bool:
        pass

class MultimodalProvidersRequest(BaseModel):
    project_id: UUID = Field(..., description="Target project UUID")
    action: str = Field(..., description="Action to perform (analyze_video, compare, embed, transcribe)")
    target_path: str = Field(..., description="Path to media file")
    prompt: Optional[str] = None
    parameters: Dict[str, Any] = Field(default_factory=dict)

class MultimodalProvidersResponse(BaseModel):
    success: bool
    provider: str
    data: Dict[str, Any] = Field(default_factory=dict)
    cost_usd: float = 0.0

class IMultimodalProviders(ABC):
    """
    Department 05 Master Contract.
    """
    @abstractmethod
    async def execute(self, request: MultimodalProvidersRequest) -> MultimodalProvidersResponse:
        pass

    @abstractmethod
    def health_check(self) -> bool:
        pass
