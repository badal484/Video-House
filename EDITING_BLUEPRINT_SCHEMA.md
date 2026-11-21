# Editing Blueprint Specification & Data Schema (Mode B)
**Project:** Universal AI Video Production Studio  
**Document Version:** 1.0.0  
**Department:** 07 Production Planning  
**Last Verified:** 2026-11-21  

---

## 1. Overview

In **Mode B (Edit Existing Footage with References)**, the studio does not blindly prompt an LLM to hallucinate timecodes. The `EditingBlueprintService` synthesizes a deterministic, evidence-grounded editorial plan by mapping verified source footage shots (from Part 03 shot boundaries) against the stylistic and rhythmic pacing profile of a reference video.

---

## 2. Evidence-Based Clip Mapping

For every cut, the blueprint defines the exact timecode correspondence:
$$\text{Source Footage Range: } [t_{\text{src\_in}}, t_{\text{src\_out}}] \longrightarrow \text{Timeline Position: } [t_{\text{timeline\_in}}, t_{\text{timeline\_out}}]$$

All timecodes conform to rational time representations (`RationalTime(value, rate)`), preventing floating-point drift over multi-minute sequences.

---

## 3. Missing Coverage Detection & Remediation

When available source footage cannot fulfill the desired timeline duration or pacing rhythm, the engine flags explicit `MissingCoverageItem` entries:

| Missing Element | Detection Trigger | Recommended Remediation |
| :--- | :--- | :--- |
| **Duration Deficit** | Total source take duration < Target duration | Generate supplementary AI B-Roll (`AI_VIDEO_GENERATION`) |
| **Scale Deficit** | Narrative requires establishing shot, but only close-ups exist | Recommend wide drone generation (`AI_VIDEO_GENERATION`) |
| **Detail Deficit** | Narrative mentions fine object, but no macro cut exists | Generate insert shot or motion graphics text overlay |
| **Transition Gap** | Fast reference cut rhythm requires short reaction shots | Ingest stock footage or motion graphics bumpers |

---

## 4. Canonical Data Model (`EditingBlueprint`)

```python
@dataclass
class EditShotMapping:
    mapping_id: UUID
    timeline_in_sec: float
    timeline_out_sec: float
    source_asset_id: UUID
    source_in_sec: float
    source_out_sec: float
    shot_purpose: str
    transition_in: TransitionType = TransitionType.HARD_CUT
    transition_out: TransitionType = TransitionType.HARD_CUT
    color_treatment: str = "Rec.709 Standard"
    speed_ratio: float = 1.0

@dataclass
class MissingCoverageItem:
    item_id: UUID
    intended_timeline_sec: float
    duration_sec: float
    description: str
    recommended_solution: MissingCoverageSolution
    suggested_prompt: str = ""

@dataclass
class EditingBlueprint:
    blueprint_id: UUID
    project_id: UUID
    target_duration_sec: float
    narrative_order: List[EditShotMapping] = field(default_factory=list)
    pacing_style: PacingStyle = PacingStyle.DYNAMIC_BALANCED
    transitions: List[Dict[str, Any]] = field(default_factory=list)
    music_placement: List[Dict[str, Any]] = field(default_factory=list)
    dialogue_placement: List[Dict[str, Any]] = field(default_factory=list)
    sound_effects: List[Dict[str, Any]] = field(default_factory=list)
    motion_graphics: List[Dict[str, Any]] = field(default_factory=list)
    missing_coverage: List[MissingCoverageItem] = field(default_factory=list)
    version: int = 1
    created_at: str = field(default_factory=utc_now_iso)
```
