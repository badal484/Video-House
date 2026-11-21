"""
Department: 04_media_intelligence
PySceneDetect cuts, optical flow camera motion, faster-whisper speech,
audio onset/energy intelligence, person/object tracking, OCR detection,
reference video style deconstruction, and hybrid semantic search.
"""
from .interface import (
    IMediaIntelligence,
    MediaIntelligenceRequest,
    MediaIntelligenceResponse
)
from .service import MediaIntelligenceService
from .shot_detector import ShotDetectionService
from .camera_motion import CameraMotionService
from .speech_transcriber import SpeechRecognitionService
from .audio_intelligence import AudioIntelligenceService
from .computer_vision import ComputerVisionService
from .ocr_service import OCRService
from .reference_analyzer import ReferenceAnalysisService
from .video_comparator import MultiVideoComparisonService
from .semantic_search import SemanticSearchService

__all__ = [
    "IMediaIntelligence",
    "MediaIntelligenceRequest",
    "MediaIntelligenceResponse",
    "MediaIntelligenceService",
    "ShotDetectionService",
    "CameraMotionService",
    "SpeechRecognitionService",
    "AudioIntelligenceService",
    "ComputerVisionService",
    "OCRService",
    "ReferenceAnalysisService",
    "MultiVideoComparisonService",
    "SemanticSearchService"
]
