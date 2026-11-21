"""
Point & Feature Tracking Module
Implements Shi-Tomasi corner detection and Lucas-Kanade optical flow tracking.
"""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
import cv2
import numpy as np


@dataclass
class TrackedPoint:
    point_id: int
    frame_index: int
    x: float
    y: float
    status: int  # 1 = tracked, 0 = lost
    error: float = 0.0


@dataclass
class TrackSequence:
    points: List[TrackedPoint] = field(default_factory=list)

    def get_positions(self) -> List[Tuple[float, float]]:
        return [(p.x, p.y) for p in self.points if p.status == 1]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "points": [
                {
                    "point_id": p.point_id,
                    "frame_index": p.frame_index,
                    "x": p.x,
                    "y": p.y,
                    "status": p.status,
                    "error": p.error,
                }
                for p in self.points
            ]
        }


class FeatureTracker:
    """
    Tracks 2D feature points across a sequence of image frames.
    """
    def __init__(
        self,
        max_corners: int = 100,
        quality_level: float = 0.01,
        min_distance: float = 10.0,
        block_size: int = 7,
    ):
        self.max_corners = max_corners
        self.quality_level = quality_level
        self.min_distance = min_distance
        self.block_size = block_size

    def detect_features(self, frame: np.ndarray, mask: Optional[np.ndarray] = None) -> np.ndarray:
        """
        Detects strong corners using Shi-Tomasi detector.
        Returns array of shape (N, 1, 2).
        """
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY) if frame.ndim == 3 else frame
        corners = cv2.goodFeaturesToTrack(
            gray,
            maxCorners=self.max_corners,
            qualityLevel=self.quality_level,
            minDistance=self.min_distance,
            blockSize=self.block_size,
            mask=mask,
        )
        if corners is None:
            return np.empty((0, 1, 2), dtype=np.float32)
        return corners

    def track_sequence(
        self,
        frames: List[np.ndarray],
        initial_points: Optional[np.ndarray] = None,
    ) -> List[TrackSequence]:
        """
        Tracks points across consecutive frames using Pyramidal Lucas-Kanade.
        """
        if not frames:
            return []

        if initial_points is None or len(initial_points) == 0:
            initial_points = self.detect_features(frames[0])

        if len(initial_points) == 0:
            return []

        num_points = len(initial_points)
        sequences = [TrackSequence() for _ in range(num_points)]

        prev_gray = cv2.cvtColor(frames[0], cv2.COLOR_BGR2GRAY) if frames[0].ndim == 3 else frames[0]
        curr_pts = initial_points.astype(np.float32)

        for i in range(num_points):
            sequences[i].points.append(
                TrackedPoint(
                    point_id=i,
                    frame_index=0,
                    x=float(curr_pts[i, 0, 0]),
                    y=float(curr_pts[i, 0, 1]),
                    status=1,
                    error=0.0,
                )
            )

        lk_params = dict(
            winSize=(21, 21),
            maxLevel=3,
            criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 30, 0.01),
        )

        for frame_idx in range(1, len(frames)):
            frame = frames[frame_idx]
            curr_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY) if frame.ndim == 3 else frame

            next_pts, status, err = cv2.calcOpticalFlowPyrLK(
                prev_gray, curr_gray, curr_pts, None, **lk_params
            )

            for i in range(num_points):
                st = int(status[i, 0]) if status is not None else 0
                error_val = float(err[i, 0]) if err is not None else 0.0
                if st == 1:
                    x = float(next_pts[i, 0, 0])
                    y = float(next_pts[i, 0, 1])
                else:
                    x = float(curr_pts[i, 0, 0])
                    y = float(curr_pts[i, 0, 1])

                sequences[i].points.append(
                    TrackedPoint(
                        point_id=i,
                        frame_index=frame_idx,
                        x=x,
                        y=y,
                        status=st,
                        error=error_val,
                    )
                )

            curr_pts = next_pts
            prev_gray = curr_gray

        return sequences
