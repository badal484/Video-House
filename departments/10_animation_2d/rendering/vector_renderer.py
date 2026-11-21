"""
Vector Animation Renderer
Renders resolution-independent 2D animation frames and skeletal rigs to clean SVG XML strings.
"""
from typing import Any, Dict, List, Optional, Tuple
from ..core.models import AnimationScene, AnimationShot
from ..rigging.bone_models import CharacterRig


class VectorAnimationRenderer:
    """
    Generates scalable SVG vector XML frames from 2D animation data.
    """

    @staticmethod
    def render_rig_svg(
        rig: CharacterRig,
        resolution: Tuple[int, int] = (1920, 1080),
        bone_color: str = "#00dcf0",
        joint_color: str = "#ffffff",
    ) -> str:
        """
        Renders a CharacterRig to an SVG XML document.
        """
        w, h = resolution
        transforms = rig.compute_world_transforms()

        svg_lines = [
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}">',
            f'  <defs>',
            f'    <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">',
            f'      <feGaussianBlur stdDeviation="3" result="blur" />',
            f'      <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>',
            f'    </filter>',
            f'  </defs>',
            f'  <g id="rig_{rig.name}">',
        ]

        # Draw bones in depth order
        for b_id in rig.draw_order:
            if b_id not in transforms:
                continue
            t = transforms[b_id]
            x1, y1 = t["start"]
            x2, y2 = t["end"]

            # Bone limb segment
            svg_lines.append(
                f'    <line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
                f'stroke="{bone_color}" stroke-width="5" stroke-linecap="round" filter="url(#glow)" />'
            )
            # Joint marker
            svg_lines.append(
                f'    <circle cx="{x1:.1f}" cy="{y1:.1f}" r="5" fill="{joint_color}" stroke="#222" stroke-width="1.5" />'
            )

        svg_lines.append("  </g>")
        svg_lines.append("</svg>")
        return "\n".join(svg_lines)

