"""
Media Intelligence Master Service.
Orchestrates multi-resolution video, audio, vision, motion, and reference analysis.
Persists evidence-grounded observations into the Central Asset Registry.
"""
import asyncio
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from core.assets.database import (
    AssetDatabase,
    MediaType,
    ProcessingStatus
)
from core.assets.intelligence_models import (
    AnalysisProfile,
    ReferenceProfile,
    ShotRecord
)
from .interface import IMediaIntelligence
from .audio_intelligence import AudioIntelligenceService
from .camera_motion import CameraMotionService
from .computer_vision import ComputerVisionService
from .ocr_service import OCRService
from .reference_analyzer import ReferenceAnalysisService
from .semantic_search import SemanticSearchService
from .shot_detector import ShotDetectionService
from .speech_transcriber import SpeechRecognitionService
from .video_comparator import MultiVideoComparisonService
from .master_reverse_engineer import MasterVideoReverseEngineeringService, ReferenceReconstructionManifest
from core.intelligence.event_graph import TemporalEventGraph

logger = logging.getLogger("studio.media_intelligence")

class MediaIntelligenceService(IMediaIntelligence):
    def __init__(
        self,
        db: AssetDatabase,
        shot_detector: Optional[ShotDetectionService] = None,
        camera_motion: Optional[CameraMotionService] = None,
        speech_service: Optional[SpeechRecognitionService] = None,
        audio_service: Optional[AudioIntelligenceService] = None,
        vision_service: Optional[ComputerVisionService] = None,
        ocr_service: Optional[OCRService] = None,
        reference_analyzer: Optional[ReferenceAnalysisService] = None,
        comparator: Optional[MultiVideoComparisonService] = None,
        search_service: Optional[SemanticSearchService] = None,
        master_engineer: Optional[MasterVideoReverseEngineeringService] = None
    ):
        self.db = db
        self.shot_detector = shot_detector or ShotDetectionService()
        self.camera_motion = camera_motion or CameraMotionService()
        self.speech_service = speech_service or SpeechRecognitionService()
        self.audio_service = audio_service or AudioIntelligenceService()
        self.vision_service = vision_service or ComputerVisionService()
        self.ocr_service = ocr_service or OCRService()
        self.reference_analyzer = reference_analyzer or ReferenceAnalysisService(
            self.shot_detector, self.camera_motion, self.audio_service
        )
        self.comparator = comparator or MultiVideoComparisonService()
        self.search_service = search_service or SemanticSearchService(db)
        self.master_engineer = master_engineer or MasterVideoReverseEngineeringService(db=db)

    async def analyze_asset(
        self,
        asset_id: UUID,
        profile: AnalysisProfile = AnalysisProfile.STANDARD
    ) -> Dict[str, Any]:
        """
        Executes end-to-end multimodal intelligence analysis based on selected profile.
        """
        asset = self.db.get_asset(asset_id)
        if not asset:
            raise FileNotFoundError(f"Asset {asset_id} not found.")

        file_path = Path(asset.storage_path)
        if not file_path.exists():
            raise FileNotFoundError(f"Physical media file missing: {file_path}")

        meta = self.db.get_technical_metadata(asset_id)
        fps = meta.frame_rate if meta and meta.frame_rate else 24.0

        manifest: Dict[str, Any] = {
            "asset_id": str(asset_id),
            "project_id": str(asset.project_id),
            "analysis_profile": profile.value,
            "observations_summary": {}
        }

        # 1. Shot & Cut Boundary Detection (for Videos)
        if asset.media_type == MediaType.VIDEO:
            shots = self.shot_detector.detect_shots(file_path, asset_id, fps)
            self.db.save_shots(shots)
            manifest["observations_summary"]["shots_count"] = len(shots)

            # 2. Camera Motion Analysis
            if profile in (AnalysisProfile.STANDARD, AnalysisProfile.DETAILED, AnalysisProfile.REFERENCE_ANALYSIS):
                movements = self.camera_motion.analyze_camera_motion(file_path, asset_id, fps)
                self.db.save_camera_movements(movements)
                manifest["observations_summary"]["camera_movements_count"] = len(movements)

            # 3. Computer Vision & Subject Tracking
            if profile in (AnalysisProfile.STANDARD, AnalysisProfile.DETAILED):
                detections = self.vision_service.detect_and_track(file_path, asset_id, fps)
                self.db.save_detected_objects(detections)
                manifest["observations_summary"]["detected_objects_count"] = len(detections)

            # 4. On-Screen Typography & OCR
            if profile in (AnalysisProfile.STANDARD, AnalysisProfile.DETAILED):
                ocr_obs = self.ocr_service.extract_text(file_path, asset_id, fps)
                self.db.save_ocr_observations(ocr_obs)
                manifest["observations_summary"]["ocr_observations_count"] = len(ocr_obs)

        # 5. Audio Intelligence & Speech Recognition
        # Check if asset has an extracted audio derivative or is native audio
        audio_target = None
        if asset.media_type == MediaType.AUDIO:
            audio_target = file_path
        elif asset.media_type == MediaType.VIDEO:
            derivatives = self.db.get_derivatives(asset_id)
            extracted_wav = next(
                (Path(d.storage_path) for d in derivatives if d.derivative_type.value == "EXTRACTED_AUDIO"),
                None
            )
            if extracted_wav and extracted_wav.exists():
                audio_target = extracted_wav
            elif meta and meta.audio_codec:
                # Use source video directly if it has audio stream
                audio_target = file_path

        if audio_target and audio_target.exists():
            # A. Speech Recognition
            transcripts = self.speech_service.transcribe(audio_target, asset_id)
            self.db.save_transcripts(transcripts)
            manifest["observations_summary"]["transcript_segments_count"] = len(transcripts)

            # B. Acoustic Events & Music Analysis
            if audio_target.suffix.lower() == ".wav":
                events, music = self.audio_service.analyze_audio(audio_target, asset_id)
                self.db.save_audio_events(events)
                self.db.save_music_segments(music)
                manifest["observations_summary"]["audio_events_count"] = len(events)
                manifest["observations_summary"]["music_segments_count"] = len(music)

        # 6. Reference Profile Deconstruction
        if profile == AnalysisProfile.REFERENCE_ANALYSIS and asset.media_type == MediaType.VIDEO:
            ref_profile = self.reference_analyzer.generate_reference_profile(
                file_path, asset_id, name=asset.display_name or asset.original_filename
            )
            self.db.save_reference_profile(ref_profile)
            manifest["reference_profile"] = {
                "pacing": ref_profile.editing_style.get("pacing"),
                "asl": ref_profile.editing_style.get("average_shot_length_sec"),
                "palette": ref_profile.visual_style.get("dominant_palette_hex")
            }

        manifest["status"] = "SUCCESS"
        return manifest

    def search(self, project_id: UUID, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        return self.search_service.search_project_media(project_id, query, limit)

    def compare_assets(
        self, source_asset_id: UUID, reference_asset_id: UUID
    ) -> Dict[str, Any]:
        source_profile_dict = self.db.get_reference_profile(source_asset_id)
        ref_profile_dict = self.db.get_reference_profile(reference_asset_id)

        if not ref_profile_dict:
            raise FileNotFoundError(f"Reference profile for asset {reference_asset_id} not found. Please analyze reference first.")
        if not source_profile_dict:
            raise FileNotFoundError(f"Reference profile for source asset {source_asset_id} not found. Please analyze source first.")

        from core.assets.intelligence_models import ReferenceProfile
        src_p = ReferenceProfile(**source_profile_dict)
        ref_p = ReferenceProfile(**ref_profile_dict)

        return self.comparator.compare_to_reference(src_p, ref_p)

    def compare_multiple_references(self, reference_asset_ids: List[UUID]) -> Dict[str, Any]:
        """Compares two or more reference assets registered in the database."""
        from core.assets.intelligence_models import ReferenceProfile
        profiles: List[ReferenceProfile] = []
        for a_id in reference_asset_ids:
            p_dict = self.db.get_reference_profile(a_id)
            if p_dict:
                profiles.append(ReferenceProfile(**p_dict))
        if not profiles:
            raise FileNotFoundError("No valid reference profiles found for given asset IDs.")
        return self.reference_analyzer.compare_multiple_references(profiles)

    def generate_inspired_production_spec(
        self, reference_asset_id: UUID, target_topic: str, duration_sec: float = 50.0
    ) -> Dict[str, Any]:
        """Generates an original production plan inspired by the reference's grammar and pacing."""
        from core.assets.intelligence_models import ReferenceProfile
        p_dict = self.db.get_reference_profile(reference_asset_id)
        if not p_dict:
            raise FileNotFoundError(f"Reference profile for asset {reference_asset_id} not found.")
        profile = ReferenceProfile(**p_dict)
        return self.reference_analyzer.generate_inspired_production_spec(profile, target_topic, duration_sec)

    def reverse_engineer_asset(
        self, asset_id: UUID, title: Optional[str] = None
    ) -> Tuple[ReferenceReconstructionManifest, TemporalEventGraph]:
        """
        Executes deep multimodal reverse engineering on an asset, returning the manifest and event graph.
        """
        asset = self.db.get_asset(asset_id)
        if not asset:
            raise FileNotFoundError(f"Asset {asset_id} not found.")
        file_path = Path(asset.storage_path)
        if not file_path.exists():
            raise FileNotFoundError(f"Physical media file missing: {file_path}")
        return self.master_engineer.reverse_engineer_video(
            video_path=file_path,
            asset_id=asset_id,
            video_title=title or asset.display_name or asset.original_filename
        )

    def health_check(self) -> bool:
        """
        Verifies OpenCV, scenedetect, signal processing, and DB are operational.
        """
        try:
            import cv2
            import scenedetect
            import scipy.signal
            return True
        except Exception as e:
            logger.error(f"MediaIntelligence health check failed: {e}")
            return False

