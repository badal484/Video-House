# AI Colorist Assistant & Explainable Grading Recommendations
**Project:** Universal AI Video Production Studio  
**Department:** 16 — Color Grading, Color Management, Video Restoration & Enhancement  
**Document Version:** 1.0.0  
**Verification Date:** 2026-11-21  

---

## 1. Executive Summary

The **AI Colorist Assistant** (`AIColoristAssistant`) provides intelligent, automated visual inspection and objective grading recommendations. Unlike simplistic black-box AI filters, the assistant measures physical and colorimetric properties across footage, generates explainable justifications, and constructs a standard, human-editable `GradingGraph`.

---

## 2. Objective Image Analysis Metrics

1. **Mean Luminance & Exposure Evaluation:**
   Calculates weighted photometric luminance ($Y = 0.2126 R + 0.7152 G + 0.0722 B$). Detects underexposure ($Y < 0.12$) or overexposure ($Y > 0.35$), recommending exposure compensation in EV stops:
   $$\Delta EV = \log_2\left(\frac{0.18}{Y_{mean}}\right)$$
2. **Clipping & Dynamic Range:**
   Measures the exact percentage of pixels clipped in highlights ($Y \ge 0.98$) and crushed in shadows ($Y \le 0.02$).
3. **White Balance & Color Cast (Gray World Hypothesis):**
   Evaluates channel deviations from neutral gray ($R_{dev}, B_{dev}$) to estimate correlated color temperature in Kelvin and green/magenta tint.
4. **Vectorscope Skin-Tone Alignment:**
   Detects human skin pixels in $YCbCr$ ($133 \le Cr \le 173, 77 \le Cb \le 127$) and measures angular deviation from the historical $123^\circ$ vectorscope I-line.

---

## 3. Explainability & Human Approval

The assistant produces natural language explanations alongside every recommended parameter:
- *"Underexposed frame (mean luminance 0.09); recommended +1.0 EV exposure compensation."*
- *"Color temperature cast detected (4800K); compensated to 6200K."*
- *"Skin tone deviation (-6 deg from I-line); isolated and aligned to standard melanin hue."*
The user can preview the recommended grade, tweak individual node sliders, or approve it with a single click.
