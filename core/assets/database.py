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
