"""
AI-Assisted In-Betweening Engine
Interpolates intermediate candidate drawings between approved key poses (Genga),
maintaining stroke continuity and exposure timing on 2s or 3s.
"""
from typing import Any, Dict, List, Optional
import numpy as np


class InBetweenEngine:
    """
    Interpolates bone rotations and spatial properties between key animation poses.
    """

    @staticmethod
    def interpolate_poses(
        pose_start: Dict[str, float],
        pose_end: Dict[str, float],
        t: float,  # Normalized 0.0 to 1.0
        easing: str = "EASE_IN_OUT",
    ) -> Dict[str, float]:
        """
        Interpolates joint angles between pose_start and pose_end using easing curves.
        """
        # Apply easing function
        if easing == "EASE_IN_OUT":
            factor = t * t * (3.0 - 2.0 * t)  # Smoothstep
        elif easing == "EASE_IN":
            factor = t * t
        elif easing == "EASE_OUT":
            factor = t * (2.0 - t)
        else:
            factor = t  # Linear

        interpolated: Dict[str, float] = {}
        all_keys = set(pose_start.keys()).union(set(pose_end.keys()))

        for k in all_keys:
            val_start = pose_start.get(k, 0.0)
            val_end = pose_end.get(k, val_start)
            interpolated[k] = float(val_start + (val_end - val_start) * factor)

        return interpolated

    @staticmethod
    def generate_inbetween_sequence(
        key_poses: List[Dict[str, float]],
        frames_per_transition: int = 8,
        hold_rate: int = 2,  # Step on 2s
    ) -> List[Dict[str, float]]:
        """
        Generates a sequence of poses stepped on hold_rate frames.
        """
        sequence: List[Dict[str, float]] = []
        if not key_poses:
            return []

        for i in range(len(key_poses) - 1):
            p0 = key_poses[i]
            p1 = key_poses[i + 1]

            for f in range(frames_per_transition):
                stepped_f = (f // hold_rate) * hold_rate
                t = stepped_f / float(frames_per_transition)
                pose_f = InBetweenEngine.interpolate_poses(p0, p1, t)
                sequence.append(pose_f)

        sequence.append(key_poses[-1])
        return sequence

