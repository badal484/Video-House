# VFX QUALITY CONTROL & ARTIFACT AUDITING
**Department:** 13_vfx_compositing  
**Topic:** Automated Optical and Geometric Verification of Composited Shots  

---

## 1. Quality Control Objectives

Automated VFX quality control ensures that composite renders are free of amateur artifacts before being committed to the master editorial timeline.

---

## 2. Key Auditing Metrics

### 2.1 Matte Pinholes and Transparency Leaks
- **Description:** Accidental holes in foreground subjects caused by overly aggressive keying or noisy thresholding.
- **Detection Algorithm:** Analyzes the internal region of the foreground alpha channel for isolated clusters of low alpha ($\alpha < 0.9$) surrounded by high alpha ($\alpha = 1.0$) using morphological flood-fill.

### 2.2 Color Spill Leakage
- **Description:** Unsuppressed green/blue color cast reflecting on subject skin, clothing, or hair.
- **Detection Algorithm:** Calculates excess green ratio on skin-tone pixels:
  $$\text{Spill} = \frac{G}{R + B + 1e-5}$$
  Flagged as warning if $\text{Spill} > 0.65$ within high-alpha foreground regions.

### 2.3 Edge Halos and Dark Fringes
- **Description:** Black or discolored borders around keyed subjects resulting from incorrect straight-vs-premultiplied alpha blending.
- **Detection Algorithm:** Evaluates luminance variance along the 1-pixel boundary transition $(\alpha \in [0.1, 0.9])$.

### 2.4 Tracking Jitter & Temporal Inconsistency
- **Description:** High-frequency vibration or sudden coordinate jumps in planar or point-tracked overlays.
- **Detection Algorithm:** Measures second derivative of track positions (acceleration):
  $$\Delta^2 P(t) = P(t+1) - 2P(t) + P(t-1)$$
  Values exceeding the motion threshold are flagged for smoothing.

---

## 3. Automated QC Report Schema

```json
{
  "qc_status": "PASSED",
  "score": 0.96,
  "checks": {
    "matte_integrity": {"passed": true, "holes_detected": 0},
    "color_spill": {"passed": true, "spill_ratio_max": 0.48},
    "edge_halo": {"passed": true, "halo_variance": 0.02},
    "tracking_stability": {"passed": true, "max_jitter_px": 0.4}
  },
  "recommendations": []
}
```
