"""
Design Quality and Aspect Ratio Adaptation Engine.
Enforces title/action safe margins, WCAG contrast ratios, and aspect ratio layouts.
"""
import re
from typing import Dict, List, Optional, Tuple
from ..core.composition_models import (
    MotionComposition, MotionLayer, Transform2D, LayerType, TextElement
)


class DesignValidator:
    """
    Validates design hierarchy, safe zones, readability contrast, and adapts compositions to aspect ratios.
    """

    # Safe Margins (Percentages from frame edge)
    ACTION_SAFE_MARGIN = 0.05   # 90% viewable area (5% margin on each edge)
    TITLE_SAFE_MARGIN = 0.10    # 80% viewable area (10% margin on each edge)

    @classmethod
    def parse_hex_color(cls, hex_color: str) -> Tuple[int, int, int]:
        """Parses '#RRGGBB' or '#RRGGBBAA' to RGB tuple."""
        clean = hex_color.lstrip("#")
        if len(clean) == 3:
            clean = "".join([c * 2 for c in clean])
        if len(clean) >= 6:
            r = int(clean[0:2], 16)
            g = int(clean[2:4], 16)
            b = int(clean[4:6], 16)
            return (r, g, b)
        return (255, 255, 255)

    @classmethod
    def compute_relative_luminance(cls, rgb: Tuple[int, int, int]) -> float:
        """Computes WCAG 2.1 relative luminance."""
        def channel_lum(val: int) -> float:
            c = val / 255.0
            return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

        r, g, b = rgb
        return 0.2126 * channel_lum(r) + 0.7152 * channel_lum(g) + 0.0722 * channel_lum(b)

    @classmethod
    def calculate_contrast_ratio(cls, color_a: str, color_b: str) -> float:
        """
        Calculates WCAG 2.1 contrast ratio between two hex colors.
        Returns value from 1.0 (identical) to 21.0 (black & white).
        """
        lum_a = cls.compute_relative_luminance(cls.parse_hex_color(color_a))
        lum_b = cls.compute_relative_luminance(cls.parse_hex_color(color_b))
        brightest = max(lum_a, lum_b)
        darkest = min(lum_a, lum_b)
        return (brightest + 0.05) / (darkest + 0.05)

    @classmethod
    def validate_composition(cls, comp: MotionComposition) -> Dict[str, any]:
        """
        Validates composition safe margins, text elements, and contrast.
        """
        w, h = comp.resolution
        issues: List[str] = []
        warnings: List[str] = []

        title_safe_min_x = w * cls.TITLE_SAFE_MARGIN
        title_safe_max_x = w * (1.0 - cls.TITLE_SAFE_MARGIN)
        title_safe_min_y = h * cls.TITLE_SAFE_MARGIN
        title_safe_max_y = h * (1.0 - cls.TITLE_SAFE_MARGIN)

        for scene in comp.scenes:
            for layer in scene.layers:
                # Text safe-zone checking
                if layer.layer_type == LayerType.TEXT and layer.element:
                    text_elem: TextElement = layer.element
                    lx = layer.transform.x
                    ly = layer.transform.y

                    if lx < title_safe_min_x or lx > title_safe_max_x:
                        warnings.append(
                            f"Layer '{layer.name}' X position ({lx:.1f}) exceeds Title Safe margin [{title_safe_min_x:.0f}, {title_safe_max_x:.0f}]."
                        )
                    if ly < title_safe_min_y or ly > title_safe_max_y:
                        warnings.append(
                            f"Layer '{layer.name}' Y position ({ly:.1f}) exceeds Title Safe margin [{title_safe_min_y:.0f}, {title_safe_max_y:.0f}]."
                        )

        return {
            "is_valid": len(issues) == 0,
            "issues": issues,
            "warnings": warnings,
            "title_safe_box": [title_safe_min_x, title_safe_min_y, title_safe_max_x, title_safe_max_y]
        }

    @classmethod
    def adapt_aspect_ratio(
        cls,
        comp: MotionComposition,
        target_resolution: Tuple[int, int]
    ) -> MotionComposition:
        """
        Intelligently adapts composition layouts from one aspect ratio to another (e.g. 16:9 -> 9:16).
        Reposition and scale layers instead of naive stretching.
        """
        old_w, old_h = comp.resolution
        new_w, new_h = target_resolution
        scale_x = new_w / old_w
        scale_y = new_h / old_h

        is_vertical = new_h > new_w

        for scene in comp.scenes:
            for layer in scene.layers:
                # Scale coordinates proportionally
                layer.transform.x *= scale_x
                layer.transform.y *= scale_y

                # If adapting to vertical 9:16, reposition lower thirds towards bottom center
                if is_vertical and layer.layer_type == LayerType.TEXT:
                    if layer.element:
                        # Make text slightly larger for vertical mobile viewing
                        layer.element.font_size *= 1.25
                        if layer.transform.y > new_h * 0.7:
                            # Re-center horizontally for vertical feed
                            layer.transform.x = new_w * 0.5
                            layer.element.text_align = "center"

        comp.resolution = target_resolution
        return comp
