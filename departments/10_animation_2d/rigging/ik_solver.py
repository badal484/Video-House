"""
2D Analytical Inverse Kinematics (IK) Solver
Computes exact joint rotations for 2-bone kinematic chains (arms, legs)
using the Law of Cosines with hyperextension reach clamping.
"""
from typing import Any, Dict, Optional, Tuple
import numpy as np


class IKSolver2D:
    """
    Analytical 2-bone Inverse Kinematics solver.
    Solves for joint angles given root position, bone lengths, target position, and bend polarity.
    """

    @staticmethod
    def solve_2bone_ik(
        root_pos: Tuple[float, float],
        target_pos: Tuple[float, float],
        length_upper: float,
        length_lower: float,
        bend_positive: bool = True,
    ) -> Dict[str, Any]:
        """
        Solves 2-bone IK.
        Returns:
            {
                'success': bool,
                'angle_upper_deg': float,
                'angle_lower_deg': float,
                'elbow_pos': (x, y),
                'clamped': bool
            }
        """
        x0, y0 = root_pos
        xt, yt = target_pos
        dx = xt - x0
        dy = yt - y0
        dist = np.hypot(dx, dy)

        max_reach = (length_upper + length_lower) * 0.9999
        min_reach = abs(length_upper - length_lower) * 1.0001
        is_clamped = False

        if dist > max_reach:
            dist = max_reach
            is_clamped = True
        elif dist < min_reach:
            dist = max(min_reach, 1e-4)
            is_clamped = True

        # Angle of direct vector from root to target
        base_angle = np.arctan2(dy, dx)

        # Law of Cosines for elbow/knee angle (theta_lower)
        # c^2 = a^2 + b^2 - 2ab*cos(C)
        cos_elbow = (length_upper**2 + length_lower**2 - dist**2) / (2.0 * length_upper * length_lower)
        cos_elbow = np.clip(cos_elbow, -1.0, 1.0)
        elbow_angle_internal = np.arccos(cos_elbow)

        # Law of Cosines for shoulder offset angle (alpha)
        cos_shoulder = (length_upper**2 + dist**2 - length_lower**2) / (2.0 * length_upper * dist)
        cos_shoulder = np.clip(cos_shoulder, -1.0, 1.0)
        shoulder_offset = np.arccos(cos_shoulder)

        polarity = 1.0 if bend_positive else -1.0
        angle_upper = base_angle + (shoulder_offset * polarity)
        angle_lower = (np.pi - elbow_angle_internal) * (-polarity)

        # Compute intermediate elbow joint position
        elbow_x = x0 + length_upper * np.cos(angle_upper)
        elbow_y = y0 + length_upper * np.sin(angle_upper)

        return {
            "success": True,
            "angle_upper_deg": float(np.degrees(angle_upper)),
            "angle_lower_deg": float(np.degrees(angle_lower)),
            "elbow_pos": (float(elbow_x), float(elbow_y)),
            "clamped": is_clamped,
        }

