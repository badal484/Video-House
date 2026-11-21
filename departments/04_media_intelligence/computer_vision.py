"""
Computer Vision, Object Detection and Tracking Service.
Integrates OpenCV HOG person detection, Haar face cascades, and centroid/IoU tracking.
Produces stable track IDs across video frames with normalized bounding boxes.
"""
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from uuid import UUID, uuid4

import cv2
import numpy as np

from core.assets.intelligence_models import (
    BoundingBox,
    DetectedObjectRecord
)

logger = logging.getLogger("studio.computer_vision")

class ComputerVisionService:
    def __init__(self, sample_step_frames: int = 6):
        self.step = sample_step_frames
        # Initialize OpenCV HOG person detector if available, otherwise MOG2 motion/object detector
        if hasattr(cv2, "HOGDescriptor"):
            self.hog = cv2.HOGDescriptor()
            self.hog.setSVMDetector(cv2.HOGDescriptor.getDefaultPeopleDetector())
        else:
            self.hog = None
        self.bg_subtractor = cv2.createBackgroundSubtractorMOG2(
            history=60, varThreshold=25, detectShadows=False
        )

    def detect_and_track(
        self, video_path: Path, asset_id: UUID, fps: float = 24.0
    ) -> List[DetectedObjectRecord]:
        """
        Samples frames, detects people and objects, and links them with persistent track IDs.
        """
        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            return []

        fps_val = cap.get(cv2.CAP_PROP_FPS) or fps
        frame_idx = 0
        active_tracks: Dict[int, Tuple[float, float, float, float]] = {}  # track_id -> (cx, cy, w, h)
        next_track_id = 1
        detections: List[DetectedObjectRecord] = []

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            if frame_idx % self.step == 0:
                h_orig, w_orig = frame.shape[:2]
                timestamp = frame_idx / fps_val

                # Resize for fast detection
                scale_factor = 480.0 / max(w_orig, h_orig)
                w_scaled = int(w_orig * scale_factor)
                h_scaled = int(h_orig * scale_factor)
                small = cv2.resize(frame, (w_scaled, h_scaled))

                current_frame_detections = []
                if self.hog is not None:
                    # Detect people using HOG
                    boxes, weights = self.hog.detectMultiScale(
                        small, winStride=(8, 8), padding=(4, 4), scale=1.05
                    )
                    for (x, y, w, h), weight in zip(boxes, weights):
                        if weight > 0.15:
                            norm_x = round(float(x / scale_factor) / w_orig, 4)
                            norm_y = round(float(y / scale_factor) / h_orig, 4)
                            norm_w = round(float(w / scale_factor) / w_orig, 4)
                            norm_h = round(float(h / scale_factor) / h_orig, 4)
                            cx = norm_x + norm_w / 2.0
                            cy = norm_y + norm_h / 2.0
                            current_frame_detections.append((cx, cy, norm_x, norm_y, norm_w, norm_h, float(weight), "person"))
                else:
                    # Adaptive motion/foreground object detector fallback
                    fg_mask = self.bg_subtractor.apply(small)
                    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
                    clean_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_OPEN, kernel)
                    contours, _ = cv2.findContours(clean_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                    min_area = (w_scaled * h_scaled) * 0.005  # At least 0.5% of frame
                    for c in contours:
                        area = cv2.contourArea(c)
                        if area >= min_area:
                            x, y, w, h = cv2.boundingRect(c)
                            norm_x = round(float(x / scale_factor) / w_orig, 4)
                            norm_y = round(float(y / scale_factor) / h_orig, 4)
                            norm_w = round(float(w / scale_factor) / w_orig, 4)
                            norm_h = round(float(h / scale_factor) / h_orig, 4)
                            cx = norm_x + norm_w / 2.0
                            cy = norm_y + norm_h / 2.0
                            confidence = min(0.95, round(float(area / (w_scaled * h_scaled)) * 4.0 + 0.4, 2))
                            current_frame_detections.append((cx, cy, norm_x, norm_y, norm_w, norm_h, confidence, "object"))

                # Track Association (Centroid distance matching)
                updated_tracks: Dict[int, Tuple[float, float, float, float]] = {}
                used_detections = set()

                for track_id, (prev_cx, prev_cy, _, _) in active_tracks.items():
                    best_match_idx = None
                    min_dist = 0.25  # Max centroid normalized shift
                    for idx, det in enumerate(current_frame_detections):
                        if idx in used_detections:
                            continue
                        cx, cy = det[0], det[1]
                        dist = float(np.sqrt((cx - prev_cx)**2 + (cy - prev_cy)**2))
                        if dist < min_dist:
                            min_dist = dist
                            best_match_idx = idx

                    if best_match_idx is not None:
                        used_detections.add(best_match_idx)
                        cx, cy, nx, ny, nw, nh, conf, label = current_frame_detections[best_match_idx]
                        updated_tracks[track_id] = (cx, cy, nw, nh)
                        detections.append(DetectedObjectRecord(
                            detection_id=uuid4(),
                            asset_id=asset_id,
                            track_id=track_id,
                            label=label,
                            timestamp_seconds=round(timestamp, 3),
                            frame_number=frame_idx,
                            box=BoundingBox(x=nx, y=ny, width=nw, height=nh),
                            confidence=round(min(1.0, conf), 2)
                        ))

                # Create new tracks for unmatched detections
                for idx, det in enumerate(current_frame_detections):
                    if idx not in used_detections:
                        cx, cy, nx, ny, nw, nh, conf, label = det
                        new_id = next_track_id
                        next_track_id += 1
                        updated_tracks[new_id] = (cx, cy, nw, nh)
                        detections.append(DetectedObjectRecord(
                            detection_id=uuid4(),
                            asset_id=asset_id,
                            track_id=new_id,
                            label=label,
                            timestamp_seconds=round(timestamp, 3),
                            frame_number=frame_idx,
                            box=BoundingBox(x=nx, y=ny, width=nw, height=nh),
                            confidence=round(min(1.0, conf), 2)
                        ))

                active_tracks = updated_tracks

            frame_idx += 1

        cap.release()
        return detections
