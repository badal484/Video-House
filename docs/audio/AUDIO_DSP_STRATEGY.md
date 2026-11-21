# Digital Signal Processing (DSP) Strategy
**Project:** Universal AI Video Production Studio  
**Department:** 14_audio_production  
**Document:** AUDIO_DSP_STRATEGY.md  
**Version:** 1.0.0  

---

## 1. Mathematical Foundations & Sample Arithmetic

All internal audio signals are processed at standard professional studio rates:
- **Default Sample Rate ($f_s$)**: 48,000 Hz (48 kHz, standard for film and video synchronization).
- **Internal Data Representation**: IEEE 754 32-bit or 64-bit floating point arrays normalized to $[-1.0, +1.0]$, offering $>1500\text{ dB}$ of internal processing headroom to eliminate digital clipping prior to the final master limiter.
- **Conversion to Integer PCM**:
  - 16-bit integer PCM ($[-32768, +32767]$) for standard distribution.
  - 24-bit integer PCM ($[-8388608, +8388607]$) for studio master delivery.

---

## 2. Parametric Equalization (Biquad IIR Architecture)

Parametric filtering is implemented using Robert Bristow-Johnson's Audio EQ Cookbook digital biquad filter topologies:

$$H(z) = \frac{b_0 + b_1 z^{-1} + b_2 z^{-2}}{a_0 + a_1 z^{-1} + a_2 z^{-2}}$$

Normalized with $a_0 = 1$:
$$y[n] = b_0 x[n] + b_1 x[n-1] + b_2 x[n-2] - a_1 y[n-1] - a_2 y[n-2]$$

### Supported Filter Topologies:
1. **High-Pass Filter (HPF)**: Second-order Butterworth response ($Q = 0.7071$) attenuating rumble and DC offset below cutoff $f_c$ (default 80 Hz for voice).
2. **Low-Pass Filter (LPF)**: Second-order high-frequency rolloff above $f_c$ (default 16 kHz for natural warmth).
3. **Peaking / Bell Filter**: Centered at frequency $f_0$ with bandwidth $Q$ and gain $A = 10^{G_{\text{dB}}/40}$.
4. **Low Shelf / High Shelf**: Smooth gain transition below or above transition frequency with slope parameter $S = 1.0$.
5. **Notch / Bandstop Filter**: Extreme high-Q rejection ($Q \ge 30$) for removing 50 Hz / 60 Hz electrical mains hum and CRT monitor hum.

---

## 3. Dynamic Range Control

### 3.1 Peak & RMS Compression
The compressor operates on decibel envelope detection:
1. **Detection**:
   $$x_{\text{dB}}[n] = 20 \log_{10}(\max(|x[n]|, 10^{-6}))$$
2. **Gain Computing Function ($f(x_{\text{dB}})$)**:
   $$y_{\text{dB}} = \begin{cases} x_{\text{dB}} & x_{\text{dB}} \le T - \frac{W}{2} \\ x_{\text{dB}} + \frac{(1/R - 1)(x_{\text{dB}} - T + W/2)^2}{2W} & T - \frac{W}{2} < x_{\text{dB}} \le T + \frac{W}{2} \\ T + \frac{x_{\text{dB}} - T}{R} & x_{\text{dB}} > T + \frac{W}{2} \end{cases}$$
   Where $T$ is threshold (dBFS), $R$ is compression ratio ($\ge 1.0$), and $W$ is knee width (dB).
3. **Ballistics Smoothing (Attack & Release)**:
   Single-pole low-pass filter smoothing envelope gain changes:
   $$\alpha = 1 - e^{-\frac{1}{f_s \tau}}$$
   - $\tau_{\text{attack}}$: typical 5 ms to 25 ms.
   - $\tau_{\text{release}}$: typical 50 ms to 250 ms.

### 3.2 True Peak Limiting
To prevent inter-sample clipping on consumer DAC reconstruction filters, the master limiter employs $4\times$ Whittaker-Shannon sinc interpolation oversampling to calculate inter-sample peaks before applying a zero-overshoot lookahead gain reduction ceiling (default $-1.0\text{ dBTP}$).

---

## 4. Time-Stretching & Pitch Shifting

- **Pitch Shift without Tempo Change**: Solved via Phase Vocoder analysis with phase unwrapping, or via Spotify Pedalboard JUCE C++ implementation.
- **Tempo Shift without Pitch Change**: WSOLA (Waveform Similarity Overlap-Add) or resampling followed by pitch restoration.
