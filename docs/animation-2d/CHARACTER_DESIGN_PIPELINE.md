# CHARACTER DESIGN PIPELINE SPECIFICATION
**Department:** 12_character_production & 10_animation_2d  
**Topic:** From Creative Brief to Production-Ready Model Sheets  

---

## 1. Character Design Workflow

```
[ Natural Language Character Brief / Script ]
                     │
                     ▼
        [ Character Concept Generator ]
        • Name, Age, Archetype, Personality
        • Anatomical head-to-body ratio
        • Costume specification & color palette
                     │
                     ▼
        [ Turnaround Geometry Synthesis ]
        • Multi-angle orthographic generation (Front, 3/4, Side, Back)
        • Horizontal alignment guides (head, eyes, hips, heels)
                     │
                     ▼
        [ Model Sheet & Expression Matrix ]
        • 8 Core facial expressions
        • Settei color reference chips (Day, Night, Sunset)
                     │
                     ▼
        [ Identity Registration & Approval ]
        • Registered in Central Asset Registry (SQLite)
        • SHA-256 asset checksums & versioning
        • Ready for 2D rigging or traditional cel animation
```

---

## 2. Character Concept Data Structure

```json
{
  "character_id": "char-9b1deb4d-3b7d",
  "name": "Kaito Vance",
  "visual_style": "ANIME_CEL",
  "age_appearance": "17-19",
  "head_ratio": 7.0,
  "color_palette": {
    "skin_base": "#f8d5c2",
    "skin_shadow": "#dca894",
    "hair_base": "#1a2238",
    "hair_highlight": "#3b558c",
    "eye_iris": "#2b7cd3",
    "costume_primary": "#1f2937",
    "costume_accent": "#f59e0b"
  },
  "distinctive_features": [
    "Asymmetrical bangs parted to left",
    "Amber cybernetic streak in left iris",
    "High-collar jacket with yellow trim"
  ]
}
```

---

## 3. Human Director Approval Gates

Before any character design is transitioned to high-cost production animation:
1. **Design Review:** Director inspects front, 3/4, side, and back turnaround alignment.
2. **Palette Review:** Color chips are approved for daylight, interior, and night scene lighting.
3. **Approval Status:** State transitions from `DRAFT` $\to$ `APPROVED` $\to$ `LOCKED`. Locked characters cannot be mutated without a major version increment.

