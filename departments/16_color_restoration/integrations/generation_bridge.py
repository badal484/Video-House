"""
Generated Media Color Conformance Bridge for Department 16.
Conforms and color-harmonizes AI-generated media from Department 15 (Runway, Kling, Flux)
to match the master project color science.
"""
import numpy as np
from typing import Optional, Tuple
from ..core.models import ColorSpace
from ..color_management.color_manager import ColorManager
from ..grading.primary_corrector import PrimaryCorrector
from ..core.models import PrimaryGradingParameters


class GeneratedMediaColorBridge:
    """
    Normalizes synthetic and AI-generated media into project color spaces.
    """

    def __init__(self, color_manager: Optional[ColorManager] = None):
        self.color_manager = color_manager or ColorManager()

    def normalize_ai_generated_frame(
        self,
        frame_rgb: np.ndarray,
        source_generator: str = "runway",
        target_color_space: ColorSpace = ColorSpace.REC709
    ) -> np.ndarray:
        """
        Removes common AI generative artifacts:
        - Runway/Kling slight cyan shadow cast
        - Flux hypersaturated contrast
        - Gamma expansion
        """
        # Convert to ACEScg
        acescg = self.color_manager.to_linear_acescg(frame_rgb, source_cs=ColorSpace.SRGB)

        # Gentle normalization
        params = PrimaryGradingParameters()
        gen = source_generator.lower()
        if "runway" in gen:
            # Subtle cyan neutralization in deep shadows
            params.lift = (0.02, 0.0, -0.03)
        elif "flux" in gen:
            # Slight highlight roll-off and saturation harmonization
            params.highlights = -0.15
            params.saturation = 0.95

        corrected_acescg = PrimaryCorrector.apply_primary(acescg, params)

        # Convert to target space
        return self.color_manager.from_linear_acescg(corrected_acescg, target_cs=target_color_space)
