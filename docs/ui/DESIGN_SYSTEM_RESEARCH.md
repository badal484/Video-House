# Design System Research: Studio Aesthetic & Design Tokens

## 1. Aesthetic Foundations: High-Density Dark Theme

Creative software requires a distinctive aesthetic that differs fundamentally from marketing websites or consumer apps:
- **Chromatic Neutrality:** The user interface must never compete with the content being created. Backgrounds use strictly neutral slate tones (`#121316`, `#18191D`, `#22242A`) with zero hue tinting to prevent chromatic adaptation errors when grading footage.
- **High Information Density:** Controls must be compact (28px input heights, 12px/13px font sizes, 4px/8px gutters) so that maximum screen real estate is reserved for video playback and timeline tracks.
- **Visual Hierarchy Through Contrast & Elevation:** Subtle borders (`#2D3139`), micro-shadows, and 3-tier elevation surfaces provide depth without distracting glassmorphism or blur effects.
- **Targeted Accent Colors:** An electrifying Cyan (`#00F0FF`) and Studio Indigo (`#6366F1`) indicate active selection, playhead position, and primary actions. Functional alerts use standardized amber warnings (`#F59E0B`), emerald successes (`#10B981`), and crimson errors (`#EF4444`).

---

## 2. Standardized Design Tokens

### Color Palette Tokens
```css
:root {
  /* Surface Layers */
  --studio-bg-canvas: #0D0E11;
  --studio-bg-surface: #14161B;
  --studio-bg-panel: #1A1D24;
  --studio-bg-panel-elevated: #222630;
  --studio-bg-hover: #2B303C;
  --studio-bg-active: #343B4A;

  /* Borders & Dividers */
  --studio-border-subtle: #252932;
  --studio-border-default: #323846;
  --studio-border-focus: #00F0FF;

  /* Text & Foreground */
  --studio-text-primary: #F3F4F6;
  --studio-text-secondary: #9CA3AF;
  --studio-text-muted: #6B7280;
  --studio-text-inverse: #0D0E11;

  /* Accents & Roles */
  --studio-accent-primary: #00F0FF;
  --studio-accent-secondary: #6366F1;
  --studio-accent-hover: #38F5FF;
  --studio-status-success: #10B981;
  --studio-status-warning: #F59E0B;
  --studio-status-error: #EF4444;
  --studio-status-info: #3B82F6;

  /* Track Categorization Colors */
  --studio-track-video: #2563EB;
  --studio-track-audio: #059669;
  --studio-track-graphics: #D97706;
  --studio-track-vfx: #7C3AED;
  --studio-track-subtitle: #DB2777;
}
```

### Typography Scale
- **Display / Headers:** Clean modern sans-serif (`Inter`, system `-apple-system`, `BlinkMacSystemFont`, `Segoe UI`, `sans-serif`).
- **Timecode & Technical Data:** Monospaced tabular figures (`JetBrains Mono`, `Roboto Mono`, `SF Mono`, `monospace`) guaranteeing zero horizontal jitter when scrubbing timecodes.
- **Sizes:**
  - `font-xs`: 11px (line-height: 14px) — Track labels, timecode sub-frames, badges.
  - `font-sm`: 12px (line-height: 16px) — Standard UI labels, inspector properties, table cells.
  - `font-base`: 13px (line-height: 18px) — Buttons, input text, dropdown items.
  - `font-md`: 15px (line-height: 22px) — Section headings, panel titles.
  - `font-lg`: 18px (line-height: 24px) — Modal titles, project names.
  - `font-xl`: 24px (line-height: 32px) — Dashboard stats, major headers.

### Spacing & Grid Tokens
- 4px baseline rhythm: `4px` (`--space-1`), `8px` (`--space-2`), `12px` (`--space-3`), `16px` (`--space-4`), `24px` (`--space-6`), `32px` (`--space-8`).

---

## 3. Component Interaction States

Every component implements five mandatory states:
1. **Default:** Subdued borders, high contrast text.
2. **Hover:** Subtle surface brightening (`--studio-bg-hover`), clear cursor indicators.
3. **Active / Pressed:** Inner micro-shadow or accent highlight.
4. **Focus-Visible:** 2px solid cyan focus ring (`--studio-border-focus`) with 2px offset for complete keyboard navigation.
5. **Disabled:** 40% opacity, `cursor: not-allowed`, no hover reaction.

