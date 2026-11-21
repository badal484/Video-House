"""
Canonical Planning and Creative Direction Data Models for Part 04.
Supports Mode A (Create from Scratch) and Mode B (Edit Existing Footage with References).
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from core.assets.intelligence_models import (
    CameraAngle,
    CameraMotionType,
    ShotScale,
    TimecodeRange,
    TransitionType
)

def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

# ---------------------------------------------------------
# Categorical Enums
# ---------------------------------------------------------

class ProductionType(str, Enum):
    CINEMATIC_FILM = "CINEMATIC_FILM"
    SHORT_FILM = "SHORT_FILM"
    COMMERCIAL = "COMMERCIAL"
    SOCIAL_MEDIA = "SOCIAL_MEDIA"
    YOUTUBE_VIDEO = "YOUTUBE_VIDEO"
    DOCUMENTARY = "DOCUMENTARY"
    MUSIC_VIDEO = "MUSIC_VIDEO"
    EXPLAINER = "EXPLAINER"
    FACELESS_CONTENT = "FACELESS_CONTENT"
    ANIMATION_2D = "ANIMATION_2D"
    ANIMATION_3D = "ANIMATION_3D"
    ANIME = "ANIME"
    MOTION_GRAPHICS = "MOTION_GRAPHICS"
    VFX_SEQUENCE = "VFX_SEQUENCE"
    HYBRID_LIVE_AI = "HYBRID_LIVE_AI"

class PacingStyle(str, Enum):
    FAST_PACED = "FAST_PACED"
    DYNAMIC_BALANCED = "DYNAMIC_BALANCED"
    CALM_CONTEMPLATIVE = "CALM_CONTEMPLATIVE"
    RHYTHMIC_MONTAGE = "RHYTHMIC_MONTAGE"
    SLOW_BURN = "SLOW_BURN"

class ApprovalStatus(str, Enum):
    DRAFT = "DRAFT"
    PENDING_REVIEW = "PENDING_REVIEW"
    APPROVED = "APPROVED"
    REVISION_REQUESTED = "REVISION_REQUESTED"
    REJECTED = "REJECTED"

class PlanningEntityType(str, Enum):
    CREATIVE_BRIEF = "CREATIVE_BRIEF"
    CREATIVE_CONCEPTS = "CREATIVE_CONCEPTS"
    SCRIPT = "SCRIPT"
    SHOT_LIST = "SHOT_LIST"
    STORYBOARD = "STORYBOARD"
    EDITING_BLUEPRINT = "EDITING_BLUEPRINT"
    PRODUCTION_BREAKDOWN = "PRODUCTION_BREAKDOWN"
    PRODUCTION_BLUEPRINT = "PRODUCTION_BLUEPRINT"

class ProductionTaskType(str, Enum):
    EXISTING_FOOTAGE_CONFORMANCE = "EXISTING_FOOTAGE_CONFORMANCE"
    AI_VIDEO_GENERATION = "AI_VIDEO_GENERATION"
    AI_IMAGE_GENERATION = "AI_IMAGE_GENERATION"
    MOTION_GRAPHICS_CREATION = "MOTION_GRAPHICS_CREATION"
    ANIMATION_2D = "ANIMATION_2D"
    ANIMATION_3D = "ANIMATION_3D"
    VFX_COMPOSITING = "VFX_COMPOSITING"
    VOICEOVER_RECORDING = "VOICEOVER_RECORDING"
    MUSIC_INTEGRATION = "MUSIC_INTEGRATION"
    SOUND_DESIGN = "SOUND_DESIGN"

class ContinuityRuleType(str, Enum):
    CHARACTER_APPEARANCE = "CHARACTER_APPEARANCE"
    WARDROBE = "WARDROBE"
    PROP = "PROP"
    SPATIAL_AXIS = "SPATIAL_AXIS"
    LIGHTING = "LIGHTING"
    TIMELINE = "TIMELINE"
    AUDIO_VOICE = "AUDIO_VOICE"

class MissingCoverageSolution(str, Enum):
    AI_VIDEO_GENERATION = "AI_VIDEO_GENERATION"
    STOCK_FOOTAGE = "STOCK_FOOTAGE"
    MOTION_GRAPHICS = "MOTION_GRAPHICS"
    REVISE_EDIT = "REVISE_EDIT"
    VOICEOVER_ONLY = "VOICEOVER_ONLY"

class ComplexityCategory(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class DialogueType(str, Enum):
    DIALOGUE = "DIALOGUE"
    VOICEOVER = "VOICEOVER"
    NARRATION = "NARRATION"
    OFF_SCREEN = "OFF_SCREEN"

# ---------------------------------------------------------
# Core Planning Data Structures
# ---------------------------------------------------------

@dataclass
class CreativeBrief:
    brief_id: UUID
    project_id: UUID
    # Project Identity
    project_name: str
    production_type: ProductionType
    genre: str
    target_duration_sec: float
    intended_platform: str
    aspect_ratio: str = "16:9"
    resolution: str = "1920x1080"
    fps: float = 24.0
    language: str = "en"
    target_audience: str = "General audience"
    # Creative Objective
    purpose: str = ""
    core_message: str = ""
    desired_audience_response: str = ""
    call_to_action: Optional[str] = None
    emotional_objective: str = ""
    narrative_objective: str = ""
    # Creative Direction
    visual_style: str = "Cinematic Realism"
    cinematography: str = "Smooth dynamic camera moves"
    lighting_style: str = "High contrast dramatic lighting"
    color_palette: List[str] = field(default_factory=lambda: ["#000000", "#FFFFFF", "#1E3A8A", "#D97706"])
    pacing_style: PacingStyle = PacingStyle.DYNAMIC_BALANCED
    typography_style: str = "Clean modern sans-serif"
    sound_design_notes: str = "Punchy impact sound design with deep sub-bass hits"
    music_direction: str = "Driving cinematic electronic orchestral"
    # Production Constraints
    available_footage_ids: List[UUID] = field(default_factory=list)
    reference_asset_ids: List[UUID] = field(default_factory=list)
    budget_tier: str = "STANDARD"
    model_restrictions: List[str] = field(default_factory=list)
    exclusions: List[str] = field(default_factory=list)
    assumptions: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=utc_now_iso)
    version: int = 1

@dataclass
class CreativeConcept:
    concept_id: UUID
    project_id: UUID
    name: str
    creative_premise: str
    narrative_approach: str
    visual_treatment: str
    cinematography_style: str
    color_direction: str
    sound_direction: str
    editing_rhythm: str
    motion_graphics_style: str
    production_complexity: ComplexityCategory
    estimated_generation_requirements: Dict[str, Any] = field(default_factory=dict)
    risks_and_limitations: List[str] = field(default_factory=list)
    is_selected: bool = False
    created_at: str = field(default_factory=utc_now_iso)

@dataclass
class DialogueEntry:
    entry_id: UUID
    speaker: str
    text: str
    entry_type: DialogueType = DialogueType.VOICEOVER
    estimated_duration_sec: float = 2.0
    emotional_direction: str = "Neutral"

@dataclass
class ScriptScene:
    scene_id: UUID
    script_id: UUID
    scene_number: int
    title: str
    slugline: str  # e.g. "EXT. MOUNTAIN HIGHWAY - NIGHT"
    narrative_purpose: str
    location: str
    time_of_day: str
    characters_present: List[str] = field(default_factory=list)
    action_description: str = ""
    dialogue_entries: List[DialogueEntry] = field(default_factory=list)
    emotional_tone: str = "Tense anticipation"
    estimated_duration_sec: float = 8.0
    continuity_notes: str = ""

@dataclass
class ProductionScript:
    script_id: UUID
    project_id: UUID
    title: str
    logline: str
    target_duration_sec: float
    estimated_spoken_duration_sec: float
    total_words: int
    scenes: List[ScriptScene] = field(default_factory=list)
    version: int = 1
    created_at: str = field(default_factory=utc_now_iso)

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

@dataclass
class CharacterProfile:
    character_id: UUID
    project_id: UUID
    name: str
    age_appearance: str
    gender: str
    physical_description: str
    costume_wardrobe: str
    personality_traits: List[str] = field(default_factory=list)
    reference_asset_ids: List[UUID] = field(default_factory=list)
    voice_profile_id: Optional[str] = None
    continuity_rules: List[str] = field(default_factory=list)

@dataclass
class EnvironmentProfile:
    environment_id: UUID
    project_id: UUID
    name: str
    description: str
    location_type: str  # "INTERIOR", "EXTERIOR", "STUDIO", "ABSTRACT"
    lighting_conditions: str
    time_of_day: str
    spatial_layout: str
    reference_asset_ids: List[UUID] = field(default_factory=list)

@dataclass
class PropEntity:
    prop_id: UUID
    project_id: UUID
    name: str
    description: str
    reference_asset_ids: List[UUID] = field(default_factory=list)
    continuity_rules: List[str] = field(default_factory=list)

@dataclass
class ContinuityRule:
    rule_id: UUID
    project_id: UUID
    rule_type: ContinuityRuleType
    description: str
    affected_scenes: List[UUID] = field(default_factory=list)
    affected_shots: List[UUID] = field(default_factory=list)
    is_active: bool = True

@dataclass
class ProductionTask:
    task_id: UUID
    shot_id: Optional[UUID]
    task_type: ProductionTaskType
    description: str
    assigned_department: str
    status: str = "PLANNED"
    dependencies: List[UUID] = field(default_factory=list)
    estimated_duration_sec: float = 3.0
    estimated_cost_usd: float = 0.0

@dataclass
class ProductionBreakdown:
    breakdown_id: UUID
    project_id: UUID
    tasks: List[ProductionTask] = field(default_factory=list)
    total_shots: int = 0
    shots_by_type: Dict[str, int] = field(default_factory=dict)
    required_assets_summary: Dict[str, Any] = field(default_factory=dict)
    missing_assets_summary: Dict[str, Any] = field(default_factory=dict)
    estimated_cost_usd: float = 0.0
    technical_risks: List[str] = field(default_factory=list)

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

@dataclass
class ProductionFeasibility:
    feasibility_id: UUID
    project_id: UUID
    overall_feasibility_score: float  # 0.0 to 1.0
    complexity_category: ComplexityCategory
    estimated_cost_range: Dict[str, float] = field(default_factory=lambda: {
        "min_usd": 0.0,
        "max_usd": 0.0,
        "known_cost_usd": 0.0,
        "uncertainty_usd": 0.0
    })
    cloud_dependencies: List[str] = field(default_factory=list)
    local_hardware_feasibility: Dict[str, Any] = field(default_factory=dict)
    technical_risks: List[str] = field(default_factory=list)
    recommended_alternatives: List[str] = field(default_factory=list)

@dataclass
class CreativeApproval:
    approval_id: UUID
    project_id: UUID
    entity_type: PlanningEntityType
    entity_id: UUID
    version: int
    status: ApprovalStatus = ApprovalStatus.PENDING_REVIEW
    reviewer_notes: str = ""
    approved_by: Optional[str] = None
    approved_at: Optional[str] = None

@dataclass
class ProductionBlueprint:
    blueprint_id: UUID
    project_id: UUID
    version: int
    brief: CreativeBrief
    selected_concept: Optional[CreativeConcept]
    script: Optional[ProductionScript]
    planned_shots: List[PlannedShot] = field(default_factory=list)
    storyboard: List[StoryboardFrame] = field(default_factory=list)
    characters: List[CharacterProfile] = field(default_factory=list)
    environments: List[EnvironmentProfile] = field(default_factory=list)
    props: List[PropEntity] = field(default_factory=list)
    continuity_rules: List[ContinuityRule] = field(default_factory=list)
    breakdown: Optional[ProductionBreakdown] = None
    editing_blueprint: Optional[EditingBlueprint] = None
    feasibility: Optional[ProductionFeasibility] = None
    approvals: List[CreativeApproval] = field(default_factory=list)
    is_ready_for_production: bool = False
    created_at: str = field(default_factory=utc_now_iso)

