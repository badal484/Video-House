# Audio Quality Control Specification

## 1. Automated Audio QC Architecture
The `AudioValidator` inspects rendered audio streams for technical defects, loudness compliance, clipping, and audio-video synchronization.

## 2. Core Audio QC Validations

### 2.1 Loudness Measurement (EBU R128 / ITU-R BS.1770-4)
- **Integrated Loudness ($LUFS$):** Measures program loudness over entire duration using standard K-weighting and relative $-10\text{ LU}$ gating.
- **Loudness Range ($LRA$):** Computes difference between 95th and 10th percentile loudness distributions.
- **True-Peak Detection ($dBTP$):** Uses $4\times$ oversampling to detect inter-sample peaks that clip analog output converters.

### 2.2 Clipping & Distortion Detection
- Scans audio samples for sequences of 3 or more consecutive full-scale samples ($0.0\text{ dBFS}$ / $\ge 0.9999$).
- Flags digital clipping events with exact millisecond timestamps.

### 2.3 Silence & Channel Dropout Detection
- Flags unexpected silence intervals (audio energy $< -60\text{ dBFS}$) longer than $2.0\text{ seconds}$ during non-dialogue scenes.
- Detects phase cancellation or one-sided mute in stereo/surround pairs.

### 2.4 Audio/Video Synchronization & Drift Verification
- Compares audio stream duration against video stream duration:
  $$\Delta t_{\text{sync}} = |t_{\text{audio}} - t_{\text{video}}|$$
- Flags any discrepancy $> 0.040\text{ seconds}$ ($> 1$ video frame at 24fps) as a synchronization error.
