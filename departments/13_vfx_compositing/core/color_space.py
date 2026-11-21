"""
Color Space Transformations & Radiance Mathematics
Implements linear color transformations, straight vs premultiplied alpha conversions,
despill color corrections, and color grading operators.
"""
from typing import Tuple
import numpy as np


def srgb_to_linear(image: np.ndarray) -> np.ndarray:
    """
    Converts standard sRGB / Rec.709 8-bit or float array to linear radiance float32 [0.0, 1.0].
    """
    arr = image.astype(np.float32)
    if image.dtype == np.uint8:
        arr = arr / 255.0

    # Retain alpha if 4-channel
    if arr.ndim == 3 and arr.shape[2] == 4:
        rgb = arr[:, :, :3]
        alpha = arr[:, :, 3:4]
        linear_rgb = np.where(
            rgb <= 0.04045,
            rgb / 12.92,
            np.power((rgb + 0.055) / 1.055, 2.4)
        )
        return np.concatenate([linear_rgb, alpha], axis=2)
    else:
        return np.where(
            arr <= 0.04045,
            arr / 12.92,
            np.power((arr + 0.055) / 1.055, 2.4)
        )


def linear_to_srgb(image: np.ndarray, to_uint8: bool = True) -> np.ndarray:
    """
    Converts linear radiance float32 [0.0, 1.0] array to sRGB [0.0, 1.0] or uint8 [0, 255].
    """
    arr = np.clip(image, 0.0, 1.0)
    if arr.ndim == 3 and arr.shape[2] == 4:
        rgb = arr[:, :, :3]
        alpha = arr[:, :, 3:4]
        srgb_rgb = np.where(
            rgb <= 0.0031308,
            rgb * 12.92,
            1.055 * np.power(rgb, 1.0 / 2.4) - 0.055
        )
        out = np.concatenate([srgb_rgb, alpha], axis=2)
    else:
        out = np.where(
            arr <= 0.0031308,
            arr * 12.92,
            1.055 * np.power(arr, 1.0 / 2.4) - 0.055
        )
    if to_uint8:
        return np.clip(out * 255.0, 0, 255).astype(np.uint8)
    return out


def straight_to_premultiplied(rgba_float: np.ndarray) -> np.ndarray:
    """
    Converts straight RGBA float image to premultiplied RGBA:
    RGB_premul = RGB_straight * Alpha
    """
    if rgba_float.ndim != 3 or rgba_float.shape[2] != 4:
        raise ValueError("Image must be 4-channel RGBA float array.")
    rgb = rgba_float[:, :, :3]
    alpha = rgba_float[:, :, 3:4]
    return np.concatenate([rgb * alpha, alpha], axis=2)


def premultiplied_to_straight(rgba_float: np.ndarray, epsilon: float = 1e-6) -> np.ndarray:
    """
    Converts premultiplied RGBA float image to straight RGBA:
    RGB_straight = RGB_premul / max(Alpha, epsilon)
    """
    if rgba_float.ndim != 3 or rgba_float.shape[2] != 4:
        raise ValueError("Image must be 4-channel RGBA float array.")
    rgb = rgba_float[:, :, :3]
    alpha = rgba_float[:, :, 3:4]
    safe_alpha = np.maximum(alpha, epsilon)
    straight_rgb = np.clip(rgb / safe_alpha, 0.0, 1.0)
    return np.concatenate([straight_rgb, alpha], axis=2)


def apply_green_despill(rgba_float: np.ndarray, strength: float = 1.0) -> np.ndarray:
    """
    Applies color difference green despill algorithm:
    G_despill = min(G, (R + B) / 2)
    strength controls blending between original G and despilled G.
    """
    out = rgba_float.copy()
    r = out[:, :, 0]
    g = out[:, :, 1]
    b = out[:, :, 2]
    
    avg_rb = (r + b) * 0.5
    despilled_g = np.minimum(g, avg_rb)
    out[:, :, 1] = g * (1.0 - strength) + despilled_g * strength
    return out


def apply_blue_despill(rgba_float: np.ndarray, strength: float = 1.0) -> np.ndarray:
    """
    Applies color difference blue despill algorithm:
    B_despill = min(B, (R + G) / 2)
    """
    out = rgba_float.copy()
    r = out[:, :, 0]
    g = out[:, :, 1]
    b = out[:, :, 2]
    
    avg_rg = (r + g) * 0.5
    despilled_b = np.minimum(b, avg_rg)
    out[:, :, 2] = b * (1.0 - strength) + despilled_b * strength
    return out


def grade_image(
    image_float: np.ndarray,
    exposure: float = 0.0,
    contrast: float = 1.0,
    saturation: float = 1.0,
    tint_rgb: Tuple[float, float, float] = (1.0, 1.0, 1.0),
) -> np.ndarray:
    """
    Applies color grading controls in linear space:
    - Exposure (EV stops: 2^EV)
    - Contrast (pivot around 0.18 middle gray)
    - Saturation (Rec.709 luminance weights: 0.2126 R, 0.7152 G, 0.0722 B)
    - Tint (RGB channel multipliers)
    """
    out = image_float.copy()
    has_alpha = out.ndim == 3 and out.shape[2] == 4
    rgb = out[:, :, :3] if has_alpha else out

    # 1. Exposure
    if exposure != 0.0:
        rgb = rgb * (2.0 ** exposure)

    # 2. Contrast
    if contrast != 1.0:
        pivot = 0.18
        rgb = np.maximum(0.0, pivot + (rgb - pivot) * contrast)

    # 3. Saturation
    if saturation != 1.0:
        luminance = 0.2126 * rgb[:, :, 0:1] + 0.7152 * rgb[:, :, 1:2] + 0.0722 * rgb[:, :, 2:3]
        rgb = luminance + (rgb - luminance) * saturation

    # 4. Tint
    tint = np.array(tint_rgb, dtype=np.float32).reshape(1, 1, 3)
    rgb = rgb * tint

    rgb = np.clip(rgb, 0.0, 10.0)  # High dynamic range clamp

    if has_alpha:
        out[:, :, :3] = rgb
        return out
    return rgb
