# Dialogue Processing, Cleaning & Voice Restoration
**Project:** Universal AI Video Production Studio  
**Department:** 14_audio_production  
**Document:** DIALOGUE_PROCESSING.md  
**Version:** 1.0.0  

---

## 1. Dialogue Signal Path

In professional film and video production, dialogue is the paramount storytelling channel. A noisy, muddy, or inconsistent dialogue track destroys viewer comprehension.

Department 14 implements a five-stage dialogue restoration pipeline:

```
Raw Speech Input
   │
   ▼
[1. DC & Rumble Filter]  --> High-Pass Butterworth at 80 Hz (18 dB/oct)
   │
   ▼
[2. Hum Notch Cascade]   --> Sharp Notch at 50/60 Hz and harmonics (100, 120, 150, 180 Hz)
   │
   ▼
[3. Spectral Denoising]  --> Noise floor estimation via pause analysis + spectral gating
   │
   ▼
[4. De-Esser Band]       --> Sidechain compressor on 4.5 kHz - 8.5 kHz sibilance band
   │
   ▼
[5. Leveler & Dynamic EQ]--> Gentle speech compression (Ratio 2.5:1, Target -24 dBFS)
   │
   ▼
Cleaned Dialogue Master
```

---

## 2. Spectral Subtraction & Noise Floor Estimation

1. **Noise Profile Extraction**:
   - The dialogue engine identifies speech pauses using short-term energy and zero-crossing rates.
   - FFT frames during pauses are averaged to compute a stationary noise spectral power density $\hat{N}(f)$.
2. **Spectral Subtraction**:
   $$|\hat{S}(f)|^2 = \max\left(|Y(f)|^2 - \alpha |\hat{N}(f)|^2, \; \beta |Y(f)|^2\right)$$
   Where $\alpha \approx 1.5$ is the over-subtraction factor and $\beta \approx 0.02$ is the spectral floor parameter to prevent musical noise artifacts.
3. **Phase Preservation**:
   The reconstructed clean time signal is synthesized using the original phase:
   $$\hat{s}[n] = \text{ISTFT}\left(|\hat{S}(f)| e^{j \angle Y(f)}\right)$$

---

## 3. Hum Removal via Harmonic Notch Filters

Electrical interference introduces distinct hum:
- North America / Japan: 60 Hz fundamental + 120 Hz, 180 Hz harmonics.
- Europe / India / World: 50 Hz fundamental + 100 Hz, 150 Hz harmonics.
A cascade of high-Q ($Q = 35$) IIR notch filters eliminates hum with less than $0.5\text{ dB}$ attenuation outside the notch bandwidth.

---

## 4. Split-Band De-Essing

Sibilant phonemes ('s', 'sh', 'ch', 'z') create harsh energy in the 4 kHz to 9 kHz range.
- The signal is split into a low band and sibilance high band.
- When high-band energy exceeds the speech threshold, high-band gain is dynamically attenuated by up to $-8.0\text{ dB}$ with ultra-fast attack ($1.0\text{ ms}$) and release ($20\text{ ms}$).
- The bands are recombined with zero phase distortion.
