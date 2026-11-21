"""
Deterministic Shot and Cut Detection Service.
Uses PySceneDetect with adaptive thresholding and OpenCV frame-delta analysis.
Captures frame-accurate cuts, transitions, shot durations, and keyframe timestamps.
"""
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID, uuid4

import cv2
import numpy as np
import scenedetect
from scenedetect import SceneManager, open_video
from scenedetect.detectors import AdaptiveDetector, ContentDetector

from core.assets.intelligence_models import (
    CameraAngle,
    CameraMotionType,
    EvidenceRecord,
    ShotRecord,
    ShotScale,
    TimecodeRange,
    TransitionType
)

logger = logging.getLogger("studio.shot_detector")

class ShotDetectionService:
    def __init__(self, adaptive_threshold: float = 3.0, min_scene_len_frames: int = 15):
        self.adaptive_threshold = adaptive_threshold
        self.min_scene_len = min_scene_len_frames

    def detect_shots(
        self, video_path: Path, asset_id: UUID, fps: float = 24.0
    ) -> List[ShotRecord]:
        """
        Executes deterministic shot boundary detection using PySceneDetect.
        Falls back to frame-difference delta analysis if video backend encounters errors.
        """
        video_path = video_path.resolve()
        if not video_path.exists():
            raise FileNotFoundError(f"Video file {video_path} not found.")

        shots: List[ShotRecord] = []
        try:
            video = open_video(str(video_path))
            scene_manager = SceneManager()
            scene_manager.add_detector(
                AdaptiveDetector(
                    adaptive_threshold=self.adaptive_threshold,
                    min_scene_len=self.min_scene_len
                )
            )
            scene_manager.detect_scenes(video=video)
            scene_list = scene_manager.get_scene_list()

            if not scene_list:
                # Video has no hard cut; treat entire clip as single shot
                cap = cv2.VideoCapture(str(video_path))
                total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 1
                fps_detected = cap.get(cv2.CAP_PROP_FPS) or fps
                cap.release()
                duration_sec = total_frames / fps_detected
                
                single_shot = ShotRecord(
                    shot_id=uuid4(),
                    asset_id=asset_id,
                    shot_number=1,
                    timecode_range=TimecodeRange.from_seconds(0.0, duration_sec, fps_detected),
                    transition_in=TransitionType.HARD_CUT,
                    transition_out=TransitionType.HARD_CUT,
                    summary="Continuous single shot",
                    confidence=1.0,
                    evidence=EvidenceRecord(
                        provider="PySceneDetect",
                        model="AdaptiveDetector",
                        source_metric="single_scene_continuous",
                        confidence=1.0
                    )
                )
                return [single_shot]

            for idx, (start_tc, end_tc) in enumerate(scene_list, start=1):
                start_sec = start_tc.seconds if hasattr(start_tc, "seconds") else start_tc.get_seconds()
                end_sec = end_tc.seconds if hasattr(end_tc, "seconds") else end_tc.get_seconds()
                fps_val = start_tc.frame_rate if hasattr(start_tc, "frame_rate") else (start_tc.framerate or fps)

                time_range = TimecodeRange.from_seconds(start_sec, end_sec, fps_val)
                start_f = start_tc.frame_num if hasattr(start_tc, "frame_num") else start_tc.get_frames()
                end_f = end_tc.frame_num if hasattr(end_tc, "frame_num") else end_tc.get_frames()
                shot = ShotRecord(
                    shot_id=uuid4(),
                    asset_id=asset_id,
                    shot_number=idx,
                    timecode_range=time_range,
                    transition_in=TransitionType.HARD_CUT,
                    transition_out=TransitionType.HARD_CUT,
                    confidence=0.98,
                    evidence=EvidenceRecord(
                        provider="PySceneDetect",
                        model="AdaptiveDetector",
                        source_metric="luminance_and_content_delta",
                        raw_measurement={
                            "start_frame": start_f,
                            "end_frame": end_f,
                            "adaptive_threshold": self.adaptive_threshold
                        },
                        confidence=0.98
                    )
                )
                shots.append(shot)

            return shots

        except Exception as e:
            logger.warning(f"PySceneDetect error: {e}. Executing OpenCV histogram fallback.")
            return self._detect_shots_opencv_fallback(video_path, asset_id, fps)

    def _detect_shots_opencv_fallback(
        self, video_path: Path, asset_id: UUID, default_fps: float = 24.0
    ) -> List[ShotRecord]:
        """Fallback color histogram frame-difference cut detector using OpenCV."""
        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            return []

        fps = cap.get(cv2.CAP_PROP_FPS) or default_fps
        prev_hist = None
        cut_frames = [0]
        frame_idx = 0

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            # Convert to HSV and compute 2D Hue-Saturation histogram
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            hist = cv2.calcHist([hsv], [0, 1], None, [30, 32], [0, 180, 0, 256])
            cv2.normalize(hist, hist, alpha=0, beta=1, norm_type=cv2.NORM_MINMAX)

            if prev_hist is not None:
                # Compare histograms using correlation
                corr = cv2.compareHist(prev_hist, hist, cv2.HISTCMP_CORREL)
                if corr < 0.65 and (frame_idx - cut_frames[-1]) >= self.min_scene_len:
                    cut_frames.append(frame_idx)

            prev_hist = hist
            frame_idx += 1

        total_frames = max(1, frame_idx)
        cap.release()

        if cut_frames[-1] != total_frames:
            cut_frames.append(total_frames)

        shots = []
        for i in range(len(cut_frames) - 1):
            s_frame = cut_frames[i]
            e_frame = cut_frames[i + 1]
            start_sec = s_frame / fps
            end_sec = e_frame / fps

            shots.append(ShotRecord(
                shot_id=uuid4(),
                asset_id=asset_id,
                shot_number=i + 1,
                timecode_range=TimecodeRange.from_seconds(start_sec, end_sec, fps),
                confidence=0.90,
                evidence=EvidenceRecord(
                    provider="OpenCV",
                    model="ColorHistogramCorrelation",
                    source_metric="hist_correlation_drop",
                    raw_measurement={"start_frame": s_frame, "end_frame": e_frame},
                    confidence=0.90
                )
            ))
        return shots
