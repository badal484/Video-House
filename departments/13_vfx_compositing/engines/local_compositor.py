"""
Local Deterministic Compositor Engine
Evaluates CompositingGraph node trees topologically using pure NumPy, OpenCV, and PIL.
"""
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import cv2
import numpy as np
from PIL import Image

from .base import ICompositorEngine
from ..core.graph_models import CompositingGraph, VFXNode, VFXNodeType, BlendMode
from ..core.color_space import (
    srgb_to_linear,
    linear_to_srgb,
    straight_to_premultiplied,
    premultiplied_to_straight,
    grade_image,
)
from ..keying.chroma_keyer import ChromaKeyer
from ..tracking.planar_tracker import PlanarTracker
from ..tracking.feature_tracker import FeatureTracker
from ..cleanup.inpainting_engine import InpaintingEngine
from ..effects.atmospheric import AtmosphericEffects
from ..effects.cinematic_fx import CinematicEffects


class LocalCompositorEngine(ICompositorEngine):
    """
    High-performance, deterministic local compositing engine.
    """

    def evaluate_frame(
        self,
        graph: CompositingGraph,
        frame_index: int = 0,
        inputs: Optional[Dict[str, np.ndarray]] = None,
    ) -> np.ndarray:
        """
        Evaluates graph topologically and returns the terminal node's output buffer (RGBA uint8 or float32).
        """
        nodes_order = graph.topological_sort()
        node_outputs: Dict[str, Dict[str, Any]] = {}

        # Pre-seed provided external inputs
        if inputs:
            for k, v in inputs.items():
                node_outputs[k] = {"output": v}

        terminal_image: Optional[np.ndarray] = None

        for node in nodes_order:
            # Gather inputs for this node from upstream outputs via edges
            resolved_inputs: Dict[str, Any] = {}
            for edge in graph.edges:
                if edge.target_node_id == node.node_id:
                    source_val = node_outputs.get(edge.source_node_id, {}).get(edge.source_port)
                    resolved_inputs[edge.target_port] = source_val

            # Execute node logic
            out_ports = self._execute_node(node, resolved_inputs, graph, frame_index)
            node_outputs[node.node_id] = out_ports

            if node.node_type == VFXNodeType.MEDIA_OUTPUT:
                terminal_image = out_ports.get("output")

        if terminal_image is None:
            # If no explicit MEDIA_OUTPUT node, return output of the last node in topological order
            last_node = nodes_order[-1]
            terminal_image = node_outputs.get(last_node.node_id, {}).get("output")

        if terminal_image is None:
            # Fallback black canvas
            terminal_image = np.zeros((graph.resolution_h, graph.resolution_w, 4), dtype=np.uint8)

        return terminal_image

    def _execute_node(
        self,
        node: VFXNode,
        inputs: Dict[str, Any],
        graph: CompositingGraph,
        frame_index: int,
    ) -> Dict[str, Any]:
        """
        Executes an individual node according to its VFXNodeType.
        """
        params = node.parameters

        if node.node_type == VFXNodeType.MEDIA_INPUT:
            # Check if input already supplied
            if "source" in inputs and inputs["source"] is not None:
                return {"output": inputs["source"]}
            asset_path = params.get("path")
            if asset_path and Path(asset_path).exists():
                img = cv2.imread(asset_path, cv2.IMREAD_UNCHANGED)
                if img is not None:
                    if img.ndim == 2:
                        img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGRA)
                    elif img.shape[2] == 3:
                        img = cv2.cvtColor(img, cv2.COLOR_BGR2BGRA)
                    return {"output": img}
            # Fallback generated solid color
            color = params.get("color", [0, 0, 0, 255])
            h = params.get("height", graph.resolution_h)
            w = params.get("width", graph.resolution_w)
            solid = np.full((h, w, 4), color, dtype=np.uint8)
            return {"output": solid}

        elif node.node_type == VFXNodeType.CHROMA_KEY:
            source = inputs.get("source")
            if source is None:
                return {"output": None}
            keyer = ChromaKeyer(
                key_color=params.get("key_color", "GREEN"),
                threshold_low=params.get("threshold_low", 0.05),
                threshold_high=params.get("threshold_high", 0.35),
                despill_strength=params.get("despill_strength", 1.0),
                edge_erode=params.get("edge_erode", 1),
                edge_dilate=params.get("edge_dilate", 1),
                edge_feather=params.get("edge_feather", 1.5),
            )
            matte = keyer.extract_matte(source)
            processed = keyer.process(source)
            return {"output": processed, "matte": matte}

        elif node.node_type == VFXNodeType.MERGE:
            bg = inputs.get("background")
            fg = inputs.get("foreground")
            blend_mode_str = params.get("blend_mode", BlendMode.OVER.value).upper()
            opacity = float(params.get("opacity", 1.0))

            if bg is None and fg is not None:
                return {"output": fg}
            if fg is None and bg is not None:
                return {"output": bg}
            if bg is None and fg is None:
                return {"output": np.zeros((graph.resolution_h, graph.resolution_w, 4), dtype=np.uint8)}

            merged = self._blend_layers(bg, fg, blend_mode_str, opacity)
            return {"output": merged}

        elif node.node_type == VFXNodeType.PLANAR_WARP:
            source = inputs.get("source")
            if source is None:
                return {"output": None}
            dst_corners = np.array(params.get("dst_corners"), dtype=np.float32)
            target_shape = (params.get("height", graph.resolution_h), params.get("width", graph.resolution_w))
            warped = PlanarTracker.warp_graphic(source, target_shape, dst_corners)
            return {"output": warped}

        elif node.node_type == VFXNodeType.BLUR:
            source = inputs.get("source")
            if source is None:
                return {"output": None}
            radius = params.get("radius", 5)
            ksize = (radius * 2 + 1, radius * 2 + 1)
            blurred = cv2.GaussianBlur(source, ksize, radius / 2.0)
            return {"output": blurred}

        elif node.node_type == VFXNodeType.COLOR_GRADE:
            source = inputs.get("source")
            if source is None:
                return {"output": None}
            exposure = float(params.get("exposure", 0.0))
            contrast = float(params.get("contrast", 1.0))
            saturation = float(params.get("saturation", 1.0))
            tint = tuple(params.get("tint_rgb", [1.0, 1.0, 1.0]))

            lin = srgb_to_linear(source)
            graded = grade_image(lin, exposure=exposure, contrast=contrast, saturation=saturation, tint_rgb=tint)
            out_srgb = linear_to_srgb(graded, to_uint8=(source.dtype == np.uint8))
            return {"output": out_srgb}

        elif node.node_type == VFXNodeType.INPAINT:
            source = inputs.get("source")
            mask = inputs.get("mask") or params.get("mask")
            if source is None or mask is None:
                return {"output": source}
            method = params.get("method", "TELEA")
            radius = params.get("radius", 3)
            cleaned = InpaintingEngine.inpaint_frame(source, mask, method=method, inpaint_radius=radius)
            return {"output": cleaned}

        elif node.node_type == VFXNodeType.ATMOSPHERIC:
            source = inputs.get("source")
            effect_type = params.get("type", "DUST").upper()
            if effect_type == "LIGHT_WRAP":
                bg = inputs.get("background")
                if source is not None and bg is not None:
                    wrapped = AtmosphericEffects.apply_light_wrap(
                        source, bg,
                        wrap_amount=params.get("wrap_amount", 0.5),
                        wrap_radius=params.get("wrap_radius", 15),
                    )
                    return {"output": wrapped}
                return {"output": source}
            elif effect_type == "DUST":
                h = params.get("height", graph.resolution_h)
                w = params.get("width", graph.resolution_w)
                dust = AtmosphericEffects.generate_dust_particles(
                    (h, w),
                    count=params.get("count", 100),
                    seed=params.get("seed", 42 + frame_index),
                )
                dust_uint8 = (dust * 255.0).astype(np.uint8)
                if source is not None:
                    blended = self._blend_layers(source, dust_uint8, BlendMode.ADD.value, 1.0)
                    return {"output": blended}
                return {"output": dust_uint8}
            return {"output": source}

        elif node.node_type == VFXNodeType.CINEMATIC_FX:
            source = inputs.get("source")
            if source is None:
                return {"output": None}
            fx_type = params.get("type", "GLOW").upper()
            if fx_type == "CHROMATIC_ABERRATION":
                shifted = CinematicEffects.chromatic_aberration(source, shift_pixels=params.get("shift", 3))
                return {"output": shifted}
            elif fx_type == "GLOW":
                glowed = CinematicEffects.lens_glow(
                    source,
                    threshold=params.get("threshold", 0.7),
                    glow_radius=params.get("radius", 25),
                    glow_intensity=params.get("intensity", 0.5),
                )
                return {"output": glowed}
            return {"output": source}

        elif node.node_type == VFXNodeType.MEDIA_OUTPUT:
            source = inputs.get("source")
            output_path = params.get("output_path")
            if source is not None and output_path:
                Path(output_path).parent.mkdir(parents=True, exist_ok=True)
                cv2.imwrite(output_path, source)
            return {"output": source}

        return {"output": inputs.get("source")}

    def _blend_layers(
        self,
        bg: np.ndarray,
        fg: np.ndarray,
        mode: str,
        opacity: float,
    ) -> np.ndarray:
        """
        Merges foreground over background using specified blend mode in premultiplied space.
        """
        # Ensure identical spatial dimensions
        h_bg, w_bg = bg.shape[:2]
        h_fg, w_fg = fg.shape[:2]
        if (h_bg, w_bg) != (h_fg, w_fg):
            fg = cv2.resize(fg, (w_bg, h_bg), interpolation=cv2.INTER_LANCZOS4)

        is_uint8 = (bg.dtype == np.uint8) or (fg.dtype == np.uint8)
        bg_f = bg.astype(np.float32) / 255.0 if bg.dtype == np.uint8 else bg.copy()
        fg_f = fg.astype(np.float32) / 255.0 if fg.dtype == np.uint8 else fg.copy()

        # Ensure 4-channel RGBA
        if bg_f.ndim == 2:
            bg_f = cv2.cvtColor(bg_f, cv2.COLOR_GRAY2BGRA)
        elif bg_f.shape[2] == 3:
            bg_f = np.concatenate([bg_f, np.ones((h_bg, w_bg, 1), dtype=np.float32)], axis=2)

        if fg_f.ndim == 2:
            fg_f = cv2.cvtColor(fg_f, cv2.COLOR_GRAY2BGRA)
        elif fg_f.shape[2] == 3:
            fg_f = np.concatenate([fg_f, np.ones((h_bg, w_bg, 1), dtype=np.float32)], axis=2)

        # Apply layer opacity
        fg_f[:, :, 3] *= opacity

        fg_alpha = fg_f[:, :, 3:4]
        bg_alpha = bg_f[:, :, 3:4]

        fg_rgb = fg_f[:, :, :3]
        bg_rgb = bg_f[:, :, :3]

        if mode == BlendMode.OVER.value:
            # Over: C_out = C_fg * a_fg + C_bg * (1 - a_fg)
            out_rgb = fg_rgb * fg_alpha + bg_rgb * (1.0 - fg_alpha)
            out_alpha = fg_alpha + bg_alpha * (1.0 - fg_alpha)
        elif mode == BlendMode.ADD.value:
            out_rgb = np.clip(bg_rgb + fg_rgb * fg_alpha, 0.0, 1.0)
            out_alpha = np.clip(bg_alpha + fg_alpha, 0.0, 1.0)
        elif mode == BlendMode.MULTIPLY.value:
            mult = bg_rgb * fg_rgb
            out_rgb = mult * fg_alpha + bg_rgb * (1.0 - fg_alpha)
            out_alpha = bg_alpha
        elif mode == BlendMode.SCREEN.value:
            screen = 1.0 - (1.0 - bg_rgb) * (1.0 - fg_rgb)
            out_rgb = screen * fg_alpha + bg_rgb * (1.0 - fg_alpha)
            out_alpha = np.clip(bg_alpha + fg_alpha, 0.0, 1.0)
        elif mode == BlendMode.DIFFERENCE.value:
            diff = np.abs(bg_rgb - fg_rgb)
            out_rgb = diff * fg_alpha + bg_rgb * (1.0 - fg_alpha)
            out_alpha = bg_alpha
        else:
            # Fallback OVER
            out_rgb = fg_rgb * fg_alpha + bg_rgb * (1.0 - fg_alpha)
            out_alpha = fg_alpha + bg_alpha * (1.0 - fg_alpha)

        out = np.concatenate([out_rgb, out_alpha], axis=2)
        if is_uint8:
            return np.clip(out * 255.0, 0, 255).astype(np.uint8)
        return out

    def render_sequence(
        self,
        graph: CompositingGraph,
        start_frame: int = 0,
        end_frame: Optional[int] = None,
        output_path: Optional[str] = None,
        inputs: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Renders frame sequence or writes video.
        """
        end_f = end_frame if end_frame is not None else graph.duration_frames
        rendered_frames = []

        for f_idx in range(start_frame, end_f):
            frame = self.evaluate_frame(graph, frame_index=f_idx, inputs=inputs)
            rendered_frames.append(frame)

        if output_path:
            p = Path(output_path)
            p.parent.mkdir(parents=True, exist_ok=True)
            if p.suffix.lower() in [".png", ".jpg", ".jpeg"]:
                cv2.imwrite(str(p), rendered_frames[0])
            elif p.suffix.lower() in [".mp4", ".mov"]:
                h, w = rendered_frames[0].shape[:2]
                fourcc = cv2.VideoWriter_fourcc(*"mp4v")
                writer = cv2.VideoWriter(str(p), fourcc, graph.fps, (w, h))
                for f in rendered_frames:
                    bgr = cv2.cvtColor(f, cv2.COLOR_BGRA2BGR) if f.shape[2] == 4 else f
                    writer.write(bgr)
                writer.release()

        return {
            "status": "COMPLETED",
            "frame_count": len(rendered_frames),
            "output_path": output_path,
        }
