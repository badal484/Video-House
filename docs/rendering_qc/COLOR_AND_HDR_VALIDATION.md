# Color and HDR Validation Specification

## 1. Colorimetry & High Dynamic Range (HDR) Validation
The `ColorValidator` verifies that output media complies with declared color spaces, avoids illegal gamut clipping, and preserves HDR mastering metadata.

## 2. Validation Checks

### 2.1 NCLX Color Metadata Verification
- Inspects container stream tags for standard NCLX triples:
  - **Color Primaries:** `bt709` (SDR), `bt2020` (HDR), `display_p3` (Apple/DCI).
  - **Transfer Characteristics:** `bt709` (SDR Gamma 2.4), `smpte2084` (HDR10 PQ), `arib-std-b67` (HLG).
  - **Matrix Coefficients:** `bt709`, `bt2020nc`.
- Verifies that pixel data matches declared transfer curves (e.g. flagging SDR gamma streams tagged as PQ).

### 2.2 HDR Mastering Display Metadata (SMPTE ST 2086)
- For HDR10 exports, verifies presence of:
  - Mastering Display Color Primaries ($x, y$ coordinates for Red, Green, Blue, White point).
  - Luminance Bounds: Minimum luminance ($0.0001\text{ nits}$) and Maximum luminance ($1000\text{ nits}$ or $4000\text{ nits}$).
  - Content Light Level (CTA-861.3): MaxCLL (Maximum Content Light Level) and MaxFALL (Maximum Frame Average Light Level).

### 2.3 Legal Range & Gamut Violation Auditing
- Verifies whether output requires Studio/Limited Range ($16–235$ in 8-bit) or Full Range ($0–255$).
- Flags out-of-gamut Rec.2020 excursions when converting to Rec.709 delivery targets.
