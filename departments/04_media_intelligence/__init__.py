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
from .temporal_engine.normalization import MediaNormalizationService
from .temporal_engine.sampling_engine import HighResolutionTemporalSamplingEngine, MultiResolutionTimeline
from .cinematography import CinematographyIntelligenceEngine, ShotCinematographyAnalysis
from .editing_intelligence import EditingIntelligenceEngine, EditorialRhythmProfile, TransitionDetail
from .motion_graphics_intelligence import MotionGraphicsReverseEngineeringEngine, TrackedGraphicElement
from .animation_vfx import AnimationAndVFXIntelligenceEngine, VisualMediumAnalysis
from .audio_intelligence_v2 import AdvancedAudioIntelligenceEngine, AudioMasterIntelligenceResult
from .color_grading_intelligence import ColorGradingIntelligenceEngine, ColorGradingProfile
from .narrative_intelligence import StorytellingIntelligenceEngine, StorytellingProfile
from .master_reverse_engineer import MasterVideoReverseEngineeringService, ReferenceReconstructionManifest

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
    "SemanticSearchService",
    "MediaNormalizationService",
    "HighResolutionTemporalSamplingEngine",
    "MultiResolutionTimeline",
    "CinematographyIntelligenceEngine",
    "ShotCinematographyAnalysis",
    "EditingIntelligenceEngine",
    "EditorialRhythmProfile",
    "TransitionDetail",
    "MotionGraphicsReverseEngineeringEngine",
    "TrackedGraphicElement",
    "AnimationAndVFXIntelligenceEngine",
    "VisualMediumAnalysis",
    "AdvancedAudioIntelligenceEngine",
    "AudioMasterIntelligenceResult",
    "ColorGradingIntelligenceEngine",
    "ColorGradingProfile",
    "StorytellingIntelligenceEngine",
    "StorytellingProfile",
    "MasterVideoReverseEngineeringService",
    "ReferenceReconstructionManifest"
]
