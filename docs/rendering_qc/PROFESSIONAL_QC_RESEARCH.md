# Professional Media Quality Control (QC) Research

## 1. Quality Control Objectives & Failure Taxonomy
Professional automated Quality Control (QC) protects broadcast networks, streaming platforms, and theatrical releases from technical defects that degrade viewer experience or violate strict delivery specifications.

### 1.1 Structural Video Defect Taxonomy
1. **Black Frames:** Sequences of pure black luminance ($Y \le 16$ in 8-bit limited range) exceeding allowable program thresholds (e.g., unexpected black frames in the middle of a scene vs. intentional scene-to-black transitions).
2. **Frozen Frames:** Consecutive identical or near-identical frames ($PSNR > 60\text{ dB}$, $\Delta Y < 0.1\%$) indicating rendering pipeline stalls, dropped inputs, or buffer starvation.
3. **Flash Frames:** Single-frame or two-frame bursts of high luminance or unrelated content caused by editorial splicing errors.
4. **Frame Rate Irregularities:** Unintended variable frame rate (VFR) timestamps causing audio desynchronization and jitter in broadcast playout servers.
5. **Cadence & Interlacing Artifacts:** Combing artifacts resulting from improper deinterlacing (telecine 3:2 pull-down mismatch).

### 1.2 Inspection Tools Evaluated

| Tool | Focus Area | Strengths | Limitations | License |
| :--- | :--- | :--- | :--- | :--- |
| **MediaInfo** | Container & Stream Metadata | Fast metadata extraction (codecs, bit depths, duration, audio layouts) | Does not inspect internal decoded frame pixels | BSD-2-Clause |
| **FFprobe** | Packet & Frame Inspection | Frame-level timestamp verification (`show_frames`), VFR detection, packet corruption | Slower than header parsing; requires stream reading | LGPL / GPL |
| **MediaConch** | File Format Policy Checker | Enforces strict XML-based container conformance (Matroska, FFV1, MXF) | Specialized for archival preservation workflows | BSD-2-Clause |
| **Netflix VMAF** | Perceptual Video Quality | Strong correlation with human MOS (Mean Opinion Score); supports 4K & HDR models | **Full-reference metric only** (requires uncompressed original reference) | BSD-2-Clause |
| **SSIM / PSNR** | Mathematical Fidelity | Fast, standardized, universal reference comparison | Sensitive to slight spatial shifts; does not measure aesthetic quality | Standard Math |
| **CAMBI (Netflix)** | Banding Artifact Detection | Detects 12-bit/10-bit downsampling staircasing in gradients | Requires clean source comparison | BSD-2-Clause |

## 2. VMAF & Full-Reference Metrics Evaluation
> [!IMPORTANT]
> **Operational Directive on VMAF:**
> Netflix VMAF (Video Multi-Method Assessment Fusion) is a **full-reference metric**. It evaluates the perceptual difference between a compressed encode and its pristine master reference.
> - VMAF **CANNOT** evaluate whether the original creative edit was "good" or "bad".
> - When transcoding masters for streaming delivery (e.g. ProRes master -> H.264 web delivery), VMAF is applied with a target threshold $\ge 93.0$ (SDR) or $\ge 90.0$ (HDR model `vmaf_b_v0.6.3`).
> - When no reference master exists, non-reference statistical checks (bitrate variance, black frames, freeze frames, audio clipping) are applied.
