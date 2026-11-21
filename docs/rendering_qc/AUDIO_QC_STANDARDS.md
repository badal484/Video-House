# Audio Quality Control Standards & Loudness Regulations

## 1. Loudness Compliance Mandates
In global broadcasting, audio loudness is strictly regulated by law to eliminate disruptive volume jumps between television programming and advertisements:
- **CALM Act (United States / FCC):** Mandates compliance with **ATSC A/85**. Target: $-24.0\text{ LUFS} \pm 1.0\text{ LUFS}$.
- **EBU R128 (Europe / International):** Target: $-23.0\text{ LUFS} \pm 0.5\text{ LUFS}$, with maximum true peak $-1.0\text{ dBTP}$.
- **YouTube / Spotify / Web Streaming:** Target: $-14.0\text{ LUFS}$ to $-16.0\text{ LUFS}$ with true peak $-1.0\text{ dBTP}$ to $-2.0\text{ dBTP}$.
- **Apple Podcasts / Music:** Target: $-16.0\text{ LUFS} \pm 1.0\text{ LUFS}$.

## 2. Audio Measurement Specifications (ITU-R BS.1770-4)
ITU-R BS.1770-4 defines the algorithms for objective loudness measurement:
1. **K-Weighting Filter:** A two-stage filter simulating the acoustic frequency sensitivity of the human ear (pre-filter shelf + high-pass filter).
2. **Gating Algorithm:**
   - Absolute Threshold: Gates out signals below $-70\text{ LUFS}$.
   - Relative Threshold: Gates out signals $10\text{ LU}$ below the ungated average, preventing long silent pauses from lowering the dialogue loudness calculation.
3. **Loudness Range (LRA - EBU Tech 3342):** Measures the statistical distribution of loudness across the program:
   $$\text{LRA} = P_{95} - P_{10}$$
   A high LRA ($> 18\text{ LU}$) indicates high cinematic dynamic range; a low LRA ($< 6\text{ LU}$) indicates heavily compressed commercial audio.
4. **True-Peak Measurement:** $4\times$ oversampled inter-sample peak detection preventing clipping during digital-to-analog conversion on consumer playback hardware.

## 3. Platform Delivery Specifications Matrix

| Platform Target | Integrated Loudness | Max True Peak | Max Loudness Range (LRA) | Audio Codec & Sample Rate |
| :--- | :--- | :--- | :--- | :--- |
| **Broadcast (EBU R128)** | $-23.0\text{ LUFS} \pm 0.5\text{ LU}$ | $-1.0\text{ dBTP}$ | Profile dependent (typically $\le 20\text{ LU}$) | 24-bit 48kHz Linear PCM |
| **Broadcast (ATSC A/85)** | $-24.0\text{ LUFS} \pm 1.0\text{ LU}$ | $-2.0\text{ dBTP}$ | $\le 18\text{ LU}$ | 24-bit 48kHz Linear PCM / AC-3 |
| **Streaming (YouTube)** | $-14.0\text{ LUFS}$ | $-1.0\text{ dBTP}$ | Unconstrained | AAC-LC $\ge 384\text{ kbps}$ / Opus |
| **Streaming (Netflix Master)**| $-27.0\text{ LUFS} \pm 1.0\text{ LU}$ (Dialogue) | $-2.0\text{ dBTP}$ | Narrative dynamic range | 24-bit 48kHz 5.1 / Atmos PCM |
| **Social (Instagram / TikTok)**| $-14.0\text{ LUFS} \pm 1.0\text{ LU}$ | $-1.0\text{ dBTP}$ | $\le 10\text{ LU}$ (Mobile punchy) | AAC-LC 192–320 kbps Stereo |

## 4. QC Engine Enforcement Strategy
Department 18 evaluates audio against the active `RenderProfile`. A deviation of $> 1.0\text{ LUFS}$ on an EBU R128 profile triggers an automatic `ERROR`, whereas for a social web profile it triggers an `INFO` or `WARNING` with automatic gain normalization remediation advice.

