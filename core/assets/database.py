"""
Database models and schema for Central Asset Registry.
Uses SQLite for zero-dependency, local-first transactional storage.
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
    SQLite Database Manager for Asset Registry.
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
            
            CREATE INDEX IF NOT EXISTS idx_assets_project ON assets(project_id);
            CREATE INDEX IF NOT EXISTS idx_assets_checksum ON assets(checksum_sha256);
            CREATE INDEX IF NOT EXISTS idx_assets_media_type ON assets(media_type);
            CREATE INDEX IF NOT EXISTS idx_derivatives_asset ON derivatives(asset_id);
            CREATE INDEX IF NOT EXISTS idx_jobs_status ON processing_jobs(status);
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
