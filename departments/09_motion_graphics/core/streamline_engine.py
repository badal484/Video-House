"""
Biometric Vascular Streamline & Flow Simulation Engine.
Department: 09_motion_graphics/core
Simulates organic cephalopod circulatory flow paths, systolic pulse rings,
and real-time oxygenation particle color-shifting.
"""
import math
from typing import List, Tuple
import numpy as np


class BloodParticle:
    """Individual simulated hemocyanin blood packet moving along a streamline."""

    def __init__(self, streamline_id: int, offset_t: float, speed: float = 1.6):
        self.streamline_id = streamline_id
        self.offset_t = offset_t
        self.speed = speed

    def get_progress(self, current_time: float) -> float:
        """Returns normalized position [0.0, 1.0] along the streamline."""
        return (current_time * self.speed + self.offset_t) % 1.0


class StreamlineEngine:
    """
    Simulates physiological fluid vascular flow between organ chambers and gill arches.
    """

    def __init__(self):
        # Color definitions: Venous Cobalt (Deoxygenated) -> Cyan (Oxygenated)
        self.color_venous = np.array([216, 78, 29], dtype=np.float32)       # BGR for #1D4ED8
        self.color_oxygenated = np.array([255, 240, 0], dtype=np.float32)   # BGR for #00F0FF

    def interpolate_streamline_point(
        self,
        p_start: Tuple[int, int],
        p_end: Tuple[int, int],
        progress: float,
        curvature: float = 0.0
    ) -> Tuple[int, int]:
        """Calculates point along a curved vascular streamline."""
        x0, y0 = p_start
        x1, y1 = p_end
        # Linear base
        x = x0 + progress * (x1 - x0)
        y = y0 + progress * (y1 - y0)
        # Add perpendicular parabolic arc
        dx = x1 - x0
        dy = y1 - y0
        norm_len = math.hypot(dx, dy)
        if norm_len > 0:
            perp_x = -dy / norm_len
            perp_y = dx / norm_len
            arc = math.sin(math.pi * progress) * curvature
            x += perp_x * arc
            y += perp_y * arc
        return int(x), int(y)

    def get_particle_color_bgr(self, progress: float, gill_entry_threshold: float = 0.45) -> Tuple[int, int, int]:
        """
        Dynamically calculates particle color:
        Deoxygenated venous cobalt before gills; shifts to luminous hemocyanin cyan inside/after gills.
        """
        if progress < gill_entry_threshold:
            c = self.color_venous
        else:
            # Smooth oxygenation transition
            blend_pct = min(1.0, (progress - gill_entry_threshold) / 0.25)
            c = (1.0 - blend_pct) * self.color_venous + blend_pct * self.color_oxygenated
        return int(c[0]), int(c[1]), int(c[2])
