"""
Timeline Motion Graphics Adapter.
Renders motion graphics compositions and inserts them directly as alpha clips onto Part 05 NLE timelines.
"""
import os
import uuid
import hashlib
from typing import Optional, Tuple

from ..core.composition_models import MotionComposition, RenderConfig
from ..renderers.router import MotionRendererRouter
from core.timeline.timeline_models import Clip, TrackType
from core.timeline.time_model import RationalTime
from core.assets.database import AssetDatabase
from core.storage.storage_service import StorageService
from departments.video_editing.timeline_manager import TimelineManager


class TimelineMotionAdapter:
    """
    Bridges Department 09 Motion Graphics into Department 08 NLE Timelines.
    """

    def __init__(
        self,
        db: Optional[AssetDatabase] = None,
        storage: Optional[StorageService] = None,
        timeline_manager: Optional[TimelineManager] = None
    ):
        self.db = db or AssetDatabase()
        self.storage = storage or StorageService(self.db)
        self.timeline_manager = timeline_manager or TimelineManager(self.db)
        self.router = MotionRendererRouter()

    def render_and_insert_to_timeline(
        self,
        composition: MotionComposition,
        timeline_id: str,
        target_track_name: str = "V3 - Graphics",
        timeline_in: Optional[RationalTime] = None,
        codec: str = "prores_ks"
    ) -> Clip:
        """
        Renders the motion composition to a transparent video file, registers it
        in the Central Asset Registry, and inserts it as a Clip on the target timeline track.
        """
        tl_uuid = uuid.UUID(timeline_id) if isinstance(timeline_id, str) else timeline_id
        tl = self.timeline_manager.get_timeline(tl_uuid)
        if not tl:
            raise KeyError(f"Timeline '{timeline_id}' not found.")

        # Find or create target video track (e.g. V3)
        target_track = None
        for trk in tl.tracks:
            t_type = getattr(trk, "track_type", getattr(trk, "kind", None))
            if t_type == TrackType.VIDEO and (trk.name == target_track_name or getattr(trk, "order_index", 0) == 3 or getattr(trk, "index", 0) == 3):
                target_track = trk
                break

        if not target_track:
            target_track = self.timeline_manager.add_track(
                timeline_id=tl_uuid,
                track_type=TrackType.VIDEO,
                name=target_track_name
            )

        # Determine output file path
        proj_uuid = tl.project_id if isinstance(tl.project_id, uuid.UUID) else uuid.UUID(tl.project_id)
        project_id_str = str(proj_uuid)
        ext = "mov" if codec == "prores_ks" else "webm"
        file_name = f"mograph_{composition.composition_id}.{ext}"
        storage_root = str(getattr(self.storage, "root_storage", getattr(self.storage, "base_dir", "assets")))
        output_dir = os.path.join(storage_root, project_id_str, "derivatives", "motion_graphics")
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, file_name)

        # Configure renderer
        config = RenderConfig(
            resolution=composition.resolution,
            fps=composition.fps,
            pixel_format="yuva444p10le" if codec == "prores_ks" else "yuva420p",
            output_format=ext,
            codec=codec
        )

        # Render composition
        self.router.render(composition, output_path, config)

        # Register asset in AssetDatabase
        asset_id = uuid.uuid4()
        file_size = os.path.getsize(output_path)
        sha256 = self._calculate_file_hash(output_path)

        from core.assets.database import AssetRecord, MediaType, ProcessingStatus
        now = "2026-11-21T18:00:00Z"
        record = AssetRecord(
            asset_id=asset_id,
            project_id=proj_uuid,
            original_filename=file_name,
            display_name=f"Overlay: {composition.name}",
            media_type=MediaType.VIDEO,
            detected_format=ext,
            mime_type=f"video/{ext}",
            byte_size=file_size,
            checksum_sha256=sha256,
            storage_path=output_path,
            import_timestamp=now,
            processing_status=ProcessingStatus.COMPLETED,
            metadata_status=ProcessingStatus.COMPLETED,
            derivative_status=ProcessingStatus.COMPLETED
        )
        self.db.register_asset(record)

        # Compute clip timeline placement
        ins_in = timeline_in or RationalTime(0, composition.fps)
        clip_uuid = uuid.uuid4()
        track_uuid = target_track.track_id if isinstance(target_track.track_id, uuid.UUID) else uuid.UUID(target_track.track_id)

        # Add clip to track in NLE
        created_clip = self.timeline_manager.add_clip_to_track(
            timeline_id=tl_uuid,
            track_id=track_uuid,
            asset_id=asset_id,
            timeline_start_sec=ins_in.to_seconds(),
            duration_sec=composition.duration.to_seconds(),
            source_in_sec=0.0,
            name=f"Overlay: {composition.name}"
        )
        return created_clip

    @staticmethod
    def _calculate_file_hash(path: str) -> str:
        hasher = hashlib.sha256()
        with open(path, "rb") as f:
            while chunk := f.read(65536):
                hasher.update(chunk)
        return hasher.hexdigest()
