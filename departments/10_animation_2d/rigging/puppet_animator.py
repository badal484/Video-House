"""
2D Puppet Animator
Renders skeletal bones, evaluates cut-out sprite mapping, and computes walk cycle dynamics.
"""
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4
import cv2
import numpy as np

from .bone_models import BoneNode, CharacterRig
from ..characters.character_models import CharacterIdentity


class PuppetAnimator:
    """
    Animates 2D puppet character rigs and generates procedural motion cycles.
    """

    @staticmethod
    def build_standard_humanoid_rig(
        character: CharacterIdentity,
        root_origin: Tuple[float, float] = (500.0, 300.0),
    ) -> CharacterRig:
        """
        Constructs a standard 12-bone humanoid 2D skeletal rig proportioned to character.head_ratio.
        """
        rig = CharacterRig(
            rig_id=str(uuid4()),
            character_id=character.character_id,
            name=f"{character.name}_Rig",
            root_bone_id="pelvis",
        )

        total_h = 450.0
        head_len = total_h / character.head_ratio
        torso_len = head_len * 1.8
        arm_len = head_len * 1.3
        leg_len = head_len * 1.9

        # Pelvis / Root
        rig.add_bone(BoneNode(
            bone_id="pelvis",
            parent_id=None,
            name="Pelvis",
            length=10.0,
            local_position=root_origin,
            local_rotation=-90.0,  # Points upward
        ))

        # Spine & Chest
        rig.add_bone(BoneNode(
            bone_id="spine",
            parent_id="pelvis",
            name="Spine",
            length=torso_len * 0.5,
            local_position=(10.0, 0.0),
            local_rotation=0.0,
        ))
        rig.add_bone(BoneNode(
            bone_id="chest",
            parent_id="spine",
            name="Chest",
            length=torso_len * 0.5,
            local_position=(torso_len * 0.5, 0.0),
            local_rotation=0.0,
        ))

        # Neck & Head
        rig.add_bone(BoneNode(
            bone_id="head",
            parent_id="chest",
            name="Head",
            length=head_len,
            local_position=(torso_len * 0.5, 0.0),
            local_rotation=0.0,
        ))

        # Left Arm (Back Arm in 3/4 view)
        rig.add_bone(BoneNode(
            bone_id="upper_arm_l",
            parent_id="chest",
            name="Upper Arm L",
            length=arm_len * 0.5,
            local_position=(torso_len * 0.45, -25.0),
            local_rotation=120.0,
        ))
        rig.add_bone(BoneNode(
            bone_id="forearm_l",
            parent_id="upper_arm_l",
            name="Forearm L",
            length=arm_len * 0.5,
            local_position=(arm_len * 0.5, 0.0),
            local_rotation=15.0,
        ))

        # Right Arm (Front Arm in 3/4 view)
        rig.add_bone(BoneNode(
            bone_id="upper_arm_r",
            parent_id="chest",
            name="Upper Arm R",
            length=arm_len * 0.5,
            local_position=(torso_len * 0.45, 25.0),
            local_rotation=60.0,
        ))
        rig.add_bone(BoneNode(
            bone_id="forearm_r",
            parent_id="upper_arm_r",
            name="Forearm R",
            length=arm_len * 0.5,
            local_position=(arm_len * 0.5, 0.0),
            local_rotation=-15.0,
        ))

        # Left Leg (Back Leg)
        rig.add_bone(BoneNode(
            bone_id="thigh_l",
            parent_id="pelvis",
            name="Thigh L",
            length=leg_len * 0.5,
            local_position=(0.0, -18.0),
            local_rotation=175.0,
        ))
        rig.add_bone(BoneNode(
            bone_id="shin_l",
            parent_id="thigh_l",
            name="Shin L",
            length=leg_len * 0.5,
            local_position=(leg_len * 0.5, 0.0),
            local_rotation=5.0,
        ))

        # Right Leg (Front Leg)
        rig.add_bone(BoneNode(
            bone_id="thigh_r",
            parent_id="pelvis",
            name="Thigh R",
            length=leg_len * 0.5,
            local_position=(0.0, 18.0),
            local_rotation=185.0,
        ))
        rig.add_bone(BoneNode(
            bone_id="shin_r",
            parent_id="thigh_r",
            name="Shin R",
            length=leg_len * 0.5,
            local_position=(leg_len * 0.5, 0.0),
            local_rotation=-5.0,
        ))

        # Layered draw order (back to front)
        rig.draw_order = [
            "upper_arm_l", "forearm_l",
            "thigh_l", "shin_l",
            "pelvis", "spine", "chest", "head",
            "thigh_r", "shin_r",
            "upper_arm_r", "forearm_r"
        ]
        return rig

    @staticmethod
    def render_rig_skeleton(
        rig: CharacterRig,
        canvas_shape: Tuple[int, int] = (600, 800),  # (H, W)
        draw_joints: bool = True,
        bone_color: Tuple[int, int, int] = (0, 220, 240),  # Amber/Yellow BGR
        joint_color: Tuple[int, int, int] = (255, 255, 255),
    ) -> np.ndarray:
        """
        Renders the hierarchical 2D skeleton to an RGBA canvas.
        """
        h, w = canvas_shape
        canvas = np.zeros((h, w, 4), dtype=np.uint8)
        transforms = rig.compute_world_transforms()

        for b_id in rig.draw_order:
            if b_id not in transforms:
                continue
            t = transforms[b_id]
            pt_start = (int(t["start"][0]), int(t["start"][1]))
            pt_end = (int(t["end"][0]), int(t["end"][1]))

            # Draw bone line with antialiasing
            cv2.line(canvas, pt_start, pt_end, (*bone_color, 255), 4, cv2.LINE_AA)

            if draw_joints:
                cv2.circle(canvas, pt_start, 6, (*joint_color, 255), -1, cv2.LINE_AA)
                cv2.circle(canvas, pt_start, 6, (40, 40, 50, 255), 1, cv2.LINE_AA)

        return canvas

    @staticmethod
    def generate_walk_cycle_frame(
        rig: CharacterRig,
        cycle_phase: float,  # Normalized 0.0 to 1.0 (phase through walk loop)
    ) -> None:
        """
        Modifies rig bone local rotations to generate an authentic 2D walk cycle pose.
        Uses harmonic trigonometric curves:
        - Legs oscillate in counter-phase.
        - Arms oscillate opposite to corresponding legs.
        - Pelvis oscillates vertically (double frequency: contact low, pass high).
        """
        phase_rad = cycle_phase * 2.0 * np.pi

        # Leg swing amplitude (degrees)
        thigh_amp = 32.0
        shin_amp = 25.0

        # Right leg (Phase 0)
        rig.bones["thigh_r"].local_rotation = 180.0 + thigh_amp * np.sin(phase_rad)
        rig.bones["shin_r"].local_rotation = max(0.0, shin_amp * np.sin(phase_rad - 0.8))

        # Left leg (Phase pi - counter-phase)
        rig.bones["thigh_l"].local_rotation = 180.0 + thigh_amp * np.sin(phase_rad + np.pi)
        rig.bones["shin_l"].local_rotation = max(0.0, shin_amp * np.sin(phase_rad + np.pi - 0.8))

        # Arm swing (opposite to legs)
        arm_amp = 28.0
        rig.bones["upper_arm_r"].local_rotation = 60.0 - arm_amp * np.sin(phase_rad)
        rig.bones["forearm_r"].local_rotation = -15.0 - (arm_amp * 0.4) * np.sin(phase_rad)

        rig.bones["upper_arm_l"].local_rotation = 120.0 + arm_amp * np.sin(phase_rad)
        rig.bones["forearm_l"].local_rotation = 15.0 + (arm_amp * 0.4) * np.sin(phase_rad)

        # Subtle spine bounce and tilt
        rig.bones["spine"].local_rotation = 4.0 * np.sin(phase_rad)

