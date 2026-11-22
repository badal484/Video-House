"""
Biometric Tracking Reticle & Micro-Optic Targeting Components.
Department: 09_motion_graphics/components
Provides high-precision anatomical tracking brackets, multi-ring reticles,
sucker-focus coordinates, and physiological pulse crosshairs.
"""
from typing import Any, Dict, List, Optional, Tuple
from ..core.composition_models import (
    EasingType,
    HUDElement,
    HUDType,
    KeyframeAnimation,
    KeyframePoint,
    LayerType,
    MotionLayer,
    Transform2D,
)
from ..core.easing_physics import EasingCurves
from core.timeline.time_model import RationalTime


class TrackingReticleBuilder:
    """
    Factory for building scientific tracking reticles, anatomical crosshairs,
    and optical callout frames.
    """

    @staticmethod
    def create_biometric_reticle_layer(
        label: str = "TENTACLE_RADIAL_SUCKER",
        pos: Tuple[float, float] = (540.0, 960.0),
        primary_color: str = "#00F0FF",
        secondary_color: str = "#1D4ED8",
        rotation_speed: float = 30.0,
        radius_px: float = 64.0,
        duration_seconds: float = 5.0,
        fps: float = 30.0,
    ) -> MotionLayer:
        """
        Creates an animated rotating reticle with telemetry coordinates and tracking locks.
        """
        telemetry = {
            "TARGET": label,
            "LOCK": "TRACKING_ACTIVE",
            "CONFIDENCE": "99.4%",
            "COORD": f"X:{pos[0]:.0f} Y:{pos[1]:.0f}",
        }

        hud = HUDElement(
            hud_type=HUDType.RETICLE,
            primary_color=primary_color,
            secondary_color=secondary_color,
            line_width=2.0,
            rotation_speed=rotation_speed,
            telemetry_data=telemetry,
            coordinates=pos,
        )

        total_frames = int(round(duration_seconds * fps))

        # Scale spring settle animation
        anim_scale = KeyframeAnimation(
            target_property="scale_x",
            keyframes=[
                KeyframePoint(offset_time=RationalTime(0, fps), value=1.8, easing=EasingType.EASE_OUT),
                KeyframePoint(offset_time=RationalTime(int(round(0.35 * fps)), fps), value=1.0, easing=EasingType.SPRING),
            ]
        )

        anim_rot = KeyframeAnimation(
            target_property="rotation_deg",
            keyframes=[
                KeyframePoint(offset_time=RationalTime(0, fps), value=0.0, easing=EasingType.LINEAR),
                KeyframePoint(offset_time=RationalTime(total_frames, fps), value=rotation_speed * duration_seconds, easing=EasingType.LINEAR),
            ]
        )

        return MotionLayer(
            name=f"Reticle ({label})",
            layer_type=LayerType.HUD,
            transform=Transform2D(x=pos[0], y=pos[1], opacity=0.92),
            element=hud,
            animations=[anim_scale, anim_rot],
        )

    @staticmethod
    def create_anatomical_callout_bracket(
        organ_name: str,
        hindi_label: str,
        pos: Tuple[float, float],
        bracket_width: float = 240.0,
        bracket_height: float = 80.0,
        accent_color: str = "#00F0FF",
        fps: float = 30.0,
    ) -> MotionLayer:
        """
        Creates an optical bracket overlay that frames an anatomical feature
        (e.g., Branchial Heart Left, Branchial Heart Right, Systemic Heart).
        """
        telemetry = {
            "ORGAN": organ_name,
            "LABEL_HI": hindi_label,
            "STATUS": "PERFUSED",
        }

        hud = HUDElement(
            hud_type=HUDType.RETICLE,
            primary_color=accent_color,
            secondary_color="#0A2540",
            line_width=1.5,
            rotation_speed=0.0,
            telemetry_data=telemetry,
            coordinates=pos,
        )

        return MotionLayer(
            name=f"Callout Bracket: {organ_name}",
            layer_type=LayerType.HUD,
            transform=Transform2D(x=pos[0], y=pos[1], opacity=0.95),
            element=hud,
        )
