# LUT Management, Interpolation & Compatibility Engine
**Project:** Universal AI Video Production Studio  
**Department:** 16 — Color Grading, Color Management, Video Restoration & Enhancement  
**Document Version:** 1.0.0  
**Verification Date:** 2026-11-21  

---

## 1. Executive Summary

Look-Up Tables (LUTs) map input color values to output color values through 1D or 3D mathematical grids. In Department 16, LUTs are divided strictly into two categories:
1. **Technical Conversion LUTs:** Perform calibrated transformations between specific color spaces and camera transfer curves (e.g. ARRI LogC3 to Rec.709). These MUST be guarded by strict input color space validation.
2. **Creative Look LUTs:** Apply aesthetic styling (e.g. film print emulation). These operate in normalized working spaces (Rec.709 or ACEScc/ACEScct) and support continuous intensity blending $[0.0, 1.0]$.

---

## 2. Supported Formats & Parsing

- **Adobe / DaVinci `.cube`:** Full support for 1D (`LUT_1D_SIZE`) and 3D (`LUT_3D_SIZE`) lattices (e.g. $17\times17\times17$, $33\times33\times33$, $65\times65\times65$).
- **Color Grading Interoperability:** Input/output color space metadata is extracted from headers or manually declared.
- **Strict Compatibility Gate:** `LUTManager.validate_lut_compatibility()` rejects applying an input-dependent technical conversion LUT if the clip's current color space does not match, eliminating accidental double-gamma or inverted color transforms.

---

## 3. Trilinear 3D Interpolation

The `LUTInterpolator` evaluates continuous float coordinates within the discrete 3D lattice using vectorized trilinear interpolation:
$$C(r, g, b) = \sum_{i=0}^1 \sum_{j=0}^1 \sum_{k=0}^1 w_{ijk} \cdot \text{LUT}[r_i, g_j, b_k]$$
With intensity blending:
$$C_{final} = C_{source} \cdot (1 - \alpha) + C_{lut} \cdot \alpha$$
where $\alpha \in [0.0, 1.0]$.
