"""
Keyframe Interpolation Engine.
Evaluates animated property curves (opacity, volume, scale, rotation, pan, etc.)
at any arbitrary RationalTime position with support for LINEAR, EASE_IN,
EASE_OUT, EASE_IN_OUT, and HOLD interpolation modes.
"""
import math
from typing import List, Optional
from core.timeline.time_model import RationalTime
from core.timeline.timeline_models import InterpolationMode, Keyframe


class KeyframeInterpolator:
    """
    Evaluates keyframed properties along a timeline.
    """

    @staticmethod
    def evaluate(keyframes: List[Keyframe], query_time: RationalTime, default_value: float = 1.0) -> float:
        if not keyframes:
            return default_value

        sorted_kfs = sorted(keyframes, key=lambda k: k.time.to_seconds())

        q_sec = query_time.to_seconds()
        first_kf = sorted_kfs[0]
        last_kf = sorted_kfs[-1]

        # Prior to first keyframe
        if q_sec <= first_kf.time.to_seconds():
            return first_kf.value

        # Past last keyframe
        if q_sec >= last_kf.time.to_seconds():
            return last_kf.value

        # Find enclosing pair
        for i in range(len(sorted_kfs) - 1):
            kf_a = sorted_kfs[i]
            kf_b = sorted_kfs[i + 1]

            t_a = kf_a.time.to_seconds()
            t_b = kf_b.time.to_seconds()

            if t_a <= q_sec <= t_b:
                if abs(t_b - t_a) < 1e-6:
                    return kf_b.value

                norm_t = (q_sec - t_a) / (t_b - t_a)
                mode = kf_a.interpolation

                if mode == InterpolationMode.HOLD:
                    return kf_a.value
                elif mode == InterpolationMode.LINEAR:
                    factor = norm_t
                elif mode == InterpolationMode.EASE_IN:
                    # Quadratic ease in: t^2
                    factor = norm_t * norm_t
                elif mode == InterpolationMode.EASE_OUT:
                    # Quadratic ease out: 1 - (1 - t)^2
                    factor = 1.0 - (1.0 - norm_t) * (1.0 - norm_t)
                elif mode == InterpolationMode.EASE_IN_OUT:
                    # Smooth sinusoidal or cubic s-curve
                    factor = 0.5 * (1.0 - math.cos(math.pi * norm_t))
                else:
                    factor = norm_t

                return kf_a.value + (kf_b.value - kf_a.value) * factor

        return default_value
