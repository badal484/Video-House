"""
Asynchronous Job Queue and Worker Manager for Media Ingestion.
Ensures uploads are non-blocking, derivatives are generated in background, and jobs are retryable.
"""
import asyncio
from datetime import datetime, timezone
import json
import logging
from pathlib import Path
from typing import Callable, Coroutine, Dict, Optional
from uuid import UUID, uuid4

from core.assets.database import (
    AssetDatabase,
    AssetRecord,
    ProcessingStatus
)

logger = logging.getLogger("studio.job_queue")

def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

class IngestionJobQueue:
    def __init__(self, db: AssetDatabase, max_concurrent_workers: int = 4):
        self.db = db
        self.queue: asyncio.Queue = asyncio.Queue()
        self.max_workers = max_concurrent_workers
        self.workers = []
        self._is_running = False

    async def start(self):
        """Starts background worker tasks."""
        if self._is_running:
            return
        self._is_running = True
        self._recover_stale_jobs()
        for i in range(self.max_workers):
            task = asyncio.create_task(self._worker_loop(i))
            self.workers.append(task)
        logger.info(f"Started {self.max_workers} ingestion background workers.")

    async def stop(self):
        """Stops background worker tasks cleanly."""
        self._is_running = False
        for task in self.workers:
            task.cancel()
        await asyncio.gather(*self.workers, return_exceptions=True)
        self.workers.clear()

    def _recover_stale_jobs(self):
        """Finds any jobs left in PROCESSING state upon service restart and fails or requeues them."""
        with self.db.get_connection() as conn:
            conn.execute("""
                UPDATE processing_jobs
                SET status = 'FAILED', error_details = 'Interrupted by service restart'
                WHERE status = 'PROCESSING'
            """)

    async def enqueue_job(self, asset_id: UUID, job_type: str, task_coro_fn: Callable[[], Coroutine]) -> UUID:
        """
        Creates a job record in SQLite and places it onto the async queue.
        """
        job_id = uuid4()
        now = utc_now_iso()
        with self.db.get_connection() as conn:
            conn.execute("""
                INSERT INTO processing_jobs (
                    job_id, asset_id, job_type, status, progress_pct,
                    retry_count, max_retries, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (str(job_id), str(asset_id), job_type, ProcessingStatus.QUEUED.value, 0, 0, 3, now, now))

        await self.queue.put((job_id, asset_id, task_coro_fn))
        return job_id

    async def _worker_loop(self, worker_id: int):
        while self._is_running:
            try:
                job_id, asset_id, task_coro_fn = await self.queue.get()
            except asyncio.CancelledError:
                break

            now = utc_now_iso()
            with self.db.get_connection() as conn:
                conn.execute(
                    "UPDATE processing_jobs SET status = ?, updated_at = ? WHERE job_id = ?",
                    (ProcessingStatus.PROCESSING.value, now, str(job_id))
                )

            try:
                # Execute background task
                await task_coro_fn()
                
                # Mark completed
                now = utc_now_iso()
                with self.db.get_connection() as conn:
                    conn.execute(
                        "UPDATE processing_jobs SET status = ?, progress_pct = 100, updated_at = ? WHERE job_id = ?",
                        (ProcessingStatus.COMPLETED.value, now, str(job_id))
                    )
            except Exception as e:
                logger.error(f"Worker {worker_id} error on job {job_id}: {e}", exc_info=True)
                now = utc_now_iso()
                with self.db.get_connection() as conn:
                    row = conn.execute("SELECT retry_count, max_retries FROM processing_jobs WHERE job_id = ?", (str(job_id),)).fetchone()
                    retries = row["retry_count"] if row else 0
                    max_retries = row["max_retries"] if row else 3
                    
                    if retries < max_retries:
                        conn.execute("""
                            UPDATE processing_jobs
                            SET retry_count = retry_count + 1, status = ?, error_details = ?, updated_at = ?
                            WHERE job_id = ?
                        """, (ProcessingStatus.QUEUED.value, str(e), now, str(job_id)))
                        # Re-enqueue
                        await self.queue.put((job_id, asset_id, task_coro_fn))
                    else:
                        conn.execute("""
                            UPDATE processing_jobs
                            SET status = ?, error_details = ?, updated_at = ?
                            WHERE job_id = ?
                        """, (ProcessingStatus.FAILED.value, str(e), now, str(job_id)))
            finally:
                self.queue.task_done()

    def get_job(self, job_id: UUID) -> Optional[Dict]:
        with self.db.get_connection() as conn:
            row = conn.execute("SELECT * FROM processing_jobs WHERE job_id = ?", (str(job_id),)).fetchone()
            if not row:
                return None
            return dict(row)

    def list_asset_jobs(self, asset_id: UUID) -> list:
        with self.db.get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM processing_jobs WHERE asset_id = ? ORDER BY created_at DESC",
                (str(asset_id),)
            ).fetchall()
            return [dict(r) for r in rows]
