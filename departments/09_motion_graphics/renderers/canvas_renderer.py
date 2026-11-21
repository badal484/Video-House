"""
Deterministic Canvas2D and Raster Engine.
Provides high-performance direct RGBA pixel buffer drawing with Pillow for complex shapes,
particle effects, raster HUD elements, and transparent alpha overlays.
"""
import io
import math
import os
import subprocess
import tempfile
from typing import Dict, List, Optional, Tuple

from PIL import Image, ImageDraw, ImageFont

from ..renderers.base import IMotionRenderer
from ..core.composition_models import (
    BackgroundType, ChartElement, ChartType, CinematicOverlayElement, GraphicElementUnion,
    HUDElement, HUDType, LayerType, MotionComposition, MotionLayer, RenderConfig,
    ShapeElement, TextElement, Transform2D
)
from ..core.animation_engine import AnimationEngine
from ..core.typography import TypographyEngine
from core.timeline.time_model import RationalTime


class CanvasRasterRenderer(IMotionRenderer):
    """High-performance deterministic 32-bit RGBA raster canvas engine."""

    def render_frame_svg(self, composition: MotionComposition, current_time: RationalTime) -> str:
        """Delegates SVG generation to SVGVectorRenderer for vector interchange."""
        from ..renderers.svg_vector_renderer import SVGVectorRenderer
        return SVGVectorRenderer().render_frame_svg(composition, current_time)

    def render_frame_raster(self, composition: MotionComposition, current_time: RationalTime) -> bytes:
        """Renders frame directly into an in-memory RGBA PNG image buffer."""
        w, h = composition.resolution
        img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # Background
        bg = composition.background
        if bg.type == BackgroundType.SOLID:
            draw.rectangle([0, 0, w, h], fill=self._parse_color_rgba(bg.color))

        t_sec = current_time.to_seconds()
        for scene in composition.scenes:
            scene_start = scene.start_time.to_seconds()
            scene_end = scene_start + scene.duration.to_seconds()

            if not (scene_start <= t_sec <= scene_end):
                continue

            sorted_layers = sorted(scene.layers, key=lambda l: l.z_index)
            for layer in sorted_layers:
                if not layer.visible or not layer.element:
                    continue
                self._draw_layer_raster(img, draw, layer, current_time, composition)

        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()

    def _draw_layer_raster(
        self,
        img: Image.Image,
        draw: ImageDraw.ImageDraw,
        layer: MotionLayer,
        current_time: RationalTime,
        comp: MotionComposition
    ) -> None:
        """Draws an individual layer into the RGBA canvas with animated transforms."""
        transform: Transform2D = AnimationEngine.evaluate_layer_transform(layer, current_time)
        if transform.opacity <= 0.001:
            return

        tx = int(round(transform.x))
        ty = int(round(transform.y))
        alpha_mult = max(0.0, min(1.0, transform.opacity))
        elem = layer.element

        if layer.layer_type == LayerType.TEXT and isinstance(elem, TextElement):
            fps = comp.fps
            dur_sec = max(0.5, comp.duration.to_seconds() * 0.6)
            progress = max(0.0, min(1.0, current_time.to_seconds() / dur_sec))
            reveal_info = TypographyEngine.compute_reveal_state(elem, progress)
            visible_text = reveal_info["visible_text"]

            if visible_text:
                color = self._parse_color_rgba(elem.fill_color, alpha_mult)
                # Text anchoring
                try:
                    font = ImageFont.load_default()
                except Exception:
                    font = None

                draw.text((tx, ty), visible_text, fill=color, font=font, anchor="mm")

        elif layer.layer_type == LayerType.SHAPE and isinstance(elem, ShapeElement):
            fill = self._parse_color_rgba(elem.fill_color, alpha_mult)
            stroke = self._parse_color_rgba(elem.stroke_color, alpha_mult)
            hw = int(round(elem.width / 2.0 * transform.scale_x))
            hh = int(round(elem.height / 2.0 * transform.scale_y))

            if elem.shape_type == "RECTANGLE":
                draw.rectangle([tx - hw, ty - hh, tx + hw, ty + hh], fill=fill, outline=stroke, width=int(elem.stroke_width))
            elif elem.shape_type == "CIRCLE":
                r = int(round(elem.radius * transform.scale_x))
                draw.ellipse([tx - r, ty - r, tx + r, ty + r], fill=fill, outline=stroke, width=int(elem.stroke_width))

        elif layer.layer_type == LayerType.HUD and isinstance(elem, HUDElement):
            col = self._parse_color_rgba(elem.primary_color, alpha_mult)
            if elem.hud_type == HUDType.RETICLE:
                r1 = 90
                r2 = 45
                draw.ellipse([tx - r1, ty - r1, tx + r1, ty + r1], outline=col, width=int(elem.line_width))
                draw.ellipse([tx - r2, ty - r2, tx + r2, ty + r2], outline=col, width=int(elem.line_width))
                draw.line([tx - 110, ty, tx - 60, ty], fill=col, width=2)
                draw.line([tx + 60, ty, tx + 110, ty], fill=col, width=2)
                draw.line([tx, ty - 110, tx, ty - 60], fill=col, width=2)
                draw.line([tx, ty + 60, tx, ty + 110], fill=col, width=2)

    @staticmethod
    def _parse_color_rgba(hex_color: str, alpha_mult: float = 1.0) -> Tuple[int, int, int, int]:
        """Parses hex code to (R, G, B, A) tuple."""
        clean = hex_color.lstrip("#")
        if len(clean) == 3:
            clean = "".join([c * 2 for c in clean])
        r = int(clean[0:2], 16) if len(clean) >= 2 else 255
        g = int(clean[2:4], 16) if len(clean) >= 4 else 255
        b = int(clean[4:6], 16) if len(clean) >= 6 else 255
        a = int(clean[6:8], 16) if len(clean) >= 8 else 255
        return (r, g, b, int(round(a * alpha_mult)))

    def render_video(
        self,
        composition: MotionComposition,
        output_path: str,
        config: Optional[RenderConfig] = None
    ) -> str:
        """Pipes raw RGBA frames directly into FFmpeg image2pipe for ultra-fast rendering."""
        cfg = config or RenderConfig(
            resolution=composition.resolution,
            fps=composition.fps,
            pixel_format="yuva444p10le",
            output_format="mov",
            codec="prores_ks"
        )

        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        total_frames = composition.total_frames()
        fps = composition.fps
        w, h = composition.resolution

        # Use image2pipe with PNG stream to FFmpeg
        if cfg.codec == "prores_ks":
            cmd = [
                "ffmpeg", "-y",
                "-f", "image2pipe",
                "-framerate", str(fps),
                "-i", "-",
                "-c:v", "prores_ks",
                "-profile:v", "4",
                "-pix_fmt", "yuva444p10le",
                output_path
            ]
        else:
            cmd = [
                "ffmpeg", "-y",
                "-f", "image2pipe",
                "-framerate", str(fps),
                "-i", "-",
                "-c:v", "libvpx-vp9",
                "-pix_fmt", "yuva420p",
                "-auto-alt-ref", "0",
                "-b:v", "2M",
                output_path
            ]

        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        for k in range(total_frames):
            current_time = RationalTime(k, fps)
            png_bytes = self.render_frame_raster(composition, current_time)
            proc.stdin.write(png_bytes)

        proc.stdin.flush()
        stdout, stderr = proc.communicate()

        if proc.returncode != 0:
            raise RuntimeError(f"Canvas raster FFmpeg render failed: {stderr.decode('utf-8', errors='replace')}")

        return output_path
