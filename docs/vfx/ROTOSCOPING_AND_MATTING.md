# ROTOSCOPING & MATTING SPECIFICATION
**Department:** 13_vfx_compositing  
**Topic:** Green/Blue Screen Keying, Despill, Roto Segmentation, and Matte Refinement  

---

## 1. Keying and Alpha Matte Extraction

Extracting clean foreground elements from color backdrops requires a multi-stage pipeline:

```
[ Input RGBA Image ]
        │
        ├──► [ Color Space Conversion (RGB -> HSV / Color Difference) ]
        │            │
        │            ▼
        │    [ Matte Generator: α = f(chroma_distance) ]
        │            │
        │            ▼
        │    [ Matte Refinement: Erode, Dilate, Gaussian Feather ]
        │            │
        ├──► [ Despill Filter: Suppress Green/Blue Edge Reflection ]
        │            │
        ▼            ▼
[ Straight Premultiplied Alpha Output ]
```

### 1.1 Chroma Difference Metric
For green screen extraction:
$$\Delta_{green} = G - \max(R, B)$$
If $\Delta_{green} > \tau_{high}$, $\alpha = 0.0$ (pure background).  
If $\Delta_{green} < \tau_{low}$, $\alpha = 1.0$ (pure foreground).  
For intermediate values:
$$\alpha = 1.0 - \frac{\Delta_{green} - \tau_{low}}{\tau_{high} - \tau_{low}}$$

### 1.2 Color Despill Algorithm
To eliminate green bounce/fringing on skin, hair, and clothing:
$$G_{despill} = \min\left(G, \frac{R + B}{2}\right)$$
For blue screens:
$$B_{despill} = \min\left(B, \frac{R + G}{2}\right)$$

---

## 2. Rotoscoping and AI Segmentation

When color screens are absent, rotoscoping isolates arbitrary objects:
1. **Interactive Bounding Box (GrabCut Fallback):**
   - User or AI Director defines bounding rectangle $[x_1, y_1, x_2, y_2]$.
   - Graph Cuts energy minimization partitions Gaussian Mixture Models (GMM) into definite background, probable background, probable foreground, and definite foreground.
2. **Matte Refinement & Anti-Aliasing:**
   - Morphological erosion (`cv2.erode`) removes fringe contamination.
   - Morphological dilation (`cv2.dilate`) bridges small pinholes.
   - Bilateral or Guided Filter preserves high-contrast edge boundaries while smoothing noise.
   - Sub-pixel Gaussian blur creates natural edge feathering.

