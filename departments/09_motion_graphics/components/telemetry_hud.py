"""
Physiological & Biometric Telemetry HUD Components.
Department: 09_motion_graphics/components
Provides live cardiac rhythm waveforms, branchial/systemic hemodynamic meters,
oxygen saturation readouts, and oceanographic depth overlays.
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
from ..core.easing_physics import CardiacWaveformGenerator, EasingCurves
from core.timeline.time_model import RationalTime


class TelemetryHUDBuilder:
    """
    Factory for building scientific, biometric, and hemodynamic telemetry HUD elements.
    Integrates parametric EKG waveforms and fluid oxygenation telemetry.
    """

    @staticmethod
    def create_cardiac_telemetry_layer(
        heart_type: str = "systemic",  # 'systemic' or 'branchial'
        base_bpm: float = 60.0,
        pos: Tuple[float, float] = (540.0, 1600.0),
        color_primary: str = "#00F0FF",
        color_secondary: str = "#1D4ED8",
        duration_seconds: float = 6.0,
        fps: float = 30.0,
    ) -> MotionLayer:
        """
        Creates an animated cardiac telemetry HUD layer with real-time rhythm data.
        """
        is_arrest = (heart_type.lower() == "systemic_arrest")
        telemetry = {
            "HEART_ID": "SYS-01" if "sys" in heart_type.lower() else "BRN-01/02",
            "MODE": "ARREST (JET PROPULSION)" if is_arrest else "ACTIVE CONTRACTION",
            "BPM": "00.0 (PAUSED)" if is_arrest else f"{base_bpm:.1f}",
            "HEMOCYANIN_O2": "94.2%" if not is_arrest else "81.0% (DECLINING)",
            "STATUS": "WARNING_JET_STRESS" if is_arrest else "NOMINAL_PERFUSION",
        }

        hud = HUDElement(
            hud_type=HUDType.TELEMETRY,
            primary_color=color_primary,
            secondary_color=color_secondary,
            line_width=1.8,
            rotation_speed=0.0,
            telemetry_data=telemetry,
            coordinates=pos,
        )

        total_frames = int(round(duration_seconds * fps))
        anim_opacity = KeyframeAnimation(
            target_property="opacity",
            keyframes=[
                KeyframePoint(offset_time=RationalTime(0, fps), value=0.0, easing=EasingType.EASE_OUT),
                KeyframePoint(offset_time=RationalTime(int(round(0.4 * fps)), fps), value=0.95, easing=EasingType.LINEAR),
                KeyframePoint(offset_time=RationalTime(total_frames - int(round(0.3 * fps)), fps), value=0.95, easing=EasingType.LINEAR),
                KeyframePoint(offset_time=RationalTime(total_frames, fps), value=0.0, easing=EasingType.EASE_IN),
            ]
        )

        return MotionLayer(
            name=f"Cardiac Telemetry ({heart_type.title()})",
            layer_type=LayerType.HUD,
            transform=Transform2D(x=pos[0], y=pos[1], opacity=0.95),
            element=hud,
            animations=[anim_opacity],
        )

    @staticmethod
    def generate_waveform_points(
        duration_seconds: float = 4.0,
        fps: float = 30.0,
        is_swimming_jet: bool = False,
        base_bpm: float = 60.0,
        width_px: float = 400.0,
        height_px: float = 80.0,
    ) -> List[Tuple[float, float]]:
        """
        Samples the parametric cardiac EKG waveform across time to produce screen-space (x, y) polyline points.
        """
        num_points = int(round(duration_seconds * fps))
        points: List[Tuple[float, float]] = []

        for i in range(num_points):
            t = i / fps
            norm_x = (i / max(1, num_points - 1)) * width_px
            deflection = CardiacWaveformGenerator.sample_ekg_waveform(
                t, is_swimming_jet=is_swimming_jet, base_bpm=base_bpm
            )
            y = (height_px / 2.0) - (deflection * (height_px * 0.45))
            points.append((round(norm_x, 2), round(y, 2)))

        return points

    @staticmethod
    def create_oceanographic_depth_gauge(
        depth_meters: float = 42.5,
        water_temp_c: float = 11.2,
        pos: Tuple[float, float] = (180.0, 320.0),
        fps: float = 30.0,
    ) -> MotionLayer:
        """
        Creates depth and environmental telemetry panel.
        """
        telemetry = {
            "DEPTH": f"{depth_meters:.1f} M",
            "PRESSURE": f"{(1.0 + depth_meters / 10.0):.2f} BAR",
            "TEMP": f"{water_temp_c:.1f} °C",
            "ZONE": "BENTHIC_PELAGIC",
        }

        hud = HUDElement(
            hud_type=HUDType.TELEMETRY,
            primary_color="#00F0FF",
            secondary_color="#0A2540",
            line_width=1.5,
            telemetry_data=telemetry,
            coordinates=pos,
        )

        return MotionLayer(
            name="Depth Telemetry Gauge",
            layer_type=LayerType.HUD,
            transform=Transform2D(x=pos[0], y=pos[1], opacity=0.88),
            element=hud,
        )
