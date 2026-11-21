"""
Multiplane Parallax Background Engine
Renders multi-layered anime environments with depth-scaled scrolling velocities.
"""
from typing import Any, Dict, List, Optional, Tuple
import cv2
import numpy as np


class MultiplaneBackgroundEngine:
    """
    Renders multiplane background environments (Foreground, Midground, Distant Skyline, Sky)
    with accurate parallax scroll speeds.
    """

    @staticmethod
    def render_parallax_frame(
        canvas_shape: Tuple[int, int] = (1080, 1920),  # (H, W)
        camera_offset_x: float = 0.0,
        time_of_day: str = "SUNSET",  # "DAY", "SUNSET", "NIGHT"
    ) -> np.ndarray:
        """
        Renders a stylized anime landscape/cityscape across 4 depth planes.
        Returns 4-channel BGRA uint8 image.
        """
        h, w = canvas_shape
        out = np.zeros((h, w, 4), dtype=np.uint8)

        # 1. Sky Plane (Depth z = 10.0, static/near-zero scroll)
        # Gradient background
        if time_of_day.upper() == "SUNSET":
            top_color = np.array([120, 50, 40], dtype=np.float32)    # Deep purple/blue BGR
            bot_color = np.array([30, 140, 240], dtype=np.float32)   # Vibrant orange BGR
        elif time_of_day.upper() == "NIGHT":
            top_color = np.array([35, 15, 10], dtype=np.float32)
            bot_color = np.array([70, 35, 25], dtype=np.float32)
        else:  # DAY
            top_color = np.array([230, 160, 50], dtype=np.float32)   # Blue sky BGR
            bot_color = np.array([245, 220, 180], dtype=np.float32)

        for y in range(h):
            t = y / float(h)
            c = (top_color * (1.0 - t) + bot_color * t).astype(np.uint8)
            out[y, :, :3] = c
        out[:, :, 3] = 255

        # Draw sunset sun / moon
        sun_center = (int(w * 0.75), int(h * 0.45))
        cv2.circle(out, sun_center, 65, (180, 240, 255, 255), -1, cv2.LINE_AA)

        # 2. Distant Mountains / Skyline (Depth z = 4.0, scroll speed = 0.20)
        scroll_dist = int(camera_offset_x * 0.20) % w
        pts_mountains = []
        for x in range(0, w + 100, 80):
            shifted_x = (x - scroll_dist)
            m_h = int(h * 0.55 + np.sin(x * 0.008) * 70.0 + np.cos(x * 0.015) * 40.0)
            pts_mountains.append((shifted_x, m_h))
        pts_mountains = [( -100, h)] + pts_mountains + [(w + 100, h)]
        poly_m = np.array(pts_mountains, dtype=np.int32)
        cv2.fillPoly(out, [poly_m], (70, 40, 60, 255))

        # 3. Midground City Buildings (Depth z = 1.5, scroll speed = 0.40)
        scroll_mid = int(camera_offset_x * 0.40) % 300
        mid_y = int(h * 0.68)
        # Draw series of building rectangles
        b_x = -scroll_mid - 200
        while b_x < w + 200:
            bw = 120
            bh = 220 + int((abs(b_x) % 7) * 35)
            cv2.rectangle(out, (b_x, mid_y - bh), (b_x + bw, h), (45, 30, 40, 255), -1)
            cv2.rectangle(out, (b_x, mid_y - bh), (b_x + bw, h), (30, 20, 25, 255), 2)
            # Glowing anime windows
            for wy in range(mid_y - bh + 25, mid_y - 20, 40):
                for wx in range(b_x + 15, b_x + bw - 15, 25):
                    if (wx + wy) % 3 == 0:
                        cv2.rectangle(out, (wx, wy), (wx + 12, wy + 20), (80, 220, 255, 255), -1)
            b_x += bw + 30

        # 4. Foreground Street & Railing (Depth z = 0.5, scroll speed = 0.67)
        scroll_fg = int(camera_offset_x * 0.67) % 150
        street_y = int(h * 0.85)
        cv2.rectangle(out, (0, street_y), (w, h), (25, 20, 25, 255), -1)
        # Railing posts
        for rx in range(-scroll_fg - 100, w + 100, 60):
            cv2.line(out, (rx, street_y - 45), (rx, street_y), (60, 60, 70, 255), 4)
        cv2.line(out, (0, street_y - 45), (w, street_y - 45), (75, 75, 85, 255), 5)

        return out

