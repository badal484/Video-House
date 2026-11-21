# Timeline Time Model & Rational Arithmetic Specification
**Project:** Universal AI Video Production Studio  
**Document Version:** 1.0.0  
**Status:** Approved Master Specification  
**Lead Architect:** Principal Video Editing Systems Architect  
**Verification Date:** 2026-11-21  

---

## 1. The Fundamental Problem: Floating-Point Temporal Drift

In standard computer programming, timestamps are commonly stored as floating-point seconds (e.g. `float64`). In professional multi-track non-linear editing, this causes **catastrophic cumulative drift**:

1. A 23.976 fps broadcast timeline running for 1 hour spans 86,313.686 frames. Representing cut points using standard IEEE-754 floats introduces rounding inaccuracies ($1/24 \approx 0.041666666666666664$).
2. Consecutive split, trim, and ripple operations accumulate fractional frame errors. Over hundreds of edits, video cuts desynchronize from audio stems by multiple frames.
3. Sub-frame audio edits (e.g. 48,000 samples/sec vs 24 frames/sec) cannot be reconciled without loss of frame alignment.

---

## 2. Rational Time Model (`RationalTime`)

The studio resolves temporal drift by enforcing immutable **Rational Time Arithmetic** via `core/timeline/time_model.py`:

$$\text{RationalTime}(\text{value}, \text{rate})$$

Where:
- $\text{value} \in \mathbb{Z}$: An integer count of temporal increments (ticks, frames, or audio samples).
- $\text{rate} \in \mathbb{R}^+$: The frequency or timebase (e.g. `24.0`, `25.0`, `29.97`, `30.0`, `48000.0`).

### 2.1 Rescaling and Normalization
When comparing or combining two rational times with different rates, `RationalTime` performs cross-multiplication or rescales to a common target rate:

$$\text{rescaled\_value} = \text{round}\left( \frac{\text{value} \times \text{target\_rate}}{\text{source\_rate}} \right)$$

### 2.2 Mathematical Operators
The `RationalTime` class implements standard Python arithmetic dunder methods:
- **Addition ($+$):** Rescales right operand to left operand's rate and sums values.
- **Subtraction ($-$):** Rescales right operand and subtracts values.
- **Multiplication ($*$):** Multiplies value by an integer or float scalar.
- **Division ($/$):** Computes fractional ratio between two rational times or divides value by scalar.
- **Comparisons ($<, \le, ==, \ne, >, \ge$):** Converts both times to high-precision rational seconds ($t = \text{value} / \text{rate}$) for exact comparison.

---

## 3. Timecode Representation (SMPTE 12M)

`RationalTime` converts bidirectionally between integer frame counts and standard SMPTE timecode strings:

$$\text{HH:MM:SS:FF}$$

### 3.1 Non-Drop-Frame Timecode (NDF)
Used for integer frame rates (24, 25, 30, 48, 50, 60 fps):
$$\text{frames\_per\_sec} = \text{round}(\text{rate})$$
$$\text{FF} = \text{frame\_number} \pmod{\text{frames\_per\_sec}}$$
$$\text{total\_seconds} = \lfloor \text{frame\_number} / \text{frames\_per\_sec} \rfloor$$
$$\text{SS} = \text{total\_seconds} \pmod{60}$$
$$\text{total\_minutes} = \lfloor \text{total\_seconds} / 60 \rfloor$$
$$\text{MM} = \text{total\_minutes} \pmod{60}$$
$$\text{HH} = \lfloor \text{total\_minutes} / 60 \rfloor$$

### 3.2 Drop-Frame Timecode (DF)
For NTSC broadcast rates (29.97 fps = 30000/1001), SMPTE 12M drops frame numbers 0 and 1 at the start of every minute, except every 10th minute, to maintain real-time clock synchronization.

---

## 4. TimeRange Specification

A continuous temporal interval defined by a starting point and a duration:

```python
@dataclass(frozen=True)
class TimeRange:
    start_time: RationalTime
    duration: RationalTime
```

### Derived Properties
- `end_time = start_time + duration`
- `contains(t: RationalTime) \iff start_time \le t < end_time`
- `overlaps(other: TimeRange) \iff \max(start_time, other.start_time) < \min(end_time, other.end_time)`
- `intersection(other: TimeRange)`: Returns overlapping interval or `None`.

---

## 5. Standard Studio Timebases

| Format / Platform | Canonical Rate | Rational Representation | Use Case |
| :--- | :---: | :---: | :--- |
| **Cinema / Feature Film** | 24.0 | `RationalTime(frames, 24)` | Mode A cinematic generations & masters |
| **NTSC Broadcast / Film** | 23.976 | `RationalTime(frames * 1001, 24000)` | Standard US delivery |
| **PAL Broadcast (EU)** | 25.0 | `RationalTime(frames, 25)` | European broadcast and streaming |
| **NTSC Video** | 29.97 | `RationalTime(frames * 1001, 30000)` | US television |
| **Web / YouTube / High Frame Rate** | 60.0 | `RationalTime(frames, 60)` | Fast action, UI screencasts, gaming |
| **Digital Audio Master** | 48000.0 | `RationalTime(samples, 48000)` | Studio standard audio synchronization |
