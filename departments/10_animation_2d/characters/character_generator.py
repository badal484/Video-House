"""
Character Generator Service
Synthesizes structured character concepts, 5-view turnaround model sheets,
expression matrices, and pose presets from creative briefs.
"""
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4
import cv2
import numpy as np

from .character_models import (
    CharacterIdentity,
    ModelSheet,
    CharacterPose,
    ExpressionType,
    PoseType,
    IdentityStatus,
)


class CharacterGenerator:
    """
    Automates the initial character design and Settei turnaround creation pipeline.
    """

    @staticmethod
    def create_character_concept(
        project_id: str,
        name: str,
        brief_text: str,
        head_ratio: float = 7.0,
        visual_style: str = "ANIME_CEL",
        custom_palette: Optional[Dict[str, str]] = None,
    ) -> CharacterIdentity:
        """
        Parses brief text and instantiates a structured CharacterIdentity.
        """
        palette = {
            "skin_base": "#f8d5c2",
            "skin_shadow": "#dca894",
            "hair_base": "#1a2238",
            "hair_highlight": "#3b558c",
            "eye_iris": "#2b7cd3",
            "costume_primary": "#1f2937",
            "costume_accent": "#f59e0b",
        }
        if custom_palette:
            palette.update(custom_palette)

        features = []
        if "bangs" in brief_text.lower() or "hair" in brief_text.lower():
            features.append("Stylized parted anime hair silhouette")
        if "jacket" in brief_text.lower() or "coat" in brief_text.lower():
            features.append("High-collar jacket with accent piping")
        if "glasses" in brief_text.lower():
            features.append("Rectangular thin-frame glasses")
        if not features:
            features.append("Distinctive high-contrast eye iris and highlight")

        char = CharacterIdentity(
            character_id=str(uuid4()),
            project_id=project_id,
            name=name,
            visual_style=visual_style,
            head_ratio=head_ratio,
            color_palette=palette,
            distinctive_features=features,
            personality=brief_text,
            status=IdentityStatus.APPROVED,
        )
        return char

    @staticmethod
    def generate_turnaround_model_sheet(
        character: CharacterIdentity,
        resolution: Tuple[int, int] = (1920, 1080),
    ) -> Tuple[ModelSheet, np.ndarray]:
        """
        Generates a 5-angle turnaround sheet (Front, 3/4, Profile, Back, Close-up)
        with horizontal alignment guides (head, eyes, hips, heels).
        Returns (ModelSheet, contact_sheet_bgr).
        """
        w, h = resolution
        sheet_canvas = np.full((h, w, 3), 245, dtype=np.uint8)  # Off-white Settei paper background

        # Draw Title Banner
        cv2.putText(sheet_canvas, f"SETTEI / MODEL SHEET: {character.name.upper()}", (60, 60),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.1, (30, 30, 30), 2)
        cv2.putText(sheet_canvas, f"STYLE: {character.visual_style} | RATIO: {character.head_ratio:.1f} HEADS | VERSION: {character.version}",
                    (60, 95), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (100, 100, 100), 1)

        # Alignment Guide Y positions
        top_y = 180
        total_h = 700
        head_h = int(total_h / character.head_ratio)
        eye_y = top_y + int(head_h * 0.55)
        chin_y = top_y + head_h
        shoulder_y = top_y + int(head_h * 1.35)
        hip_y = top_y + int(head_h * 3.5)
        knee_y = top_y + int(head_h * 5.2)
        ankle_y = top_y + total_h

        guides = {
            "top_of_head": float(top_y),
            "eye_line": float(eye_y),
            "chin": float(chin_y),
            "shoulder": float(shoulder_y),
            "hip": float(hip_y),
            "knee": float(knee_y),
            "ankle": float(ankle_y),
        }

        # Draw subtle horizontal guide lines across entire sheet
        for g_name, g_y in guides.items():
            cv2.line(sheet_canvas, (40, int(g_y)), (w - 40, int(g_y)), (215, 215, 225), 1)
            cv2.putText(sheet_canvas, g_name.replace("_", " ").upper(), (w - 180, int(g_y) - 5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.4, (160, 160, 170), 1)

        # Define 5 horizontal slots for views
        slot_w = (w - 120) // 5
        views = [
            ("FRONT (0 DEG)", 60 + slot_w * 0, "front"),
            ("3/4 VIEW (45 DEG)", 60 + slot_w * 1, "three_quarter"),
            ("PROFILE (90 DEG)", 60 + slot_w * 2, "side"),
            ("BACK (180 DEG)", 60 + slot_w * 3, "back"),
            ("HEAD CLOSE-UP", 60 + slot_w * 4, "close_up"),
        ]

        # Draw stylized anime silhouette representation in each slot
        for label, x_start, angle_mode in views:
            center_x = x_start + slot_w // 2
            cv2.putText(sheet_canvas, label, (center_x - 65, top_y - 20),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, (50, 50, 60), 2)

            if angle_mode == "close_up":
                # Render large head portrait
                face_center = (center_x, top_y + 200)
                face_r = 110
                cv2.circle(sheet_canvas, face_center, face_r, (210, 225, 245), -1)  # Skin tone BGR
                cv2.circle(sheet_canvas, face_center, face_r, (40, 40, 50), 2)      # Line art
                # Hair cap
                cv2.ellipse(sheet_canvas, (center_x, face_center[1] - 40), (face_r, int(face_r * 0.9)),
                            0, 180, 360, (50, 30, 25), -1)  # Hair dark BGR
                # Eyes
                cv2.circle(sheet_canvas, (center_x - 35, face_center[1]), 16, (210, 120, 40), -1)  # Iris
                cv2.circle(sheet_canvas, (center_x + 35, face_center[1]), 16, (210, 120, 40), -1)
                cv2.circle(sheet_canvas, (center_x - 30, face_center[1] - 4), 5, (255, 255, 255), -1)  # Highlight
                cv2.circle(sheet_canvas, (center_x + 40, face_center[1] - 4), 5, (255, 255, 255), -1)
                # Mouth smile
                cv2.ellipse(sheet_canvas, (center_x, face_center[1] + 55), (25, 12), 0, 0, 180, (40, 40, 50), 2)
            else:
                # Render full-body proportioned figure
                head_center = (center_x, top_y + head_h // 2)
                # Head
                cv2.circle(sheet_canvas, head_center, head_h // 2, (210, 225, 245), -1)
                cv2.circle(sheet_canvas, head_center, head_h // 2, (40, 40, 50), 2)
                # Hair
                cv2.ellipse(sheet_canvas, (center_x, head_center[1] - 10), (head_h // 2, int(head_h * 0.45)),
                            0, 180, 360, (50, 30, 25), -1)
                # Torso / Jacket
                cv2.rectangle(sheet_canvas, (center_x - 35, shoulder_y), (center_x + 35, hip_y), (55, 40, 30), -1)
                cv2.rectangle(sheet_canvas, (center_x - 35, shoulder_y), (center_x + 35, hip_y), (40, 40, 50), 2)
                # Collar / Accent
                cv2.line(sheet_canvas, (center_x, shoulder_y), (center_x, hip_y), (20, 150, 240), 2)
                # Legs / Trousers
                cv2.rectangle(sheet_canvas, (center_x - 30, hip_y), (center_x - 6, ankle_y), (30, 30, 40), -1)
                cv2.rectangle(sheet_canvas, (center_x + 6, hip_y), (center_x + 30, ankle_y), (30, 30, 40), -1)
                # Arms
                cv2.line(sheet_canvas, (center_x - 35, shoulder_y + 10), (center_x - 50, hip_y + 20), (55, 40, 30), 8)
                cv2.line(sheet_canvas, (center_x + 35, shoulder_y + 10), (center_x + 50, hip_y + 20), (55, 40, 30), 8)

        # Draw Color Swatches (Palette) in bottom left
        cv2.putText(sheet_canvas, "COLOR PALETTE (TOKUSYOKU):", (60, h - 70), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (60, 60, 70), 2)
        px_x = 60
        for p_name, p_hex in character.color_palette.items():
            # Convert hex to BGR
            h_str = p_hex.lstrip("#")
            rgb = tuple(int(h_str[i : i + 2], 16) for i in (0, 2, 4))
            bgr = (rgb[2], rgb[1], rgb[0])
            cv2.rectangle(sheet_canvas, (px_x, h - 55), (px_x + 35, h - 20), bgr, -1)
            cv2.rectangle(sheet_canvas, (px_x, h - 55), (px_x + 35, h - 20), (40, 40, 50), 1)
            cv2.putText(sheet_canvas, p_name[:4], (px_x, h - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (80, 80, 90), 1)
            px_x += 55

        sheet = ModelSheet(
            model_sheet_id=str(uuid4()),
            character_id=character.character_id,
            name=f"{character.name}_Turnaround",
            alignment_guides=guides,
        )
        return sheet, sheet_canvas

    @staticmethod
    def generate_expression_matrix(
        character: CharacterIdentity,
    ) -> List[Tuple[ExpressionType, np.ndarray]]:
        """
        Generates 5 facial expressions (Neutral, Happy, Sad, Angry, Surprised)
        as 200x200 pixel RGBA frames.
        """
        expressions = [
            ExpressionType.NEUTRAL,
            ExpressionType.HAPPY,
            ExpressionType.SAD,
            ExpressionType.ANGRY,
            ExpressionType.SURPRISED,
        ]
        results = []

        for expr in expressions:
            img = np.zeros((200, 200, 4), dtype=np.uint8)
            # Head circle
            cv2.circle(img, (100, 100), 70, (210, 225, 245, 255), -1)
            cv2.circle(img, (100, 100), 70, (40, 40, 50, 255), 2)
            # Hair
            cv2.ellipse(img, (100, 80), (70, 45), 0, 180, 360, (50, 30, 25, 255), -1)

            # Expression-specific eyes and mouth
            if expr == ExpressionType.NEUTRAL:
                cv2.circle(img, (75, 95), 10, (210, 120, 40, 255), -1)
                cv2.circle(img, (125, 95), 10, (210, 120, 40, 255), -1)
                cv2.line(img, (88, 140), (112, 140), (40, 40, 50, 255), 2)
            elif expr == ExpressionType.HAPPY:
                cv2.ellipse(img, (75, 95), (12, 8), 0, 180, 360, (40, 40, 50, 255), 2)
                cv2.ellipse(img, (125, 95), (12, 8), 0, 180, 360, (40, 40, 50, 255), 2)
                cv2.ellipse(img, (100, 135), (18, 12), 0, 0, 180, (40, 40, 50, 255), 2)
            elif expr == ExpressionType.SAD:
                cv2.circle(img, (75, 100), 9, (210, 120, 40, 255), -1)
                cv2.circle(img, (125, 100), 9, (210, 120, 40, 255), -1)
                cv2.ellipse(img, (100, 145), (16, 8), 0, 180, 360, (40, 40, 50, 255), 2)
            elif expr == ExpressionType.ANGRY:
                # Slanted eyebrows
                cv2.line(img, (60, 82), (90, 95), (40, 40, 50, 255), 3)
                cv2.line(img, (140, 82), (110, 95), (40, 40, 50, 255), 3)
                cv2.circle(img, (75, 100), 8, (210, 120, 40, 255), -1)
                cv2.circle(img, (125, 100), 8, (210, 120, 40, 255), -1)
                cv2.line(img, (85, 142), (115, 138), (40, 40, 50, 255), 3)
            elif expr == ExpressionType.SURPRISED:
                cv2.circle(img, (75, 95), 14, (210, 120, 40, 255), -1)
                cv2.circle(img, (125, 95), 14, (210, 120, 40, 255), -1)
                cv2.circle(img, (100, 142), 10, (40, 40, 50, 255), 2)

            results.append((expr, img))
        return results

    @staticmethod
    def generate_pose_library(
        character: CharacterIdentity,
    ) -> List[CharacterPose]:
        """
        Generates standard pose library: Standing, Walking, Running, Sitting, Jumping.
        """
        poses = [
            CharacterPose(
                pose_id=str(uuid4()),
                character_id=character.character_id,
                pose_type=PoseType.STANDING,
                name="Standing Neutral",
                joint_angles={"torso": 0.0, "shoulder_l": 10.0, "shoulder_r": -10.0, "hip_l": 0.0, "hip_r": 0.0},
            ),
            CharacterPose(
                pose_id=str(uuid4()),
                character_id=character.character_id,
                pose_type=PoseType.WALKING,
                name="Walk Contact",
                joint_angles={"torso": 5.0, "shoulder_l": -25.0, "shoulder_r": 25.0, "hip_l": 30.0, "hip_r": -25.0, "knee_r": 15.0},
            ),
            CharacterPose(
                pose_id=str(uuid4()),
                character_id=character.character_id,
                pose_type=PoseType.RUNNING,
                name="Run Stride",
                joint_angles={"torso": 15.0, "shoulder_l": -50.0, "shoulder_r": 45.0, "hip_l": 55.0, "hip_r": -40.0, "knee_r": 60.0},
            ),
            CharacterPose(
                pose_id=str(uuid4()),
                character_id=character.character_id,
                pose_type=PoseType.SITTING,
                name="Sitting Bench",
                joint_angles={"torso": 0.0, "hip_l": 90.0, "hip_r": 90.0, "knee_l": 90.0, "knee_r": 90.0},
            ),
            CharacterPose(
                pose_id=str(uuid4()),
                character_id=character.character_id,
                pose_type=PoseType.JUMPING,
                name="Jump Apex",
                joint_angles={"torso": -10.0, "shoulder_l": -140.0, "shoulder_r": -140.0, "hip_l": 20.0, "hip_r": 20.0, "knee_l": 45.0, "knee_r": 45.0},
            ),
        ]
        return poses
