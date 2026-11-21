"""
Facial Animation & Dialogue Lip-Sync Engine
Generates phonetic mouth visemes from speech timestamps and computes natural eye blinks.
"""
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
import cv2
import numpy as np


class VisemeType(str, Enum):
    REST = "REST"      # Neutral closed
    AI_A = "AI_A"      # Wide open (A, I)
    E_EE = "E_EE"      # Stretched horizontal smile (E)
    O_OH = "O_OH"      # Rounded large circle (O)
    U_OO = "U_OO"      # Pursed small circle (U, W)
    M_B_P = "M_B_P"    # Compressed closed lips (M, B, P)
    F_V = "F_V"        # Lower lip tucked (F, V)
    L_TH = "L_TH"      # Tongue behind teeth (L, TH)


class FacialAnimator:
    """
    Renders synchronized dialogue mouth shapes and realistic eye blink cycles.
    """

    @staticmethod
    def render_viseme(
        canvas_shape: Tuple[int, int] = (80, 100),  # (H, W)
        viseme: VisemeType = VisemeType.REST,
        mouth_scale: float = 1.0,
        skin_color: Tuple[int, int, int] = (210, 225, 245),  # BGR
    ) -> np.ndarray:
        """
        Renders a clean anime mouth sprite with alpha transparency for the specified viseme.
        """
        h, w = canvas_shape
        out = np.zeros((h, w, 4), dtype=np.uint8)
        cx, cy = w // 2, h // 2

        line_col = (40, 40, 50, 255)
        inside_mouth_col = (60, 40, 140, 255)  # Dark red/pink mouth cavity
        teeth_col = (250, 250, 255, 255)

        if viseme == VisemeType.REST:
            # Closed line with slight center dip
            cv2.line(out, (cx - 20, cy), (cx + 20, cy), line_col, 2, cv2.LINE_AA)
        elif viseme == VisemeType.AI_A:
            # Wide open mouth
            cv2.ellipse(out, (cx, cy), (22, 16), 0, 0, 360, inside_mouth_col, -1, cv2.LINE_AA)
            cv2.ellipse(out, (cx, cy), (22, 16), 0, 0, 360, line_col, 2, cv2.LINE_AA)
            # Upper teeth
            cv2.rectangle(out, (cx - 14, cy - 14), (cx + 14, cy - 8), teeth_col, -1)
        elif viseme == VisemeType.O_OH:
            # Tall rounded mouth
            cv2.ellipse(out, (cx, cy), (14, 18), 0, 0, 360, inside_mouth_col, -1, cv2.LINE_AA)
            cv2.ellipse(out, (cx, cy), (14, 18), 0, 0, 360, line_col, 2, cv2.LINE_AA)
        elif viseme == VisemeType.E_EE:
            # Stretched wide flat open
            cv2.ellipse(out, (cx, cy), (26, 9), 0, 0, 360, inside_mouth_col, -1, cv2.LINE_AA)
            cv2.ellipse(out, (cx, cy), (26, 9), 0, 0, 360, line_col, 2, cv2.LINE_AA)
            cv2.rectangle(out, (cx - 18, cy - 4), (cx + 18, cy + 2), teeth_col, -1)
        elif viseme == VisemeType.U_OO:
            # Small puckered circle
            cv2.circle(out, (cx, cy), 9, inside_mouth_col, -1, cv2.LINE_AA)
            cv2.circle(out, (cx, cy), 9, line_col, 2, cv2.LINE_AA)
        elif viseme == VisemeType.M_B_P:
            # Compressed horizontal line
            cv2.line(out, (cx - 18, cy), (cx + 18, cy), line_col, 3, cv2.LINE_AA)
        else:
            # Default slightly parted mouth
            cv2.ellipse(out, (cx, cy), (16, 8), 0, 0, 360, inside_mouth_col, -1, cv2.LINE_AA)
            cv2.ellipse(out, (cx, cy), (16, 8), 0, 0, 360, line_col, 2, cv2.LINE_AA)

        return out

    @staticmethod
    def compute_blink_aperture(frame_index: int, fps: float = 24.0) -> float:
        """
        Computes eye aperture $[0.0, 1.0]$ with realistic periodic blinks every 3.0 seconds (72 frames).
        A blink lasts ~4 frames (closing 1f, closed 2f, opening 1f).
        """
        cycle_len = int(fps * 3.0)
        offset = frame_index % cycle_len

        if offset == 0:
            return 0.5  # Half closed
        elif offset in (1, 2):
            return 0.0  # Fully closed
        elif offset == 3:
            return 0.7  # Opening
        return 1.0     # Normal open eyes
