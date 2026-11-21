# Creative Direction Specification
**Project:** Universal AI Video Production Studio  
**Document Version:** 1.0.0  
**Department:** 06 Creative Direction  
**Last Verified:** 2026-11-21  

---

## 1. Concept Generation Methodology

To prevent generic outputs, Department 06 executes multi-concept generation yielding at least **three materially contrasting concepts**:

| Concept Archetype | Narrative Focus | Cinematography & Motion | Sound Design & Score | Complexity |
| :--- | :--- | :--- | :--- | :---: |
| **Concept 1: The Cinematic Journey** | Atmospheric build-up, emotional mystery, dramatic reveal | Slow deliberate dolly push-ins, crane reveals, f/1.4 shallow DOF | Ambient soundscape swelling to hybrid orchestral crescendo | MEDIUM |
| **Concept 2: Kinetic Velocity** | High-energy dynamic pacing, rapid cuts, impact reveals | Whip pans, fast tracking shots, handheld energy, match cuts | Hyper-compressed modern electronic beats, syncopated impacts | HIGH |
| **Concept 3: Engineered Perfection** | Minimalist precision, macro textures, engineering elegance | Smooth robotic slider moves, architectural locked-off frames | Crisp tactile Foley, isolated acoustic frequencies, silence | LOW |

---

## 2. Stylistic Synthesis & Reference Style Transfer

Department 06 integrates with Part 03's `ReferenceProfile` to translate extracted visual metadata into editorial guidance:
- **Average Shot Length (ASL):** Calibrates target cut frequency (e.g. 2.5s ASL = 24 cuts/min).
- **Color Scripting:** Ingests the 5-color dominant palette (e.g., `#0A0E17`, `#1E2A38`, `#3B82F6`, `#60A5FA`, `#F8FAFC`) directly into prompt templates and grading LUT targets.
- **Rhythmic Sync:** Ingests detected BPM and transient peaks to position narrative transitions on musical downbeats.
- **IP Hygiene Guardrails:** Strictly prohibits cloning trademarked characters, logos, or protected likenesses from reference videos, substituting generic archetypes (e.g., "athletic footwear", "luxury sports sedan").

---

## 3. Human Director Concept Selection

Concepts are persisted to the database and surfaced via the API (`/api/v1/director/projects/{project_id}/concepts`). The human director can select an active concept via:
`POST /api/v1/director/projects/{project_id}/concepts/{concept_id}/select`

Once selected, all downstream screenplay writing, shot planning, and storyboarding align with the chosen concept's visual treatment and pacing.

