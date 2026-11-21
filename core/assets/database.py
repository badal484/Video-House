"""
Database models and schema for Central Asset Registry and Multimodal Intelligence.
Uses SQLite for zero-dependency, local-first transactional storage.
Persists all video, audio, vision, motion, OCR, and reference observations.
"""
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
import json
from pathlib import Path
import sqlite3
from typing import Any, Dict, Generator, List, Optional
from uuid import UUID, uuid4

def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

class MediaType(str, Enum):
    VIDEO = "VIDEO"
    AUDIO = "AUDIO"
    IMAGE = "IMAGE"
    SUBTITLE = "SUBTITLE"
    ANIMATION = "ANIMATION"
    THREE_D = "THREE_D"
    PRODUCTION_DOCUMENT = "PRODUCTION_DOCUMENT"
    UNKNOWN = "UNKNOWN"

class AssetRole(str, Enum):
    SOURCE_FOOTAGE = "SOURCE_FOOTAGE"
    REFERENCE_VIDEO = "REFERENCE_VIDEO"
    REFERENCE_AUDIO = "REFERENCE_AUDIO"
    REFERENCE_IMAGE = "REFERENCE_IMAGE"
    MUSIC = "MUSIC"
    SOUND_EFFECT = "SOUND_EFFECT"
    VOICE_RECORDING = "VOICE_RECORDING"
    GENERATED_VIDEO = "GENERATED_VIDEO"
    GENERATED_IMAGE = "GENERATED_IMAGE"
    CHARACTER_REFERENCE = "CHARACTER_REFERENCE"
    ANIMATION_ASSET = "ANIMATION_ASSET"
    THREE_D_MODEL = "THREE_D_MODEL"
    TEXTURE = "TEXTURE"
    LUT = "LUT"
    SUBTITLE = "SUBTITLE"
    SCRIPT = "SCRIPT"
    PROJECT_DOCUMENT = "PROJECT_DOCUMENT"

class ProcessingStatus(str, Enum):
    QUEUED = "QUEUED"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    PARTIAL_SUCCESS = "PARTIAL_SUCCESS"

class DerivativeType(str, Enum):
    THUMBNAIL = "THUMBNAIL"
    CONTACT_SHEET = "CONTACT_SHEET"
    PROXY_VIDEO = "PROXY_VIDEO"
    LIGHTWEIGHT_PREVIEW = "LIGHTWEIGHT_PREVIEW"
    EXTRACTED_AUDIO = "EXTRACTED_AUDIO"
    AUDIO_PREVIEW = "AUDIO_PREVIEW"
    AUDIO_WAVEFORM = "AUDIO_WAVEFORM"
    IMAGE_THUMBNAIL = "IMAGE_THUMBNAIL"
    IMAGE_PREVIEW = "IMAGE_PREVIEW"

@dataclass
class AssetRecord:
    asset_id: UUID
    project_id: UUID
    original_filename: str
    display_name: str
    media_type: MediaType
    detected_format: str
    mime_type: str
    byte_size: int
    checksum_sha256: str
    storage_path: str
    import_timestamp: str
    processing_status: ProcessingStatus
    metadata_status: ProcessingStatus
    derivative_status: ProcessingStatus
    error_message: Optional[str] = None
    version: int = 1
    source_type: str = "UPLOAD"
    license_info: Optional[str] = None
    roles: List[AssetRole] = field(default_factory=list)

@dataclass
class TechnicalMetadata:
    asset_id: UUID
    width: Optional[int] = None
    height: Optional[int] = None
    duration_seconds: Optional[float] = None
    frame_rate: Optional[float] = None
    avg_frame_rate: Optional[float] = None
    is_vfr: bool = False
    video_codec: Optional[str] = None
    audio_codec: Optional[str] = None
    pixel_format: Optional[str] = None
    bit_depth: Optional[int] = None
    aspect_ratio: Optional[str] = None
    color_primaries: Optional[str] = None
    color_transfer: Optional[str] = None
    color_space: Optional[str] = None
    is_hdr: bool = False
    rotation: int = 0
    timecode: Optional[str] = None
    audio_sample_rate: Optional[int] = None
    audio_channels: Optional[int] = None
    audio_channel_layout: Optional[str] = None
    stream_count: int = 0
    bitrate_bps: Optional[int] = None
    raw_probe: Dict[str, Any] = field(default_factory=dict)

@dataclass
class DerivativeRecord:
    derivative_id: UUID
    asset_id: UUID
    derivative_type: DerivativeType
    storage_path: str
    byte_size: int
    mime_type: str
    generation_params: Dict[str, Any]
    created_at: str
    status: ProcessingStatus = ProcessingStatus.COMPLETED

class AssetDatabase:
    """
    SQLite Database Manager for Asset Registry and Multimodal Intelligence.
    Guarantees thread-safe connections, automatic closure, and atomic transactions.
    """
    def __init__(self, db_path: str = "projects/studio_asset_registry.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_tables()

    @contextmanager
    def get_connection(self) -> Generator[sqlite3.Connection, None, None]:
        conn = sqlite3.connect(str(self.db_path), timeout=30.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        try:
            with conn:
                yield conn
        finally:
            conn.close()

    def _init_tables(self):
        with self.get_connection() as conn:
            conn.executescript("""
            CREATE TABLE IF NOT EXISTS projects (
                project_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                settings_json TEXT DEFAULT '{}'
            );

            CREATE TABLE IF NOT EXISTS assets (
                asset_id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                original_filename TEXT NOT NULL,
                display_name TEXT NOT NULL,
                media_type TEXT NOT NULL,
                detected_format TEXT NOT NULL,
                mime_type TEXT NOT NULL,
                byte_size INTEGER NOT NULL,
                checksum_sha256 TEXT NOT NULL,
                storage_path TEXT NOT NULL,
                import_timestamp TEXT NOT NULL,
                processing_status TEXT NOT NULL,
                metadata_status TEXT NOT NULL,
                derivative_status TEXT NOT NULL,
                error_message TEXT,
                version INTEGER DEFAULT 1,
                source_type TEXT DEFAULT 'UPLOAD',
                license_info TEXT,
                FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS asset_roles (
                asset_id TEXT NOT NULL,
                role TEXT NOT NULL,
                PRIMARY KEY (asset_id, role),
                FOREIGN KEY (asset_id) REFERENCES assets(asset_id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS technical_metadata (
                asset_id TEXT PRIMARY KEY,
                width INTEGER,
                height INTEGER,
                duration_seconds REAL,
                frame_rate REAL,
                avg_frame_rate REAL,
                is_vfr INTEGER DEFAULT 0,
                video_codec TEXT,
                audio_codec TEXT,
                pixel_format TEXT,
                bit_depth INTEGER,
                aspect_ratio TEXT,
                color_primaries TEXT,
                color_transfer TEXT,
                color_space TEXT,
                is_hdr INTEGER DEFAULT 0,
                rotation INTEGER DEFAULT 0,
                timecode TEXT,
                audio_sample_rate INTEGER,
                audio_channels INTEGER,
                audio_channel_layout TEXT,
                stream_count INTEGER DEFAULT 0,
                bitrate_bps INTEGER,
                raw_probe_json TEXT,
                FOREIGN KEY (asset_id) REFERENCES assets(asset_id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS derivatives (
                derivative_id TEXT PRIMARY KEY,
                asset_id TEXT NOT NULL,
                derivative_type TEXT NOT NULL,
                storage_path TEXT NOT NULL,
                byte_size INTEGER NOT NULL,
                mime_type TEXT NOT NULL,
                generation_params_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                status TEXT NOT NULL,
                FOREIGN KEY (asset_id) REFERENCES assets(asset_id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS processing_jobs (
                job_id TEXT PRIMARY KEY,
                asset_id TEXT NOT NULL,
                job_type TEXT NOT NULL,
                status TEXT NOT NULL,
                progress_pct INTEGER DEFAULT 0,
                retry_count INTEGER DEFAULT 0,
                max_retries INTEGER DEFAULT 3,
                error_details TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (asset_id) REFERENCES assets(asset_id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS asset_dependencies (
                asset_id TEXT NOT NULL,
                dependent_asset_id TEXT NOT NULL,
                dependency_type TEXT NOT NULL,
                PRIMARY KEY (asset_id, dependent_asset_id),
                FOREIGN KEY (asset_id) REFERENCES assets(asset_id) ON DELETE RESTRICT,
                FOREIGN KEY (dependent_asset_id) REFERENCES assets(asset_id) ON DELETE CASCADE
            );

            -- Part 03 Multimodal Intelligence Tables
            CREATE TABLE IF NOT EXISTS shots (
                shot_id TEXT PRIMARY KEY,
                asset_id TEXT NOT NULL,
                shot_number INTEGER NOT NULL,
                start_sec REAL NOT NULL,
                end_sec REAL NOT NULL,
                start_frame INTEGER NOT NULL,
                end_frame INTEGER NOT NULL,
                transition_in TEXT DEFAULT 'HARD_CUT',
                transition_out TEXT DEFAULT 'HARD_CUT',
                shot_scale TEXT DEFAULT 'UNKNOWN',
                camera_angle TEXT DEFAULT 'UNKNOWN',
                camera_motion TEXT DEFAULT 'STATIC',
                summary TEXT DEFAULT '',
                visual_features_json TEXT DEFAULT '{}',
                confidence REAL DEFAULT 1.0,
                evidence_json TEXT,
                FOREIGN KEY (asset_id) REFERENCES assets(asset_id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS scenes (
                scene_id TEXT PRIMARY KEY,
                asset_id TEXT NOT NULL,
                scene_number INTEGER NOT NULL,
                start_sec REAL NOT NULL,
                end_sec REAL NOT NULL,
                narrative_summary TEXT DEFAULT '',
                setting TEXT DEFAULT '',
                lighting_style TEXT DEFAULT '',
                dominant_mood TEXT DEFAULT '',
                shot_ids_json TEXT DEFAULT '[]',
                confidence REAL DEFAULT 1.0,
                FOREIGN KEY (asset_id) REFERENCES assets(asset_id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS transcripts (
                segment_id TEXT PRIMARY KEY,
                asset_id TEXT NOT NULL,
                speaker_id TEXT DEFAULT 'SPEAKER_00',
                text TEXT NOT NULL,
                start_sec REAL NOT NULL,
                end_sec REAL NOT NULL,
                language TEXT DEFAULT 'en',
                words_json TEXT DEFAULT '[]',
                confidence REAL DEFAULT 1.0,
                FOREIGN KEY (asset_id) REFERENCES assets(asset_id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS audio_events (
                event_id TEXT PRIMARY KEY,
                asset_id TEXT NOT NULL,
                event_type TEXT NOT NULL,
                description TEXT NOT NULL,
                start_sec REAL NOT NULL,
                end_sec REAL NOT NULL,
                spectral_energy REAL,
                confidence REAL DEFAULT 1.0,
                evidence_json TEXT,
                FOREIGN KEY (asset_id) REFERENCES assets(asset_id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS music_segments (
                segment_id TEXT PRIMARY KEY,
                asset_id TEXT NOT NULL,
                start_sec REAL NOT NULL,
                end_sec REAL NOT NULL,
                tempo_bpm REAL NOT NULL,
                beat_timestamps_json TEXT DEFAULT '[]',
                rhythmic_energy REAL DEFAULT 0.5,
                mood TEXT DEFAULT 'neutral',
                has_vocals INTEGER DEFAULT 0,
                confidence REAL DEFAULT 1.0,
                FOREIGN KEY (asset_id) REFERENCES assets(asset_id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS detected_objects (
                detection_id TEXT PRIMARY KEY,
                asset_id TEXT NOT NULL,
                track_id INTEGER NOT NULL,
                label TEXT NOT NULL,
                timestamp_sec REAL NOT NULL,
                frame_number INTEGER NOT NULL,
                box_json TEXT NOT NULL,
                confidence REAL DEFAULT 1.0,
                FOREIGN KEY (asset_id) REFERENCES assets(asset_id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS camera_movements (
                movement_id TEXT PRIMARY KEY,
                asset_id TEXT NOT NULL,
                start_sec REAL NOT NULL,
                end_sec REAL NOT NULL,
                motion_type TEXT NOT NULL,
                magnitude REAL NOT NULL,
                direction_json TEXT DEFAULT '[0.0, 0.0]',
                confidence REAL DEFAULT 1.0,
                evidence_json TEXT,
                FOREIGN KEY (asset_id) REFERENCES assets(asset_id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS ocr_observations (
                ocr_id TEXT PRIMARY KEY,
                asset_id TEXT NOT NULL,
                text TEXT NOT NULL,
                timestamp_sec REAL NOT NULL,
                frame_number INTEGER NOT NULL,
                box_json TEXT NOT NULL,
                text_category TEXT DEFAULT 'GENERAL',
                confidence REAL DEFAULT 1.0,
                FOREIGN KEY (asset_id) REFERENCES assets(asset_id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS reference_profiles (
                profile_id TEXT PRIMARY KEY,
                asset_id TEXT NOT NULL,
                name TEXT NOT NULL,
                created_at TEXT NOT NULL,
                visual_style_json TEXT NOT NULL,
                editing_style_json TEXT NOT NULL,
                mograph_json TEXT NOT NULL,
                audio_style_json TEXT NOT NULL,
                narrative_json TEXT NOT NULL,
                key_moments_json TEXT NOT NULL,
                FOREIGN KEY (asset_id) REFERENCES assets(asset_id) ON DELETE CASCADE
            );

            -- Part 04 AI Director & Production Planning Tables
            CREATE TABLE IF NOT EXISTS creative_briefs (
                brief_id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                project_name TEXT NOT NULL,
                production_type TEXT NOT NULL,
                genre TEXT NOT NULL,
                target_duration_sec REAL NOT NULL,
                intended_platform TEXT NOT NULL,
                aspect_ratio TEXT DEFAULT '16:9',
                resolution TEXT DEFAULT '1920x1080',
                fps REAL DEFAULT 24.0,
                language TEXT DEFAULT 'en',
                target_audience TEXT DEFAULT '',
                purpose TEXT DEFAULT '',
                core_message TEXT DEFAULT '',
                desired_audience_response TEXT DEFAULT '',
                call_to_action TEXT,
                emotional_objective TEXT DEFAULT '',
                narrative_objective TEXT DEFAULT '',
                visual_style TEXT DEFAULT '',
                cinematography TEXT DEFAULT '',
                lighting_style TEXT DEFAULT '',
                color_palette_json TEXT DEFAULT '[]',
                pacing_style TEXT DEFAULT 'DYNAMIC_BALANCED',
                typography_style TEXT DEFAULT '',
                sound_design_notes TEXT DEFAULT '',
                music_direction TEXT DEFAULT '',
                available_footage_ids_json TEXT DEFAULT '[]',
                reference_asset_ids_json TEXT DEFAULT '[]',
                budget_tier TEXT DEFAULT 'STANDARD',
                model_restrictions_json TEXT DEFAULT '[]',
                exclusions_json TEXT DEFAULT '[]',
                assumptions_json TEXT DEFAULT '[]',
                created_at TEXT NOT NULL,
                version INTEGER DEFAULT 1,
                FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS creative_concepts (
                concept_id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                name TEXT NOT NULL,
                creative_premise TEXT NOT NULL,
                narrative_approach TEXT NOT NULL,
                visual_treatment TEXT NOT NULL,
                cinematography_style TEXT NOT NULL,
                color_direction TEXT NOT NULL,
                sound_direction TEXT NOT NULL,
                editing_rhythm TEXT NOT NULL,
                motion_graphics_style TEXT NOT NULL,
                production_complexity TEXT NOT NULL,
                estimated_generation_reqs_json TEXT DEFAULT '{}',
                risks_and_limitations_json TEXT DEFAULT '[]',
                is_selected INTEGER DEFAULT 0,
                created_at TEXT NOT NULL,
                FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS production_scripts (
                script_id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                title TEXT NOT NULL,
                logline TEXT DEFAULT '',
                target_duration_sec REAL NOT NULL,
                estimated_spoken_duration_sec REAL NOT NULL,
                total_words INTEGER DEFAULT 0,
                version INTEGER DEFAULT 1,
                created_at TEXT NOT NULL,
                FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS script_scenes (
                scene_id TEXT PRIMARY KEY,
                script_id TEXT NOT NULL,
                scene_number INTEGER NOT NULL,
                title TEXT NOT NULL,
                slugline TEXT NOT NULL,
                narrative_purpose TEXT DEFAULT '',
                location TEXT DEFAULT '',
                time_of_day TEXT DEFAULT '',
                characters_json TEXT DEFAULT '[]',
                action_description TEXT DEFAULT '',
                dialogue_entries_json TEXT DEFAULT '[]',
                emotional_tone TEXT DEFAULT '',
                estimated_duration_sec REAL NOT NULL,
                continuity_notes TEXT DEFAULT '',
                FOREIGN KEY (script_id) REFERENCES production_scripts(script_id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS planned_shots (
                shot_id TEXT PRIMARY KEY,
                scene_id TEXT NOT NULL,
                shot_number INTEGER NOT NULL,
                narrative_purpose TEXT DEFAULT '',
                shot_scale TEXT NOT NULL,
                camera_angle TEXT NOT NULL,
                camera_motion TEXT NOT NULL,
                lens_focal_length TEXT DEFAULT '35mm',
                camera_position TEXT DEFAULT '',
                subject_action TEXT DEFAULT '',
                environment_description TEXT DEFAULT '',
                lighting_direction TEXT DEFAULT '',
                composition_notes TEXT DEFAULT '',
                depth_of_field TEXT DEFAULT '',
                focus_behavior TEXT DEFAULT '',
                motion_characteristics TEXT DEFAULT '',
                start_state TEXT DEFAULT '',
                end_state TEXT DEFAULT '',
                estimated_duration_sec REAL NOT NULL,
                aspect_ratio TEXT DEFAULT '16:9',
                visual_style TEXT DEFAULT '',
                continuity_reqs_json TEXT DEFAULT '[]',
                required_source_assets_json TEXT DEFAULT '[]',
                generation_requirements TEXT DEFAULT 'AI_VIDEO_GENERATION',
                FOREIGN KEY (scene_id) REFERENCES script_scenes(scene_id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS storyboard_frames (
                frame_id TEXT PRIMARY KEY,
                shot_id TEXT NOT NULL,
                scene_id TEXT NOT NULL,
                frame_order INTEGER NOT NULL,
                visual_prompt_spec TEXT NOT NULL,
                visual_description TEXT DEFAULT '',
                character_references_json TEXT DEFAULT '[]',
                environment_references_json TEXT DEFAULT '[]',
                camera_composition TEXT DEFAULT '',
                lighting_direction TEXT DEFAULT '',
                continuity_notes TEXT DEFAULT '',
                approval_status TEXT DEFAULT 'DRAFT',
                image_asset_id TEXT,
                FOREIGN KEY (shot_id) REFERENCES planned_shots(shot_id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS characters (
                character_id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                name TEXT NOT NULL,
                age_appearance TEXT DEFAULT '',
                gender TEXT DEFAULT '',
                physical_description TEXT DEFAULT '',
                costume_wardrobe TEXT DEFAULT '',
                personality_traits_json TEXT DEFAULT '[]',
                reference_asset_ids_json TEXT DEFAULT '[]',
                voice_profile_id TEXT,
                continuity_rules_json TEXT DEFAULT '[]',
                FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS environments (
                environment_id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                name TEXT NOT NULL,
                description TEXT DEFAULT '',
                location_type TEXT DEFAULT 'INTERIOR',
                lighting_conditions TEXT DEFAULT '',
                time_of_day TEXT DEFAULT '',
                spatial_layout TEXT DEFAULT '',
                reference_asset_ids_json TEXT DEFAULT '[]',
                FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS editing_blueprints (
                blueprint_id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                target_duration_sec REAL NOT NULL,
                narrative_order_json TEXT NOT NULL,
                pacing_style TEXT DEFAULT 'DYNAMIC_BALANCED',
                transitions_json TEXT DEFAULT '[]',
                music_placement_json TEXT DEFAULT '[]',
                dialogue_placement_json TEXT DEFAULT '[]',
                sound_effects_json TEXT DEFAULT '[]',
                motion_graphics_json TEXT DEFAULT '[]',
                missing_coverage_json TEXT DEFAULT '[]',
                version INTEGER DEFAULT 1,
                created_at TEXT NOT NULL,
                FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS production_blueprints (
                blueprint_id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                version INTEGER NOT NULL,
                brief_json TEXT NOT NULL,
                concept_json TEXT,
                script_json TEXT,
                breakdown_json TEXT,
                editing_blueprint_json TEXT,
                feasibility_json TEXT,
                is_ready_for_production INTEGER DEFAULT 0,
                created_at TEXT NOT NULL,
                FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS creative_approvals (
                approval_id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                entity_type TEXT NOT NULL,
                entity_id TEXT NOT NULL,
                version INTEGER NOT NULL,
                status TEXT DEFAULT 'PENDING_REVIEW',
                reviewer_notes TEXT DEFAULT '',
                approved_by TEXT,
                approved_at TEXT,
                FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE CASCADE
            );

            -- Part 03 Multimodal Intelligence Tables
            CREATE TABLE IF NOT EXISTS shots (
                shot_id TEXT PRIMARY KEY,
                asset_id TEXT NOT NULL,
                shot_number INTEGER NOT NULL,
                start_sec REAL NOT NULL,
                end_sec REAL NOT NULL,
                start_frame INTEGER NOT NULL,
                end_frame INTEGER NOT NULL,
                transition_in TEXT DEFAULT 'HARD_CUT',
                transition_out TEXT DEFAULT 'HARD_CUT',
                shot_scale TEXT DEFAULT 'UNKNOWN',
                camera_angle TEXT DEFAULT 'UNKNOWN',
                camera_motion TEXT DEFAULT 'STATIC',
                summary TEXT DEFAULT '',
                visual_features_json TEXT DEFAULT '{}',
                confidence REAL DEFAULT 1.0,
                evidence_json TEXT,
                FOREIGN KEY (asset_id) REFERENCES assets(asset_id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS scenes (
                scene_id TEXT PRIMARY KEY,
                asset_id TEXT NOT NULL,
                scene_number INTEGER NOT NULL,
                start_sec REAL NOT NULL,
                end_sec REAL NOT NULL,
                narrative_summary TEXT DEFAULT '',
                setting TEXT DEFAULT '',
                lighting_style TEXT DEFAULT '',
                dominant_mood TEXT DEFAULT '',
                shot_ids_json TEXT DEFAULT '[]',
                confidence REAL DEFAULT 1.0,
                FOREIGN KEY (asset_id) REFERENCES assets(asset_id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS transcripts (
                segment_id TEXT PRIMARY KEY,
                asset_id TEXT NOT NULL,
                speaker_id TEXT DEFAULT 'SPEAKER_00',
                text TEXT NOT NULL,
                start_sec REAL NOT NULL,
                end_sec REAL NOT NULL,
                language TEXT DEFAULT 'en',
                words_json TEXT DEFAULT '[]',
                confidence REAL DEFAULT 1.0,
                FOREIGN KEY (asset_id) REFERENCES assets(asset_id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS audio_events (
                event_id TEXT PRIMARY KEY,
                asset_id TEXT NOT NULL,
                event_type TEXT NOT NULL,
                description TEXT NOT NULL,
                start_sec REAL NOT NULL,
                end_sec REAL NOT NULL,
                spectral_energy REAL,
                confidence REAL DEFAULT 1.0,
                evidence_json TEXT,
                FOREIGN KEY (asset_id) REFERENCES assets(asset_id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS music_segments (
                segment_id TEXT PRIMARY KEY,
                asset_id TEXT NOT NULL,
                start_sec REAL NOT NULL,
                end_sec REAL NOT NULL,
                tempo_bpm REAL NOT NULL,
                beat_timestamps_json TEXT DEFAULT '[]',
                rhythmic_energy REAL DEFAULT 0.5,
                mood TEXT DEFAULT 'neutral',
                has_vocals INTEGER DEFAULT 0,
                confidence REAL DEFAULT 1.0,
                FOREIGN KEY (asset_id) REFERENCES assets(asset_id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS detected_objects (
                detection_id TEXT PRIMARY KEY,
                asset_id TEXT NOT NULL,
                track_id INTEGER NOT NULL,
                label TEXT NOT NULL,
                timestamp_sec REAL NOT NULL,
                frame_number INTEGER NOT NULL,
                box_json TEXT NOT NULL,
                confidence REAL DEFAULT 1.0,
                FOREIGN KEY (asset_id) REFERENCES assets(asset_id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS camera_movements (
                movement_id TEXT PRIMARY KEY,
                asset_id TEXT NOT NULL,
                start_sec REAL NOT NULL,
                end_sec REAL NOT NULL,
                motion_type TEXT NOT NULL,
                magnitude REAL NOT NULL,
                direction_json TEXT DEFAULT '[0.0, 0.0]',
                confidence REAL DEFAULT 1.0,
                evidence_json TEXT,
                FOREIGN KEY (asset_id) REFERENCES assets(asset_id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS ocr_observations (
                ocr_id TEXT PRIMARY KEY,
                asset_id TEXT NOT NULL,
                text TEXT NOT NULL,
                timestamp_sec REAL NOT NULL,
                frame_number INTEGER NOT NULL,
                box_json TEXT NOT NULL,
                text_category TEXT DEFAULT 'GENERAL',
                confidence REAL DEFAULT 1.0,
                FOREIGN KEY (asset_id) REFERENCES assets(asset_id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS reference_profiles (
                profile_id TEXT PRIMARY KEY,
                asset_id TEXT NOT NULL,
                name TEXT NOT NULL,
                created_at TEXT NOT NULL,
                visual_style_json TEXT NOT NULL,
                editing_style_json TEXT NOT NULL,
                mograph_json TEXT NOT NULL,
                audio_style_json TEXT NOT NULL,
                narrative_json TEXT NOT NULL,
                key_moments_json TEXT NOT NULL,
                FOREIGN KEY (asset_id) REFERENCES assets(asset_id) ON DELETE CASCADE
            );

            -- Part 04 AI Director & Production Planning Tables
            CREATE TABLE IF NOT EXISTS creative_briefs (
                brief_id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                project_name TEXT NOT NULL,
                production_type TEXT NOT NULL,
                genre TEXT NOT NULL,
                target_duration_sec REAL NOT NULL,
                intended_platform TEXT NOT NULL,
                aspect_ratio TEXT DEFAULT '16:9',
                resolution TEXT DEFAULT '1920x1080',
                fps REAL DEFAULT 24.0,
                language TEXT DEFAULT 'en',
                target_audience TEXT DEFAULT '',
                purpose TEXT DEFAULT '',
                core_message TEXT DEFAULT '',
                desired_audience_response TEXT DEFAULT '',
                call_to_action TEXT,
                emotional_objective TEXT DEFAULT '',
                narrative_objective TEXT DEFAULT '',
                visual_style TEXT DEFAULT '',
                cinematography TEXT DEFAULT '',
                lighting_style TEXT DEFAULT '',
                color_palette_json TEXT DEFAULT '[]',
                pacing_style TEXT DEFAULT 'DYNAMIC_BALANCED',
                typography_style TEXT DEFAULT '',
                sound_design_notes TEXT DEFAULT '',
                music_direction TEXT DEFAULT '',
                available_footage_ids_json TEXT DEFAULT '[]',
                reference_asset_ids_json TEXT DEFAULT '[]',
                budget_tier TEXT DEFAULT 'STANDARD',
                model_restrictions_json TEXT DEFAULT '[]',
                exclusions_json TEXT DEFAULT '[]',
                assumptions_json TEXT DEFAULT '[]',
                created_at TEXT NOT NULL,
                version INTEGER DEFAULT 1,
                FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS creative_concepts (
                concept_id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                name TEXT NOT NULL,
                creative_premise TEXT NOT NULL,
                narrative_approach TEXT NOT NULL,
                visual_treatment TEXT NOT NULL,
                cinematography_style TEXT NOT NULL,
                color_direction TEXT NOT NULL,
                sound_direction TEXT NOT NULL,
                editing_rhythm TEXT NOT NULL,
                motion_graphics_style TEXT NOT NULL,
                production_complexity TEXT NOT NULL,
                estimated_generation_reqs_json TEXT DEFAULT '{}',
                risks_and_limitations_json TEXT DEFAULT '[]',
                is_selected INTEGER DEFAULT 0,
                created_at TEXT NOT NULL,
                FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS production_scripts (
                script_id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                title TEXT NOT NULL,
                logline TEXT DEFAULT '',
                target_duration_sec REAL NOT NULL,
                estimated_spoken_duration_sec REAL NOT NULL,
                total_words INTEGER DEFAULT 0,
                version INTEGER DEFAULT 1,
                created_at TEXT NOT NULL,
                FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS script_scenes (
                scene_id TEXT PRIMARY KEY,
                script_id TEXT NOT NULL,
                scene_number INTEGER NOT NULL,
                title TEXT NOT NULL,
                slugline TEXT NOT NULL,
                narrative_purpose TEXT DEFAULT '',
                location TEXT DEFAULT '',
                time_of_day TEXT DEFAULT '',
                characters_json TEXT DEFAULT '[]',
                action_description TEXT DEFAULT '',
                dialogue_entries_json TEXT DEFAULT '[]',
                emotional_tone TEXT DEFAULT '',
                estimated_duration_sec REAL NOT NULL,
                continuity_notes TEXT DEFAULT '',
                FOREIGN KEY (script_id) REFERENCES production_scripts(script_id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS planned_shots (
                shot_id TEXT PRIMARY KEY,
                scene_id TEXT NOT NULL,
                shot_number INTEGER NOT NULL,
                narrative_purpose TEXT DEFAULT '',
                shot_scale TEXT NOT NULL,
                camera_angle TEXT NOT NULL,
                camera_motion TEXT NOT NULL,
                lens_focal_length TEXT DEFAULT '35mm',
                camera_position TEXT DEFAULT '',
                subject_action TEXT DEFAULT '',
                environment_description TEXT DEFAULT '',
                lighting_direction TEXT DEFAULT '',
                composition_notes TEXT DEFAULT '',
                depth_of_field TEXT DEFAULT '',
                focus_behavior TEXT DEFAULT '',
                motion_characteristics TEXT DEFAULT '',
                start_state TEXT DEFAULT '',
                end_state TEXT DEFAULT '',
                estimated_duration_sec REAL NOT NULL,
                aspect_ratio TEXT DEFAULT '16:9',
                visual_style TEXT DEFAULT '',
                continuity_reqs_json TEXT DEFAULT '[]',
                required_source_assets_json TEXT DEFAULT '[]',
                generation_requirements TEXT DEFAULT 'AI_VIDEO_GENERATION',
                FOREIGN KEY (scene_id) REFERENCES script_scenes(scene_id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS storyboard_frames (
                frame_id TEXT PRIMARY KEY,
                shot_id TEXT NOT NULL,
                scene_id TEXT NOT NULL,
                frame_order INTEGER NOT NULL,
                visual_prompt_spec TEXT NOT NULL,
                visual_description TEXT DEFAULT '',
                character_references_json TEXT DEFAULT '[]',
                environment_references_json TEXT DEFAULT '[]',
                camera_composition TEXT DEFAULT '',
                lighting_direction TEXT DEFAULT '',
                continuity_notes TEXT DEFAULT '',
                approval_status TEXT DEFAULT 'DRAFT',
                image_asset_id TEXT,
                FOREIGN KEY (shot_id) REFERENCES planned_shots(shot_id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS characters (
                character_id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                name TEXT NOT NULL,
                age_appearance TEXT DEFAULT '',
                gender TEXT DEFAULT '',
                physical_description TEXT DEFAULT '',
                costume_wardrobe TEXT DEFAULT '',
                personality_traits_json TEXT DEFAULT '[]',
                reference_asset_ids_json TEXT DEFAULT '[]',
                voice_profile_id TEXT,
                continuity_rules_json TEXT DEFAULT '[]',
                FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS environments (
                environment_id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                name TEXT NOT NULL,
                description TEXT DEFAULT '',
                location_type TEXT DEFAULT 'INTERIOR',
                lighting_conditions TEXT DEFAULT '',
                time_of_day TEXT DEFAULT '',
                spatial_layout TEXT DEFAULT '',
                reference_asset_ids_json TEXT DEFAULT '[]',
                FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS editing_blueprints (
                blueprint_id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                target_duration_sec REAL NOT NULL,
                narrative_order_json TEXT NOT NULL,
                pacing_style TEXT DEFAULT 'DYNAMIC_BALANCED',
                transitions_json TEXT DEFAULT '[]',
                music_placement_json TEXT DEFAULT '[]',
                dialogue_placement_json TEXT DEFAULT '[]',
                sound_effects_json TEXT DEFAULT '[]',
                motion_graphics_json TEXT DEFAULT '[]',
                missing_coverage_json TEXT DEFAULT '[]',
                version INTEGER DEFAULT 1,
                created_at TEXT NOT NULL,
                FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS production_blueprints (
                blueprint_id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                version INTEGER NOT NULL,
                brief_json TEXT NOT NULL,
                concept_json TEXT,
                script_json TEXT,
                breakdown_json TEXT,
                editing_blueprint_json TEXT,
                feasibility_json TEXT,
                is_ready_for_production INTEGER DEFAULT 0,
                created_at TEXT NOT NULL,
                FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS creative_approvals (
                approval_id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                entity_type TEXT NOT NULL,
                entity_id TEXT NOT NULL,
                version INTEGER NOT NULL,
                status TEXT DEFAULT 'PENDING_REVIEW',
                reviewer_notes TEXT DEFAULT '',
                approved_by TEXT,
                approved_at TEXT,
                FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE CASCADE
            );
            
            -- Part 05 Non-Linear Editing Engine Tables
            CREATE TABLE IF NOT EXISTS editing_projects (
                project_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                active_timeline_id TEXT,
                settings_json TEXT DEFAULT '{}',
                revision INTEGER DEFAULT 1,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS timelines (
                timeline_id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                name TEXT NOT NULL,
                time_base REAL DEFAULT 24.0,
                duration_sec REAL DEFAULT 0.0,
                resolution_width INTEGER DEFAULT 1920,
                resolution_height INTEGER DEFAULT 1080,
                fps REAL DEFAULT 24.0,
                sample_rate INTEGER DEFAULT 48000,
                version INTEGER DEFAULT 1,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS tracks (
                track_id TEXT PRIMARY KEY,
                timeline_id TEXT NOT NULL,
                track_type TEXT NOT NULL,
                name TEXT NOT NULL,
                order_index INTEGER DEFAULT 0,
                is_muted INTEGER DEFAULT 0,
                is_visible INTEGER DEFAULT 1,
                is_locked INTEGER DEFAULT 0,
                is_solo INTEGER DEFAULT 0,
                gain REAL DEFAULT 1.0,
                opacity REAL DEFAULT 1.0,
                FOREIGN KEY (timeline_id) REFERENCES timelines(timeline_id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS clips (
                clip_id TEXT PRIMARY KEY,
                track_id TEXT NOT NULL,
                asset_id TEXT NOT NULL,
                timeline_start_sec REAL NOT NULL,
                timeline_dur_sec REAL NOT NULL,
                source_in_sec REAL NOT NULL,
                source_out_sec REAL NOT NULL,
                speed REAL DEFAULT 1.0,
                transform_json TEXT DEFAULT '{}',
                opacity REAL DEFAULT 1.0,
                volume REAL DEFAULT 1.0,
                pan REAL DEFAULT 0.0,
                enabled INTEGER DEFAULT 1,
                linked_clip_id TEXT,
                name TEXT NOT NULL,
                FOREIGN KEY (track_id) REFERENCES tracks(track_id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS transitions (
                transition_id TEXT PRIMARY KEY,
                track_id TEXT NOT NULL,
                transition_type TEXT NOT NULL,
                start_time_sec REAL NOT NULL,
                duration_sec REAL NOT NULL,
                from_clip_id TEXT,
                to_clip_id TEXT,
                parameters_json TEXT DEFAULT '{}',
                easing TEXT DEFAULT 'LINEAR',
                FOREIGN KEY (track_id) REFERENCES tracks(track_id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS effects (
                effect_id TEXT PRIMARY KEY,
                clip_id TEXT NOT NULL,
                effect_type TEXT NOT NULL,
                parameters_json TEXT NOT NULL,
                enabled INTEGER DEFAULT 1,
                start_sec REAL,
                duration_sec REAL,
                processing_order INTEGER DEFAULT 0,
                FOREIGN KEY (clip_id) REFERENCES clips(clip_id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS keyframes (
                keyframe_id TEXT PRIMARY KEY,
                parent_entity_type TEXT NOT NULL,
                parent_entity_id TEXT NOT NULL,
                property_name TEXT NOT NULL,
                time_sec REAL NOT NULL,
                value REAL NOT NULL,
                interpolation TEXT DEFAULT 'LINEAR',
                easing_params_json TEXT DEFAULT '{}'
            );

            CREATE TABLE IF NOT EXISTS timeline_markers (
                marker_id TEXT PRIMARY KEY,
                timeline_id TEXT NOT NULL,
                time_sec REAL NOT NULL,
                name TEXT NOT NULL,
                color TEXT DEFAULT '#00FF00',
                comment TEXT DEFAULT '',
                FOREIGN KEY (timeline_id) REFERENCES timelines(timeline_id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS render_jobs (
                render_id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                timeline_id TEXT NOT NULL,
                output_path TEXT NOT NULL,
                is_preview INTEGER DEFAULT 0,
                format_preset TEXT DEFAULT 'H264_1080P',
                status TEXT DEFAULT 'QUEUED',
                progress REAL DEFAULT 0.0,
                error_message TEXT,
                created_at TEXT NOT NULL,
                completed_at TEXT,
                FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE CASCADE,
                FOREIGN KEY (timeline_id) REFERENCES timelines(timeline_id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS motion_compositions (
                composition_id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                name TEXT NOT NULL,
                resolution_w INTEGER NOT NULL,
                resolution_h INTEGER NOT NULL,
                fps REAL NOT NULL,
                duration_frames INTEGER NOT NULL,
                duration_rate REAL NOT NULL,
                composition_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE CASCADE
            );
            
            CREATE INDEX IF NOT EXISTS idx_assets_project ON assets(project_id);
            CREATE INDEX IF NOT EXISTS idx_assets_checksum ON assets(checksum_sha256);
            CREATE INDEX IF NOT EXISTS idx_assets_media_type ON assets(media_type);
            CREATE INDEX IF NOT EXISTS idx_derivatives_asset ON derivatives(asset_id);
            CREATE INDEX IF NOT EXISTS idx_jobs_status ON processing_jobs(status);
            CREATE INDEX IF NOT EXISTS idx_shots_asset ON shots(asset_id);
            CREATE INDEX IF NOT EXISTS idx_scenes_asset ON scenes(asset_id);
            CREATE INDEX IF NOT EXISTS idx_transcripts_asset ON transcripts(asset_id);
            CREATE INDEX IF NOT EXISTS idx_audio_events_asset ON audio_events(asset_id);
            CREATE INDEX IF NOT EXISTS idx_camera_motion_asset ON camera_movements(asset_id);
            CREATE INDEX IF NOT EXISTS idx_ocr_asset ON ocr_observations(asset_id);
            CREATE INDEX IF NOT EXISTS idx_detected_objects_asset ON detected_objects(asset_id);
            CREATE INDEX IF NOT EXISTS idx_briefs_project ON creative_briefs(project_id);
            CREATE INDEX IF NOT EXISTS idx_concepts_project ON creative_concepts(project_id);
            CREATE INDEX IF NOT EXISTS idx_scripts_project ON production_scripts(project_id);
            CREATE INDEX IF NOT EXISTS idx_scenes_script ON script_scenes(script_id);
            CREATE INDEX IF NOT EXISTS idx_shots_scene ON planned_shots(scene_id);
            CREATE INDEX IF NOT EXISTS idx_frames_shot ON storyboard_frames(shot_id);
            CREATE INDEX IF NOT EXISTS idx_characters_project ON characters(project_id);
            CREATE INDEX IF NOT EXISTS idx_environments_project ON environments(project_id);
            CREATE INDEX IF NOT EXISTS idx_edit_bp_project ON editing_blueprints(project_id);
            CREATE INDEX IF NOT EXISTS idx_prod_bp_project ON production_blueprints(project_id);
            CREATE INDEX IF NOT EXISTS idx_approvals_project ON creative_approvals(project_id);
            CREATE INDEX IF NOT EXISTS idx_timelines_project ON timelines(project_id);
            CREATE INDEX IF NOT EXISTS idx_tracks_timeline ON tracks(timeline_id);
            CREATE INDEX IF NOT EXISTS idx_clips_track ON clips(track_id);
            CREATE INDEX IF NOT EXISTS idx_transitions_track ON transitions(track_id);
            CREATE INDEX IF NOT EXISTS idx_effects_clip ON effects(clip_id);
            CREATE INDEX IF NOT EXISTS idx_keyframes_parent ON keyframes(parent_entity_id);
            CREATE INDEX IF NOT EXISTS idx_markers_timeline ON timeline_markers(timeline_id);
            CREATE INDEX IF NOT EXISTS idx_renders_timeline ON render_jobs(timeline_id);
            CREATE INDEX IF NOT EXISTS idx_mograph_project ON motion_compositions(project_id);
            """)

    def create_project(self, project_id: UUID, name: str, settings: Optional[Dict[str, Any]] = None) -> None:
        now = utc_now_iso()
        with self.get_connection() as conn:
            conn.execute(
                "INSERT INTO projects (project_id, name, created_at, updated_at, settings_json) VALUES (?, ?, ?, ?, ?)",
                (str(project_id), name, now, now, json.dumps(settings or {}))
            )

    def get_project(self, project_id: UUID) -> Optional[Dict[str, Any]]:
        with self.get_connection() as conn:
            row = conn.execute("SELECT * FROM projects WHERE project_id = ?", (str(project_id),)).fetchone()
            if not row:
                return None
            return {
                "project_id": UUID(row["project_id"]),
                "name": row["name"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
                "settings": json.loads(row["settings_json"])
            }

    def register_asset(self, asset: AssetRecord) -> None:
        with self.get_connection() as conn:
            conn.execute("""
                INSERT INTO assets (
                    asset_id, project_id, original_filename, display_name,
                    media_type, detected_format, mime_type, byte_size,
                    checksum_sha256, storage_path, import_timestamp,
                    processing_status, metadata_status, derivative_status,
                    error_message, version, source_type, license_info
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                str(asset.asset_id), str(asset.project_id), asset.original_filename, asset.display_name,
                asset.media_type.value, asset.detected_format, asset.mime_type, asset.byte_size,
                asset.checksum_sha256, asset.storage_path, asset.import_timestamp,
                asset.processing_status.value, asset.metadata_status.value, asset.derivative_status.value,
                asset.error_message, asset.version, asset.source_type, asset.license_info
            ))
            for role in asset.roles:
                conn.execute(
                    "INSERT OR IGNORE INTO asset_roles (asset_id, role) VALUES (?, ?)",
                    (str(asset.asset_id), role.value)
                )

    def update_asset_status(
        self, asset_id: UUID,
        processing_status: Optional[ProcessingStatus] = None,
        metadata_status: Optional[ProcessingStatus] = None,
        derivative_status: Optional[ProcessingStatus] = None,
        error_message: Optional[str] = None
    ) -> None:
        updates = []
        params = []
        if processing_status is not None:
            updates.append("processing_status = ?")
            params.append(processing_status.value)
        if metadata_status is not None:
            updates.append("metadata_status = ?")
            params.append(metadata_status.value)
        if derivative_status is not None:
            updates.append("derivative_status = ?")
            params.append(derivative_status.value)
        if error_message is not None:
            updates.append("error_message = ?")
            params.append(error_message)

        if not updates:
            return

        params.append(str(asset_id))
        query = f"UPDATE assets SET {', '.join(updates)} WHERE asset_id = ?"
        with self.get_connection() as conn:
            conn.execute(query, params)

    def set_technical_metadata(self, meta: TechnicalMetadata) -> None:
        with self.get_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO technical_metadata (
                    asset_id, width, height, duration_seconds, frame_rate,
                    avg_frame_rate, is_vfr, video_codec, audio_codec,
                    pixel_format, bit_depth, aspect_ratio, color_primaries,
                    color_transfer, color_space, is_hdr, rotation, timecode,
                    audio_sample_rate, audio_channels, audio_channel_layout,
                    stream_count, bitrate_bps, raw_probe_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                str(meta.asset_id), meta.width, meta.height, meta.duration_seconds, meta.frame_rate,
                meta.avg_frame_rate, 1 if meta.is_vfr else 0, meta.video_codec, meta.audio_codec,
                meta.pixel_format, meta.bit_depth, meta.aspect_ratio, meta.color_primaries,
                meta.color_transfer, meta.color_space, 1 if meta.is_hdr else 0, meta.rotation, meta.timecode,
                meta.audio_sample_rate, meta.audio_channels, meta.audio_channel_layout,
                meta.stream_count, meta.bitrate_bps, json.dumps(meta.raw_probe)
            ))

    def add_derivative(self, deriv: DerivativeRecord) -> None:
        with self.get_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO derivatives (
                    derivative_id, asset_id, derivative_type, storage_path,
                    byte_size, mime_type, generation_params_json, created_at, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                str(deriv.derivative_id), str(deriv.asset_id), deriv.derivative_type.value, deriv.storage_path,
                deriv.byte_size, deriv.mime_type, json.dumps(deriv.generation_params), deriv.created_at,
                deriv.status.value
            ))

    def get_asset(self, asset_id: UUID) -> Optional[AssetRecord]:
        with self.get_connection() as conn:
            row = conn.execute("SELECT * FROM assets WHERE asset_id = ?", (str(asset_id),)).fetchone()
            if not row:
                return None
            roles_rows = conn.execute("SELECT role FROM asset_roles WHERE asset_id = ?", (str(asset_id),)).fetchall()
            roles = [AssetRole(r["role"]) for r in roles_rows]
            return AssetRecord(
                asset_id=UUID(row["asset_id"]),
                project_id=UUID(row["project_id"]),
                original_filename=row["original_filename"],
                display_name=row["display_name"],
                media_type=MediaType(row["media_type"]),
                detected_format=row["detected_format"],
                mime_type=row["mime_type"],
                byte_size=row["byte_size"],
                checksum_sha256=row["checksum_sha256"],
                storage_path=row["storage_path"],
                import_timestamp=row["import_timestamp"],
                processing_status=ProcessingStatus(row["processing_status"]),
                metadata_status=ProcessingStatus(row["metadata_status"]),
                derivative_status=ProcessingStatus(row["derivative_status"]),
                error_message=row["error_message"],
                version=row["version"],
                source_type=row["source_type"],
                license_info=row["license_info"],
                roles=roles
            )

    def get_technical_metadata(self, asset_id: UUID) -> Optional[TechnicalMetadata]:
        with self.get_connection() as conn:
            row = conn.execute("SELECT * FROM technical_metadata WHERE asset_id = ?", (str(asset_id),)).fetchone()
            if not row:
                return None
            raw_probe = json.loads(row["raw_probe_json"]) if row["raw_probe_json"] else {}
            return TechnicalMetadata(
                asset_id=UUID(row["asset_id"]),
                width=row["width"],
                height=row["height"],
                duration_seconds=row["duration_seconds"],
                frame_rate=row["frame_rate"],
                avg_frame_rate=row["avg_frame_rate"],
                is_vfr=bool(row["is_vfr"]),
                video_codec=row["video_codec"],
                audio_codec=row["audio_codec"],
                pixel_format=row["pixel_format"],
                bit_depth=row["bit_depth"],
                aspect_ratio=row["aspect_ratio"],
                color_primaries=row["color_primaries"],
                color_transfer=row["color_transfer"],
                color_space=row["color_space"],
                is_hdr=bool(row["is_hdr"]),
                rotation=row["rotation"],
                timecode=row["timecode"],
                audio_sample_rate=row["audio_sample_rate"],
                audio_channels=row["audio_channels"],
                audio_channel_layout=row["audio_channel_layout"],
                stream_count=row["stream_count"],
                bitrate_bps=row["bitrate_bps"],
                raw_probe=raw_probe
            )

    def get_derivatives(self, asset_id: UUID) -> List[DerivativeRecord]:
        with self.get_connection() as conn:
            rows = conn.execute("SELECT * FROM derivatives WHERE asset_id = ?", (str(asset_id),)).fetchall()
            derivatives = []
            for r in rows:
                derivatives.append(DerivativeRecord(
                    derivative_id=UUID(r["derivative_id"]),
                    asset_id=UUID(r["asset_id"]),
                    derivative_type=DerivativeType(r["derivative_type"]),
                    storage_path=r["storage_path"],
                    byte_size=r["byte_size"],
                    mime_type=r["mime_type"],
                    generation_params=json.loads(r["generation_params_json"]),
                    created_at=r["created_at"],
                    status=ProcessingStatus(r["status"])
                ))
            return derivatives

    def list_project_assets(
        self, project_id: UUID,
        media_type: Optional[MediaType] = None,
        role: Optional[AssetRole] = None,
        status: Optional[ProcessingStatus] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[AssetRecord]:
        query = """
            SELECT DISTINCT a.* FROM assets a
            LEFT JOIN asset_roles r ON a.asset_id = r.asset_id
            WHERE a.project_id = ?
        """
        params: List[Any] = [str(project_id)]

        if media_type is not None:
            query += " AND a.media_type = ?"
            params.append(media_type.value)
        if role is not None:
            query += " AND r.role = ?"
            params.append(role.value)
        if status is not None:
            query += " AND a.processing_status = ?"
            params.append(status.value)

        query += " ORDER BY a.import_timestamp DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        with self.get_connection() as conn:
            rows = conn.execute(query, params).fetchall()
            assets = []
            for r in rows:
                roles_rows = conn.execute("SELECT role FROM asset_roles WHERE asset_id = ?", (r["asset_id"],)).fetchall()
                roles = [AssetRole(rr["role"]) for rr in roles_rows]
                assets.append(AssetRecord(
                    asset_id=UUID(r["asset_id"]),
                    project_id=UUID(r["project_id"]),
                    original_filename=r["original_filename"],
                    display_name=r["display_name"],
                    media_type=MediaType(r["media_type"]),
                    detected_format=r["detected_format"],
                    mime_type=r["mime_type"],
                    byte_size=r["byte_size"],
                    checksum_sha256=r["checksum_sha256"],
                    storage_path=r["storage_path"],
                    import_timestamp=r["import_timestamp"],
                    processing_status=ProcessingStatus(r["processing_status"]),
                    metadata_status=ProcessingStatus(r["metadata_status"]),
                    derivative_status=ProcessingStatus(r["derivative_status"]),
                    error_message=r["error_message"],
                    version=r["version"],
                    source_type=r["source_type"],
                    license_info=r["license_info"],
                    roles=roles
                ))
            return assets

    def add_asset_role(self, asset_id: UUID, role: AssetRole) -> None:
        with self.get_connection() as conn:
            conn.execute("INSERT OR IGNORE INTO asset_roles (asset_id, role) VALUES (?, ?)", (str(asset_id), role.value))

    def remove_asset_role(self, asset_id: UUID, role: AssetRole) -> None:
        with self.get_connection() as conn:
            conn.execute("DELETE FROM asset_roles WHERE asset_id = ? AND role = ?", (str(asset_id), role.value))

    def update_display_name(self, asset_id: UUID, new_name: str) -> None:
        with self.get_connection() as conn:
            conn.execute("UPDATE assets SET display_name = ? WHERE asset_id = ?", (new_name, str(asset_id)))

    def delete_asset(self, asset_id: UUID) -> bool:
        with self.get_connection() as conn:
            deps = conn.execute(
                "SELECT COUNT(*) as cnt FROM asset_dependencies WHERE dependent_asset_id = ?",
                (str(asset_id),)
            ).fetchone()
            if deps and deps["cnt"] > 0:
                return False

            conn.execute("DELETE FROM assets WHERE asset_id = ?", (str(asset_id),))
            return True

    def find_by_checksum(self, project_id: UUID, checksum_sha256: str) -> Optional[AssetRecord]:
        with self.get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM assets WHERE project_id = ? AND checksum_sha256 = ?",
                (str(project_id), checksum_sha256)
            ).fetchone()
            if not row:
                return None
            return self.get_asset(UUID(row["asset_id"]))

    # -------------------------------------------------------------
    # Multimodal Intelligence Persistence Methods (Part 03)
    # -------------------------------------------------------------
    def save_shots(self, shots: List[Any]) -> None:
        with self.get_connection() as conn:
            for s in shots:
                evidence_json = json.dumps(s.evidence.raw_measurement) if s.evidence else "{}"
                conn.execute("""
                    INSERT OR REPLACE INTO shots (
                        shot_id, asset_id, shot_number, start_sec, end_sec,
                        start_frame, end_frame, transition_in, transition_out,
                        shot_scale, camera_angle, camera_motion, summary,
                        visual_features_json, confidence, evidence_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    str(s.shot_id), str(s.asset_id), s.shot_number,
                    s.timecode_range.start_seconds, s.timecode_range.end_seconds,
                    s.timecode_range.start_frame, s.timecode_range.end_frame,
                    s.transition_in.value if hasattr(s.transition_in, "value") else str(s.transition_in),
                    s.transition_out.value if hasattr(s.transition_out, "value") else str(s.transition_out),
                    s.shot_scale.value if hasattr(s.shot_scale, "value") else str(s.shot_scale),
                    s.camera_angle.value if hasattr(s.camera_angle, "value") else str(s.camera_angle),
                    s.camera_motion.value if hasattr(s.camera_motion, "value") else str(s.camera_motion),
                    s.summary, json.dumps(s.visual_features), s.confidence, evidence_json
                ))

    def get_shots(self, asset_id: UUID) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM shots WHERE asset_id = ? ORDER BY shot_number ASC",
                (str(asset_id),)
            ).fetchall()
            return [dict(r) for r in rows]

    def save_scenes(self, scenes: List[Any]) -> None:
        with self.get_connection() as conn:
            for sc in scenes:
                conn.execute("""
                    INSERT OR REPLACE INTO scenes (
                        scene_id, asset_id, scene_number, start_sec, end_sec,
                        narrative_summary, setting, lighting_style, dominant_mood,
                        shot_ids_json, confidence
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    str(sc.scene_id), str(sc.asset_id), sc.scene_number,
                    sc.timecode_range.start_seconds, sc.timecode_range.end_seconds,
                    sc.narrative_summary, sc.setting, sc.lighting_style, sc.dominant_mood,
                    json.dumps([str(sid) for sid in sc.shot_ids]), sc.confidence
                ))

    def get_scenes(self, asset_id: UUID) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM scenes WHERE asset_id = ? ORDER BY scene_number ASC",
                (str(asset_id),)
            ).fetchall()
            return [dict(r) for r in rows]

    def save_transcripts(self, segments: List[Any]) -> None:
        with self.get_connection() as conn:
            for t in segments:
                words_data = [
                    {"word": w.word, "start": w.start_seconds, "end": w.end_seconds, "confidence": w.confidence}
                    for w in getattr(t, "words", [])
                ]
                conn.execute("""
                    INSERT OR REPLACE INTO transcripts (
                        segment_id, asset_id, speaker_id, text, start_sec, end_sec,
                        language, words_json, confidence
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    str(t.segment_id), str(t.asset_id), t.speaker_id, t.text,
                    t.timecode_range.start_seconds, t.timecode_range.end_seconds,
                    t.language, json.dumps(words_data), t.confidence
                ))

    def get_transcripts(self, asset_id: UUID) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM transcripts WHERE asset_id = ? ORDER BY start_sec ASC",
                (str(asset_id),)
            ).fetchall()
            return [dict(r) for r in rows]

    def save_audio_events(self, events: List[Any]) -> None:
        with self.get_connection() as conn:
            for ev in events:
                conn.execute("""
                    INSERT OR REPLACE INTO audio_events (
                        event_id, asset_id, event_type, description, start_sec, end_sec,
                        spectral_energy, confidence, evidence_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    str(ev.event_id), str(ev.asset_id),
                    ev.event_type.value if hasattr(ev.event_type, "value") else str(ev.event_type),
                    ev.description, ev.timecode_range.start_seconds, ev.timecode_range.end_seconds,
                    ev.spectral_energy, ev.confidence, "{}"
                ))

    def get_audio_events(self, asset_id: UUID) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM audio_events WHERE asset_id = ? ORDER BY start_sec ASC",
                (str(asset_id),)
            ).fetchall()
            return [dict(r) for r in rows]

    def save_music_segments(self, segments: List[Any]) -> None:
        with self.get_connection() as conn:
            for m in segments:
                conn.execute("""
                    INSERT OR REPLACE INTO music_segments (
                        segment_id, asset_id, start_sec, end_sec, tempo_bpm,
                        beat_timestamps_json, rhythmic_energy, mood, has_vocals, confidence
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    str(m.segment_id), str(m.asset_id),
                    m.timecode_range.start_seconds, m.timecode_range.end_seconds,
                    m.tempo_bpm, json.dumps(m.beat_timestamps), m.rhythmic_energy,
                    m.mood, 1 if m.has_vocals else 0, m.confidence
                ))

    def get_music_segments(self, asset_id: UUID) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM music_segments WHERE asset_id = ? ORDER BY start_sec ASC",
                (str(asset_id),)
            ).fetchall()
            return [dict(r) for r in rows]

    def save_detected_objects(self, detections: List[Any]) -> None:
        with self.get_connection() as conn:
            for d in detections:
                box_dict = {"x": d.box.x, "y": d.box.y, "w": d.box.width, "h": d.box.height}
                conn.execute("""
                    INSERT OR REPLACE INTO detected_objects (
                        detection_id, asset_id, track_id, label, timestamp_sec,
                        frame_number, box_json, confidence
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    str(d.detection_id), str(d.asset_id), d.track_id, d.label,
                    d.timestamp_seconds, d.frame_number, json.dumps(box_dict), d.confidence
                ))

    def get_detected_objects(self, asset_id: UUID) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM detected_objects WHERE asset_id = ? ORDER BY timestamp_sec ASC",
                (str(asset_id),)
            ).fetchall()
            return [dict(r) for r in rows]

    def save_camera_movements(self, movements: List[Any]) -> None:
        with self.get_connection() as conn:
            for c in movements:
                conn.execute("""
                    INSERT OR REPLACE INTO camera_movements (
                        movement_id, asset_id, start_sec, end_sec, motion_type,
                        magnitude, direction_json, confidence, evidence_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    str(c.movement_id), str(c.asset_id),
                    c.timecode_range.start_seconds, c.timecode_range.end_seconds,
                    c.motion_type.value if hasattr(c.motion_type, "value") else str(c.motion_type),
                    c.magnitude, json.dumps(c.direction_vector), c.confidence, "{}"
                ))

    def get_camera_movements(self, asset_id: UUID) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM camera_movements WHERE asset_id = ? ORDER BY start_sec ASC",
                (str(asset_id),)
            ).fetchall()
            return [dict(r) for r in rows]

    def save_ocr_observations(self, ocr_list: List[Any]) -> None:
        with self.get_connection() as conn:
            for o in ocr_list:
                box_dict = {"x": o.box.x, "y": o.box.y, "w": o.box.width, "h": o.box.height}
                conn.execute("""
                    INSERT OR REPLACE INTO ocr_observations (
                        ocr_id, asset_id, text, timestamp_sec, frame_number,
                        box_json, text_category, confidence
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    str(o.ocr_id), str(o.asset_id), o.text, o.timestamp_seconds,
                    o.frame_number, json.dumps(box_dict), o.text_category, o.confidence
                ))

    def get_ocr_observations(self, asset_id: UUID) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM ocr_observations WHERE asset_id = ? ORDER BY timestamp_sec ASC",
                (str(asset_id),)
            ).fetchall()
            return [dict(r) for r in rows]

    def save_reference_profile(self, profile: Any) -> None:
        with self.get_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO reference_profiles (
                    profile_id, asset_id, name, created_at, visual_style_json,
                    editing_style_json, mograph_json, audio_style_json, narrative_json, key_moments_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                str(profile.profile_id), str(profile.asset_id), profile.name, profile.created_at,
                json.dumps(profile.visual_style), json.dumps(profile.editing_style),
                json.dumps(profile.motion_graphics), json.dumps(profile.audio_style),
                json.dumps(profile.narrative_arc), json.dumps(profile.key_moments)
            ))

    def get_reference_profile(self, asset_id: UUID) -> Optional[Dict[str, Any]]:
        with self.get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM reference_profiles WHERE asset_id = ?",
                (str(asset_id),)
            ).fetchone()
            if not row:
                return None
            return {
                "profile_id": UUID(row["profile_id"]),
                "asset_id": UUID(row["asset_id"]),
                "name": row["name"],
                "created_at": row["created_at"],
                "visual_style": json.loads(row["visual_style_json"]),
                "editing_style": json.loads(row["editing_style_json"]),
                "motion_graphics": json.loads(row["mograph_json"]),
                "audio_style": json.loads(row["audio_style_json"]),
                "narrative_arc": json.loads(row["narrative_json"]),
                "key_moments": json.loads(row["key_moments_json"])
            }

    # ---------------------------------------------------------
    # Part 04: Creative Direction & Production Planning Methods
    # ---------------------------------------------------------

    def save_creative_brief(self, brief: Any) -> None:
        with self.get_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO creative_briefs (
                    brief_id, project_id, project_name, production_type, genre,
                    target_duration_sec, intended_platform, aspect_ratio, resolution,
                    fps, language, target_audience, purpose, core_message,
                    desired_audience_response, call_to_action, emotional_objective,
                    narrative_objective, visual_style, cinematography, lighting_style,
                    color_palette_json, pacing_style, typography_style, sound_design_notes,
                    music_direction, available_footage_ids_json, reference_asset_ids_json,
                    budget_tier, model_restrictions_json, exclusions_json, assumptions_json,
                    created_at, version
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                str(brief.brief_id), str(brief.project_id), brief.project_name,
                getattr(brief.production_type, "value", str(brief.production_type)),
                brief.genre, float(brief.target_duration_sec), brief.intended_platform,
                brief.aspect_ratio, brief.resolution, float(brief.fps), brief.language,
                brief.target_audience, brief.purpose, brief.core_message,
                brief.desired_audience_response, brief.call_to_action, brief.emotional_objective,
                brief.narrative_objective, brief.visual_style, brief.cinematography,
                brief.lighting_style, json.dumps(brief.color_palette),
                getattr(brief.pacing_style, "value", str(brief.pacing_style)),
                brief.typography_style, brief.sound_design_notes, brief.music_direction,
                json.dumps([str(x) for x in brief.available_footage_ids]),
                json.dumps([str(x) for x in brief.reference_asset_ids]),
                brief.budget_tier, json.dumps(brief.model_restrictions),
                json.dumps(brief.exclusions), json.dumps(brief.assumptions),
                brief.created_at, int(brief.version)
            ))

    def get_creative_brief(self, project_id: UUID) -> Optional[Dict[str, Any]]:
        with self.get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM creative_briefs WHERE project_id = ? ORDER BY version DESC LIMIT 1",
                (str(project_id),)
            ).fetchone()
            if not row:
                return None
            return {
                "brief_id": UUID(row["brief_id"]),
                "project_id": UUID(row["project_id"]),
                "project_name": row["project_name"],
                "production_type": row["production_type"],
                "genre": row["genre"],
                "target_duration_sec": row["target_duration_sec"],
                "intended_platform": row["intended_platform"],
                "aspect_ratio": row["aspect_ratio"],
                "resolution": row["resolution"],
                "fps": row["fps"],
                "language": row["language"],
                "target_audience": row["target_audience"],
                "purpose": row["purpose"],
                "core_message": row["core_message"],
                "desired_audience_response": row["desired_audience_response"],
                "call_to_action": row["call_to_action"],
                "emotional_objective": row["emotional_objective"],
                "narrative_objective": row["narrative_objective"],
                "visual_style": row["visual_style"],
                "cinematography": row["cinematography"],
                "lighting_style": row["lighting_style"],
                "color_palette": json.loads(row["color_palette_json"]),
                "pacing_style": row["pacing_style"],
                "typography_style": row["typography_style"],
                "sound_design_notes": row["sound_design_notes"],
                "music_direction": row["music_direction"],
                "available_footage_ids": [UUID(x) for x in json.loads(row["available_footage_ids_json"])],
                "reference_asset_ids": [UUID(x) for x in json.loads(row["reference_asset_ids_json"])],
                "budget_tier": row["budget_tier"],
                "model_restrictions": json.loads(row["model_restrictions_json"]),
                "exclusions": json.loads(row["exclusions_json"]),
                "assumptions": json.loads(row["assumptions_json"]),
                "created_at": row["created_at"],
                "version": row["version"]
            }

    def save_creative_concepts(self, concepts: List[Any]) -> None:
        with self.get_connection() as conn:
            for c in concepts:
                conn.execute("""
                    INSERT OR REPLACE INTO creative_concepts (
                        concept_id, project_id, name, creative_premise,
                        narrative_approach, visual_treatment, cinematography_style,
                        color_direction, sound_direction, editing_rhythm,
                        motion_graphics_style, production_complexity,
                        estimated_generation_reqs_json, risks_and_limitations_json,
                        is_selected, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    str(c.concept_id), str(c.project_id), c.name, c.creative_premise,
                    c.narrative_approach, c.visual_treatment, c.cinematography_style,
                    c.color_direction, c.sound_direction, c.editing_rhythm,
                    c.motion_graphics_style,
                    getattr(c.production_complexity, "value", str(c.production_complexity)),
                    json.dumps(c.estimated_generation_requirements),
                    json.dumps(c.risks_and_limitations), 1 if c.is_selected else 0,
                    c.created_at
                ))

    def get_creative_concepts(self, project_id: UUID) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM creative_concepts WHERE project_id = ? ORDER BY created_at ASC",
                (str(project_id),)
            ).fetchall()
            return [{
                "concept_id": UUID(r["concept_id"]),
                "project_id": UUID(r["project_id"]),
                "name": r["name"],
                "creative_premise": r["creative_premise"],
                "narrative_approach": r["narrative_approach"],
                "visual_treatment": r["visual_treatment"],
                "cinematography_style": r["cinematography_style"],
                "color_direction": r["color_direction"],
                "sound_direction": r["sound_direction"],
                "editing_rhythm": r["editing_rhythm"],
                "motion_graphics_style": r["motion_graphics_style"],
                "production_complexity": r["production_complexity"],
                "estimated_generation_requirements": json.loads(r["estimated_generation_reqs_json"]),
                "risks_and_limitations": json.loads(r["risks_and_limitations_json"]),
                "is_selected": bool(r["is_selected"]),
                "created_at": r["created_at"]
            } for r in rows]

    def select_concept(self, project_id: UUID, concept_id: UUID) -> None:
        with self.get_connection() as conn:
            conn.execute("UPDATE creative_concepts SET is_selected = 0 WHERE project_id = ?", (str(project_id),))
            conn.execute("UPDATE creative_concepts SET is_selected = 1 WHERE concept_id = ?", (str(concept_id),))

    def save_script(self, script: Any) -> None:
        with self.get_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO production_scripts (
                    script_id, project_id, title, logline, target_duration_sec,
                    estimated_spoken_duration_sec, total_words, version, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                str(script.script_id), str(script.project_id), script.title, script.logline,
                float(script.target_duration_sec), float(script.estimated_spoken_duration_sec),
                int(script.total_words), int(script.version), script.created_at
            ))
            for sc in script.scenes:
                diag_list = []
                for d in sc.dialogue_entries:
                    diag_list.append({
                        "entry_id": str(d.entry_id),
                        "speaker": d.speaker,
                        "text": d.text,
                        "entry_type": getattr(d.entry_type, "value", str(d.entry_type)),
                        "estimated_duration_sec": d.estimated_duration_sec,
                        "emotional_direction": d.emotional_direction
                    })
                conn.execute("""
                    INSERT OR REPLACE INTO script_scenes (
                        scene_id, script_id, scene_number, title, slugline,
                        narrative_purpose, location, time_of_day, characters_json,
                        action_description, dialogue_entries_json, emotional_tone,
                        estimated_duration_sec, continuity_notes
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    str(sc.scene_id), str(sc.script_id), int(sc.scene_number), sc.title,
                    sc.slugline, sc.narrative_purpose, sc.location, sc.time_of_day,
                    json.dumps(sc.characters_present), sc.action_description,
                    json.dumps(diag_list), sc.emotional_tone, float(sc.estimated_duration_sec),
                    sc.continuity_notes
                ))

    def get_script(self, project_id: UUID) -> Optional[Dict[str, Any]]:
        with self.get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM production_scripts WHERE project_id = ? ORDER BY version DESC LIMIT 1",
                (str(project_id),)
            ).fetchone()
            if not row:
                return None
            script_id = row["script_id"]
            scene_rows = conn.execute(
                "SELECT * FROM script_scenes WHERE script_id = ? ORDER BY scene_number ASC",
                (script_id,)
            ).fetchall()
            scenes = [{
                "scene_id": UUID(sc["scene_id"]),
                "script_id": UUID(sc["script_id"]),
                "scene_number": sc["scene_number"],
                "title": sc["title"],
                "slugline": sc["slugline"],
                "narrative_purpose": sc["narrative_purpose"],
                "location": sc["location"],
                "time_of_day": sc["time_of_day"],
                "characters_present": json.loads(sc["characters_json"]),
                "action_description": sc["action_description"],
                "dialogue_entries": json.loads(sc["dialogue_entries_json"]),
                "emotional_tone": sc["emotional_tone"],
                "estimated_duration_sec": sc["estimated_duration_sec"],
                "continuity_notes": sc["continuity_notes"]
            } for sc in scene_rows]

            return {
                "script_id": UUID(row["script_id"]),
                "project_id": UUID(row["project_id"]),
                "title": row["title"],
                "logline": row["logline"],
                "target_duration_sec": row["target_duration_sec"],
                "estimated_spoken_duration_sec": row["estimated_spoken_duration_sec"],
                "total_words": row["total_words"],
                "version": row["version"],
                "created_at": row["created_at"],
                "scenes": scenes
            }

    def save_planned_shots(self, shots: List[Any]) -> None:
        with self.get_connection() as conn:
            for s in shots:
                conn.execute("""
                    INSERT OR REPLACE INTO planned_shots (
                        shot_id, scene_id, shot_number, narrative_purpose,
                        shot_scale, camera_angle, camera_motion, lens_focal_length,
                        camera_position, subject_action, environment_description,
                        lighting_direction, composition_notes, depth_of_field,
                        focus_behavior, motion_characteristics, start_state, end_state,
                        estimated_duration_sec, aspect_ratio, visual_style,
                        continuity_reqs_json, required_source_assets_json,
                        generation_requirements
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    str(s.shot_id), str(s.scene_id), int(s.shot_number), s.narrative_purpose,
                    getattr(s.shot_scale, "value", str(s.shot_scale)),
                    getattr(s.camera_angle, "value", str(s.camera_angle)),
                    getattr(s.camera_motion, "value", str(s.camera_motion)),
                    s.lens_focal_length, s.camera_position, s.subject_action,
                    s.environment_description, s.lighting_direction, s.composition_notes,
                    s.depth_of_field, s.focus_behavior, s.motion_characteristics,
                    s.start_state, s.end_state, float(s.estimated_duration_sec),
                    s.aspect_ratio, s.visual_style,
                    json.dumps(s.continuity_requirements),
                    json.dumps([str(x) for x in s.required_source_assets]),
                    getattr(s.generation_requirements, "value", str(s.generation_requirements))
                ))

    def get_planned_shots(self, scene_id: Optional[UUID] = None) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            if scene_id:
                rows = conn.execute(
                    "SELECT * FROM planned_shots WHERE scene_id = ? ORDER BY shot_number ASC",
                    (str(scene_id),)
                ).fetchall()
            else:
                rows = conn.execute("SELECT * FROM planned_shots ORDER BY shot_number ASC").fetchall()
            return [{
                "shot_id": UUID(r["shot_id"]),
                "scene_id": UUID(r["scene_id"]),
                "shot_number": r["shot_number"],
                "narrative_purpose": r["narrative_purpose"],
                "shot_scale": r["shot_scale"],
                "camera_angle": r["camera_angle"],
                "camera_motion": r["camera_motion"],
                "lens_focal_length": r["lens_focal_length"],
                "camera_position": r["camera_position"],
                "subject_action": r["subject_action"],
                "environment_description": r["environment_description"],
                "lighting_direction": r["lighting_direction"],
                "composition_notes": r["composition_notes"],
                "depth_of_field": r["depth_of_field"],
                "focus_behavior": r["focus_behavior"],
                "motion_characteristics": r["motion_characteristics"],
                "start_state": r["start_state"],
                "end_state": r["end_state"],
                "estimated_duration_sec": r["estimated_duration_sec"],
                "aspect_ratio": r["aspect_ratio"],
                "visual_style": r["visual_style"],
                "continuity_requirements": json.loads(r["continuity_reqs_json"]),
                "required_source_assets": [UUID(x) for x in json.loads(r["required_source_assets_json"])],
                "generation_requirements": r["generation_requirements"]
            } for r in rows]

    def save_storyboard_frames(self, frames: List[Any]) -> None:
        with self.get_connection() as conn:
            for f in frames:
                conn.execute("""
                    INSERT OR REPLACE INTO storyboard_frames (
                        frame_id, shot_id, scene_id, frame_order, visual_prompt_spec,
                        visual_description, character_references_json,
                        environment_references_json, camera_composition,
                        lighting_direction, continuity_notes, approval_status,
                        image_asset_id
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    str(f.frame_id), str(f.shot_id), str(f.scene_id), int(f.frame_order),
                    f.visual_prompt_spec, f.visual_description,
                    json.dumps(f.character_references), json.dumps(f.environment_references),
                    f.camera_composition, f.lighting_direction, f.continuity_notes,
                    getattr(f.approval_status, "value", str(f.approval_status)),
                    str(f.image_asset_id) if f.image_asset_id else None
                ))

    def get_storyboard_frames(self, shot_id: Optional[UUID] = None) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            if shot_id:
                rows = conn.execute(
                    "SELECT * FROM storyboard_frames WHERE shot_id = ? ORDER BY frame_order ASC",
                    (str(shot_id),)
                ).fetchall()
            else:
                rows = conn.execute("SELECT * FROM storyboard_frames ORDER BY frame_order ASC").fetchall()
            return [{
                "frame_id": UUID(r["frame_id"]),
                "shot_id": UUID(r["shot_id"]),
                "scene_id": UUID(r["scene_id"]),
                "frame_order": r["frame_order"],
                "visual_prompt_spec": r["visual_prompt_spec"],
                "visual_description": r["visual_description"],
                "character_references": json.loads(r["character_references_json"]),
                "environment_references": json.loads(r["environment_references_json"]),
                "camera_composition": r["camera_composition"],
                "lighting_direction": r["lighting_direction"],
                "continuity_notes": r["continuity_notes"],
                "approval_status": r["approval_status"],
                "image_asset_id": UUID(r["image_asset_id"]) if r["image_asset_id"] else None
            } for r in rows]

    def save_character(self, character: Any) -> None:
        with self.get_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO characters (
                    character_id, project_id, name, age_appearance, gender,
                    physical_description, costume_wardrobe, personality_traits_json,
                    reference_asset_ids_json, voice_profile_id, continuity_rules_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                str(character.character_id), str(character.project_id), character.name,
                character.age_appearance, character.gender, character.physical_description,
                character.costume_wardrobe, json.dumps(character.personality_traits),
                json.dumps([str(x) for x in character.reference_asset_ids]),
                character.voice_profile_id, json.dumps(character.continuity_rules)
            ))

    def get_characters(self, project_id: UUID) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            rows = conn.execute("SELECT * FROM characters WHERE project_id = ?", (str(project_id),)).fetchall()
            return [{
                "character_id": UUID(r["character_id"]),
                "project_id": UUID(r["project_id"]),
                "name": r["name"],
                "age_appearance": r["age_appearance"],
                "gender": r["gender"],
                "physical_description": r["physical_description"],
                "costume_wardrobe": r["costume_wardrobe"],
                "personality_traits": json.loads(r["personality_traits_json"]),
                "reference_asset_ids": [UUID(x) for x in json.loads(r["reference_asset_ids_json"])],
                "voice_profile_id": r["voice_profile_id"],
                "continuity_rules": json.loads(r["continuity_rules_json"])
            } for r in rows]

    def save_environment(self, env: Any) -> None:
        with self.get_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO environments (
                    environment_id, project_id, name, description, location_type,
                    lighting_conditions, time_of_day, spatial_layout, reference_asset_ids_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                str(env.environment_id), str(env.project_id), env.name, env.description,
                env.location_type, env.lighting_conditions, env.time_of_day,
                env.spatial_layout, json.dumps([str(x) for x in env.reference_asset_ids])
            ))

    def get_environments(self, project_id: UUID) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            rows = conn.execute("SELECT * FROM environments WHERE project_id = ?", (str(project_id),)).fetchall()
            return [{
                "environment_id": UUID(r["environment_id"]),
                "project_id": UUID(r["project_id"]),
                "name": r["name"],
                "description": r["description"],
                "location_type": r["location_type"],
                "lighting_conditions": r["lighting_conditions"],
                "time_of_day": r["time_of_day"],
                "spatial_layout": r["spatial_layout"],
                "reference_asset_ids": [UUID(x) for x in json.loads(r["reference_asset_ids_json"])]
            } for r in rows]

    def save_editing_blueprint(self, blueprint: Any) -> None:
        with self.get_connection() as conn:
            order_list = []
            for s in blueprint.narrative_order:
                order_list.append({
                    "mapping_id": str(s.mapping_id),
                    "timeline_in_sec": s.timeline_in_sec,
                    "timeline_out_sec": s.timeline_out_sec,
                    "source_asset_id": str(s.source_asset_id),
                    "source_in_sec": s.source_in_sec,
                    "source_out_sec": s.source_out_sec,
                    "shot_purpose": s.shot_purpose,
                    "transition_in": getattr(s.transition_in, "value", str(s.transition_in)),
                    "transition_out": getattr(s.transition_out, "value", str(s.transition_out)),
                    "color_treatment": s.color_treatment,
                    "speed_ratio": s.speed_ratio
                })
            missing_list = []
            for m in blueprint.missing_coverage:
                missing_list.append({
                    "item_id": str(m.item_id),
                    "intended_timeline_sec": m.intended_timeline_sec,
                    "duration_sec": m.duration_sec,
                    "description": m.description,
                    "recommended_solution": getattr(m.recommended_solution, "value", str(m.recommended_solution)),
                    "suggested_prompt": m.suggested_prompt
                })
            conn.execute("""
                INSERT OR REPLACE INTO editing_blueprints (
                    blueprint_id, project_id, target_duration_sec, narrative_order_json,
                    pacing_style, transitions_json, music_placement_json,
                    dialogue_placement_json, sound_effects_json, motion_graphics_json,
                    missing_coverage_json, version, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                str(blueprint.blueprint_id), str(blueprint.project_id),
                float(blueprint.target_duration_sec), json.dumps(order_list),
                getattr(blueprint.pacing_style, "value", str(blueprint.pacing_style)),
                json.dumps(blueprint.transitions), json.dumps(blueprint.music_placement),
                json.dumps(blueprint.dialogue_placement), json.dumps(blueprint.sound_effects),
                json.dumps(blueprint.motion_graphics), json.dumps(missing_list),
                int(blueprint.version), blueprint.created_at
            ))

    def get_editing_blueprint(self, project_id: UUID) -> Optional[Dict[str, Any]]:
        with self.get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM editing_blueprints WHERE project_id = ? ORDER BY version DESC LIMIT 1",
                (str(project_id),)
            ).fetchone()
            if not row:
                return None
            return {
                "blueprint_id": UUID(row["blueprint_id"]),
                "project_id": UUID(row["project_id"]),
                "target_duration_sec": row["target_duration_sec"],
                "narrative_order": json.loads(row["narrative_order_json"]),
                "pacing_style": row["pacing_style"],
                "transitions": json.loads(row["transitions_json"]),
                "music_placement": json.loads(row["music_placement_json"]),
                "dialogue_placement": json.loads(row["dialogue_placement_json"]),
                "sound_effects": json.loads(row["sound_effects_json"]),
                "motion_graphics": json.loads(row["motion_graphics_json"]),
                "missing_coverage": json.loads(row["missing_coverage_json"]),
                "version": row["version"],
                "created_at": row["created_at"]
            }

    def save_production_blueprint(self, blueprint: Any) -> None:
        with self.get_connection() as conn:
            # Serialize blueprint sections
            brief_dict = {
                "brief_id": str(blueprint.brief.brief_id),
                "project_name": blueprint.brief.project_name,
                "production_type": getattr(blueprint.brief.production_type, "value", str(blueprint.brief.production_type)),
                "genre": blueprint.brief.genre,
                "target_duration_sec": blueprint.brief.target_duration_sec
            }
            concept_dict = None
            if blueprint.selected_concept:
                concept_dict = {
                    "concept_id": str(blueprint.selected_concept.concept_id),
                    "name": blueprint.selected_concept.name,
                    "premise": blueprint.selected_concept.creative_premise
                }
            script_dict = None
            if blueprint.script:
                script_dict = {
                    "script_id": str(blueprint.script.script_id),
                    "title": blueprint.script.title,
                    "scenes_count": len(blueprint.script.scenes)
                }
            breakdown_dict = None
            if blueprint.breakdown:
                breakdown_dict = {
                    "total_shots": blueprint.breakdown.total_shots,
                    "estimated_cost_usd": blueprint.breakdown.estimated_cost_usd,
                    "technical_risks": blueprint.breakdown.technical_risks
                }
            edit_dict = None
            if blueprint.editing_blueprint:
                edit_dict = {
                    "blueprint_id": str(blueprint.editing_blueprint.blueprint_id),
                    "target_duration_sec": blueprint.editing_blueprint.target_duration_sec,
                    "cuts_count": len(blueprint.editing_blueprint.narrative_order)
                }
            feasibility_dict = None
            if blueprint.feasibility:
                feasibility_dict = {
                    "feasibility_score": blueprint.feasibility.overall_feasibility_score,
                    "complexity": getattr(blueprint.feasibility.complexity_category, "value", str(blueprint.feasibility.complexity_category)),
                    "cost_range": blueprint.feasibility.estimated_cost_range
                }

            conn.execute("""
                INSERT OR REPLACE INTO production_blueprints (
                    blueprint_id, project_id, version, brief_json, concept_json,
                    script_json, breakdown_json, editing_blueprint_json,
                    feasibility_json, is_ready_for_production, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                str(blueprint.blueprint_id), str(blueprint.project_id), int(blueprint.version),
                json.dumps(brief_dict), json.dumps(concept_dict) if concept_dict else None,
                json.dumps(script_dict) if script_dict else None,
                json.dumps(breakdown_dict) if breakdown_dict else None,
                json.dumps(edit_dict) if edit_dict else None,
                json.dumps(feasibility_dict) if feasibility_dict else None,
                1 if blueprint.is_ready_for_production else 0, blueprint.created_at
            ))

    def get_production_blueprint(self, project_id: UUID, version: Optional[int] = None) -> Optional[Dict[str, Any]]:
        with self.get_connection() as conn:
            if version:
                row = conn.execute(
                    "SELECT * FROM production_blueprints WHERE project_id = ? AND version = ?",
                    (str(project_id), version)
                ).fetchone()
            else:
                row = conn.execute(
                    "SELECT * FROM production_blueprints WHERE project_id = ? ORDER BY version DESC LIMIT 1",
                    (str(project_id),)
                ).fetchone()
            if not row:
                return None
            return {
                "blueprint_id": UUID(row["blueprint_id"]),
                "project_id": UUID(row["project_id"]),
                "version": row["version"],
                "brief": json.loads(row["brief_json"]),
                "selected_concept": json.loads(row["concept_json"]) if row["concept_json"] else None,
                "script": json.loads(row["script_json"]) if row["script_json"] else None,
                "breakdown": json.loads(row["breakdown_json"]) if row["breakdown_json"] else None,
                "editing_blueprint": json.loads(row["editing_blueprint_json"]) if row["editing_blueprint_json"] else None,
                "feasibility": json.loads(row["feasibility_json"]) if row["feasibility_json"] else None,
                "is_ready_for_production": bool(row["is_ready_for_production"]),
                "created_at": row["created_at"]
            }

    def save_creative_approval(self, approval: Any) -> None:
        with self.get_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO creative_approvals (
                    approval_id, project_id, entity_type, entity_id, version,
                    status, reviewer_notes, approved_by, approved_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                str(approval.approval_id), str(approval.project_id),
                getattr(approval.entity_type, "value", str(approval.entity_type)),
                str(approval.entity_id), int(approval.version),
                getattr(approval.status, "value", str(approval.status)),
                approval.reviewer_notes, approval.approved_by, approval.approved_at
            ))

    def get_creative_approvals(self, project_id: UUID, entity_type: Optional[str] = None) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            if entity_type:
                rows = conn.execute(
                    "SELECT * FROM creative_approvals WHERE project_id = ? AND entity_type = ? ORDER BY version DESC",
                    (str(project_id), entity_type)
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM creative_approvals WHERE project_id = ? ORDER BY version DESC",
                    (str(project_id),)
                ).fetchall()
            return [{
                "approval_id": UUID(r["approval_id"]),
                "project_id": UUID(r["project_id"]),
                "entity_type": r["entity_type"],
                "entity_id": UUID(r["entity_id"]),
                "version": r["version"],
                "status": r["status"],
                "reviewer_notes": r["reviewer_notes"],
                "approved_by": r["approved_by"],
                "approved_at": r["approved_at"]
            } for r in rows]

    # -------------------------------------------------------------------------
    # Part 05 Non-Linear Editing Engine CRUD Methods
    # -------------------------------------------------------------------------

    def save_editing_project(self, project: Any) -> None:
        """Saves or updates an EditingProject and all child timelines."""
        with self.get_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO editing_projects (
                    project_id, name, active_timeline_id, settings_json, revision, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                str(project.project_id),
                project.name,
                str(project.active_timeline_id) if project.active_timeline_id else None,
                json.dumps(project.settings),
                int(project.revision),
                project.created_at,
                project.updated_at
            ))

    def get_editing_project(self, project_id: UUID) -> Optional[Dict[str, Any]]:
        with self.get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM editing_projects WHERE project_id = ?",
                (str(project_id),)
            ).fetchone()
            if not row:
                return None
            return {
                "project_id": UUID(row["project_id"]),
                "name": row["name"],
                "active_timeline_id": UUID(row["active_timeline_id"]) if row["active_timeline_id"] else None,
                "settings": json.loads(row["settings_json"]),
                "revision": row["revision"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"]
            }

    def save_timeline(self, timeline: Any) -> None:
        """Saves full timeline hierarchy: timeline, tracks, clips, transitions, markers."""
        with self.get_connection() as conn:
            # 1. Timeline
            conn.execute("""
                INSERT OR REPLACE INTO timelines (
                    timeline_id, project_id, name, time_base, duration_sec,
                    resolution_width, resolution_height, fps, sample_rate,
                    version, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                str(timeline.timeline_id),
                str(timeline.project_id),
                timeline.name,
                float(timeline.time_base),
                float(timeline.duration.to_seconds()),
                int(timeline.resolution_width),
                int(timeline.resolution_height),
                float(timeline.fps),
                int(timeline.sample_rate),
                int(timeline.version),
                timeline.created_at,
                timeline.updated_at
            ))

            # 2. Tracks & Children
            for track in timeline.tracks:
                conn.execute("""
                    INSERT OR REPLACE INTO tracks (
                        track_id, timeline_id, track_type, name, order_index,
                        is_muted, is_visible, is_locked, is_solo, gain, opacity
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    str(track.track_id),
                    str(timeline.timeline_id),
                    getattr(track.track_type, "value", str(track.track_type)),
                    track.name,
                    int(track.order_index),
                    1 if track.is_muted else 0,
                    1 if track.is_visible else 0,
                    1 if track.is_locked else 0,
                    1 if track.is_solo else 0,
                    float(track.gain),
                    float(track.opacity)
                ))

                # Clips
                for clip in track.clips:
                    conn.execute("""
                        INSERT OR REPLACE INTO clips (
                            clip_id, track_id, asset_id, timeline_start_sec, timeline_dur_sec,
                            source_in_sec, source_out_sec, speed, transform_json,
                            opacity, volume, pan, enabled, linked_clip_id, name
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        str(clip.clip_id),
                        str(track.track_id),
                        str(clip.asset_id),
                        float(clip.timeline_start.to_seconds()),
                        float(clip.timeline_duration.to_seconds()),
                        float(clip.source_in.to_seconds()),
                        float(clip.source_out.to_seconds()),
                        float(clip.speed),
                        json.dumps(clip.transform),
                        float(clip.opacity),
                        float(clip.volume),
                        float(clip.pan),
                        1 if clip.enabled else 0,
                        str(clip.linked_clip_id) if clip.linked_clip_id else None,
                        clip.name
                    ))

                    # Effects
                    for eff in clip.effects:
                        conn.execute("""
                            INSERT OR REPLACE INTO effects (
                                effect_id, clip_id, effect_type, parameters_json,
                                enabled, start_sec, duration_sec, processing_order
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            str(eff.effect_id),
                            str(clip.clip_id),
                            getattr(eff.effect_type, "value", str(eff.effect_type)),
                            json.dumps(eff.parameters),
                            1 if eff.enabled else 0,
                            eff.start_time.to_seconds() if eff.start_time else None,
                            eff.duration.to_seconds() if eff.duration else None,
                            int(eff.processing_order)
                        ))

                # Transitions
                for trans in track.transitions:
                    conn.execute("""
                        INSERT OR REPLACE INTO transitions (
                            transition_id, track_id, transition_type, start_time_sec,
                            duration_sec, from_clip_id, to_clip_id, parameters_json, easing
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        str(trans.transition_id),
                        str(track.track_id),
                        getattr(trans.transition_type, "value", str(trans.transition_type)),
                        float(trans.start_time.to_seconds()),
                        float(trans.duration.to_seconds()),
                        str(trans.from_clip_id) if trans.from_clip_id else None,
                        str(trans.to_clip_id) if trans.to_clip_id else None,
                        json.dumps(trans.parameters),
                        trans.easing
                    ))

            # Markers
            for marker in timeline.markers:
                conn.execute("""
                    INSERT OR REPLACE INTO timeline_markers (
                        marker_id, timeline_id, time_sec, name, color, comment
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    str(marker.marker_id),
                    str(timeline.timeline_id),
                    float(marker.time.to_seconds()),
                    marker.name,
                    marker.color,
                    marker.comment
                ))

    def get_timeline(self, timeline_id: UUID) -> Optional[Dict[str, Any]]:
        with self.get_connection() as conn:
            tl_row = conn.execute("SELECT * FROM timelines WHERE timeline_id = ?", (str(timeline_id),)).fetchone()
            if not tl_row:
                return None

            # Tracks
            track_rows = conn.execute(
                "SELECT * FROM tracks WHERE timeline_id = ? ORDER BY order_index ASC",
                (str(timeline_id),)
            ).fetchall()

            tracks = []
            for tr in track_rows:
                t_id = tr["track_id"]
                # Clips
                clip_rows = conn.execute(
                    "SELECT * FROM clips WHERE track_id = ? ORDER BY timeline_start_sec ASC",
                    (t_id,)
                ).fetchall()
                clips = []
                for c in clip_rows:
                    c_id = c["clip_id"]
                    eff_rows = conn.execute("SELECT * FROM effects WHERE clip_id = ? ORDER BY processing_order ASC", (c_id,)).fetchall()
                    clips.append({
                        "clip_id": UUID(c["clip_id"]),
                        "asset_id": UUID(c["asset_id"]),
                        "track_id": UUID(c["track_id"]),
                        "timeline_start_sec": c["timeline_start_sec"],
                        "timeline_dur_sec": c["timeline_dur_sec"],
                        "source_in_sec": c["source_in_sec"],
                        "source_out_sec": c["source_out_sec"],
                        "speed": c["speed"],
                        "transform": json.loads(c["transform_json"]),
                        "opacity": c["opacity"],
                        "volume": c["volume"],
                        "pan": c["pan"],
                        "enabled": bool(c["enabled"]),
                        "linked_clip_id": UUID(c["linked_clip_id"]) if c["linked_clip_id"] else None,
                        "name": c["name"],
                        "effects": [{
                            "effect_id": UUID(e["effect_id"]),
                            "effect_type": e["effect_type"],
                            "parameters": json.loads(e["parameters_json"]),
                            "enabled": bool(e["enabled"]),
                            "start_sec": e["start_sec"],
                            "duration_sec": e["duration_sec"],
                            "processing_order": e["processing_order"]
                        } for e in eff_rows]
                    })

                # Transitions
                trans_rows = conn.execute("SELECT * FROM transitions WHERE track_id = ?", (t_id,)).fetchall()
                transitions = [{
                    "transition_id": UUID(t["transition_id"]),
                    "track_id": UUID(t["track_id"]),
                    "transition_type": t["transition_type"],
                    "start_time_sec": t["start_time_sec"],
                    "duration_sec": t["duration_sec"],
                    "from_clip_id": UUID(t["from_clip_id"]) if t["from_clip_id"] else None,
                    "to_clip_id": UUID(t["to_clip_id"]) if t["to_clip_id"] else None,
                    "parameters": json.loads(t["parameters_json"]),
                    "easing": t["easing"]
                } for t in trans_rows]

                tracks.append({
                    "track_id": UUID(tr["track_id"]),
                    "timeline_id": UUID(tr["timeline_id"]),
                    "track_type": tr["track_type"],
                    "name": tr["name"],
                    "order_index": tr["order_index"],
                    "is_muted": bool(tr["is_muted"]),
                    "is_visible": bool(tr["is_visible"]),
                    "is_locked": bool(tr["is_locked"]),
                    "is_solo": bool(tr["is_solo"]),
                    "gain": tr["gain"],
                    "opacity": tr["opacity"],
                    "clips": clips,
                    "transitions": transitions
                })

            marker_rows = conn.execute("SELECT * FROM timeline_markers WHERE timeline_id = ?", (str(timeline_id),)).fetchall()
            markers = [{
                "marker_id": UUID(m["marker_id"]),
                "timeline_id": UUID(m["timeline_id"]),
                "time_sec": m["time_sec"],
                "name": m["name"],
                "color": m["color"],
                "comment": m["comment"]
            } for m in marker_rows]

            return {
                "timeline_id": UUID(tl_row["timeline_id"]),
                "project_id": UUID(tl_row["project_id"]),
                "name": tl_row["name"],
                "time_base": tl_row["time_base"],
                "duration_sec": tl_row["duration_sec"],
                "resolution_width": tl_row["resolution_width"],
                "resolution_height": tl_row["resolution_height"],
                "fps": tl_row["fps"],
                "sample_rate": tl_row["sample_rate"],
                "version": tl_row["version"],
                "created_at": tl_row["created_at"],
                "updated_at": tl_row["updated_at"],
                "tracks": tracks,
                "markers": markers
            }

    def delete_timeline(self, timeline_id: UUID) -> None:
        with self.get_connection() as conn:
            conn.execute("DELETE FROM timelines WHERE timeline_id = ?", (str(timeline_id),))

    def save_render_job(self, job: Any) -> None:
        with self.get_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO render_jobs (
                    render_id, project_id, timeline_id, output_path, is_preview,
                    format_preset, status, progress, error_message, created_at, completed_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                str(job.render_id),
                str(job.project_id),
                str(job.timeline_id),
                job.output_path,
                1 if job.is_preview else 0,
                job.format_preset,
                getattr(job.status, "value", str(job.status)),
                float(job.progress),
                job.error_message,
                job.created_at,
                job.completed_at
            ))

    def update_render_job(
        self,
        render_id: UUID,
        status: str,
        progress: float = 0.0,
        error_message: Optional[str] = None,
        completed_at: Optional[str] = None
    ) -> None:
        with self.get_connection() as conn:
            conn.execute("""
                UPDATE render_jobs
                SET status = ?, progress = ?, error_message = ?, completed_at = ?
                WHERE render_id = ?
            """, (
                status,
                progress,
                error_message,
                completed_at,
                str(render_id)
            ))

    def get_render_job(self, render_id: UUID) -> Optional[Dict[str, Any]]:
        with self.get_connection() as conn:
            row = conn.execute("SELECT * FROM render_jobs WHERE render_id = ?", (str(render_id),)).fetchone()
            if not row:
                return None
            return {
                "render_id": UUID(row["render_id"]),
                "project_id": UUID(row["project_id"]),
                "timeline_id": UUID(row["timeline_id"]),
                "output_path": row["output_path"],
                "is_preview": bool(row["is_preview"]),
                "format_preset": row["format_preset"],
                "status": row["status"],
                "progress": row["progress"],
                "error_message": row["error_message"],
                "created_at": row["created_at"],
                "completed_at": row["completed_at"]
            }

    def save_motion_composition(self, composition: Any) -> None:
        """Saves or updates a MotionComposition in the database."""
        now = utc_now_iso()
        comp_dict = composition.to_dict() if hasattr(composition, "to_dict") else composition
        comp_id = comp_dict.get("composition_id")
        project_id = comp_dict.get("project_id", "default")
        name = comp_dict.get("name", "Motion Composition")
        res = comp_dict.get("resolution", [1920, 1080])
        fps = float(comp_dict.get("fps", 24.0))
        dur_raw = comp_dict.get("duration", {"value": 120, "rate": 24.0})
        frames = int(dur_raw.get("value", 120))
        rate = float(dur_raw.get("rate", 24.0))

        with self.get_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO motion_compositions (
                    composition_id, project_id, name, resolution_w, resolution_h,
                    fps, duration_frames, duration_rate, composition_json, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                str(comp_id),
                str(project_id),
                name,
                int(res[0]),
                int(res[1]),
                fps,
                frames,
                rate,
                json.dumps(comp_dict),
                now,
                now
            ))

    def get_motion_composition(self, composition_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves a MotionComposition by composition_id."""
        with self.get_connection() as conn:
            row = conn.execute("SELECT * FROM motion_compositions WHERE composition_id = ?", (str(composition_id),)).fetchone()
            if not row:
                return None
            return json.loads(row["composition_json"])

    def list_motion_compositions(self, project_id: str) -> List[Dict[str, Any]]:
        """Lists all MotionCompositions for a given project_id."""
        with self.get_connection() as conn:
            rows = conn.execute("SELECT * FROM motion_compositions WHERE project_id = ? ORDER BY created_at DESC", (str(project_id),)).fetchall()
            return [json.loads(r["composition_json"]) for r in rows]

    def delete_motion_composition(self, composition_id: str) -> bool:
        """Deletes a MotionComposition by composition_id."""
        with self.get_connection() as conn:
            cur = conn.execute("DELETE FROM motion_compositions WHERE composition_id = ?", (str(composition_id),))
            return cur.rowcount > 0

    # -------------------------------------------------------------
    # Multimodal Intelligence Persistence Methods (Part 03)
    # -------------------------------------------------------------
    def save_shots(self, shots: List[Any]) -> None:
        with self.get_connection() as conn:
            for s in shots:
                evidence_json = json.dumps(s.evidence.raw_measurement) if s.evidence else "{}"
                conn.execute("""
                    INSERT OR REPLACE INTO shots (
                        shot_id, asset_id, shot_number, start_sec, end_sec,
                        start_frame, end_frame, transition_in, transition_out,
                        shot_scale, camera_angle, camera_motion, summary,
                        visual_features_json, confidence, evidence_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    str(s.shot_id), str(s.asset_id), s.shot_number,
                    s.timecode_range.start_seconds, s.timecode_range.end_seconds,
                    s.timecode_range.start_frame, s.timecode_range.end_frame,
                    s.transition_in.value if hasattr(s.transition_in, "value") else str(s.transition_in),
                    s.transition_out.value if hasattr(s.transition_out, "value") else str(s.transition_out),
                    s.shot_scale.value if hasattr(s.shot_scale, "value") else str(s.shot_scale),
                    s.camera_angle.value if hasattr(s.camera_angle, "value") else str(s.camera_angle),
                    s.camera_motion.value if hasattr(s.camera_motion, "value") else str(s.camera_motion),
                    s.summary, json.dumps(s.visual_features), s.confidence, evidence_json
                ))

    def get_shots(self, asset_id: UUID) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM shots WHERE asset_id = ? ORDER BY shot_number ASC",
                (str(asset_id),)
            ).fetchall()
            return [dict(r) for r in rows]

    def save_scenes(self, scenes: List[Any]) -> None:
        with self.get_connection() as conn:
            for sc in scenes:
                conn.execute("""
                    INSERT OR REPLACE INTO scenes (
                        scene_id, asset_id, scene_number, start_sec, end_sec,
                        narrative_summary, setting, lighting_style, dominant_mood,
                        shot_ids_json, confidence
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    str(sc.scene_id), str(sc.asset_id), sc.scene_number,
                    sc.timecode_range.start_seconds, sc.timecode_range.end_seconds,
                    sc.narrative_summary, sc.setting, sc.lighting_style, sc.dominant_mood,
                    json.dumps([str(sid) for sid in sc.shot_ids]), sc.confidence
                ))

    def get_scenes(self, asset_id: UUID) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM scenes WHERE asset_id = ? ORDER BY scene_number ASC",
                (str(asset_id),)
            ).fetchall()
            return [dict(r) for r in rows]

    def save_transcripts(self, segments: List[Any]) -> None:
        with self.get_connection() as conn:
            for t in segments:
                words_data = [
                    {"word": w.word, "start": w.start_seconds, "end": w.end_seconds, "confidence": w.confidence}
                    for w in getattr(t, "words", [])
                ]
                conn.execute("""
                    INSERT OR REPLACE INTO transcripts (
                        segment_id, asset_id, speaker_id, text, start_sec, end_sec,
                        language, words_json, confidence
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    str(t.segment_id), str(t.asset_id), t.speaker_id, t.text,
                    t.timecode_range.start_seconds, t.timecode_range.end_seconds,
                    t.language, json.dumps(words_data), t.confidence
                ))

    def get_transcripts(self, asset_id: UUID) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM transcripts WHERE asset_id = ? ORDER BY start_sec ASC",
                (str(asset_id),)
            ).fetchall()
            return [dict(r) for r in rows]

    def save_audio_events(self, events: List[Any]) -> None:
        with self.get_connection() as conn:
            for ev in events:
                conn.execute("""
                    INSERT OR REPLACE INTO audio_events (
                        event_id, asset_id, event_type, description, start_sec, end_sec,
                        spectral_energy, confidence, evidence_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    str(ev.event_id), str(ev.asset_id),
                    ev.event_type.value if hasattr(ev.event_type, "value") else str(ev.event_type),
                    ev.description, ev.timecode_range.start_seconds, ev.timecode_range.end_seconds,
                    ev.spectral_energy, ev.confidence, "{}"
                ))

    def get_audio_events(self, asset_id: UUID) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM audio_events WHERE asset_id = ? ORDER BY start_sec ASC",
                (str(asset_id),)
            ).fetchall()
            return [dict(r) for r in rows]

    def save_music_segments(self, segments: List[Any]) -> None:
        with self.get_connection() as conn:
            for m in segments:
                conn.execute("""
                    INSERT OR REPLACE INTO music_segments (
                        segment_id, asset_id, start_sec, end_sec, tempo_bpm,
                        beat_timestamps_json, rhythmic_energy, mood, has_vocals, confidence
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    str(m.segment_id), str(m.asset_id),
                    m.timecode_range.start_seconds, m.timecode_range.end_seconds,
                    m.tempo_bpm, json.dumps(m.beat_timestamps), m.rhythmic_energy,
                    m.mood, 1 if m.has_vocals else 0, m.confidence
                ))

    def get_music_segments(self, asset_id: UUID) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM music_segments WHERE asset_id = ? ORDER BY start_sec ASC",
                (str(asset_id),)
            ).fetchall()
            return [dict(r) for r in rows]

    def save_detected_objects(self, detections: List[Any]) -> None:
        with self.get_connection() as conn:
            for d in detections:
                box_dict = {"x": d.box.x, "y": d.box.y, "w": d.box.width, "h": d.box.height}
                conn.execute("""
                    INSERT OR REPLACE INTO detected_objects (
                        detection_id, asset_id, track_id, label, timestamp_sec,
                        frame_number, box_json, confidence
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    str(d.detection_id), str(d.asset_id), d.track_id, d.label,
                    d.timestamp_seconds, d.frame_number, json.dumps(box_dict), d.confidence
                ))

    def get_detected_objects(self, asset_id: UUID) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM detected_objects WHERE asset_id = ? ORDER BY timestamp_sec ASC",
                (str(asset_id),)
            ).fetchall()
            return [dict(r) for r in rows]

    def save_camera_movements(self, movements: List[Any]) -> None:
        with self.get_connection() as conn:
            for c in movements:
                conn.execute("""
                    INSERT OR REPLACE INTO camera_movements (
                        movement_id, asset_id, start_sec, end_sec, motion_type,
                        magnitude, direction_json, confidence, evidence_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    str(c.movement_id), str(c.asset_id),
                    c.timecode_range.start_seconds, c.timecode_range.end_seconds,
                    c.motion_type.value if hasattr(c.motion_type, "value") else str(c.motion_type),
                    c.magnitude, json.dumps(c.direction_vector), c.confidence, "{}"
                ))

    def get_camera_movements(self, asset_id: UUID) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM camera_movements WHERE asset_id = ? ORDER BY start_sec ASC",
                (str(asset_id),)
            ).fetchall()
            return [dict(r) for r in rows]

    def save_ocr_observations(self, ocr_list: List[Any]) -> None:
        with self.get_connection() as conn:
            for o in ocr_list:
                box_dict = {"x": o.box.x, "y": o.box.y, "w": o.box.width, "h": o.box.height}
                conn.execute("""
                    INSERT OR REPLACE INTO ocr_observations (
                        ocr_id, asset_id, text, timestamp_sec, frame_number,
                        box_json, text_category, confidence
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    str(o.ocr_id), str(o.asset_id), o.text, o.timestamp_seconds,
                    o.frame_number, json.dumps(box_dict), o.text_category, o.confidence
                ))

    def get_ocr_observations(self, asset_id: UUID) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM ocr_observations WHERE asset_id = ? ORDER BY timestamp_sec ASC",
                (str(asset_id),)
            ).fetchall()
            return [dict(r) for r in rows]

    def save_reference_profile(self, profile: Any) -> None:
        with self.get_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO reference_profiles (
                    profile_id, asset_id, name, created_at, visual_style_json,
                    editing_style_json, mograph_json, audio_style_json, narrative_json, key_moments_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                str(profile.profile_id), str(profile.asset_id), profile.name, profile.created_at,
                json.dumps(profile.visual_style), json.dumps(profile.editing_style),
                json.dumps(profile.motion_graphics), json.dumps(profile.audio_style),
                json.dumps(profile.narrative_arc), json.dumps(profile.key_moments)
            ))

    def get_reference_profile(self, asset_id: UUID) -> Optional[Dict[str, Any]]:
        with self.get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM reference_profiles WHERE asset_id = ?",
                (str(asset_id),)
            ).fetchone()
            if not row:
                return None
            return {
                "profile_id": UUID(row["profile_id"]),
                "asset_id": UUID(row["asset_id"]),
                "name": row["name"],
                "created_at": row["created_at"],
                "visual_style": json.loads(row["visual_style_json"]),
                "editing_style": json.loads(row["editing_style_json"]),
                "motion_graphics": json.loads(row["mograph_json"]),
                "audio_style": json.loads(row["audio_style_json"]),
                "narrative_arc": json.loads(row["narrative_json"]),
                "key_moments": json.loads(row["key_moments_json"])
            }

    # ---------------------------------------------------------
    # Part 04: Creative Direction & Production Planning Methods
    # ---------------------------------------------------------

    def save_creative_brief(self, brief: Any) -> None:
        with self.get_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO creative_briefs (
                    brief_id, project_id, project_name, production_type, genre,
                    target_duration_sec, intended_platform, aspect_ratio, resolution,
                    fps, language, target_audience, purpose, core_message,
                    desired_audience_response, call_to_action, emotional_objective,
                    narrative_objective, visual_style, cinematography, lighting_style,
                    color_palette_json, pacing_style, typography_style, sound_design_notes,
                    music_direction, available_footage_ids_json, reference_asset_ids_json,
                    budget_tier, model_restrictions_json, exclusions_json, assumptions_json,
                    created_at, version
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                str(brief.brief_id), str(brief.project_id), brief.project_name,
                getattr(brief.production_type, "value", str(brief.production_type)),
                brief.genre, float(brief.target_duration_sec), brief.intended_platform,
                brief.aspect_ratio, brief.resolution, float(brief.fps), brief.language,
                brief.target_audience, brief.purpose, brief.core_message,
                brief.desired_audience_response, brief.call_to_action, brief.emotional_objective,
                brief.narrative_objective, brief.visual_style, brief.cinematography,
                brief.lighting_style, json.dumps(brief.color_palette),
                getattr(brief.pacing_style, "value", str(brief.pacing_style)),
                brief.typography_style, brief.sound_design_notes, brief.music_direction,
                json.dumps([str(x) for x in brief.available_footage_ids]),
                json.dumps([str(x) for x in brief.reference_asset_ids]),
                brief.budget_tier, json.dumps(brief.model_restrictions),
                json.dumps(brief.exclusions), json.dumps(brief.assumptions),
                brief.created_at, int(brief.version)
            ))

    def get_creative_brief(self, project_id: UUID) -> Optional[Dict[str, Any]]:
        with self.get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM creative_briefs WHERE project_id = ? ORDER BY version DESC LIMIT 1",
                (str(project_id),)
            ).fetchone()
            if not row:
                return None
            return {
                "brief_id": UUID(row["brief_id"]),
                "project_id": UUID(row["project_id"]),
                "project_name": row["project_name"],
                "production_type": row["production_type"],
                "genre": row["genre"],
                "target_duration_sec": row["target_duration_sec"],
                "intended_platform": row["intended_platform"],
                "aspect_ratio": row["aspect_ratio"],
                "resolution": row["resolution"],
                "fps": row["fps"],
                "language": row["language"],
                "target_audience": row["target_audience"],
                "purpose": row["purpose"],
                "core_message": row["core_message"],
                "desired_audience_response": row["desired_audience_response"],
                "call_to_action": row["call_to_action"],
                "emotional_objective": row["emotional_objective"],
                "narrative_objective": row["narrative_objective"],
                "visual_style": row["visual_style"],
                "cinematography": row["cinematography"],
                "lighting_style": row["lighting_style"],
                "color_palette": json.loads(row["color_palette_json"]),
                "pacing_style": row["pacing_style"],
                "typography_style": row["typography_style"],
                "sound_design_notes": row["sound_design_notes"],
                "music_direction": row["music_direction"],
                "available_footage_ids": [UUID(x) for x in json.loads(row["available_footage_ids_json"])],
                "reference_asset_ids": [UUID(x) for x in json.loads(row["reference_asset_ids_json"])],
                "budget_tier": row["budget_tier"],
                "model_restrictions": json.loads(row["model_restrictions_json"]),
                "exclusions": json.loads(row["exclusions_json"]),
                "assumptions": json.loads(row["assumptions_json"]),
                "created_at": row["created_at"],
                "version": row["version"]
            }

    def save_creative_concepts(self, concepts: List[Any]) -> None:
        with self.get_connection() as conn:
            for c in concepts:
                conn.execute("""
                    INSERT OR REPLACE INTO creative_concepts (
                        concept_id, project_id, name, creative_premise,
                        narrative_approach, visual_treatment, cinematography_style,
                        color_direction, sound_direction, editing_rhythm,
                        motion_graphics_style, production_complexity,
                        estimated_generation_reqs_json, risks_and_limitations_json,
                        is_selected, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    str(c.concept_id), str(c.project_id), c.name, c.creative_premise,
                    c.narrative_approach, c.visual_treatment, c.cinematography_style,
                    c.color_direction, c.sound_direction, c.editing_rhythm,
                    c.motion_graphics_style,
                    getattr(c.production_complexity, "value", str(c.production_complexity)),
                    json.dumps(c.estimated_generation_requirements),
                    json.dumps(c.risks_and_limitations), 1 if c.is_selected else 0,
                    c.created_at
                ))

    def get_creative_concepts(self, project_id: UUID) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM creative_concepts WHERE project_id = ? ORDER BY created_at ASC",
                (str(project_id),)
            ).fetchall()
            return [{
                "concept_id": UUID(r["concept_id"]),
                "project_id": UUID(r["project_id"]),
                "name": r["name"],
                "creative_premise": r["creative_premise"],
                "narrative_approach": r["narrative_approach"],
                "visual_treatment": r["visual_treatment"],
                "cinematography_style": r["cinematography_style"],
                "color_direction": r["color_direction"],
                "sound_direction": r["sound_direction"],
                "editing_rhythm": r["editing_rhythm"],
                "motion_graphics_style": r["motion_graphics_style"],
                "production_complexity": r["production_complexity"],
                "estimated_generation_requirements": json.loads(r["estimated_generation_reqs_json"]),
                "risks_and_limitations": json.loads(r["risks_and_limitations_json"]),
                "is_selected": bool(r["is_selected"]),
                "created_at": r["created_at"]
            } for r in rows]

    def select_concept(self, project_id: UUID, concept_id: UUID) -> None:
        with self.get_connection() as conn:
            conn.execute("UPDATE creative_concepts SET is_selected = 0 WHERE project_id = ?", (str(project_id),))
            conn.execute("UPDATE creative_concepts SET is_selected = 1 WHERE concept_id = ?", (str(concept_id),))

    def save_script(self, script: Any) -> None:
        with self.get_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO production_scripts (
                    script_id, project_id, title, logline, target_duration_sec,
                    estimated_spoken_duration_sec, total_words, version, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                str(script.script_id), str(script.project_id), script.title, script.logline,
                float(script.target_duration_sec), float(script.estimated_spoken_duration_sec),
                int(script.total_words), int(script.version), script.created_at
            ))
            for sc in script.scenes:
                diag_list = []
                for d in sc.dialogue_entries:
                    diag_list.append({
                        "entry_id": str(d.entry_id),
                        "speaker": d.speaker,
                        "text": d.text,
                        "entry_type": getattr(d.entry_type, "value", str(d.entry_type)),
                        "estimated_duration_sec": d.estimated_duration_sec,
                        "emotional_direction": d.emotional_direction
                    })
                conn.execute("""
                    INSERT OR REPLACE INTO script_scenes (
                        scene_id, script_id, scene_number, title, slugline,
                        narrative_purpose, location, time_of_day, characters_json,
                        action_description, dialogue_entries_json, emotional_tone,
                        estimated_duration_sec, continuity_notes
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    str(sc.scene_id), str(sc.script_id), int(sc.scene_number), sc.title,
                    sc.slugline, sc.narrative_purpose, sc.location, sc.time_of_day,
                    json.dumps(sc.characters_present), sc.action_description,
                    json.dumps(diag_list), sc.emotional_tone, float(sc.estimated_duration_sec),
                    sc.continuity_notes
                ))

    def get_script(self, project_id: UUID) -> Optional[Dict[str, Any]]:
        with self.get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM production_scripts WHERE project_id = ? ORDER BY version DESC LIMIT 1",
                (str(project_id),)
            ).fetchone()
            if not row:
                return None
            script_id = row["script_id"]
            scene_rows = conn.execute(
                "SELECT * FROM script_scenes WHERE script_id = ? ORDER BY scene_number ASC",
                (script_id,)
            ).fetchall()
            scenes = [{
                "scene_id": UUID(sc["scene_id"]),
                "script_id": UUID(sc["script_id"]),
                "scene_number": sc["scene_number"],
                "title": sc["title"],
                "slugline": sc["slugline"],
                "narrative_purpose": sc["narrative_purpose"],
                "location": sc["location"],
                "time_of_day": sc["time_of_day"],
                "characters_present": json.loads(sc["characters_json"]),
                "action_description": sc["action_description"],
                "dialogue_entries": json.loads(sc["dialogue_entries_json"]),
                "emotional_tone": sc["emotional_tone"],
                "estimated_duration_sec": sc["estimated_duration_sec"],
                "continuity_notes": sc["continuity_notes"]
            } for sc in scene_rows]

            return {
                "script_id": UUID(row["script_id"]),
                "project_id": UUID(row["project_id"]),
                "title": row["title"],
                "logline": row["logline"],
                "target_duration_sec": row["target_duration_sec"],
                "estimated_spoken_duration_sec": row["estimated_spoken_duration_sec"],
                "total_words": row["total_words"],
                "version": row["version"],
                "created_at": row["created_at"],
                "scenes": scenes
            }

    def save_planned_shots(self, shots: List[Any]) -> None:
        with self.get_connection() as conn:
            for s in shots:
                conn.execute("""
                    INSERT OR REPLACE INTO planned_shots (
                        shot_id, scene_id, shot_number, narrative_purpose,
                        shot_scale, camera_angle, camera_motion, lens_focal_length,
                        camera_position, subject_action, environment_description,
                        lighting_direction, composition_notes, depth_of_field,
                        focus_behavior, motion_characteristics, start_state, end_state,
                        estimated_duration_sec, aspect_ratio, visual_style,
                        continuity_reqs_json, required_source_assets_json,
                        generation_requirements
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    str(s.shot_id), str(s.scene_id), int(s.shot_number), s.narrative_purpose,
                    getattr(s.shot_scale, "value", str(s.shot_scale)),
                    getattr(s.camera_angle, "value", str(s.camera_angle)),
                    getattr(s.camera_motion, "value", str(s.camera_motion)),
                    s.lens_focal_length, s.camera_position, s.subject_action,
                    s.environment_description, s.lighting_direction, s.composition_notes,
                    s.depth_of_field, s.focus_behavior, s.motion_characteristics,
                    s.start_state, s.end_state, float(s.estimated_duration_sec),
                    s.aspect_ratio, s.visual_style,
                    json.dumps(s.continuity_requirements),
                    json.dumps([str(x) for x in s.required_source_assets]),
                    getattr(s.generation_requirements, "value", str(s.generation_requirements))
                ))

    def get_planned_shots(self, scene_id: Optional[UUID] = None) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            if scene_id:
                rows = conn.execute(
                    "SELECT * FROM planned_shots WHERE scene_id = ? ORDER BY shot_number ASC",
                    (str(scene_id),)
                ).fetchall()
            else:
                rows = conn.execute("SELECT * FROM planned_shots ORDER BY shot_number ASC").fetchall()
            return [{
                "shot_id": UUID(r["shot_id"]),
                "scene_id": UUID(r["scene_id"]),
                "shot_number": r["shot_number"],
                "narrative_purpose": r["narrative_purpose"],
                "shot_scale": r["shot_scale"],
                "camera_angle": r["camera_angle"],
                "camera_motion": r["camera_motion"],
                "lens_focal_length": r["lens_focal_length"],
                "camera_position": r["camera_position"],
                "subject_action": r["subject_action"],
                "environment_description": r["environment_description"],
                "lighting_direction": r["lighting_direction"],
                "composition_notes": r["composition_notes"],
                "depth_of_field": r["depth_of_field"],
                "focus_behavior": r["focus_behavior"],
                "motion_characteristics": r["motion_characteristics"],
                "start_state": r["start_state"],
                "end_state": r["end_state"],
                "estimated_duration_sec": r["estimated_duration_sec"],
                "aspect_ratio": r["aspect_ratio"],
                "visual_style": r["visual_style"],
                "continuity_requirements": json.loads(r["continuity_reqs_json"]),
                "required_source_assets": [UUID(x) for x in json.loads(r["required_source_assets_json"])],
                "generation_requirements": r["generation_requirements"]
            } for r in rows]

    def save_storyboard_frames(self, frames: List[Any]) -> None:
        with self.get_connection() as conn:
            for f in frames:
                conn.execute("""
                    INSERT OR REPLACE INTO storyboard_frames (
                        frame_id, shot_id, scene_id, frame_order, visual_prompt_spec,
                        visual_description, character_references_json,
                        environment_references_json, camera_composition,
                        lighting_direction, continuity_notes, approval_status,
                        image_asset_id
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    str(f.frame_id), str(f.shot_id), str(f.scene_id), int(f.frame_order),
                    f.visual_prompt_spec, f.visual_description,
                    json.dumps(f.character_references), json.dumps(f.environment_references),
                    f.camera_composition, f.lighting_direction, f.continuity_notes,
                    getattr(f.approval_status, "value", str(f.approval_status)),
                    str(f.image_asset_id) if f.image_asset_id else None
                ))

    def get_storyboard_frames(self, shot_id: Optional[UUID] = None) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            if shot_id:
                rows = conn.execute(
                    "SELECT * FROM storyboard_frames WHERE shot_id = ? ORDER BY frame_order ASC",
                    (str(shot_id),)
                ).fetchall()
            else:
                rows = conn.execute("SELECT * FROM storyboard_frames ORDER BY frame_order ASC").fetchall()
            return [{
                "frame_id": UUID(r["frame_id"]),
                "shot_id": UUID(r["shot_id"]),
                "scene_id": UUID(r["scene_id"]),
                "frame_order": r["frame_order"],
                "visual_prompt_spec": r["visual_prompt_spec"],
                "visual_description": r["visual_description"],
                "character_references": json.loads(r["character_references_json"]),
                "environment_references": json.loads(r["environment_references_json"]),
                "camera_composition": r["camera_composition"],
                "lighting_direction": r["lighting_direction"],
                "continuity_notes": r["continuity_notes"],
                "approval_status": r["approval_status"],
                "image_asset_id": UUID(r["image_asset_id"]) if r["image_asset_id"] else None
            } for r in rows]

    def save_character(self, character: Any) -> None:
        with self.get_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO characters (
                    character_id, project_id, name, age_appearance, gender,
                    physical_description, costume_wardrobe, personality_traits_json,
                    reference_asset_ids_json, voice_profile_id, continuity_rules_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                str(character.character_id), str(character.project_id), character.name,
                character.age_appearance, character.gender, character.physical_description,
                character.costume_wardrobe, json.dumps(character.personality_traits),
                json.dumps([str(x) for x in character.reference_asset_ids]),
                character.voice_profile_id, json.dumps(character.continuity_rules)
            ))

    def get_characters(self, project_id: UUID) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            rows = conn.execute("SELECT * FROM characters WHERE project_id = ?", (str(project_id),)).fetchall()
            return [{
                "character_id": UUID(r["character_id"]),
                "project_id": UUID(r["project_id"]),
                "name": r["name"],
                "age_appearance": r["age_appearance"],
                "gender": r["gender"],
                "physical_description": r["physical_description"],
                "costume_wardrobe": r["costume_wardrobe"],
                "personality_traits": json.loads(r["personality_traits_json"]),
                "reference_asset_ids": [UUID(x) for x in json.loads(r["reference_asset_ids_json"])],
                "voice_profile_id": r["voice_profile_id"],
                "continuity_rules": json.loads(r["continuity_rules_json"])
            } for r in rows]

    def save_environment(self, env: Any) -> None:
        with self.get_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO environments (
                    environment_id, project_id, name, description, location_type,
                    lighting_conditions, time_of_day, spatial_layout, reference_asset_ids_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                str(env.environment_id), str(env.project_id), env.name, env.description,
                env.location_type, env.lighting_conditions, env.time_of_day,
                env.spatial_layout, json.dumps([str(x) for x in env.reference_asset_ids])
            ))

    def get_environments(self, project_id: UUID) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            rows = conn.execute("SELECT * FROM environments WHERE project_id = ?", (str(project_id),)).fetchall()
            return [{
                "environment_id": UUID(r["environment_id"]),
                "project_id": UUID(r["project_id"]),
                "name": r["name"],
                "description": r["description"],
                "location_type": r["location_type"],
                "lighting_conditions": r["lighting_conditions"],
                "time_of_day": r["time_of_day"],
                "spatial_layout": r["spatial_layout"],
                "reference_asset_ids": [UUID(x) for x in json.loads(r["reference_asset_ids_json"])]
            } for r in rows]

    def save_editing_blueprint(self, blueprint: Any) -> None:
        with self.get_connection() as conn:
            order_list = []
            for s in blueprint.narrative_order:
                order_list.append({
                    "mapping_id": str(s.mapping_id),
                    "timeline_in_sec": s.timeline_in_sec,
                    "timeline_out_sec": s.timeline_out_sec,
                    "source_asset_id": str(s.source_asset_id),
                    "source_in_sec": s.source_in_sec,
                    "source_out_sec": s.source_out_sec,
                    "shot_purpose": s.shot_purpose,
                    "transition_in": getattr(s.transition_in, "value", str(s.transition_in)),
                    "transition_out": getattr(s.transition_out, "value", str(s.transition_out)),
                    "color_treatment": s.color_treatment,
                    "speed_ratio": s.speed_ratio
                })
            missing_list = []
            for m in blueprint.missing_coverage:
                missing_list.append({
                    "item_id": str(m.item_id),
                    "intended_timeline_sec": m.intended_timeline_sec,
                    "duration_sec": m.duration_sec,
                    "description": m.description,
                    "recommended_solution": getattr(m.recommended_solution, "value", str(m.recommended_solution)),
                    "suggested_prompt": m.suggested_prompt
                })
            conn.execute("""
                INSERT OR REPLACE INTO editing_blueprints (
                    blueprint_id, project_id, target_duration_sec, narrative_order_json,
                    pacing_style, transitions_json, music_placement_json,
                    dialogue_placement_json, sound_effects_json, motion_graphics_json,
                    missing_coverage_json, version, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                str(blueprint.blueprint_id), str(blueprint.project_id),
                float(blueprint.target_duration_sec), json.dumps(order_list),
                getattr(blueprint.pacing_style, "value", str(blueprint.pacing_style)),
                json.dumps(blueprint.transitions), json.dumps(blueprint.music_placement),
                json.dumps(blueprint.dialogue_placement), json.dumps(blueprint.sound_effects),
                json.dumps(blueprint.motion_graphics), json.dumps(missing_list),
                int(blueprint.version), blueprint.created_at
            ))

    def get_editing_blueprint(self, project_id: UUID) -> Optional[Dict[str, Any]]:
        with self.get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM editing_blueprints WHERE project_id = ? ORDER BY version DESC LIMIT 1",
                (str(project_id),)
            ).fetchone()
            if not row:
                return None
            return {
                "blueprint_id": UUID(row["blueprint_id"]),
                "project_id": UUID(row["project_id"]),
                "target_duration_sec": row["target_duration_sec"],
                "narrative_order": json.loads(row["narrative_order_json"]),
                "pacing_style": row["pacing_style"],
                "transitions": json.loads(row["transitions_json"]),
                "music_placement": json.loads(row["music_placement_json"]),
                "dialogue_placement": json.loads(row["dialogue_placement_json"]),
                "sound_effects": json.loads(row["sound_effects_json"]),
                "motion_graphics": json.loads(row["motion_graphics_json"]),
                "missing_coverage": json.loads(row["missing_coverage_json"]),
                "version": row["version"],
                "created_at": row["created_at"]
            }

    def save_production_blueprint(self, blueprint: Any) -> None:
        with self.get_connection() as conn:
            # Serialize blueprint sections
            brief_dict = {
                "brief_id": str(blueprint.brief.brief_id),
                "project_name": blueprint.brief.project_name,
                "production_type": getattr(blueprint.brief.production_type, "value", str(blueprint.brief.production_type)),
                "genre": blueprint.brief.genre,
                "target_duration_sec": blueprint.brief.target_duration_sec
            }
            concept_dict = None
            if blueprint.selected_concept:
                concept_dict = {
                    "concept_id": str(blueprint.selected_concept.concept_id),
                    "name": blueprint.selected_concept.name,
                    "premise": blueprint.selected_concept.creative_premise
                }
            script_dict = None
            if blueprint.script:
                script_dict = {
                    "script_id": str(blueprint.script.script_id),
                    "title": blueprint.script.title,
                    "scenes_count": len(blueprint.script.scenes)
                }
            breakdown_dict = None
            if blueprint.breakdown:
                breakdown_dict = {
                    "total_shots": blueprint.breakdown.total_shots,
                    "estimated_cost_usd": blueprint.breakdown.estimated_cost_usd,
                    "technical_risks": blueprint.breakdown.technical_risks
                }
            edit_dict = None
            if blueprint.editing_blueprint:
                edit_dict = {
                    "blueprint_id": str(blueprint.editing_blueprint.blueprint_id),
                    "target_duration_sec": blueprint.editing_blueprint.target_duration_sec,
                    "cuts_count": len(blueprint.editing_blueprint.narrative_order)
                }
            feasibility_dict = None
            if blueprint.feasibility:
                feasibility_dict = {
                    "feasibility_score": blueprint.feasibility.overall_feasibility_score,
                    "complexity": getattr(blueprint.feasibility.complexity_category, "value", str(blueprint.feasibility.complexity_category)),
                    "cost_range": blueprint.feasibility.estimated_cost_range
                }

            conn.execute("""
                INSERT OR REPLACE INTO production_blueprints (
                    blueprint_id, project_id, version, brief_json, concept_json,
                    script_json, breakdown_json, editing_blueprint_json,
                    feasibility_json, is_ready_for_production, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                str(blueprint.blueprint_id), str(blueprint.project_id), int(blueprint.version),
                json.dumps(brief_dict), json.dumps(concept_dict) if concept_dict else None,
                json.dumps(script_dict) if script_dict else None,
                json.dumps(breakdown_dict) if breakdown_dict else None,
                json.dumps(edit_dict) if edit_dict else None,
                json.dumps(feasibility_dict) if feasibility_dict else None,
                1 if blueprint.is_ready_for_production else 0, blueprint.created_at
            ))

    def get_production_blueprint(self, project_id: UUID, version: Optional[int] = None) -> Optional[Dict[str, Any]]:
        with self.get_connection() as conn:
            if version:
                row = conn.execute(
                    "SELECT * FROM production_blueprints WHERE project_id = ? AND version = ?",
                    (str(project_id), version)
                ).fetchone()
            else:
                row = conn.execute(
                    "SELECT * FROM production_blueprints WHERE project_id = ? ORDER BY version DESC LIMIT 1",
                    (str(project_id),)
                ).fetchone()
            if not row:
                return None
            return {
                "blueprint_id": UUID(row["blueprint_id"]),
                "project_id": UUID(row["project_id"]),
                "version": row["version"],
                "brief": json.loads(row["brief_json"]),
                "selected_concept": json.loads(row["concept_json"]) if row["concept_json"] else None,
                "script": json.loads(row["script_json"]) if row["script_json"] else None,
                "breakdown": json.loads(row["breakdown_json"]) if row["breakdown_json"] else None,
                "editing_blueprint": json.loads(row["editing_blueprint_json"]) if row["editing_blueprint_json"] else None,
                "feasibility": json.loads(row["feasibility_json"]) if row["feasibility_json"] else None,
                "is_ready_for_production": bool(row["is_ready_for_production"]),
                "created_at": row["created_at"]
            }

    def save_creative_approval(self, approval: Any) -> None:
        with self.get_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO creative_approvals (
                    approval_id, project_id, entity_type, entity_id, version,
                    status, reviewer_notes, approved_by, approved_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                str(approval.approval_id), str(approval.project_id),
                getattr(approval.entity_type, "value", str(approval.entity_type)),
                str(approval.entity_id), int(approval.version),
                getattr(approval.status, "value", str(approval.status)),
                approval.reviewer_notes, approval.approved_by, approval.approved_at
            ))

    def get_creative_approvals(self, project_id: UUID, entity_type: Optional[str] = None) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            if entity_type:
                rows = conn.execute(
                    "SELECT * FROM creative_approvals WHERE project_id = ? AND entity_type = ? ORDER BY version DESC",
                    (str(project_id), entity_type)
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM creative_approvals WHERE project_id = ? ORDER BY version DESC",
                    (str(project_id),)
                ).fetchall()
            return [{
                "approval_id": UUID(r["approval_id"]),
                "project_id": UUID(r["project_id"]),
                "entity_type": r["entity_type"],
                "entity_id": UUID(r["entity_id"]),
                "version": r["version"],
                "status": r["status"],
                "reviewer_notes": r["reviewer_notes"],
                "approved_by": r["approved_by"],
                "approved_at": r["approved_at"]
            } for r in rows]

    # -------------------------------------------------------------------------
    # Part 05 Non-Linear Editing Engine CRUD Methods
    # -------------------------------------------------------------------------

    def save_editing_project(self, project: Any) -> None:
        """Saves or updates an EditingProject and all child timelines."""
        with self.get_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO editing_projects (
                    project_id, name, active_timeline_id, settings_json, revision, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                str(project.project_id),
                project.name,
                str(project.active_timeline_id) if project.active_timeline_id else None,
                json.dumps(project.settings),
                int(project.revision),
                project.created_at,
                project.updated_at
            ))

    def get_editing_project(self, project_id: UUID) -> Optional[Dict[str, Any]]:
        with self.get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM editing_projects WHERE project_id = ?",
                (str(project_id),)
            ).fetchone()
            if not row:
                return None
            return {
                "project_id": UUID(row["project_id"]),
                "name": row["name"],
                "active_timeline_id": UUID(row["active_timeline_id"]) if row["active_timeline_id"] else None,
                "settings": json.loads(row["settings_json"]),
                "revision": row["revision"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"]
            }

    def save_timeline(self, timeline: Any) -> None:
        """Saves full timeline hierarchy: timeline, tracks, clips, transitions, markers."""
        with self.get_connection() as conn:
            # 1. Timeline
            conn.execute("""
                INSERT OR REPLACE INTO timelines (
                    timeline_id, project_id, name, time_base, duration_sec,
                    resolution_width, resolution_height, fps, sample_rate,
                    version, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                str(timeline.timeline_id),
                str(timeline.project_id),
                timeline.name,
                float(timeline.time_base),
                float(timeline.duration.to_seconds()),
                int(timeline.resolution_width),
                int(timeline.resolution_height),
                float(timeline.fps),
                int(timeline.sample_rate),
                int(timeline.version),
                timeline.created_at,
                timeline.updated_at
            ))

            # 2. Tracks & Children
            for track in timeline.tracks:
                conn.execute("""
                    INSERT OR REPLACE INTO tracks (
                        track_id, timeline_id, track_type, name, order_index,
                        is_muted, is_visible, is_locked, is_solo, gain, opacity
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    str(track.track_id),
                    str(timeline.timeline_id),
                    getattr(track.track_type, "value", str(track.track_type)),
                    track.name,
                    int(track.order_index),
                    1 if track.is_muted else 0,
                    1 if track.is_visible else 0,
                    1 if track.is_locked else 0,
                    1 if track.is_solo else 0,
                    float(track.gain),
                    float(track.opacity)
                ))

                # Clips
                for clip in track.clips:
                    conn.execute("""
                        INSERT OR REPLACE INTO clips (
                            clip_id, track_id, asset_id, timeline_start_sec, timeline_dur_sec,
                            source_in_sec, source_out_sec, speed, transform_json,
                            opacity, volume, pan, enabled, linked_clip_id, name
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        str(clip.clip_id),
                        str(track.track_id),
                        str(clip.asset_id),
                        float(clip.timeline_start.to_seconds()),
                        float(clip.timeline_duration.to_seconds()),
                        float(clip.source_in.to_seconds()),
                        float(clip.source_out.to_seconds()),
                        float(clip.speed),
                        json.dumps(clip.transform),
                        float(clip.opacity),
                        float(clip.volume),
                        float(clip.pan),
                        1 if clip.enabled else 0,
                        str(clip.linked_clip_id) if clip.linked_clip_id else None,
                        clip.name
                    ))

                    # Effects
                    for eff in clip.effects:
                        conn.execute("""
                            INSERT OR REPLACE INTO effects (
                                effect_id, clip_id, effect_type, parameters_json,
                                enabled, start_sec, duration_sec, processing_order
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            str(eff.effect_id),
                            str(clip.clip_id),
                            getattr(eff.effect_type, "value", str(eff.effect_type)),
                            json.dumps(eff.parameters),
                            1 if eff.enabled else 0,
                            eff.start_time.to_seconds() if eff.start_time else None,
                            eff.duration.to_seconds() if eff.duration else None,
                            int(eff.processing_order)
                        ))

                # Transitions
                for trans in track.transitions:
                    conn.execute("""
                        INSERT OR REPLACE INTO transitions (
                            transition_id, track_id, transition_type, start_time_sec,
                            duration_sec, from_clip_id, to_clip_id, parameters_json, easing
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        str(trans.transition_id),
                        str(track.track_id),
                        getattr(trans.transition_type, "value", str(trans.transition_type)),
                        float(trans.start_time.to_seconds()),
                        float(trans.duration.to_seconds()),
                        str(trans.from_clip_id) if trans.from_clip_id else None,
                        str(trans.to_clip_id) if trans.to_clip_id else None,
                        json.dumps(trans.parameters),
                        trans.easing
                    ))

            # Markers
            for marker in timeline.markers:
                conn.execute("""
                    INSERT OR REPLACE INTO timeline_markers (
                        marker_id, timeline_id, time_sec, name, color, comment
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    str(marker.marker_id),
                    str(timeline.timeline_id),
                    float(marker.time.to_seconds()),
                    marker.name,
                    marker.color,
                    marker.comment
                ))

    def get_timeline(self, timeline_id: UUID) -> Optional[Dict[str, Any]]:
        with self.get_connection() as conn:
            tl_row = conn.execute("SELECT * FROM timelines WHERE timeline_id = ?", (str(timeline_id),)).fetchone()
            if not tl_row:
                return None

            # Tracks
            track_rows = conn.execute(
                "SELECT * FROM tracks WHERE timeline_id = ? ORDER BY order_index ASC",
                (str(timeline_id),)
            ).fetchall()

            tracks = []
            for tr in track_rows:
                t_id = tr["track_id"]
                # Clips
                clip_rows = conn.execute(
                    "SELECT * FROM clips WHERE track_id = ? ORDER BY timeline_start_sec ASC",
                    (t_id,)
                ).fetchall()
                clips = []
                for c in clip_rows:
                    c_id = c["clip_id"]
                    eff_rows = conn.execute("SELECT * FROM effects WHERE clip_id = ? ORDER BY processing_order ASC", (c_id,)).fetchall()
                    clips.append({
                        "clip_id": UUID(c["clip_id"]),
                        "asset_id": UUID(c["asset_id"]),
                        "track_id": UUID(c["track_id"]),
                        "timeline_start_sec": c["timeline_start_sec"],
                        "timeline_dur_sec": c["timeline_dur_sec"],
                        "source_in_sec": c["source_in_sec"],
                        "source_out_sec": c["source_out_sec"],
                        "speed": c["speed"],
                        "transform": json.loads(c["transform_json"]),
                        "opacity": c["opacity"],
                        "volume": c["volume"],
                        "pan": c["pan"],
                        "enabled": bool(c["enabled"]),
                        "linked_clip_id": UUID(c["linked_clip_id"]) if c["linked_clip_id"] else None,
                        "name": c["name"],
                        "effects": [{
                            "effect_id": UUID(e["effect_id"]),
                            "effect_type": e["effect_type"],
                            "parameters": json.loads(e["parameters_json"]),
                            "enabled": bool(e["enabled"]),
                            "start_sec": e["start_sec"],
                            "duration_sec": e["duration_sec"],
                            "processing_order": e["processing_order"]
                        } for e in eff_rows]
                    })

                # Transitions
                trans_rows = conn.execute("SELECT * FROM transitions WHERE track_id = ?", (t_id,)).fetchall()
                transitions = [{
                    "transition_id": UUID(t["transition_id"]),
                    "track_id": UUID(t["track_id"]),
                    "transition_type": t["transition_type"],
                    "start_time_sec": t["start_time_sec"],
                    "duration_sec": t["duration_sec"],
                    "from_clip_id": UUID(t["from_clip_id"]) if t["from_clip_id"] else None,
                    "to_clip_id": UUID(t["to_clip_id"]) if t["to_clip_id"] else None,
                    "parameters": json.loads(t["parameters_json"]),
                    "easing": t["easing"]
                } for t in trans_rows]

                tracks.append({
                    "track_id": UUID(tr["track_id"]),
                    "timeline_id": UUID(tr["timeline_id"]),
                    "track_type": tr["track_type"],
                    "name": tr["name"],
                    "order_index": tr["order_index"],
                    "is_muted": bool(tr["is_muted"]),
                    "is_visible": bool(tr["is_visible"]),
                    "is_locked": bool(tr["is_locked"]),
                    "is_solo": bool(tr["is_solo"]),
                    "gain": tr["gain"],
                    "opacity": tr["opacity"],
                    "clips": clips,
                    "transitions": transitions
                })

            marker_rows = conn.execute("SELECT * FROM timeline_markers WHERE timeline_id = ?", (str(timeline_id),)).fetchall()
            markers = [{
                "marker_id": UUID(m["marker_id"]),
                "timeline_id": UUID(m["timeline_id"]),
                "time_sec": m["time_sec"],
                "name": m["name"],
                "color": m["color"],
                "comment": m["comment"]
            } for m in marker_rows]

            return {
                "timeline_id": UUID(tl_row["timeline_id"]),
                "project_id": UUID(tl_row["project_id"]),
                "name": tl_row["name"],
                "time_base": tl_row["time_base"],
                "duration_sec": tl_row["duration_sec"],
                "resolution_width": tl_row["resolution_width"],
                "resolution_height": tl_row["resolution_height"],
                "fps": tl_row["fps"],
                "sample_rate": tl_row["sample_rate"],
                "version": tl_row["version"],
                "created_at": tl_row["created_at"],
                "updated_at": tl_row["updated_at"],
                "tracks": tracks,
                "markers": markers
            }

    def delete_timeline(self, timeline_id: UUID) -> None:
        with self.get_connection() as conn:
            conn.execute("DELETE FROM timelines WHERE timeline_id = ?", (str(timeline_id),))

    def save_render_job(self, job: Any) -> None:
        with self.get_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO render_jobs (
                    render_id, project_id, timeline_id, output_path, is_preview,
                    format_preset, status, progress, error_message, created_at, completed_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                str(job.render_id),
                str(job.project_id),
                str(job.timeline_id),
                job.output_path,
                1 if job.is_preview else 0,
                job.format_preset,
                getattr(job.status, "value", str(job.status)),
                float(job.progress),
                job.error_message,
                job.created_at,
                job.completed_at
            ))

    def update_render_job(
        self,
        render_id: UUID,
        status: str,
        progress: float = 0.0,
        error_message: Optional[str] = None,
        completed_at: Optional[str] = None
    ) -> None:
        with self.get_connection() as conn:
            conn.execute("""
                UPDATE render_jobs
                SET status = ?, progress = ?, error_message = ?, completed_at = ?
                WHERE render_id = ?
            """, (
                status,
                progress,
                error_message,
                completed_at,
                str(render_id)
            ))

    def get_render_job(self, render_id: UUID) -> Optional[Dict[str, Any]]:
        with self.get_connection() as conn:
            row = conn.execute("SELECT * FROM render_jobs WHERE render_id = ?", (str(render_id),)).fetchone()
            if not row:
                return None
            return {
                "render_id": UUID(row["render_id"]),
                "project_id": UUID(row["project_id"]),
                "timeline_id": UUID(row["timeline_id"]),
                "output_path": row["output_path"],
                "is_preview": bool(row["is_preview"]),
                "format_preset": row["format_preset"],
                "status": row["status"],
                "progress": row["progress"],
                "error_message": row["error_message"],
                "created_at": row["created_at"],
                "completed_at": row["completed_at"]
            }

    def save_motion_composition(self, composition: Any) -> None:
        """Saves or updates a MotionComposition in the database."""
        now = utc_now_iso()
        comp_dict = composition.to_dict() if hasattr(composition, "to_dict") else composition
        comp_id = comp_dict.get("composition_id")
        project_id = comp_dict.get("project_id", "default")
        name = comp_dict.get("name", "Motion Composition")
        res = comp_dict.get("resolution", [1920, 1080])
        fps = float(comp_dict.get("fps", 24.0))
        dur_raw = comp_dict.get("duration", {"value": 120, "rate": 24.0})
        frames = int(dur_raw.get("value", 120))
        rate = float(dur_raw.get("rate", 24.0))

        with self.get_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO motion_compositions (
                    composition_id, project_id, name, resolution_w, resolution_h,
                    fps, duration_frames, duration_rate, composition_json, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                str(comp_id),
                str(project_id),
                name,
                int(res[0]),
                int(res[1]),
                fps,
                frames,
                rate,
                json.dumps(comp_dict),
                now,
                now
            ))

    def get_motion_composition(self, composition_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves a MotionComposition by composition_id."""
        with self.get_connection() as conn:
            row = conn.execute("SELECT * FROM motion_compositions WHERE composition_id = ?", (str(composition_id),)).fetchone()
            if not row:
                return None
            return json.loads(row["composition_json"])

    def list_motion_compositions(self, project_id: str) -> List[Dict[str, Any]]:
        """Lists all MotionCompositions for a given project_id."""
        with self.get_connection() as conn:
            rows = conn.execute("SELECT * FROM motion_compositions WHERE project_id = ? ORDER BY created_at DESC", (str(project_id),)).fetchall()
            return [json.loads(r["composition_json"]) for r in rows]

    def delete_motion_composition(self, composition_id: str) -> bool:
        """Deletes a MotionComposition by composition_id."""
        with self.get_connection() as conn:
            cur = conn.execute("DELETE FROM motion_compositions WHERE composition_id = ?", (str(composition_id),))
            return cur.rowcount > 0
