# Project Management UI Specification

## 1. Project Management Cockpit

The **Project Management System** (Department 02) orchestrates production lifecycles from creative inception to final multi-format delivery:

### 1. Home Dashboard Overview
- **Active Projects Grid:** Visual cards displaying project thumbnail, title, aspect ratio (16:9, 9:16), framerate, duration, last modified timestamp, and active stage pill.
- **Quick Create Actions:**
  - Blank Project
  - YouTube Long-Form (1920x1080 @ 24fps)
  - Social Vertical Reel (1080x1920 @ 30fps)
  - Cinematic 4K Feature (3840x2160 @ 23.976fps)
  - Anime / 2D Animation (1920x1080 @ 12fps on 2s)
- **Production Stage Pipeline Tracker:**
  - Tracks projects across 12 standardized phases: Planning -> Scripting -> Assets -> Generation -> Assembly -> Animation -> VFX -> Audio -> Grading -> Localization -> QC -> Delivery.

### 2. Project Settings Modal
- Configures Canvas Width/Height, Aspect Ratio, Frame Rate, Timebase, Color Space (Rec.709, ACEScg, P3-D65), Audio Sample Rate (48,000 Hz), and Target Platforms.
