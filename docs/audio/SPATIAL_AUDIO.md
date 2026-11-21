# Spatial Audio, Binaural & Surround Panning
**Project:** Universal AI Video Production Studio  
**Department:** 14_audio_production  
**Document:** SPATIAL_AUDIO.md  
**Version:** 1.0.0  

---

## 1. Spatial Channel Layouts

Department 14 supports three standard output channel configurations:
1. **MONO (1.0)**: Center channel only. Ideal for podcasts and telephone voice prompts.
2. **STEREO (2.0)**: Standard Left and Right channels.
3. **5.1 SURROUND**: L (Left), R (Right), C (Center - Dialogue), LFE (Low Frequency Effects Subwoofer), Ls (Left Surround), Rs (Right Surround).

---

## 2. 5.1 Downmixing & Upmixing Matrix

Conforming 5.1 audio down to stereo uses the ITU-R BS.775 standard matrix:

$$\begin{pmatrix} L_t \\ R_t \end{pmatrix} = \begin{pmatrix} 1.0 & 0 & \frac{1}{\sqrt{2}} & 0 & \frac{1}{\sqrt{2}} & 0 \\ 0 & 1.0 & \frac{1}{\sqrt{2}} & 0 & 0 & \frac{1}{\sqrt{2}} \end{pmatrix} \begin{pmatrix} L \\ R \\ C \\ LFE \\ L_s \\ R_s \end{pmatrix}$$

Center and surround channels are attenuated by $-3.0\text{ dB}$ ($1/\sqrt{2} \approx 0.7071$) before folding into stereo Left and Right.

---

## 3. Binaural HRTF Simulation for Headphones

Using Head-Related Transfer Function (HRTF) filtering via FFmpeg `sofalizer` or convolution with KEMAR impulse responses, stereo headphones can simulate 3D directional positioning (left, right, behind, above) for immersive audio-visual presentations.
