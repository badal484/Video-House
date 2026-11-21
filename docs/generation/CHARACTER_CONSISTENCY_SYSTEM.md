# Character & Scene Consistency System
**Project:** Universal AI Video Production Studio  
**Department:** 15_ai_generation & 12_character_production  
**Document:** CHARACTER_CONSISTENCY_SYSTEM.md  
**Version:** 1.0.0  

---

## 1. The Multi-Layer Consistency Hierarchy

To maintain continuity across scenes, character attributes are partitioned into immutable vs variable layers:

```
[Layer 1: Identity DNA (Immutable)]  --> Bone structure, eye shape, ear height, scars
                 │
[Layer 2: Grooming (Semi-Stable)]    --> Hairstyle, beard, hair color
                 │
[Layer 3: Wardrobe (Scene-Specific)] --> Costume, armor, jewelry, glasses
                 │
[Layer 4: State (Dynamic)]           --> Facial expression, dirt, blood, sweat, wetness
```

---

## 2. Review & Approval Protocol

1. When a new shot is generated, the character crop is scored against approved references in `character_profiles`.
2. If similarity $\ge 0.75$, the shot is automatically tagged `VALIDATION_PASSED`.
3. If similarity is between $0.65$ and $0.74$, the shot is tagged `NEEDS_REVIEW` and routed to the Human-in-the-Loop approval dashboard.
4. If similarity $< 0.65$, the generation is flagged as character drift and discarded.
