"""
Color Quality Control & Gamut Validator for Department 16.
Validates color space limits, clipping percentages, and HDR metadata integrity.
"""
from typing import Any, Dict, List, Optional
import numpy as np
from ..core.models import ColorProfileMetadata, QualityReviewState


class ColorQualityController:
    """
    Audits color space boundaries and detects technical color flaws.
    """

    @staticmethod
    def audit_frame(
        image_rgb: np.ndarray,
        color_profile: ColorProfileMetadata,
        is_display_referred: bool = True
    ) -> Dict[str, Any]:
        """
        Validates clipping, gamut boundaries, and HDR metadata.
        """
        arr = image_rgb[:, :, :3].astype(np.float32)
        total_pixels = float(arr.shape[0] * arr.shape[1])

        issues: List[str] = []
        review_state = QualityReviewState.PASSED

        # 1. Out of range / illegal values
        out_of_range_low = float(np.sum(arr < 0.0) / total_pixels) * 100.0
        out_of_range_high = float(np.sum(arr > 1.0) / total_pixels) * 100.0

        if is_display_referred and (out_of_range_low > 0.01 or out_of_range_high > 0.01):
            issues.append(f"Out of range pixel values in display output ({out_of_range_low:.2f}% low, {out_of_range_high:.2f}% high).")
            review_state = QualityReviewState.WARNING

        # 2. Clipping detection
        hl_clipping_pct = float(np.sum(arr >= 0.999) / total_pixels) * 100.0
        sh_clipping_pct = float(np.sum(arr <= 0.001) / total_pixels) * 100.0

        if hl_clipping_pct > 10.0:
            issues.append(f"Severe highlight clipping detected ({hl_clipping_pct:.1f}% of frame).")
            review_state = QualityReviewState.NEEDS_HUMAN_REVIEW

        # 3. HDR Metadata validation
        if color_profile.is_hdr:
            if color_profile.max_cll and color_profile.max_cll > 10000.0:
                issues.append("MaxCLL exceeds SMPTE ST 2084 absolute physical maximum of 10,000 nits.")
                review_state = QualityReviewState.FAILED
            if color_profile.max_fall and color_profile.max_cll and color_profile.max_fall > color_profile.max_cll:
                issues.append("MaxFALL cannot exceed MaxCLL.")
                review_state = QualityReviewState.FAILED

        return {
            "review_state": review_state,
            "highlight_clipping_pct": round(hl_clipping_pct, 2),
            "shadow_clipping_pct": round(sh_clipping_pct, 2),
            "out_of_range_low_pct": round(out_of_range_low, 2),
            "out_of_range_high_pct": round(out_of_range_high, 2),
            "issues": issues
        }
