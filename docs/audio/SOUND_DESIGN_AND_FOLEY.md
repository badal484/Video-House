# Sound Design & Procedural Foley Engine
**Project:** Universal AI Video Production Studio  
**Department:** 14_audio_production  
**Document:** SOUND_DESIGN_AND_FOLEY.md  
**Version:** 1.0.0  

---

## 1. Sound Design Overview

Sound effects (SFX) and Foley create tactile physical reality and cinematic impact. Department 14 provides two complementary mechanisms:
1. **Curated Audio Asset Library**: Semantic catalog of high-definition recordings (impacts, footsteps, environment, transitions).
2. **Procedural Sound Synthesizer**: Pure programmatic synthesis of cinematic audio assets without external media dependencies.

---

## 2. Procedural Sound Synthesizer Topologies

The procedural engine (`departments/14_audio_production/sound_design/procedural_sfx.py`) uses mathematical equations to synthesize studio sound elements:

### 2.1 Cinematic Impact / Boom
- **Formula**: Swept sine sub-oscillator decaying from $120\text{ Hz}$ to $28\text{ Hz}$ combined with shaped noise transient.
  $$s(t) = e^{-t / \tau_{\text{decay}}} \cdot \sin\left(2\pi \int (f_{\text{start}} e^{-k t}) dt\right) + \text{noise}(t) e^{-t / \tau_{\text{transient}}}$$

### 2.2 Cinematic Whoosh / Transition
- **Formula**: Bandpass-filtered white noise with center frequency swept from $200\text{ Hz}$ up to $4500\text{ Hz}$ and down to $400\text{ Hz}$, modulated by stereo panning across the stereo image $[-0.9, +0.9]$.

### 2.3 Tension Riser
- **Formula**: Dual harmonic saw wave generator with frequency sweeping exponentially from $80\text{ Hz}$ to $1800\text{ Hz}$ over $4.0\text{ seconds}$, terminating in a reverb tail.

### 2.4 Ambient Room Drone
- **Formula**: Multi-sine additive drone ($55\text{ Hz}$, $110\text{ Hz}$, $165\text{ Hz}$) with slow LFO phase modulation ($0.15\text{ Hz}$) and stereo spatial decorrelation.
