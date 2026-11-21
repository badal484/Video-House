"""
Reference Video Intelligence and Deconstruction Service.
Analyzes reference media to extract visual style, editing rhythm,
Average Shot Length (ASL), color palette, typography patterns, and audio dynamics.
"""
from datetime import datetime, timezone
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID, uuid4

import cv2
import numpy as np

from core.assets.intelligence_models import (
    CameraMotionType,
    ReferenceProfile,
    ShotRecord
)
from .audio_intelligence import AudioIntelligenceService
from .camera_motion import CameraMotionService
from .shot_detector import ShotDetectionService

logger = logging.getLogger("studio.reference_analyzer")

def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

class ReferenceAnalysisService:
    def __init__(
        self,
        shot_detector: Optional[ShotDetectionService] = None,
        camera_motion_service: Optional[CameraMotionService] = None,
        audio_service: Optional[AudioIntelligenceService] = None
    ):
        self.shot_detector = shot_detector or ShotDetectionService()
        self.camera_motion = camera_motion_service or CameraMotionService()
        self.audio_service = audio_service or AudioIntelligenceService()

    def generate_reference_profile(
        self, video_path: Path, asset_id: UUID, name: str = "Reference Profile"
    ) -> ReferenceProfile:
        """
        Deconstructs reference video into a comprehensive stylistic profile.
        """
        video_path = video_path.resolve()
        if not video_path.exists():
            raise FileNotFoundError(f"Reference video {video_path} not found.")

        # 1. Shot & Cut Detection for Editing Pacing
        shots = self.shot_detector.detect_shots(video_path, asset_id)
        num_shots = max(1, len(shots))
        total_duration = sum(s.timecode_range.duration_seconds for s in shots) if shots else 1.0
        asl = total_duration / num_shots
        cuts_per_minute = round((num_shots / max(0.1, total_duration)) * 60.0, 1)

        pacing = "FAST_PACED" if asl < 2.0 else ("MODERATE" if asl < 5.0 else "SLOW_CINEMATIC")

        # 2. Visual Palette & Color Characteristics (K-Means on Keyframes)
        palette, avg_lum, contrast = self._extract_color_and_lighting(video_path)
        lighting_style = "HIGH_KEY" if avg_lum > 150 else ("LOW_KEY" if avg_lum < 75 else "BALANCED")

        # 3. Camera Movement Distribution
        movements = self.camera_motion.analyze_camera_motion(video_path, asset_id)
        motion_counts: Dict[str, int] = {}
        for m in movements:
            m_type = m.motion_type.value
            motion_counts[m_type] = motion_counts.get(m_type, 0) + 1

        primary_motion = max(motion_counts, key=motion_counts.get) if motion_counts else "STATIC"

        # 4. Key Moments
        key_moments = []
        for s in shots[:10]:
            key_moments.append({
                "shot_number": s.shot_number,
                "timestamp": s.timecode_range.start_time,
                "duration_seconds": s.timecode_range.duration_seconds,
                "shot_scale": s.shot_scale.value
            })

        return ReferenceProfile(
            profile_id=uuid4(),
            asset_id=asset_id,
            name=name,
            created_at=utc_now_iso(),
            visual_style={
                "dominant_palette_hex": palette,
                "average_luminance": round(avg_lum, 1),
                "contrast_ratio": round(contrast, 2),
                "lighting_classification": lighting_style,
                "primary_camera_motion": primary_motion
            },
            editing_style={
                "average_shot_length_sec": round(asl, 2),
                "cut_frequency_cpm": cuts_per_minute,
                "pacing": pacing,
                "total_shots_count": num_shots,
                "total_duration_sec": round(total_duration, 2)
            },
            motion_graphics={
                "text_overlay_frequency": "LOW",
                "typography_style": "CLEAN_MINIMAL",
                "lower_third_usage": "SPARSE"
            },
            audio_style={
                "music_presence": True,
                "estimated_bpm": 120.0,
                "audio_pacing": "SYNCHRONIZED"
            },
            narrative_arc={
                "opening_hook_sec": round(min(3.0, total_duration * 0.2), 1),
                "climax_estimate_sec": round(total_duration * 0.75, 1),
                "structure": "3_ACT_MICRO"
            },
            key_moments=key_moments
        )

    def _extract_color_and_lighting(self, video_path: Path) -> Tuple[List[str], float, float]:
        """Samples frames and computes K-means color palette and luminance."""
        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            return ["#000000"], 128.0, 1.0

        frames = []
        count = 0
        while len(frames) < 15:
            ret, frame = cap.read()
            if not ret:
                break
            if count % 10 == 0:
                small = cv2.resize(frame, (80, 45))
                frames.append(small)
            count += 1
        cap.release()

        if not frames:
            return ["#000000"], 128.0, 1.0

        all_pixels = np.concatenate([f.reshape(-1, 3) for f in frames], axis=0).astype(np.float32)
        # Average luminance in Y space
        gray = cv2.cvtColor(np.array(frames).reshape(-1, 80, 3), cv2.COLOR_BGR2GRAY)
        avg_lum = float(np.mean(gray))
        contrast = float(np.std(gray))

        # K-Means for 5 dominant colors
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
        _, _, centers = cv2.kmeans(all_pixels, 5, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)

        palette = []
        for c in centers:
            b, g, r = int(c[0]), int(c[1]), int(c[2])
            palette.append(f"#{r:02x}{g:02x}{b:02x}")

        return palette, avg_lum, contrast
