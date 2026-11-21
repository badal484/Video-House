# Color Preview & Non-Destructive Version Control
**Project:** Universal AI Video Production Studio  
**Department:** 16 — Color Grading, Color Management, Video Restoration & Enhancement  
**Document Version:** 1.0.0  
**Verification Date:** 2026-11-21  

---

## 1. Executive Summary

Color grading and video restoration in Department 16 are **100% non-destructive**. Original media files are never overwritten or altered. Every grade is stored as a versioned, serializable `GradingGraph`, allowing instant A/B comparisons, undo/redo operations, and cross-scene look copying.

---

## 2. Preview Modes

1. **Original vs Graded (Split Wipe):**
   Splits the frame vertically or horizontally to compare uncorrected camera footage against the active grade.
2. **Before vs After (Difference Matte):**
   Computes absolute difference ($|I_{graded} - I_{orig}|$) to visualize localized adjustments.
3. **Reference vs Target (Side-by-Side):**
   Displays the target footage alongside an aesthetic reference clip for shot matching.
4. **Resolution-Independent Proxy Grading:**
   The `GradingEngine` evaluates identically on $720\text{p}$ interactive editing proxies and $4\text{K}$ full-resolution masters, guaranteeing zero colorimetric drift between preview and export.

---

## 3. Database Persistence & Versioning

- Table `color_grades`: Stores `grade_id`, `project_id`, `clip_id`, `graph_json`, `version`, `created_at`, `updated_at`.
- Re-saving a grade increments its `version` counter while preserving previous revisions.
- Full provenance metadata is recorded, including algorithm name, model version, and processing parameters.
