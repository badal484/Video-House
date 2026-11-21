# TRACKING & MATCHMOVING SPECIFICATION
**Department:** 13_vfx_compositing  
**Topic:** 2D Point Tracking, 4-Point Planar Homography, and Camera Solving  

---

## 1. Point Feature Tracking

Tracking individual 2D features across consecutive frames enables graphic attachment, callout pins, and stabilization.

### 1.1 Shi-Tomasi Corner Detector
Identifies trackable points by computing the minimum eigenvalue of the image gradient structure tensor:
$$M = \sum_{(x,y) \in W} \begin{bmatrix} I_x^2 & I_x I_y \\ I_x I_y & I_y^2 \end{bmatrix}$$
Points where $\min(\lambda_1, \lambda_2) > \lambda_{threshold}$ are selected.

### 1.2 Lucas-Kanade Optical Flow
Tracks points between frame $I(t)$ and $I(t+1)$ assuming local brightness constancy:
$$I_x u + I_y v + I_t = 0$$
Using multi-level Gaussian pyramids, large displacements can be tracked with sub-pixel precision.

---

## 2. 4-Point Planar Tracking & Perspective Warping

Planar tracking is essential for replacing content on screens (smartphones, monitors, televisions), billboards, posters, and road signs.

### 2.1 Homography Transformation
A planar surface in 3D projects to 2D via a $3 \times 3$ projective homography matrix $H$:
$$\begin{bmatrix} x' \\ y' \\ 1 \end{bmatrix} \sim H \begin{bmatrix} x \\ y \\ 1 \end{bmatrix} = \begin{bmatrix} h_{11} & h_{12} & h_{13} \\ h_{21} & h_{22} & h_{23} \\ h_{31} & h_{32} & h_{33} \end{bmatrix} \begin{bmatrix} x \\ y \\ 1 \end{bmatrix}$$

Given 4 pairs of corresponding corner coordinates (source asset corners $\leftrightarrow$ target quadrilateral in the scene plate), $H$ is computed deterministically via Singular Value Decomposition (SVD) or RANSAC (`cv2.getPerspectiveTransform` or `cv2.findHomography`).

### 2.2 Perspective Image Warping
The source image (e.g. animated Motion Canvas UI or static graphic) is warped into the target quadrilateral via `cv2.warpPerspective` with Lanczos4 or bicubic interpolation, preserving sharp text and sub-pixel edge boundaries.

---

## 3. 3D Camera Solving

For placing 3D objects (Blender USD assets, 3D text) into live footage:
1. 8 or more stable feature points are tracked across $N$ frames.
2. The Essential Matrix $E$ is estimated using RANSAC:
   $$x_2^T E x_1 = 0$$
3. Singular Value Decomposition of $E$ recovers the relative camera rotation $R$ and translation $t$.
4. Camera intrinsics (focal length, principal point) and extrinsic trajectories are exported for headless Blender rendering.
