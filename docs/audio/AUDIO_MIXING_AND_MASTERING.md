# Audio Mixing, Stem Routing & Mastering Engine
**Project:** Universal AI Video Production Studio  
**Department:** 14_audio_production  
**Document:** AUDIO_MIXING_AND_MASTERING.md  
**Version:** 1.0.0  

---

## 1. Multitrack Mixing Architecture

The multitrack mixer processes multi-bus audio sessions into pristine stereo or surround masters:

```
[Track 1: Lav Dialogue]   ──┐
[Track 2: Boom Dialogue]  ──┼──> [Dialogue Bus] ──┐
[Track 3: Voiceover]      ──┘                     │
                                                  │
[Track 4: Score Music]    ──┐                     │
[Track 5: Beat Layer]     ──┼──> [Music Bus]    ──┼──> [Master Bus] ──> [Mastering Engine]
                            │                     │    - 32-bit Float     - Limiter (-1.0 dBTP)
[Track 6: Foley Steps]    ──┤                     │    - Gain Automation  - EBU R128 Norm
[Track 7: Action Impact]  ──┼──> [SFX/Foley Bus]──┘
[Track 8: City Ambience]  ──┘
```

---

## 2. Panning & Stereo Imaging

- **Constant Power Panning Law**:
  $$\text{Gain}_{\text{Left}} = \cos\left(\frac{\pi}{4}(1 + p)\right), \quad \text{Gain}_{\text{Right}} = \sin\left(\frac{\pi}{4}(1 + p)\right)$$
  Where $p \in [-1.0, +1.0]$ represents pan position ($-1.0 = \text{Hard Left}$, $0.0 = \text{Center}$, $+1.0 = \text{Hard Right}$).
  At center ($p = 0$), both channels receive $\cos(\pi/4) \approx 0.7071$ ($-3.0\text{ dB}$ attenuation), preventing an acoustic center power bump.

---

## 3. Two-Pass Mastering & Standards Conformance

Mastering guarantees exact compliance with broadcasting and streaming specifications:
1. **Pass 1: Measurement**:
   - The master mix is analyzed using ITU-R BS.1770-4 K-weighting filter.
   - Calculates Integrated Loudness ($I$), Loudness Range ($LRA$), and True Peak ($TP$).
2. **Pass 2: Normalization & Brickwall Limiting**:
   - Normalization gain is calculated: $\Delta G = I_{\text{target}} - I_{\text{measured}}$.
   - If $TP + \Delta G > TP_{\text{ceiling}}$ (e.g. $-1.0\text{ dBTP}$), dynamic limiting reduces transients without squashing macro dynamics.
   - Outputs conformant 48 kHz, 24-bit PCM WAV and streaming-ready AAC.
