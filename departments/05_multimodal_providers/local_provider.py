"""
Local Machine Multimodal Intelligence Provider.
Executes completely on-device (Apple Silicon M4 / CPU) using local open-weight and deterministic
computer vision, speech, and signal processing toolchains.
Zero cloud network dependencies, zero API token cost, 100% data privacy.
"""
import asyncio
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4

from core.assets.intelligence_models import (
    AnalysisProfile,
    BoundingBox,
    CameraMotionType,
    DetectedObjectRecord,
    ShotRecord
)
from departments.media_intelligence.audio_intelligence import AudioIntelligenceService
from departments.media_intelligence.camera_motion import CameraMotionService
from departments.media_intelligence.computer_vision import ComputerVisionService
from departments.media_intelligence.shot_detector import ShotDetectionService
from departments.media_intelligence.speech_transcriber import SpeechRecognitionService

from .interface import (
    ISpeechProvider,
    IVideoUnderstandingProvider,
    VideoAnalysisResult
)

logger = logging.getLogger("studio.providers.local")

class LocalMultimodalProvider(IVideoUnderstandingProvider, ISpeechProvider):
    def __init__(
        self,
        shot_detector: Optional[ShotDetectionService] = None,
        camera_motion: Optional[CameraMotionService] = None,
        vision_service: Optional[ComputerVisionService] = None,
        audio_service: Optional[AudioIntelligenceService] = None,
        speech_service: Optional[SpeechRecognitionService] = None
    ):
        self.shot_detector = shot_detector or ShotDetectionService()
        self.camera_motion = camera_motion or CameraMotionService()
        self.vision_service = vision_service or ComputerVisionService()
        self.audio_service = audio_service or AudioIntelligenceService()
        self.speech_service = speech_service or SpeechRecognitionService()

    def health_check(self) -> bool:
        return True

    async def analyze_video(
        self,
        video_path: Path,
        prompt: str,
        fps: Optional[float] = None
    ) -> VideoAnalysisResult:
        if not video_path.exists():
            raise FileNotFoundError(f"Video file not found: {video_path}")

        dummy_asset_id = uuid4()
        # 1. Cuts
        shots = self.shot_detector.detect_shots(video_path, dummy_asset_id)
        # 2. Camera motion
        motion = self.camera_motion.analyze_camera_motion(video_path, dummy_asset_id)
        # 3. Vision objects
        objects = self.vision_service.detect_and_track(video_path, dummy_asset_id)

        events = []
        for s in shots:
            events.append({
                "timecode": f"{s.timecode_range.start_seconds:.2f}s - {s.timecode_range.end_seconds:.2f}s",
                "label": f"Shot {s.shot_number} [{s.shot_scale.value}]"
            })
        for m in motion[:5]:
            events.append({
                "timecode": f"{m.timecode_range.start_seconds:.2f}s",
                "label": f"Camera motion: {m.motion_type.value} (conf: {m.confidence:.2f})"
            })

        summary = (
            f"Local Deterministic Analysis [{video_path.name}]: "
            f"Detected {len(shots)} shots, {len(motion)} camera motion segments, "
            f"and {len(objects)} tracked object observations. "
            f"Prompt focus: '{prompt}'."
        )

        return VideoAnalysisResult(
            provider="local-engine (on-device M4)",
            model="PySceneDetect + Farneback + CentroidTracker",
            summary=summary,
            events=events,
            tokens_used=0,
            estimated_cost_usd=0.0,
            raw_response={
                "shots_count": len(shots),
                "camera_movements_count": len(motion),
                "detected_objects_count": len(objects)
            }
        )

    async def compare_videos(
        self,
        video_a_path: Path,
        video_b_path: Path,
        comparison_prompt: str
    ) -> Dict[str, Any]:
        dummy_id_a = uuid4()
        dummy_id_b = uuid4()
        shots_a = self.shot_detector.detect_shots(video_a_path, dummy_id_a)
        shots_b = self.shot_detector.detect_shots(video_b_path, dummy_id_b)

        asl_a = sum(s.timecode_range.duration_seconds for s in shots_a) / max(1, len(shots_a))
        asl_b = sum(s.timecode_range.duration_seconds for s in shots_b) / max(1, len(shots_b))

        pacing_ratio = round(asl_a / max(0.1, asl_b), 2)
        return {
            "provider": "local-deterministic",
            "source_asl_sec": round(asl_a, 2),
            "reference_asl_sec": round(asl_b, 2),
            "pacing_ratio": pacing_ratio,
            "comparison_summary": (
                f"Source footage has ASL of {asl_a:.2f}s vs reference ASL of {asl_b:.2f}s. "
                f"Pacing ratio is {pacing_ratio}x. Prompt: {comparison_prompt}"
            ),
            "cost_usd": 0.0
        }

    async def transcribe(
        self,
        audio_path: Path,
        language: Optional[str] = None
    ) -> Dict[str, Any]:
        dummy_id = uuid4()
        segments = self.speech_service.transcribe(audio_path, dummy_id, language=language)
        return {
            "provider": "faster-whisper-local",
            "segments_count": len(segments),
            "text": " ".join(s.text for s in segments),
            "cost_usd": 0.0
        }
