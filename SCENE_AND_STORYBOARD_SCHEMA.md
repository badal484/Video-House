# Scene & Storyboard Specification and Data Schema
**Project:** Universal AI Video Production Studio  
**Document Version:** 1.0.0  
**Department:** 06 Creative Direction  
**Last Verified:** 2026-11-21  

---

## 1. Overview

Storyboards in the studio are not decorative sketches. They are **generative prompt specifications** and **composition blueprints** that bridge planned shots to downstream visual generation models (Flux.1, Midjourney, Stable Diffusion XL) and human artists.

---

## 2. Canonical Data Models

### 2.1 PlannedShot Data Model
```python
@dataclass
class PlannedShot:
    shot_id: UUID
    scene_id: UUID
    shot_number: int
    narrative_purpose: str
    shot_scale: ShotScale
    camera_angle: CameraAngle
    camera_motion: CameraMotionType
    lens_focal_length: str = "35mm"
    camera_position: str = "Eye level centered"
    subject_action: str = ""
    environment_description: str = ""
    lighting_direction: str = "Key light from camera left"
    composition_notes: str = "Rule of thirds, subject in right third"
    depth_of_field: str = "Shallow depth of field (f/1.8)"
    focus_behavior: str = "Rack focus from foreground to subject"
    motion_characteristics: str = "Smooth linear push-in"
    start_state: str = "Wide view of darkened environment"
    end_state: str = "Close-up reveal of key product detail"
    estimated_duration_sec: float = 3.0
    aspect_ratio: str = "16:9"
    visual_style: str = "Cinematic hyper-real"
    continuity_requirements: List[str] = field(default_factory=list)
    required_source_assets: List[UUID] = field(default_factory=list)
    generation_requirements: ProductionTaskType = ProductionTaskType.AI_VIDEO_GENERATION
```

### 2.2 StoryboardFrame Data Model
```python
@dataclass
class StoryboardFrame:
    frame_id: UUID
    shot_id: UUID
    scene_id: UUID
    frame_order: int
    visual_prompt_spec: str
    visual_description: str
    character_references: List[str] = field(default_factory=list)
    environment_references: List[str] = field(default_factory=list)
    camera_composition: str = "Medium wide, subject centered"
    lighting_direction: str = "Dramatic rim light"
    continuity_notes: str = ""
    approval_status: ApprovalStatus = ApprovalStatus.DRAFT
    image_asset_id: Optional[UUID] = None
```

---

## 3. Relational Database Tables

### 3.1 `planned_shots` Table
Persists technical cinematography variables, lens focal lengths, camera angles, motions, lighting directions, and task generation requirements with foreign key link to `script_scenes(scene_id)`.

### 3.2 `storyboard_frames` Table
Persists prompt specs, composition guidelines, character/environment cross-references, and approval status with foreign key link to `planned_shots(shot_id)`.

