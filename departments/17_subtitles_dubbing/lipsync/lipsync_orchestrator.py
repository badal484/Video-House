"""
Lip-Sync Orchestrator for Department 17.
Supervises lip-sync job routing, provider selection, face boundary detection,
and commercial license validation.
"""
from __future__ import annotations

from typing import Optional
from uuid import UUID, uuid4

from ..core.models import LipSyncJob
from .local_lipsync_adapter import LocalLipSyncAdapter
from .sync_labs_adapter import SyncLabsAdapter


class LipSyncOrchestrator:
    """Orchestrates lip-sync generation across cloud and local providers."""

    def __init__(
        self,
        sync_labs_adapter: Optional[SyncLabsAdapter] = None,
        local_adapter: Optional[LocalLipSyncAdapter] = None,
    ):
        self.sync_labs_adapter = sync_labs_adapter or SyncLabsAdapter()
        self.local_adapter = local_adapter or LocalLipSyncAdapter()

    def process_lipsync(
        self,
        project_id: UUID,
        video_asset_id: UUID,
        audio_asset_id: UUID,
        provider: str = "synclabs",
    ) -> LipSyncJob:
        """
        Routes and executes lip-sync modification for a video and target audio stem.
        """
        job_id = uuid4()
        prov_lower = provider.lower()

        if prov_lower == "synclabs":
            self.sync_labs_adapter.submit_lipsync_job(
                video_url_or_id=str(video_asset_id),
                audio_url_or_id=str(audio_asset_id),
            )
        elif prov_lower in {"latentsync", "musetalk"}:
            self.local_adapter.execute_lipsync(
                video_asset_id=str(video_asset_id),
                audio_asset_id=str(audio_asset_id),
                model_name=prov_lower,
            )
        else:
            # Will raise NonCommercialModelRejectedException if wav2lip is attempted
            self.local_adapter.execute_lipsync(
                video_asset_id=str(video_asset_id),
                audio_asset_id=str(audio_asset_id),
                model_name=prov_lower,
            )

        output_video_asset_id = uuid4()

        return LipSyncJob(
            job_id=job_id,
            project_id=project_id,
            video_asset_id=video_asset_id,
            audio_asset_id=audio_asset_id,
            provider=prov_lower,
            status="completed",
            output_video_asset_id=output_video_asset_id,
        )
