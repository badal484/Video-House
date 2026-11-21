# Product UX Research: Universal AI Video Production Studio

## 1. Executive Summary & Vision

The **Universal AI Video Production Studio** is designed as a unified, high-density, professional creative workspace. In traditional post-production workflows, creators, directors, editors, colorists, sound designers, and VFX artists work across fragmented, isolated desktop applications (e.g., Avid Media Composer, Premiere Pro, After Effects, DaVinci Resolve, Pro Tools, Nuke). In modern AI workflows, creators are forced into fragmented web dashboards and chat interfaces (e.g., Runway, Midjourney on Discord, ElevenLabs, Suno, ChatGPT, Claude).

This application bridges both paradigms:
1. **The Rigor and Tactile Feel of Professional Creative Workspaces:** Multi-track non-linear editorial timelines, multi-monitor preview viewports, color wheels, DAW audio mixers, node-based compositing DAGs, and exposure sheets.
2. **Context-Aware Agentic Intelligence:** Deep integration with the AI Director (Department 06), Creative Planning (Department 07), Multimodal Intelligence (Department 04), and Generative Routers (Department 15).

Instead of treating AI as a conversational gimmick or text chatbot sidecar, the studio surfaces AI intelligence as actionable proposals, deterministic tool parameters, and inspectable visual assets directly inside the creative panels.

---

## 2. Core User Personas & Workflows

### Persona A: The Auteur / Independent AI Filmmaker
- **Goal:** Directing an end-to-end cinematic film or short with unified narrative, character continuity, and photorealistic pacing.
- **Pain Point:** Character face drift across generations, disjointed camera movements, manual stitching of video clips with zero temporal rhythm.
- **Studio Solution:** AI Director natural-language brief intake, automatic Settei character turnarounds, shot-by-shot storyboard generation, automated timeline assembly with rational timecode arithmetic, and automated EBU R128 audio finishing.

### Persona B: Commercial Video Producer & Creative Director
- **Goal:** Delivering 16:9 4K master commercials and multi-aspect ratio social derivatives (9:16 vertical reels, 1:1 square feeds) under tight brand guidelines.
- **Pain Point:** Manual re-editing, re-timing subtitles, re-framing graphics, and complex multi-format exports.
- **Studio Solution:** Integrated motion graphics presets, automatic aspect ratio reframing, isochronic subtitle translation, and preflight QC checks for broadcast and streaming deliverables.

### Persona C: Technical Post-Production Supervisor & Editor
- **Goal:** Maintaining strict quality standards, accurate color spaces (ACEScg, Rec.709), broadcast loudness (-23 LUFS), and clean timeline conform.
- **Pain Point:** Opaque AI tools that export low-bitrate compressed MP4s with burned-in defects, audio clipping, and no metadata.
- **Studio Solution:** Visual metrics (PSNR, SSIM, VMAF), automated defect detection (black frames, freeze frames, VFR), ProRes 422 HQ mezzanine intermediate masters, and standardized `delivery_manifest.json` packages.

---

## 3. Guiding Interaction Principles

1. **Direct Manipulation Over Conversational Ambiguity:** Users can click, drag, trim, scrub, and slide parameters. AI generation produces concrete timeline clips, color nodes, and audio envelopes that remain fully editable.
2. **Explainable AI with Approval Gates:** High-cost generations (> $1.00) or structural timeline changes are never executed destructively. They are presented as structured proposals with visual diffs and explicit Approve/Reject controls.
3. **High Information Density Without Visual Clutter:** Standardized 8px grid, compact 28px/32px row heights, collapsible tool drawers, and customizable 4-quadrant docking layouts.
4. **Sub-Millisecond Keyboard Navigation:** Complete J/K/L transport control, 1-frame stepping (`Left`/`Right`), 10-frame jumping (`Shift+Left`/`Shift+Right`), blade cuts (`B`), save (`Cmd+S`), and global search (`Cmd+K`).
5. **Zero-Loss Data Integrity:** Continuous background autosave with visual indicators, project snapshot branching, and persistent SQLite database state.
