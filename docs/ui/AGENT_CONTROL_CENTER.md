# Agent Control Center Specification: Departmental Agents & Telemetry

## 1. Agent Roster & Department Governance

The **Agent Control Center** surfaces the operational state of the studio's 12 autonomous specialist agents:
1. **AI Director Agent:** Creative concepting, screenplay drafting, and production supervision.
2. **Media Ingestion Agent:** Demuxing, proxy generation, and metadata extraction.
3. **Multimodal Intelligence Agent:** Scene detection, audio analysis, optical flow, and OCR.
4. **Editorial Assembly Agent:** OpenTimelineIO cut assembly and transition placement.
5. **Motion Graphics Agent:** Kinetic typography and SVG lower-third generation.
6. **VFX Compositor Agent:** Chroma keying, tracking, and planar compositing.
7. **2D Animation Agent:** Character turnaround synthesis, rigging, and cel shading.
8. **3D Animation Agent:** OpenUSD scene assembly and Blender integration.
9. **Audio Post-Production Agent:** Stem separation, sidechain ducking, and EBU R128 loudness.
10. **Generative Router Agent:** Multi-provider model selection and prompt compilation.
11. **Colorist & Restoration Agent:** ACES grading, look presets, and Super-Resolution upscaling.
12. **Localization & QC Agent:** Multi-language dubbing, lip-sync, and technical QC defect auditing.

---

## 2. Agent Telemetry Card Layout

Each agent is rendered as an actionable telemetry card displaying:
- **Header:** Agent Name, Department Badge, Model/Provider (e.g. `Gemini 1.5 Pro`, `TwelveLabs`, `In-Process DSP`, `VideoToolbox`).
- **Status Indicator:** `IDLE`, `RUNNING`, `AWAITING_APPROVAL`, `COMPLETED`, `FAILED`.
- **Current Task:** Real-time description of active task and elapsed duration.
- **Estimated Cost:** Spend accrued in dollars (`$0.00` to `$1.25`).
- **Action Buttons:** "Assign Task", "Cancel", "Retry", "View Logs", and "Take Over Manually".
