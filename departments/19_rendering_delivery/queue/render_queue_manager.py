"""
Render Queue Manager for Department 19.
Manages asynchronous job queues, priority scheduling, progress updates, and idempotency caching.
"""
from __future__ import annotations

import asyncio
from typing import Dict, List, Optional
from uuid import UUID

from ..core.models import RenderJob, RenderJobStatus


class RenderQueueManager:
    """Asynchronous priority queue for render jobs."""

    def __init__(self):
        self._jobs: Dict[UUID, RenderJob] = {}
        self._idempotency_index: Dict[str, UUID] = {}

    def submit_job(self, job: RenderJob) -> RenderJob:
        """Submits a job to the queue, checking for idempotency duplicates."""
        if job.idempotency_key and job.idempotency_key in self._idempotency_index:
            existing_id = self._idempotency_index[job.idempotency_key]
            existing_job = self._jobs.get(existing_id)
            if existing_job and existing_job.status not in {RenderJobStatus.FAILED, RenderJobStatus.CANCELLED}:
                return existing_job

        job.status = RenderJobStatus.QUEUED
        self._jobs[job.job_id] = job
        if job.idempotency_key:
            self._idempotency_index[job.idempotency_key] = job.job_id
        return job

    def get_job(self, job_id: UUID) -> Optional[RenderJob]:
        """Retrieves a render job by UUID."""
        return self._jobs.get(job_id)

    def list_jobs(self, project_id: Optional[UUID] = None) -> List[RenderJob]:
        """Lists jobs, optionally filtered by project_id, sorted by priority and creation time."""
        jobs = list(self._jobs.values())
        if project_id:
            jobs = [j for j in jobs if j.project_id == project_id]
        return sorted(jobs, key=lambda j: (j.priority, j.created_at), reverse=True)

    def update_progress(self, job_id: UUID, progress: float, status: Optional[RenderJobStatus] = None) -> bool:
        """Updates job progress and status."""
        job = self.get_job(job_id)
        if not job:
            return False
        job.progress = round(progress, 1)
        if status:
            job.status = status
        return True

    def cancel_job(self, job_id: UUID) -> bool:
        """Cancels a pending or running render job."""
        job = self.get_job(job_id)
        if not job or job.status in {RenderJobStatus.DELIVERED, RenderJobStatus.RENDERED}:
            return False
        job.status = RenderJobStatus.CANCELLED
        return True

