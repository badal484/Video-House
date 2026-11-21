# Audio Editing Workflows & Non-Destructive Operations
**Project:** Universal AI Video Production Studio  
**Department:** 14_audio_production  
**Document:** AUDIO_EDITING_WORKFLOWS.md  
**Version:** 1.0.0  

---

## 1. Non-Destructive Editorial Philosophy

All audio editing operations in Department 14 are strictly **non-destructive**. The underlying source audio assets in storage remain immutable. Edits represent metadata offsets, gain transformations, crossfades, and routing instructions evaluated at render time.

---

## 2. Core Editing Operations

### 2.1 Trimming, Splitting & Slip Editing
1. **Trim In / Trim Out**: Modifies `source_in_sec` and `duration_sec` without moving the original media file.
2. **Split at Timestamp ($t$)**:
   - Clip A: Duration becomes $t - \text{start\_time}$.
   - Clip B: Start time becomes $t$, `source_in` becomes $\text{source\_in} + (t - \text{start\_time})$, duration becomes remaining duration.
3. **Slip Edit**: Shifts `source_in_sec` forward or backward while preserving timeline position (`start_time_sec`) and clip duration.

### 2.2 Fades & Equal-Power Crossfading
- When two adjacent clips overlap or abut on a track, equal-power crossfading is applied:
  $$g_1(t) = \cos\left(\frac{\pi}{2} \cdot \frac{t}{T_{\text{fade}}}\right), \quad g_2(t) = \sin\left(\frac{\pi}{2} \cdot \frac{t}{T_{\text{fade}}}\right)$$
- Prevents the $3.0\text{ dB}$ center dip that occurs with linear crossfading of uncorrelated signals.

### 2.3 Pitch & Time Warping
- **Pitch Shift**: Alters playback pitch by $\pm 24$ semitones without modifying duration.
- **Time Stretch**: Scales playback speed ($0.5\times$ to $2.0\times$) while maintaining original pitch, allowing dialogue to conform to strict video shot durations.
