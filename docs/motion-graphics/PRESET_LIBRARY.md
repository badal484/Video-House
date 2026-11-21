# Motion Graphics Preset Library Specification
**Project:** Universal AI Video Production Studio  
**Milestone:** Part 06 — Professional Motion Graphics & Typography Studio  
**Document Version:** 1.0.0  
**Lead Architect:** Principal Motion Graphics Engineer  
**Date:** 2026-11-21  

---

## 1. Preset Library Architecture

The Preset Registry (`departments/09_motion_graphics/presets/preset_registry.py`) provides parameterized, production-ready motion graphics templates. Each preset defines strict input schemas, default values, aspect-ratio adaptations, and rendering configurations.

---

## 2. Core Built-In Preset Categories

### 2.1 Category 1: Kinetic Typography
- **`preset_kinetic_typewriter`:** Typewriter text with animated blinking cursor line.
- **`preset_kinetic_word_pop`:** High-energy pop-in reveal synchronized to speech cadence.
- **`preset_kinetic_split_reveal`:** Upper and lower halves slide apart revealing title text.

### 2.2 Category 2: Titles & Editorial Graphics
- **`preset_title_cinematic_hero`:** Wide-spaced, slow zoom-in title with subtle glow and letterbox bars.
- **`preset_title_film_credits`:** Vertical scrolling end credits with department headers and names.
- **`preset_title_chapter_card`:** Minimalist chapter number, title, and elegant divider line.

### 2.3 Category 3: Lower Thirds
- **`preset_lower_third_documentary`:** Two-line clean corporate/documentary nameplate with solid accent bar.
- **`preset_lower_third_breaking_news`:** Urgent banner with ticker animation and red/white high-contrast theme.
- **`preset_lower_third_tech_minimal`:** Monospace font with animated corner brackets and tracking coordinate readout.

### 2.4 Category 4: Infographics & Data Visualizations
- **`preset_chart_animated_bar`:** Dynamic vertical/horizontal bar chart with growing bars and floating values.
- **`preset_chart_progress_ring`:** Circular animated progress indicator (0% to 100%) with central value counter.
- **`preset_chart_metric_counter`:** Rapid numerical counter animation ($0 \to N$) with unit suffix.

### 2.5 Category 5: Brand & Logo Animation
- **`preset_brand_shape_reveal`:** Geometric bounding shapes sweep in, rotating into brand mark alignment.
- **`preset_brand_wordmark_glow`:** Clean brand wordmark appearing with an optical light sweep.

### 2.6 Category 6: Technical HUD Overlays
- **`preset_hud_targeting_reticle`:** Rotating targeting circle with crosshairs, distance readouts, and scanning lines.
- **`preset_hud_data_telemetry`:** Grid with animated latitude/longitude coordinates, system status, and waveform ticker.

### 2.7 Category 7: Cinematic Graphic Overlays
- **`preset_overlay_light_streaks`:** Subtle horizontal anamorphic light streak sweeps.
- **`preset_overlay_geometric_transition`:** Hexagonal or angled wipes for scene transitions.

---

## 3. Aspect Ratio Adaptation Strategies

Each preset implements automatic layout adaptation:
- **16:9 (Landscape Standard):** Horizontal arrangement, wide safe margins, lower thirds anchored at bottom-left.
- **9:16 (Vertical Social):** Centered vertical stack, larger typography for mobile screens, margins buffered against UI overlays (like, share, comment bars).
- **1:1 (Square Feed):** Balanced center composition with symmetrical margins.

