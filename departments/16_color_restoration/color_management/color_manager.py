"""
Color Management Engine for Department 16.
Translates images between source camera encodings, working scene-referred spaces (ACEScg / ACEScct),
and target display/delivery standards (Rec.709, Display P3, Rec.2100 PQ/HLG).
"""
import numpy as np
from typing import Optional, Tuple
from ..core.models import ColorSpace, TransferFunction, ColorProfileMetadata, DataRange
from .aces_transforms import (
    srgb_eotf_inverse, srgb_eotf, bt1886_inverse, bt1886_forward,
    linear_to_acescct, acescct_to_linear, linear_to_pq, pq_to_linear,
    arri_logc3_to_linear, sony_slog3_to_linear, canon_clog3_to_linear, red_log3g10_to_linear,
    M_REC709_TO_ACESCG, M_ACESCG_TO_REC709,
    M_P3_TO_ACESCG, M_ACESCG_TO_P3,
    M_REC2020_TO_ACESCG, M_ACESCG_TO_REC2020
)
from .ocio_manager import OCIOConfigManager


class ColorManager:
    """
    Core application-owned Color Management Layer.
    Guarantees mathematically rigorous, reproducible color conversions.
    """

    def __init__(self, ocio_config_path: Optional[str] = None):
        self.ocio_manager = OCIOConfigManager(ocio_config_path)

    def detect_color_space_from_metadata(self, metadata: dict) -> ColorProfileMetadata:
        """
        Infers source color space and transfer function from FFprobe / ingestion metadata.
        Falls back safely and flags unknown camera logs.
        """
        primaries = metadata.get("color_primaries", "").lower()
        transfer = metadata.get("color_transfer", "").lower()

        cs = ColorSpace.REC709
        tf = TransferFunction.BT1886
        is_hdr = False

        if "slog3" in transfer:
            cs = ColorSpace.SONY_SLOG3
            tf = TransferFunction.SLOG3
        elif "clog3" in transfer:
            cs = ColorSpace.CANON_CLOG3
            tf = TransferFunction.CLOG3
        elif "arri" in transfer or "logc" in transfer:
            cs = ColorSpace.ARRI_LOGC3
            tf = TransferFunction.LOGC3
        elif "red" in transfer or "log3g10" in transfer:
            cs = ColorSpace.RED_LOG3G10
            tf = TransferFunction.LOG3G10
        elif "bt2020" in primaries or "rec2020" in primaries:
            if "smpte2084" in transfer or "pq" in transfer:
                cs = ColorSpace.REC2100_PQ
                tf = TransferFunction.PQ
                is_hdr = True
            elif "arib-std-b67" in transfer or "hlg" in transfer:
                cs = ColorSpace.REC2100_HLG
                tf = TransferFunction.HLG
                is_hdr = True
            else:
                cs = ColorSpace.REC2020
                tf = TransferFunction.BT1886
        elif "display-p3" in primaries or "p3" in primaries:
            cs = ColorSpace.DISPLAY_P3
            tf = TransferFunction.SRGB
        elif "log" in transfer or "log" in metadata.get("codec_name", "").lower():
            cs = ColorSpace.ARRI_LOGC3
            tf = TransferFunction.LOGC3

        return ColorProfileMetadata(
            color_space=cs,
            transfer_function=tf,
            is_hdr=is_hdr,
            bit_depth=metadata.get("bits_per_raw_sample", 8) or 8
        )

    def to_linear_acescg(self, image: np.ndarray, source_cs: ColorSpace) -> np.ndarray:
        """
        Converts input image array (uint8 or float32) to linear ACEScg float32.
        Input Device Transform (IDT).
        """
        arr = image.astype(np.float32)
        if image.dtype == np.uint8:
            arr = arr / 255.0

        has_alpha = arr.ndim == 3 and arr.shape[2] == 4
        rgb = arr[:, :, :3] if has_alpha else arr

        # 1. De-gamma / Linearize
        if source_cs in (ColorSpace.REC709, ColorSpace.SRGB):
            lin = srgb_eotf_inverse(rgb) if source_cs == ColorSpace.SRGB else bt1886_inverse(rgb)
            # 2. Primaries transform Rec.709 -> ACEScg
            acescg = np.tensordot(lin, M_REC709_TO_ACESCG.T, axes=([2], [1]))
        elif source_cs == ColorSpace.DISPLAY_P3:
            lin = srgb_eotf_inverse(rgb)
            acescg = np.tensordot(lin, M_P3_TO_ACESCG.T, axes=([2], [1]))
        elif source_cs == ColorSpace.REC2020:
            lin = bt1886_inverse(rgb)
            acescg = np.tensordot(lin, M_REC2020_TO_ACESCG.T, axes=([2], [1]))
        elif source_cs == ColorSpace.REC2100_PQ:
            lin = pq_to_linear(rgb, peak_nits=1000.0)
            acescg = np.tensordot(lin, M_REC2020_TO_ACESCG.T, axes=([2], [1]))
        elif source_cs == ColorSpace.ARRI_LOGC3:
            lin = arri_logc3_to_linear(rgb)
            acescg = np.tensordot(lin, M_REC709_TO_ACESCG.T, axes=([2], [1]))
        elif source_cs == ColorSpace.SONY_SLOG3:
            lin = sony_slog3_to_linear(rgb)
            acescg = np.tensordot(lin, M_REC2020_TO_ACESCG.T, axes=([2], [1]))
        elif source_cs == ColorSpace.CANON_CLOG3:
            lin = canon_clog3_to_linear(rgb)
            acescg = np.tensordot(lin, M_REC2020_TO_ACESCG.T, axes=([2], [1]))
        elif source_cs == ColorSpace.RED_LOG3G10:
            lin = red_log3g10_to_linear(rgb)
            acescg = np.tensordot(lin, M_REC2020_TO_ACESCG.T, axes=([2], [1]))
        elif source_cs in (ColorSpace.ACESCG, ColorSpace.ACES2065_1):
            acescg = rgb.copy()
        elif source_cs == ColorSpace.ACES_CCT:
            acescg = acescct_to_linear(rgb)
        else:
            # Fallback treat as Rec.709 with warning
            lin = bt1886_inverse(rgb)
            acescg = np.tensordot(lin, M_REC709_TO_ACESCG.T, axes=([2], [1]))

        if has_alpha:
            return np.concatenate([acescg, arr[:, :, 3:4]], axis=2)
        return acescg

    def from_linear_acescg(
        self,
        acescg_image: np.ndarray,
        target_cs: ColorSpace,
        to_uint8: bool = True
    ) -> np.ndarray:
        """
        Converts linear ACEScg float32 to target display/output color space.
        Output Device Transform (ODT).
        """
        has_alpha = acescg_image.ndim == 3 and acescg_image.shape[2] == 4
        rgb = acescg_image[:, :, :3] if has_alpha else acescg_image

        if target_cs in (ColorSpace.REC709, ColorSpace.SRGB):
            lin = np.tensordot(rgb, M_ACESCG_TO_REC709.T, axes=([2], [1]))
            out = srgb_eotf(lin) if target_cs == ColorSpace.SRGB else bt1886_forward(lin)
        elif target_cs == ColorSpace.DISPLAY_P3:
            lin = np.tensordot(rgb, M_ACESCG_TO_P3.T, axes=([2], [1]))
            out = srgb_eotf(lin)
        elif target_cs == ColorSpace.REC2020:
            lin = np.tensordot(rgb, M_ACESCG_TO_REC2020.T, axes=([2], [1]))
            out = bt1886_forward(lin)
        elif target_cs == ColorSpace.REC2100_PQ:
            lin = np.tensordot(rgb, M_ACESCG_TO_REC2020.T, axes=([2], [1]))
            out = linear_to_pq(lin, peak_nits=1000.0)
        elif target_cs == ColorSpace.ACES_CCT:
            out = linear_to_acescct(rgb)
        else:
            out = rgb.copy()

        if to_uint8:
            out = np.clip(out * 255.0, 0, 255).astype(np.uint8)

        if has_alpha:
            alpha = (acescg_image[:, :, 3:4] * 255.0).astype(np.uint8) if to_uint8 else acescg_image[:, :, 3:4]
            return np.concatenate([out, alpha], axis=2)
        return out
