# Character Consistency & Reference Control Research
**Project:** Universal AI Video Production Studio  
**Department:** 15_ai_generation & 12_character_production  
**Document:** CHARACTER_CONSISTENCY_RESEARCH.md  
**Version:** 1.0.0  

---

## 1. The Character Consistency Problem in Generative Video

A fundamental challenge in AI film production is preventing character drift across different shots, angles, lighting environments, and costumes. Standard generative models sample random visual attributes if the seed or prompt phrasing changes slightly.

---

## 2. Comparative Conditioning Methodologies

| Methodology | Identity Fidelity | Pose Control | Clothing Retention | Compute Overhead | Setup Latency | Studio Evaluation |
|---|---|---|---|---|---|---|
| **IP-Adapter (Plus/Face)** | High (80-85%) | Moderate | Low (Cross-attends to image) | Low (In-inference) | Real-time (0 sec) | **Primary Rapid Shot Conditioning** |
| **Character LoRA ($r=16$)** | Very High (90-95%) | High | Configurable (Separate tokens) | Medium (Training step) | ~5-10 minutes training | **Primary Hero Character Pipeline** |
| **Reference-Only Attention Injection**| Moderate (75%) | High | Moderate | Low | Real-time | **Secondary Background Actor Control** |
| **ControlNet (OpenPose / Canny)**| N/A (Spatial only) | Absolute | N/A | Low | Real-time | **Primary Pose & Blocking Guidance** |
| **Commercial Reference API (Midjourney --cref, Kling C-Ref)**| High (85-90%) | Model-dependent | Moderate to High | API standard | Instant | **Approved Cloud Reference** |

---

## 3. Production Character Reference Profile Schema

To guarantee repeatability, every hero character is registered in `character_profiles` with a standardized reference pack:

```
┌────────────────────────────────────────────────────────┐
│              CharacterReferenceProfile                 │
├────────────────────────────────────────────────────────┤
│  character_id: UUID                                    │
│  name: "Captain Maya Lin"                              │
│  face_embeddings: 512-dim ArcFace vector               │
│  turnaround_sheet:                                     │
│    - front_view_asset_id: UUID                         │
│    - side_view_asset_id: UUID                          │
│    - three_quarter_view_asset_id: UUID                 │
│    - rear_view_asset_id: UUID                          │
│  costume_presets:                                      │
│    - "standard_flight_suit": asset_id                  │
│    - "civilian_jacket": asset_id                       │
│  hair_and_features:                                    │
│    - hairstyle: "high braided ponytail, raven black"   │
│    - eye_color: "dark amber"                           │
│    - distinguishing_mark: "scar across left eyebrow"   │
│  negative_identity_prompt: "blonde, blue eyes, glasses"│
└────────────────────────────────────────────────────────┘
```

---

## 4. Quantitative Validation Protocol

Before a generated shot is committed to the timeline:
1. Face detection extracts the actor's face crop via RetinaFace.
2. Cosine similarity between the crop embedding $e_{gen}$ and canonical embedding $e_{ref}$ must satisfy:
   $$\text{Sim}(e_{gen}, e_{ref}) = \frac{e_{gen} \cdot e_{ref}}{\|e_{gen}\| \|e_{ref}\|} \ge 0.72$$
3. If similarity falls below $0.72$, the job is flagged for human review or automatic regeneration with tightened IP-Adapter weight.
