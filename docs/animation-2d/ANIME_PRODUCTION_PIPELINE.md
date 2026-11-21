# ANIME PRODUCTION PIPELINE SPECIFICATION
**Department:** 10_animation_2d  
**Topic:** Dedicated Anime Workflow: Settei, Layout, Genga, Doga, Shiage, Bijutsu, and Satsuei  

---

## 1. Professional Anime Pipeline Stages

The studio replicates the authentic seven-stage Japanese anime production methodology:

```
[ Script & Storyboard (Ekonte) ]
               │
               ▼
   [ Character Design (Settei) ]
   • Model sheets, color specifications, turnarounds
               │
               ▼
      [ Layout (Reiauto) ]
      • Camera lens, background framing, character staging
               │
               ▼
   [ Key Animation (Genga) ]
   • Extreme poses, action breakdowns, timing charts (Tsume)
               │
               ▼
  [ In-Between Animation (Doga) ]
  • Clean line tracing, intermediate frame holds (on 2s/3s)
               │
               ▼
  [ Ink & Paint Cel Shading (Shiage) ]
  • Flat color base, core shadow layer, specular rim light
               │
               ▼
   [ Background Art (Bijutsu) ]
   • Multiplane layered painting (Foreground, Mid, Sky)
               │
               ▼
 [ Anime Photography & Compositing (Satsuei) ]
 • Multiplane camera pans, lighting blooms, lens flares (Part 07 handoff)
```

---

## 2. Anime Timing & Exposure Rules

### 2.1 Animating on 2s and 3s
Unlike Western 24 FPS full animation where every frame is unique (animating on 1s), anime standardly animates on:
- **On 2s (Ni-mai):** 1 drawing held for 2 frames ($12 \text{ fps}$). Used for walking, standard dialogue, and deliberate physical action.
- **On 3s (San-mai):** 1 drawing held for 3 frames ($8 \text{ fps}$). Used for calm conversational pacing, slow head turns, and background characters.
- **On 1s (Ichi-mai):** 1 drawing held for 1 frame ($24 \text{ fps}$). Reserved exclusively for high-speed impact frames, fast weapon swings, and explosive action moments.

### 2.2 Three-Tier Anime Cel Shading
1. **Flat Base Tone (`color_base`):** Solid base local color for skin, hair, and clothing.
2. **Core Shadow Tone (`color_shadow`):** Tinted darker tone applied along anatomical creases and clothing folds according to scene light direction.
3. **Rim / Specular Highlight (`color_highlight`):** Bright edge line along hair strands and shoulder edges simulating backlight radiance.

