# Video Quality Control (QC) Specification

## 1. Inspection Engine Architecture
The `VideoValidator` performs comprehensive frame-level and stream-level analysis on rendered video files using FFprobe and OpenCV.

## 2. Automated Defect Detectors

### 2.1 Black Frame Detector (`blackdetect`)
- Scans decoded luminance frames for intervals where pixel brightness falls below the black threshold ($Y \le 16$ on 8-bit limited range; luminance ratio $< 0.05$).
- Flags any black interval exceeding $0.25\text{ seconds}$ unless marked as an intentional creative head/tail slate.

### 2.2 Freeze Frame Detector (`freezedetect`)
- Evaluates consecutive frame differences:
  $$\Delta_{\text{frame}} = \frac{1}{W \times H} \sum_{x,y} |I(x,y,t) - I(x,y,t-1)|$$
- Flags any duration $> 1.0\text{ second}$ where $\Delta_{\text{frame}} < 0.001$, detecting stalled render buffers or crashed encoders.

### 2.3 Flash Frame Detector
- Detects single-frame luminance spikes ($> 300\%$ variance relative to surrounding 5-frame moving average) not corresponding to camera strobe or visual explosions.

### 2.4 Cadence, Resolution & Frame Rate Conformance
- **Resolution Verification:** Verifies exact pixel dimensions (e.g. $1920\times1080$, $3840\times2160$). Any deviation triggers a critical error.
- **Frame Rate & VFR Detection:** Inspects packet timestamps ($\Delta \text{PTS}$). If packet duration varies by $> 2\%$, the stream is flagged as non-standard Variable Frame Rate (VFR), recommending re-conformance to Constant Frame Rate (CFR).
- **Corrupted Frame Inspection:** Scans for decode errors, missing keyframes, macroblock artifacts, and container truncations.

