# CHARACTER IDENTITY SYSTEM SPECIFICATION
**Department:** 12_character_production & 10_animation_2d  
**Topic:** Persistent Character DNA, Identity Validation, Model Sheets, and Turnaround Specifications  

---

## 1. Character Identity Data Model

In professional anime and episodic animation, a character's visual identity must remain consistent across hundreds of shots, varying lighting conditions, and diverse emotional beats. The studio establishes a persistent `CharacterIdentity` record:

```
[ CharacterIdentity ]
       │
       ├──► [ Proportions ]: Head-to-body ratio (e.g. 7.0 heads), shoulder width, eye spacing
       ├──► [ Feature Palette ]: Skin tone, hair color, eye iris color, shadow color, highlight
       ├──► [ Facial Anatomy ]: Eye style (almond, large anime, monolid), nose shape, mouth size
       ├──► [ Hair Design ]: Base silhouette, bangs style, ponytail/length, primary highlights
       ├──► [ Costume Layers ]: Inner shirt, jacket, trousers/skirt, footwear, accessories
       └──► [ Model Sheet References ]: Front, 3/4, Profile, Back, Close-up vector/raster specs
```

---

## 2. Quantitative Identity Verification Metrics

To programmatically detect and reject character drift in generated or drawn assets, the system evaluates six quantitative consistency vectors:

### 2.1 Proportion Vector ($\Delta_{prop}$)
Measures deviation in the canonical anatomical proportions:
$$\Delta_{prop} = \frac{1}{N} \sum_{i=1}^N \left| \frac{H_{feature, i}}{H_{head}} - \text{Ratio}_{canonical, i} \right|$$
Threshold: $\Delta_{prop} < 0.05$ (maximum 5% proportion deviation).

### 2.2 Color Palette Delta ($\Delta E_{color}$)
Computes the Euclidean color distance in CIE Lab color space across designated sample zones (hair, skin, eyes, primary costume):
$$\Delta E_{ab}^* = \sqrt{(\Delta L^*)^2 + (\Delta a^*)^2 + (\Delta b^*)^2}$$
Threshold: $\Delta E_{ab}^* < 8.0$ for primary character colors.

### 2.3 Facial Feature Topology ($\Delta_{face}$)
Measures geometric alignment of the facial triangle (eyes to mouth centroid ratio).

### 2.4 Silhouette Contour Match ($\Delta_{sil}$)
Evaluates the IoU (Intersection over Union) of the normalized character outer contour against approved turnaround silhouettes.

---

## 3. Character Turnaround Sheet (Settei) Specification

A production-ready model sheet package contains 5 standardized views rendered at 1:1 scale with horizontal guide alignment lines (Top of Head, Eye Line, Chin, Shoulder, Hip, Knee, Ankle):

1. **Front View ($0^\circ$):** Symmetrical resting pose showing complete costume details, buttons, seams, and facial geometry.
2. **Three-Quarter View ($45^\circ$):** The primary acting angle in anime, showing nose projection, depth of hair volume, and ear placement.
3. **Profile View ($90^\circ$):** Pure side view detailing nose bridge angle, lip protrusion, and posture curve.
4. **Back View ($180^\circ$):** Complete rear view showing hair parting, collar back, cape/coat draping, and spine alignment.
5. **Facial Expression Array:** 8 standardized emotional keyframes demonstrating eye opening, pupil contraction, and mouth shape.

