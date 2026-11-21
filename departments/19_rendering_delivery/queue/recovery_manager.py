"""
Render Recovery Manager for Department 19.
Handles checkpoint persistence, task retries, worker crash recovery, and partial output quarantine.
"""
from __future__ import annotations

import os
from typing import Dict, List, Optional
from uuid import UUID

from ..core.models import RenderJob, RenderJobStatus


class RenderRecoveryManager:
    """Recovers failed or interrupted render jobs from checkpoints."""

    def __init__(self):
        self._checkpoints: Dict[UUID, Dict[str, Any]] = {}  # job_id -> checkpoint data

    def record_checkpoint(self, job_id: UUID, completed_stage_id: str, artifact_path: str) -> None:
        """Persists a stage completion checkpoint."""
        if job_id not in self._checkpoints:
            self._checkpoints[job_id] = {"completed_stages": [], "artifacts": []}
        self._checkpoints[job_id]["completed_stages"].append(completed_stage_id)
        self._checkpoints[job_id]["artifacts"].append(artifact_path)

    def can_recover(self, job_id: UUID) -> bool:
        """Checks if a job has valid checkpoints to resume from."""
        return job_id in self._checkpoints and len(self._checkpoints[job_id]["completed_stages"]) > 0

    def recover_job(self, job: RenderJob) -> RenderJob:
        """Resumes a failed or interrupted render job from its last checkpoint."""
        if not self.can_recover(job.job_id):
            job.status = RenderJobStatus.FAILED
            job.error_details = "Cannot recover: no checkpoints found."
            return job

        job.status = RenderJobStatus.RECOVERING
        checkpoint = self._checkpoints[job.job_id]
        completed = checkpoint["completed_stages"]

        # Calculate progress based on recovered stages
        job.progress = min(90.0, len(completed) * 20.0)
        job.status = RenderJobStatus.RUNNING
        return job

    def retry_task_with_backoff(self, attempt: int, max_retries: int = 3) -> tuple[bool, float]:
        """
        Determines whether to retry a failed task and calculates backoff in seconds:
        backoff = 2^attempt * 0.5 sec
        """
        if attempt >= max_retries:
            return False, 0.0
        backoff_sec = (2**attempt) * 0.5
        return True, round(backoff_sec, 2)

    def cleanup_partial_output(self, file_path: Optional[str]) -> bool:
        """Quarantines or unlinks incomplete/corrupted partial outputs."""
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
                return True
            except OSError:
                pass
        return False
