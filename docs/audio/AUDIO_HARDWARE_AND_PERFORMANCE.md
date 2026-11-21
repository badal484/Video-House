# Audio Hardware & Performance Optimization Guide
**Project:** Universal AI Video Production Studio  
**Department:** 14_audio_production  
**Document:** AUDIO_HARDWARE_AND_PERFORMANCE.md  
**Version:** 1.0.0  

---

## 1. Workstation Hardware Profile

The primary reference deployment workstation is:
- **SoC**: Apple M4 (10-core CPU: 4 performance cores, 6 efficiency cores; 10-core GPU).
- **Memory**: 16 GB Unified Memory Architecture (UMA) with 120 GB/s bandwidth.
- **Storage**: ~41 GB free solid-state NVMe storage.
- **Audio Subsystem**: Apple CoreAudio with hardware-accelerated sample rate conversion.

---

## 2. Memory & Buffer Optimization Strategy

In audio production, buffer allocation strategy dictates whether real-time mixing stutters or finishes instantaneously:

### 2.1 Block-Based Streaming Summing
Rather than loading an entire 2-hour 5.1 feature film soundtrack into RAM as raw float arrays (which would consume $48000 \times 6 \text{ channels} \times 4 \text{ bytes} \times 7200 \text{ s} \approx 8.3\text{ GB}$), Department 14 executes summing in sliding **audio blocks**:
- **Default Buffer Block Size**: 4096 samples ($85.33\text{ ms}$ at 48 kHz).
- **Peak RAM Footprint**: Less than 350 MB for a 32-track mixing session.

### 2.2 Vectorized NumPy & Accelerate Framework
Apple's Accelerate framework vectorizes array operations:
- Gain scaling ($y = \text{gain} \times x$) runs at $>25\text{ GB/s}$ in L2 cache.
- Equal-power crossfading uses pre-computed quarter-sine lookup tables:
  $$\text{fade\_in}[i] = \sin\left(\frac{\pi}{2} \cdot \frac{i}{N}\right), \quad \text{fade\_out}[i] = \cos\left(\frac{\pi}{2} \cdot \frac{i}{N}\right)$$
  Satisfying $\text{fade\_in}^2 + \text{fade\_out}^2 = 1.0$ at every sample $i$, preventing center-dip energy loss.

---

## 3. Storage Garbage Collection & Temp Cleanliness

Intermediate audio files (stem renders, separated vocal tracks, resampled clips) are written to `temp/audio_scratch/`:
1. Every job assigns a unique `session_id` subfolder.
2. Upon successful master render and ingestion into the Central Asset Registry, temporary intermediate WAV files are unlinked.
3. No lingering uncompressed cache files are left on disk, safeguarding the ~41GB local storage limit.
