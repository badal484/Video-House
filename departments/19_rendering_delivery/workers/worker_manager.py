"""
Worker Manager for Department 19.
Maintains available worker inventory, matches tasks based on GPU/CPU capabilities,
and monitors worker heartbeats.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, List, Optional
from uuid import UUID, uuid4


class WorkerNode:
    def __init__(
        self,
        worker_id: str,
        name: str,
        is_local: bool = True,
        capabilities: Optional[List[str]] = None,
        max_concurrent_jobs: int = 2,
    ):
        self.worker_id = worker_id
        self.name = name
        self.is_local = is_local
        self.capabilities = capabilities or ["CPU", "H264", "PRORES"]
        self.max_concurrent_jobs = max_concurrent_jobs
        self.active_jobs: List[UUID] = []
        self.last_heartbeat = datetime.now(timezone.utc)
        self.is_healthy = True


class WorkerManager:
    """Manages worker scheduling and capacity allocation."""

    def __init__(self):
        self._workers: Dict[str, WorkerNode] = {}
        self._register_default_workers()

    def _register_default_workers(self):
        # Local Apple Silicon Worker
        local_m4 = WorkerNode(
            worker_id="worker_local_m4",
            name="Apple Silicon M4 Local Worker (VideoToolbox + CPU)",
            is_local=True,
            capabilities=["CPU", "VIDEOTOOLBOX", "PRORES", "H264", "HEVC", "AV1_DECODE"],
            max_concurrent_jobs=2,
        )
        self._workers[local_m4.worker_id] = local_m4

    def register_worker(self, worker: WorkerNode) -> None:
        """Registers a worker node."""
        self._workers[worker.worker_id] = worker

    def get_worker(self, worker_id: str) -> Optional[WorkerNode]:
        """Retrieves worker by ID."""
        return self._workers.get(worker_id)

    def select_worker_for_task(self, required_capabilities: List[str]) -> Optional[WorkerNode]:
        """Finds the best matching idle worker with required capabilities."""
        for worker in self._workers.values():
            if not worker.is_healthy:
                continue
            if len(worker.active_jobs) >= worker.max_concurrent_jobs:
                continue
            # Check capability subset
            if all(cap in worker.capabilities for cap in required_capabilities):
                return worker
        # Fallback to local default if healthy
        local = self._workers.get("worker_local_m4")
        if local and local.is_healthy:
            return local
        return None
