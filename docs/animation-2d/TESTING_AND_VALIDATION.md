# 2D ANIMATION TESTING & ACCEPTANCE SPECIFICATION
**Department:** 10_animation_2d & 12_character_production  
**Topic:** Verification Protocol and Minimum Acceptance Criteria  

---

## 1. Acceptance Verification Protocol

To guarantee production readiness, Department 10 and Department 12 must pass 12 comprehensive acceptance tests:

1. **Original Character Concept Generation:** Creates structured character DNA from a text brief.
2. **Turnaround Model Sheet (Settei):** Generates 5-view turnaround with horizontal alignment guides.
3. **Identity Consistency Across Poses:** Preserves character proportions and color palette across 5 distinct poses (Standing, Walking, Running, Sitting, Jumping).
4. **Facial Expression Matrix:** Generates 8 distinct expressions with eye and mouth changes.
5. **Frame-by-Frame Walk Cycle:** Generates an 8-frame loop animating on 2s with contact, down, pass, and up poses.
6. **Skeletal 2D Character Rigging:** Evaluates 2D bone tree with analytical 2-Bone Inverse Kinematics (IK).
7. **Cut-Out Puppet Animation:** Animates segmented body parts around explicit pivot points.
8. **Anime Multiplane Background:** Renders layered parallax environment (Foreground, Midground, Sky).
9. **Two-Character Dialogue Scene:** Stages two characters with speech-synced mouth visemes.
10. **Pose-Guided Motion Sequence:** Retargets a reference motion sequence to an animated character rig.
11. **Transparent Alpha Video Export:** Renders transparent Apple ProRes 4444 / PNG sequence.
12. **NLE Editorial Timeline Insertion:** Inserts rendered animation asset onto the Part 05 timeline.

---

## 2. Consistency Pass/Fail Thresholds

- **Proportion Drift:** Maximum deviation across poses must not exceed 5%.
- **Color Palette Drift:** Euclidean distance $\Delta E$ in Lab space must be $< 8.0$.
- **Temporal Stability:** Zero single-frame flicker or limb popping.

