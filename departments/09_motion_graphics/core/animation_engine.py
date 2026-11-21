"""
Procedural Animation and Easing Evaluation Engine.
Evaluates continuous property curves, Bézier curves, and animation groups.
"""
import math
from typing import Any, Dict, List, Optional, Tuple, Union
from ..core.composition_models import (
    EasingType, KeyframeAnimation, KeyframePoint, MotionLayer, Transform2D
)
from core.timeline.time_model import RationalTime


class AnimationEngine:
    """
    Evaluates keyframe curves and transforms for motion graphics layers.
    """

    @staticmethod
    def ease(tau: float, easing: EasingType) -> float:
        """
        Evaluates easing curve for normalized time progress tau in [0.0, 1.0].
        """
        t = max(0.0, min(1.0, tau))

        if easing == EasingType.LINEAR:
            return t
        elif easing == EasingType.EASE_IN:
            return t * t
        elif easing == EasingType.EASE_OUT:
            return 1.0 - (1.0 - t) * (1.0 - t)
        elif easing == EasingType.EASE_IN_OUT:
            # Smoothstep hermite
            return 3.0 * t * t - 2.0 * t * t * t
        elif easing == EasingType.SPRING:
            # Damped spring overshoot
            c4 = (2.0 * math.pi) / 3.0
            return 1.0 + math.pow(2.0, -10.0 * t) * math.sin((t * 10.0 - 0.75) * c4) if t < 1.0 else 1.0
        elif easing == EasingType.BOUNCE:
            # Parabolic decay bounce
            n1 = 7.5625
            d1 = 2.75
            if t < 1.0 / d1:
                return n1 * t * t
            elif t < 2.0 / d1:
                t_sub = t - (1.5 / d1)
                return n1 * t_sub * t_sub + 0.75
            elif t < 2.5 / d1:
                t_sub = t - (2.25 / d1)
                return n1 * t_sub * t_sub + 0.9375
            else:
                t_sub = t - (2.625 / d1)
                return n1 * t_sub * t_sub + 0.984375
        elif easing == EasingType.HOLD:
            return 0.0 if t < 1.0 else 1.0

        return t

    @classmethod
    def evaluate_animation(
        cls,
        animation: KeyframeAnimation,
        current_time: RationalTime,
        default_value: float = 0.0
    ) -> float:
        """
        Evaluates a property value at an exact RationalTime.
        """
        keyframes = animation.keyframes
        if not keyframes:
            return default_value

        if len(keyframes) == 1:
            return float(keyframes[0].value)

        # Sort keyframes by offset_time
        sorted_kfs = sorted(keyframes, key=lambda k: k.offset_time.to_seconds())
        t_sec = current_time.to_seconds()

        # Before first keyframe -> clamp
        if t_sec <= sorted_kfs[0].offset_time.to_seconds():
            return float(sorted_kfs[0].value)

        # After last keyframe -> clamp
        if t_sec >= sorted_kfs[-1].offset_time.to_seconds():
            return float(sorted_kfs[-1].value)

        # Find enclosing interval
        for i in range(len(sorted_kfs) - 1):
            k0 = sorted_kfs[i]
            k1 = sorted_kfs[i + 1]
            t0 = k0.offset_time.to_seconds()
            t1 = k1.offset_time.to_seconds()

            if t0 <= t_sec <= t1:
                if t1 == t0:
                    return float(k1.value)

                tau = (t_sec - t0) / (t1 - t0)
                eased_tau = cls.ease(tau, k0.easing)
                v0 = float(k0.value)
                v1 = float(k1.value)
                return v0 + eased_tau * (v1 - v0)

        return default_value

    @classmethod
    def evaluate_layer_transform(
        cls,
        layer: MotionLayer,
        current_time: RationalTime
    ) -> Transform2D:
        """
        Computes the evaluated Transform2D for a layer at current_time.
        """
        base = layer.transform
        eval_t = Transform2D(
            x=base.x,
            y=base.y,
            scale_x=base.scale_x,
            scale_y=base.scale_y,
            rotation_deg=base.rotation_deg,
            opacity=base.opacity,
            anchor_x=base.anchor_x,
            anchor_y=base.anchor_y,
        )

        for anim in layer.animations:
            prop = anim.target_property
            val = cls.evaluate_animation(anim, current_time, getattr(eval_t, prop, 0.0))
            if hasattr(eval_t, prop):
                setattr(eval_t, prop, val)

        return eval_t
