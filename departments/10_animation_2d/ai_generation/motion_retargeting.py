"""
Motion Retargeting Engine
Transfers 2D joint trajectories from driving reference videos or pose trackers
onto 2D character skeletal rigs, scaling to match anatomical proportions.
"""
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
from ..rigging.bone_models import CharacterRig


class MotionRetargeter:
    """
    Retargets external 2D joint coordinates to CharacterRig joint angles.
    """

    @staticmethod
    def retarget_pose(
        joint_points: Dict[str, Tuple[float, float]],
        target_rig: CharacterRig,
    ) -> Dict[str, float]:
        """
        Calculates local bone rotation angles from 2D joint coordinates:
        joint_points: {'pelvis': (x,y), 'chest': (x,y), 'shoulder_l': (x,y), 'elbow_l': (x,y), ...}
        Returns dict: bone_id -> angle in degrees.
        """
        angles: Dict[str, float] = {}

        def get_angle(p1: Tuple[float, float], p2: Tuple[float, float]) -> float:
            dx = p2[0] - p1[0]
            dy = p2[1] - p1[1]
            return float(np.degrees(np.arctan2(dy, dx)))

        if "pelvis" in joint_points and "chest" in joint_points:
            spine_angle = get_angle(joint_points["pelvis"], joint_points["chest"])
            angles["spine"] = float(spine_angle + 90.0)  # Offset from upward normal

        if "shoulder_r" in joint_points and "elbow_r" in joint_points:
            angles["upper_arm_r"] = get_angle(joint_points["shoulder_r"], joint_points["elbow_r"])

        if "elbow_r" in joint_points and "wrist_r" in joint_points:
            angles["forearm_r"] = get_angle(joint_points["elbow_r"], joint_points["wrist_r"])

        if "shoulder_l" in joint_points and "elbow_l" in joint_points:
            angles["upper_arm_l"] = get_angle(joint_points["shoulder_l"], joint_points["elbow_l"])

        if "elbow_l" in joint_points and "wrist_l" in joint_points:
            angles["forearm_l"] = get_angle(joint_points["elbow_l"], joint_points["wrist_l"])

        if "hip_r" in joint_points and "knee_r" in joint_points:
            angles["thigh_r"] = get_angle(joint_points["hip_r"], joint_points["knee_r"])

        if "knee_r" in joint_points and "ankle_r" in joint_points:
            angles["shin_r"] = get_angle(joint_points["knee_r"], joint_points["ankle_r"])

        if "hip_l" in joint_points and "knee_l" in joint_points:
            angles["thigh_l"] = get_angle(joint_points["hip_l"], joint_points["knee_l"])

        if "knee_l" in joint_points and "ankle_l" in joint_points:
            angles["shin_l"] = get_angle(joint_points["knee_l"], joint_points["ankle_l"])

        return angles
