# OpenColorIO & ACES Configuration Specification
**Project:** Universal AI Video Production Studio  
**Department:** 16 — Color Grading, Color Management, Video Restoration & Enhancement  
**Document Version:** 1.0.0  
**Verification Date:** 2026-11-21  

---

## 1. Executive Summary

This specification establishes the OpenColorIO (OCIO) v2.3+ configuration discovery, version tracking, and ACES 1.3 / 2.0 implementation rules for Department 16.

---

## 2. Configuration Discovery Priority

The studio resolves OCIO configurations using the following priority order:
1. **Explicit API Parameter:** User-specified custom `.ocio` path.
2. **Environment Variable:** System `$OCIO` environment variable.
3. **Studio Repository Preset:** `config/ocio/aces_1.3/config.ocio`.
4. **Studio Analytical Engine (Zero Dependency Fallback):** When no external `.ocio` file is present, `ColorManager` seamlessly executes identical mathematical ACES 1.3/2.0 transforms using NumPy vectorized linear algebra.

---

## 3. Supported Standard Color Spaces

| Color Space Identifier | Description | Primaries | White Point | Transfer Function |
| :--- | :--- | :---: | :---: | :---: |
| `acescg` | Computer Graphics / VFX | AP1 | ACES (0.32168, 0.33767) | Linear |
| `aces_cct` | Colorist Tactile Grading | AP1 | ACES (0.32168, 0.33767) | Logarithmic Toe Curve |
| `aces2065_1` | Master Archive Format | AP0 | ACES (0.32168, 0.33767) | Linear |
| `rec709` | HDTV / Web SDR | Rec.709 | D65 (0.3127, 0.3290) | BT.1886 (Gamma 2.4) |
| `srgb` | Web Computer Displays | sRGB | D65 (0.3127, 0.3290) | sRGB Piecewise |
| `display_p3` | Apple Displays / Mobile | DCI-P3 | D65 (0.3127, 0.3290) | sRGB Piecewise |
| `rec2020` | Ultra HD Television | Rec.2020 | D65 (0.3127, 0.3290) | BT.1886 (Gamma 2.4) |
| `rec2100_pq` | HDR10 Broadcast | Rec.2020 | D65 (0.3127, 0.3290) | SMPTE ST 2084 (PQ) |
| `rec2100_hlg` | Hybrid Log-Gamma HDR | Rec.2020 | D65 (0.3127, 0.3290) | ARIB STD-B67 (HLG) |
| `arri_logc3` | ARRI Alexa LogC3 | ARRI Wide | D65 (0.3127, 0.3290) | LogC3 Spline |
| `sony_slog3` | Sony Venice / FX Series | S-Gamut3.Cine | D65 (0.3127, 0.3290) | S-Log3 Logarithmic |
| `canon_clog3` | Canon Cinema EOS | Cinema Gamut | D65 (0.3127, 0.3290) | C-Log3 Logarithmic |
| `red_log3g10` | RED Digital Cinema | REDWideGamut | D65 (0.3127, 0.3290) | Log3G10 Logarithmic |
