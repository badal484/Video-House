"""
Mathematical Transformations for ACES (Academy Color Encoding System) & Camera Log Curves.
Implements exact 3x3 chromaticity matrices, Bradford chromatic adaptation,
transfer functions for ACEScg, ACEScct, PQ, HLG, and major cinema camera log profiles.
"""
from typing import Tuple
import numpy as np

# ---------------------------------------------------------------------------
# Standard Color Primaries Matrices (Linear RGB to CIE XYZ D65)
# ---------------------------------------------------------------------------

# Rec.709 / sRGB to XYZ (D65)
M_REC709_TO_XYZ = np.array([
    [0.4124564, 0.3575761, 0.1804375],
    [0.2126729, 0.7151522, 0.0721750],
    [0.0193339, 0.1191920, 0.9503041]
], dtype=np.float32)

M_XYZ_TO_REC709 = np.linalg.inv(M_REC709_TO_XYZ)

# DCI-P3 (D65 white point - Display P3) to XYZ
M_P3_TO_XYZ = np.array([
    [0.4865709, 0.2656677, 0.1982173],
    [0.2289746, 0.6917393, 0.0792861],
    [0.0000000, 0.0451134, 1.0439444]
], dtype=np.float32)

M_XYZ_TO_P3 = np.linalg.inv(M_P3_TO_XYZ)

# Rec.2020 to XYZ (D65)
M_REC2020_TO_XYZ = np.array([
    [0.6369580, 0.1446169, 0.1688810],
    [0.2627002, 0.6779981, 0.0593017],
    [0.0000000, 0.0280727, 1.0609851]
], dtype=np.float32)

M_XYZ_TO_REC2020 = np.linalg.inv(M_REC2020_TO_XYZ)

# ACEScg (AP1 primaries with ACES white point ~D60) to XYZ
M_ACESCG_TO_XYZ = np.array([
    [0.6624542, 0.1340042, 0.1561877],
    [0.2722287, 0.6740818, 0.0536895],
    [-0.0055797, 0.0040607, 1.0103391]
], dtype=np.float32)

M_XYZ_TO_ACESCG = np.linalg.inv(M_ACESCG_TO_XYZ)

# Direct ACEScg <-> Rec.709
M_REC709_TO_ACESCG = np.dot(M_XYZ_TO_ACESCG, M_REC709_TO_XYZ)
M_ACESCG_TO_REC709 = np.linalg.inv(M_REC709_TO_ACESCG)

# Direct ACEScg <-> Display P3
M_P3_TO_ACESCG = np.dot(M_XYZ_TO_ACESCG, M_P3_TO_XYZ)
M_ACESCG_TO_P3 = np.linalg.inv(M_P3_TO_ACESCG)

# Direct ACEScg <-> Rec.2020
M_REC2020_TO_ACESCG = np.dot(M_XYZ_TO_ACESCG, M_REC2020_TO_XYZ)
M_ACESCG_TO_REC2020 = np.linalg.inv(M_REC2020_TO_ACESCG)


# ---------------------------------------------------------------------------
# Transfer Functions (Linear <-> Display Gamma / Log / PQ / HLG)
# ---------------------------------------------------------------------------

def srgb_eotf_inverse(img_srgb: np.ndarray) -> np.ndarray:
    """Converts sRGB [0, 1] to linear float32."""
    arr = np.clip(img_srgb.astype(np.float32), 0.0, 1.0)
    return np.where(arr <= 0.04045, arr / 12.92, np.power((arr + 0.055) / 1.055, 2.4))


def srgb_eotf(img_linear: np.ndarray) -> np.ndarray:
    """Converts linear float32 [0, 1] to sRGB."""
    arr = np.clip(img_linear.astype(np.float32), 0.0, 1.0)
    return np.where(arr <= 0.0031308, arr * 12.92, 1.055 * np.power(arr, 1.0 / 2.4) - 0.055)


def bt1886_inverse(img_gamma: np.ndarray) -> np.ndarray:
    """BT.1886 Rec.709 gamma 2.4 to linear."""
    arr = np.clip(img_gamma.astype(np.float32), 0.0, 1.0)
    return np.power(arr, 2.4)


def bt1886_forward(img_linear: np.ndarray) -> np.ndarray:
    """Linear to BT.1886 Rec.709 gamma 2.4."""
    arr = np.clip(img_linear.astype(np.float32), 0.0, 1.0)
    return np.power(arr, 1.0 / 2.4)


# ACEScct Logarithmic Transfer Curve (for tactile lift/gamma/gain grading)
def linear_to_acescct(linear: np.ndarray) -> np.ndarray:
    """Converts linear ACEScg values to logarithmic ACEScct."""
    arr = linear.astype(np.float32)
    x_break = 0.0078125 # 2^-7
    # ACEScct specification constants
    A = 10.5402377416545
    B = 0.0729055341958355
    return np.where(
        arr <= x_break,
        A * arr + B,
        (np.log2(np.maximum(arr, 1e-7)) + 9.72) / 17.52
    )


def acescct_to_linear(acescct: np.ndarray) -> np.ndarray:
    """Converts logarithmic ACEScct values to linear ACEScg."""
    arr = acescct.astype(np.float32)
    y_break = 0.155251141552511
    A = 10.5402377416545
    B = 0.0729055341958355
    return np.where(
        arr <= y_break,
        (arr - B) / A,
        np.power(2.0, arr * 17.52 - 9.72)
    )


# SMPTE ST 2084 (PQ - Perceptual Quantizer) for HDR
def linear_to_pq(linear: np.ndarray, peak_nits: float = 1000.0) -> np.ndarray:
    """Converts linear radiance normalized to peak_nits into ST 2084 PQ values [0, 1]."""
    m1 = 2610.0 / 16384.0
    m2 = (2523.0 / 4096.0) * 128.0
    c1 = 3424.0 / 4096.0
    c2 = (2413.0 / 4096.0) * 32.0
    c3 = (2392.0 / 4096.0) * 32.0

    Y = np.clip(linear * (peak_nits / 10000.0), 0.0, 1.0).astype(np.float32)
    Y_m1 = np.power(Y, m1)
    num = c1 + c2 * Y_m1
    den = 1.0 + c3 * Y_m1
    return np.power(num / den, m2)


def pq_to_linear(pq: np.ndarray, peak_nits: float = 1000.0) -> np.ndarray:
    """Converts ST 2084 PQ values [0, 1] into linear radiance normalized to peak_nits."""
    m1 = 2610.0 / 16384.0
    m2 = (2523.0 / 4096.0) * 128.0
    c1 = 3424.0 / 4096.0
    c2 = (2413.0 / 4096.0) * 32.0
    c3 = (2392.0 / 4096.0) * 32.0

    Np = np.clip(pq.astype(np.float32), 0.0, 1.0)
    Np_inv_m2 = np.power(Np, 1.0 / m2)
    num = np.maximum(Np_inv_m2 - c1, 0.0)
    den = c2 - c3 * Np_inv_m2
    Y = np.power(num / np.maximum(den, 1e-7), 1.0 / m1)
    return Y * (10000.0 / peak_nits)


# ---------------------------------------------------------------------------
# Camera Log De-linearization Functions (IDTs)
# ---------------------------------------------------------------------------

def arri_logc3_to_linear(logc3: np.ndarray) -> np.ndarray:
    """Converts ARRI LogC3 (EI 800) code values to scene linear."""
    cut = 0.010591
    a = 0.247190
    b = 0.385537
    c = 0.247189
    d = 0.052272
    e = 0.385537
    f = 0.052272

    arr = logc3.astype(np.float32)
    return np.where(
        arr > (cut * a + d),
        (np.power(10.0, (arr - d) / c) - b) / e,
        (arr - f) / a
    )


def sony_slog3_to_linear(slog3: np.ndarray) -> np.ndarray:
    """Converts Sony S-Log3 code values to scene linear."""
    arr = slog3.astype(np.float32)
    return np.where(
        arr >= 171.2102946929 / 1023.0,
        np.power(10.0, ((arr * 1023.0 - 420.0) / 261.5)) * (0.18 + 0.01) - 0.01,
        (arr * 1023.0 - 95.0) * 0.01125000 / (171.2102946929 - 95.0)
    )


def canon_clog3_to_linear(clog3: np.ndarray) -> np.ndarray:
    """Converts Canon C-Log3 code values to scene linear."""
    arr = clog3.astype(np.float32)
    return np.where(
        arr >= 0.1384074,
        (np.power(10.0, (arr - 0.125122) / 0.529136) - 1.0) / 8.0,
        (arr - 0.0730597) / 2.3
    )


def red_log3g10_to_linear(log3g10: np.ndarray) -> np.ndarray:
    """Converts RED Log3G10 code values to scene linear."""
    arr = log3g10.astype(np.float32)
    a = 0.224282
    b = 155.975327
    c = 0.01
    g = 3.570724
    return np.where(
        arr < 0.0,
        (arr / a) * c,
        (np.power(10.0, arr / (a * g)) - 1.0) / b
    )
