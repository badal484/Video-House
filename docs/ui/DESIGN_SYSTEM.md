# Design System Specification & Token Definitions

## 1. Token Taxonomy

Our design system uses a strict 3-tier token hierarchy:
1. **Global Reference Tokens:** Raw primitive values (e.g. `color-gray-900: #121316`, `font-family-mono: 'JetBrains Mono'`).
2. **Semantic System Tokens:** Functional UI roles (e.g. `--studio-bg-canvas`, `--studio-border-focus`, `--studio-text-primary`).
3. **Component Tokens:** Specific widget parameters (e.g. `--button-height-sm: 28px`, `--track-height-default: 44px`).

---

## 2. Semantic Color Specifications

| Token Name | Value | Purpose |
| :--- | :--- | :--- |
| `--studio-bg-canvas` | `#0D0E11` | Deep background behind panels and timeline |
| `--studio-bg-surface` | `#14161B` | Base surface for sidebars and toolbars |
| `--studio-bg-panel` | `#1A1D24` | Primary panel container background |
| `--studio-bg-panel-elevated` | `#222630` | Cards, popovers, dropdown menus, modals |
| `--studio-bg-hover` | `#2B303C` | Hover state for buttons and list rows |
| `--studio-bg-active` | `#343B4A` | Active, pressed, and selected item state |
| `--studio-border-subtle` | `#252932` | Subtle panel boundaries and track grid lines |
| `--studio-border-default` | `#323846` | Standard inputs, buttons, and divider borders |
| `--studio-border-focus` | `#00F0FF` | 2px focus ring for active keyboard control |
| `--studio-accent-primary` | `#00F0FF` | Cyan accent for playhead, active tools, confirm |
| `--studio-accent-secondary`| `#6366F1` | Indigo accent for secondary AI agent actions |
| `--studio-status-success` | `#10B981` | Completed renders, passed QC checks |
| `--studio-status-warning` | `#F59E0B` | Budget thresholds, non-blocking QC warnings |
| `--studio-status-error` | `#EF4444` | Render failures, offline media, blocking QC |

---

## 3. Component Gallery & Standard States

### Buttons
- **Variants:** Primary (`.btn-primary`, cyan filled), Secondary (`.btn-secondary`, panel elevated), Danger (`.btn-danger`, crimson), Ghost (`.btn-ghost`, transparent borderless).
- **Sizes:** Small (`height: 28px`, `padding: 0 10px`, `font-size: 12px`), Medium (`height: 34px`, `padding: 0 14px`, `font-size: 13px`).

### Inputs & Selects
- Height: 28px / 32px, background: `--studio-bg-canvas`, border: 1px solid `--studio-border-default`, focus: 2px solid `--studio-border-focus`.

### Timeline Track Items
- Rounded 4px corners, solid category header, waveform/thumbnail canvas backdrop, selection highlight.
