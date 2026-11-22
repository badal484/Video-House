"""
AI Motion Design Director Agent.
Department: 06_creative_direction
Translates narrative scripts, documentary themes, and scientific storyboards
into art-directed motion graphic compositions and bespoke visual systems.
"""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
import uuid

from departments.motion_graphics.core.composition_models import (
    BackgroundConfig,
    BackgroundType,
    EasingType,
    HUDElement,
    HUDType,
    KeyframeAnimation,
    KeyframePoint,
    LayerType,
    MotionComposition,
    MotionLayer,
    MotionScene,
    RenderConfig,
    TextElement,
    TextRevealMode,
    Transform2D,
)
from departments.motion_graphics.components.telemetry_hud import TelemetryHUDBuilder
from departments.motion_graphics.components.tracking_reticle import TrackingReticleBuilder
from core.timeline.time_model import RationalTime


@dataclass
class SceneMotionDirection:
    scene_index: int
    title: str
    start_sec: float
    duration_sec: float
    primary_text_hi: str
    secondary_text_hi: Optional[str] = None
    motion_motif: str = "editorial_typography"  # 'title_hero', 'macro_biometrics', 'hemodynamics', 'cardiac_arrest', 'outro'
    hud_overlay_type: Optional[str] = None
    telemetry_labels: Dict[str, str] = field(default_factory=dict)
    camera_intent: str = "floating_drift"


@dataclass
class MotionDesignSystemSpec:
    style_name: str = "Abyssal Biometrics & Micro-Optics"
    palette_primary: str = "#00F0FF"       # Bioluminescent Cyan
    palette_secondary: str = "#1D4ED8"     # Venous Cobalt
    palette_background: str = "#050B14"    # Abyssal Deep Sea
    palette_accent: str = "#FF3366"        # Cephalopod Warning Coral
    palette_text: str = "#FFFFFF"          # Pure Titanium White
    font_devanagari_display: str = "Noto Sans Devanagari"
    font_devanagari_body: str = "Mukta"
    font_telemetry: str = "JetBrains Mono"
    borderless_editorial: bool = True      # Strictly no generic PowerPoint boxes


class MotionDesignDirector:
    """
    Dedicated AI agent providing high-level motion design art direction,
    eliminating template-based generic animations in favor of bespoke visual languages.
    """

    def __init__(self, design_spec: Optional[MotionDesignSystemSpec] = None):
        self.spec = design_spec or MotionDesignSystemSpec()

    def direct_project_motion(
        self,
        project_id: str,
        topic: str,
        script_scenes: List[Dict[str, Any]],
        resolution: Tuple[int, int] = (1080, 1920),
        fps: float = 30.0,
    ) -> Dict[str, Any]:
        """
        Analyzes narrative scenes and outputs a complete motion design plan
        and composition specification.
        """
        scene_directions: List[SceneMotionDirection] = []
        accumulated_time = 0.0

        for idx, scn in enumerate(script_scenes, start=1):
            dur = float(scn.get("duration_seconds", 6.0))
            title = scn.get("title", f"Scene {idx}")
            hi_text = scn.get("narration_hi", scn.get("text_hi", ""))
            motif = self._determine_motion_motif(idx, title, hi_text)
            hud_type = self._determine_hud_type(motif)

            scene_directions.append(SceneMotionDirection(
                scene_index=idx,
                title=title,
                start_sec=accumulated_time,
                duration_sec=dur,
                primary_text_hi=hi_text,
                secondary_text_hi=scn.get("subtext_hi"),
                motion_motif=motif,
                hud_overlay_type=hud_type,
                telemetry_labels=scn.get("telemetry", {}),
            ))
            accumulated_time += dur

        return {
            "project_id": project_id,
            "topic": topic,
            "design_system": {
                "style_name": self.spec.style_name,
                "palette": {
                    "primary": self.spec.palette_primary,
                    "secondary": self.spec.palette_secondary,
                    "background": self.spec.palette_background,
                    "accent": self.spec.palette_accent,
                    "text": self.spec.palette_text,
                },
                "typography": {
                    "display": self.spec.font_devanagari_display,
                    "body": self.spec.font_devanagari_body,
                    "telemetry": self.spec.font_telemetry,
                },
                "borderless_editorial": self.spec.borderless_editorial,
            },
            "resolution": resolution,
            "fps": fps,
            "total_duration_sec": accumulated_time,
            "scenes": [s.__dict__ for s in scene_directions],
        }

    def synthesize_motion_composition(
        self,
        project_id: str,
        direction_plan: Dict[str, Any],
    ) -> MotionComposition:
        """
        Translates an art-directed motion plan into a concrete MotionComposition
        data structure ready for rendering.
        """
        res = tuple(direction_plan.get("resolution", (1080, 1920)))
        fps = float(direction_plan.get("fps", 30.0))
        total_sec = float(direction_plan.get("total_duration_sec", 50.0))
        total_frames = int(round(total_sec * fps))

        comp = MotionComposition(
            composition_id=f"comp_{uuid.uuid4().hex[:12]}",
            project_id=project_id,
            name=f"Motion Design: {direction_plan.get('topic', 'Octopus Doc')}",
            resolution=res,
            fps=fps,
            duration=RationalTime(total_frames, fps),
            background=BackgroundConfig(type=BackgroundType.TRANSPARENT),
        )

        for scn_data in direction_plan.get("scenes", []):
            start_frame = int(round(scn_data["start_sec"] * fps))
            dur_frames = int(round(scn_data["duration_sec"] * fps))

            scene = MotionScene(
                scene_id=f"scene_{scn_data['scene_index']}_{uuid.uuid4().hex[:8]}",
                name=scn_data["title"],
                start_time=RationalTime(start_frame, fps),
                duration=RationalTime(dur_frames, fps),
            )

            # 1. Floating Devanagari Title / Headline Layer
            txt_layer = self._create_editorial_text_layer(
                scn_data, res, fps, dur_frames
            )
            scene.layers.append(txt_layer)

            # 2. Dynamic HUD / Telemetry / Reticle Layer if applicable
            hud_motif = scn_data.get("motion_motif")
            if hud_motif == "macro_biometrics":
                reticle_layer = TrackingReticleBuilder.create_biometric_reticle_layer(
                    label="RADIAL_SUCKER_ARRAY",
                    pos=(res[0] * 0.5, res[1] * 0.55),
                    primary_color=self.spec.palette_primary,
                    duration_seconds=scn_data["duration_sec"],
                    fps=fps,
                )
                scene.layers.append(reticle_layer)

            elif hud_motif in ("hemodynamics", "cardiac_arrest"):
                is_arrest = (hud_motif == "cardiac_arrest")
                cardiac_layer = TelemetryHUDBuilder.create_cardiac_telemetry_layer(
                    heart_type="systemic_arrest" if is_arrest else "systemic",
                    base_bpm=0.0 if is_arrest else 58.4,
                    pos=(res[0] * 0.5, res[1] * 0.82),
                    color_primary=self.spec.palette_accent if is_arrest else self.spec.palette_primary,
                    duration_seconds=scn_data["duration_sec"],
                    fps=fps,
                )
                scene.layers.append(cardiac_layer)

            comp.scenes.append(scene)

        return comp

    def _determine_motion_motif(self, idx: int, title: str, text: str) -> str:
        text_lower = (title + " " + text).lower()
        if idx == 1 or "hook" in text_lower:
            return "title_hero"
        if "हाथ" in text_lower or "लचीला" in text_lower or "sucker" in text_lower or "tentacle" in text_lower:
            return "macro_biometrics"
        if "गलफड़ों" in text_lower or "branchial" in text_lower or "खून" in text_lower:
            return "hemodynamics"
        if "रुक" in text_lower or "तैरता" in text_lower or "arrest" in text_lower or "दिल रुक" in text_lower:
            return "cardiac_arrest"
        if "आश्चर्यजनक" in text_lower or "secret" in text_lower or "outro" in text_lower:
            return "outro"
        return "editorial_typography"

    def _determine_hud_type(self, motif: str) -> Optional[str]:
        if motif == "macro_biometrics":
            return "RETICLE"
        if motif in ("hemodynamics", "cardiac_arrest"):
            return "TELEMETRY"
        return None

    def _create_editorial_text_layer(
        self, scn_data: Dict[str, Any], res: Tuple[int, int], fps: float, dur_frames: int
    ) -> MotionLayer:
        headline = scn_data.get("title", "")
        body = scn_data.get("primary_text_hi", "")
        # Truncate for high-impact screen layout
        display_text = headline if len(headline) < 40 else body[:45] + "..."

        text_elem = TextElement(
            text=display_text,
            font_family=self.spec.font_devanagari_display,
            font_size=52.0 if res[0] <= 1080 else 72.0,
            font_weight="bold",
            fill_color=self.spec.palette_text,
            text_align="center",
            reveal_mode=TextRevealMode.WORD_BY_WORD,
            stagger_delay_sec=0.08,
        )

        # Subtle vertical drift and smooth fade
        anim_opacity = KeyframeAnimation(
            target_property="opacity",
            keyframes=[
                KeyframePoint(offset_time=RationalTime(0, fps), value=0.0, easing=EasingType.EASE_OUT),
                KeyframePoint(offset_time=RationalTime(int(round(0.5 * fps)), fps), value=1.0, easing=EasingType.LINEAR),
                KeyframePoint(offset_time=RationalTime(dur_frames - int(round(0.4 * fps)), fps), value=1.0, easing=EasingType.LINEAR),
                KeyframePoint(offset_time=RationalTime(dur_frames, fps), value=0.0, easing=EasingType.EASE_IN),
            ]
        )

        return MotionLayer(
            name=f"Typography: {scn_data.get('title')}",
            layer_type=LayerType.TEXT,
            transform=Transform2D(x=res[0] * 0.5, y=res[1] * 0.22, opacity=1.0),
            element=text_elem,
            animations=[anim_opacity],
        )
