# Transition and Effect Registry
**Project:** Universal AI Video Production Studio  
**Document Version:** 1.0.0  
**Status:** Approved Master Specification  
**Lead Architect:** Principal Video Editing Systems Architect  
**Verification Date:** 2026-11-21  

---

## 1. Editorial Transitions

Transitions represent programmatic temporal blends between two consecutive clips on a track.

```mermaid
flowchart LR
    ClipA["Clip A (Outgoing Head)"] --> TransitionZone["Transition Zone (Overlap Duration)"]
    TransitionZone --> ClipB["Clip B (Incoming Tail)"]
```

### 1.1 Transition Types & Filtergraph Implementation

| Transition Type | Description | FFmpeg Complex Filter | Parameters |
| :--- | :--- | :--- | :--- |
| `HARD_CUT` | Instantaneous cut from outgoing to incoming frame. | Direct stream concat | None |
| `CROSS_DISSOLVE` | Linear crossfade between alpha/luma planes. | `xfade=transition=fade` | `duration`, `offset` |
| `FADE_IN` | Fades up from black to full opacity. | `fade=t=in:st=...:d=...` | `duration`, `color` |
| `FADE_OUT` | Fades down from full opacity to black. | `fade=t=out:st=...:d=...` | `duration`, `color` |
| `DIP_TO_BLACK` | Fades outgoing clip to black, then fades incoming clip up. | `xfade=transition=fadeblack` | `duration`, `color=#000000` |
| `DIP_TO_WHITE` | Fades outgoing clip to white flash, then fades incoming up. | `xfade=transition=fadewhite` | `duration`, `color=#FFFFFF` |
| `WIPE_LEFT` | Incoming clip sweeps in from right to left. | `xfade=transition=wipeleft` | `duration` |
| `WIPE_RIGHT` | Incoming clip sweeps in from left to right. | `xfade=transition=wiperight` | `duration` |
| `SLIDE_UP` | Incoming clip slides upward, pushing outgoing clip out. | `xfade=transition=slideup` | `duration` |
| `PUSH` | Incoming clip pushes outgoing frame horizontally. | `xfade=transition=smoothleft` | `duration` |

### 1.2 Audio Transitions
For audio clips on audio tracks:
- `CROSS_DISSOLVE` maps to FFmpeg `acrossfade=d=duration:c1=tri:c2=tri`.
- `FADE_IN` / `FADE_OUT` maps to `afade=t=in/out:st=start:d=duration:curve=tri`.

---

## 2. Visual & Audio Effects

Effects apply mathematical transformations to individual clips. They may be static or animated via the keyframe engine.

### 2.1 Video Effects Registry

1. **`SCALE` (Spatial Transform)**
   - FFmpeg Filter: `scale=w=iw*scale_x:h=ih*scale_y`
   - Parameters: `scale_x`, `scale_y`, `uniform: bool`
2. **`POSITION` (Translation)**
   - FFmpeg Filter: Combined with `overlay=x=pos_x:y=pos_y`
   - Parameters: `x_offset`, `y_offset` (normalized $[-1.0, 1.0]$ or pixel offsets)
3. **`ROTATION` (Geometric Angle)**
   - FFmpeg Filter: `rotate=angle*PI/180:ow=rotw(angle*PI/180):oh=roth(angle*PI/180)`
   - Parameters: `angle_degrees`
4. **`CROP` (Spatial Truncation)**
   - FFmpeg Filter: `crop=w=out_w:h=out_h:x=x_pos:y=y_pos`
   - Parameters: `left`, `top`, `right`, `bottom`
5. **`OPACITY` (Alpha Modulation)**
   - FFmpeg Filter: `format=yuva420p,colorchannelmixer=aa=opacity`
   - Parameters: `opacity` ($[0.0, 1.0]$)
6. **`BLUR` (Gaussian Spatial Smoothing)**
   - FFmpeg Filter: `gblur=sigma=sigma_val`
   - Parameters: `radius`, `sigma` ($[0.0, 50.0]$)
7. **`BRIGHTNESS` & `CONTRAST` (Luminance Modulation)**
   - FFmpeg Filter: `eq=brightness=b:contrast=c`
   - Parameters: `brightness` ($[-1.0, 1.0]$), `contrast` ($[0.0, 2.0]$)
8. **`SATURATION` (Chroma Intensity)**
   - FFmpeg Filter: `eq=saturation=s`
   - Parameters: `saturation` ($[0.0, 3.0]$, $0.0 = \text{monochrome}$)

### 2.2 Audio Effects Registry

1. **`VOLUME` (Gain Adjustment)**
   - FFmpeg Filter: `volume=eval=frame:volume='gain'`
   - Parameters: `gain_db` or linear amplitude multiplier $[0.0, 4.0]$.
2. **`PAN` (Stereo Spatial Distribution)**
   - FFmpeg Filter: `pan=stereo|c0=gain_l*c0|c1=gain_r*c1`
   - Parameters: `pan` ($-1.0$ full left, $0.0$ center, $+1.0$ full right).
3. **`EQ` (Parametric Equalization)**
   - FFmpeg Filter: `equalizer=f=freq:width_type=q:w=q:g=gain`
   - Parameters: `frequency_hz`, `gain_db`, `q_factor`.
