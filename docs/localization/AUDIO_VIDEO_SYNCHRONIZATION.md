# Audio-Video Synchronization & Drift Elimination Specification

## 1. The Clock Drift Problem in Localization
In digital media production, discrepancies between audio sample clocks (44,100 Hz vs 48,000 Hz) and video frame rates (23.976 fps, 24 fps, 25 fps, 29.97 fps, 30 fps, 60 fps) accumulate drift over time:
- In a 90-minute film, a 0.1% frame-rate mismatch causes an audio desynchronization of **5.4 seconds**, ruining lip-sync and comedic timing.
- Floating-point timestamp arithmetic causes cumulative quantization error.

## 2. Rational Time Architecture
The `SyncManager` enforces rational arithmetic across all localization timecodes:
$$\text{Time} = \text{RationalTime}(\text{value}, \text{rate})$$

### 2.1 Sync Conformance Rules
1. **Timebase Standardization:**
   - Audio is standard conformant to 48,000 Hz 24-bit PCM.
   - Timeline timebase matches the project video frame rate (e.g., 24/1, 25/1, 30000/1001).
2. **Drift Detection:**
   - The engine compares audio stem sample count $N_{samples}$ against video frame duration:
     $$\Delta t = \left| \frac{N_{samples}}{48000} - \frac{N_{frames}}{FPS} \right|$$
   - If $\Delta t > 0.5 \text{ frames}$ (approx 20ms at 24fps), the sync manager automatically inserts sample padding or applies sub-sample phase resampling (without pitch shifting) via SoX/Rubberband in Department 10.
3. **Playout Alignment Checkpoints:**
   - Subtitle cues and speech waveforms are verified at shot cut points (derived from PySceneDetect in Department 04) to prevent audio bleeding across hard scene cuts.
