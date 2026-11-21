"""
Department 19: Rendering & Delivery Service Implementation
Unified facade orchestrating render plan compilation, distributed queue management,
encoding profiles, quality control coordination, and delivery packaging.
"""
from __future__ import annotations

import os
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from .compiler.preflight import PreflightValidator
from .compiler.render_plan_compiler import RenderPlanCompiler
from .core.models import (
    ProfileCategory,
    RenderJob,
    RenderJobStatus,
    RenderPlan,
    RenderProfile,
)
from .delivery.cost_manager import RenderCostManager
from .delivery.manifest_generator import DeliveryManifestGenerator
from .delivery.package_manager import DeliveryPackageManager
from .encoding.encoding_engine import EncodingEngine
from .encoding.timeline_adapter import TimelineAdapter
from .interface import (
    IRenderingDelivery,
    RenderingDeliveryRequest,
    RenderingDeliveryResponse,
)
from .profiles.profile_registry import RenderProfileRegistry
from .queue.recovery_manager import RenderRecoveryManager
from .queue.render_queue_manager import RenderQueueManager
from .workers.local_worker import LocalRenderWorker
from .workers.remote_worker import RemoteRenderWorker
from .workers.worker_manager import WorkerManager


class RenderingDeliveryService(IRenderingDelivery):
    """Production service implementing IRenderingDelivery."""

    def __init__(self):
        self.profile_registry = RenderProfileRegistry()
        self.queue_manager = RenderQueueManager()
        self.recovery_manager = RenderRecoveryManager()
        self.worker_manager = WorkerManager()
        self.local_worker = LocalRenderWorker()
        self.cost_manager = RenderCostManager()

    async def execute(self, request: RenderingDeliveryRequest) -> RenderingDeliveryResponse:
        params = request.parameters
        action = params.get("action", "compile_render_plan")
        project_id = request.project_id

        try:
            if action == "compile_render_plan":
                meta = params.get("project_metadata", {})
                profile_id = params.get("render_profile_id", "youtube_1080p")
                timeline_id = UUID(str(params["timeline_id"])) if params.get("timeline_id") else None

                plan = RenderPlanCompiler.compile_plan(
                    project_id=project_id,
                    project_metadata=meta,
                    render_profile_id=profile_id,
                    timeline_id=timeline_id,
                )
                return RenderingDeliveryResponse(
                    success=True,
                    message="Render plan compiled successfully.",
                    data={"render_plan": plan.model_dump(mode="json")},
                )

            elif action == "submit_render_job":
                profile_id = params.get("render_profile_id", "youtube_1080p")
                profile = self.profile_registry.get_profile(profile_id)
                if not profile:
                    return RenderingDeliveryResponse(
                        success=False,
                        message=f"Unsupported render profile: '{profile_id}'.",
                    )

                job = RenderJob(
                    project_id=project_id,
                    sequence_id=UUID(str(params["sequence_id"])) if "sequence_id" in params else None,
                    render_profile_id=profile_id,
                    priority=int(params.get("priority", 5)),
                    idempotency_key=params.get("idempotency_key"),
                )
                submitted_job = self.queue_manager.submit_job(job)

                return RenderingDeliveryResponse(
                    success=True,
                    message="Render job submitted to queue.",
                    data={"render_job": submitted_job.model_dump(mode="json")},
                )

            elif action == "execute_render":
                job_id = UUID(str(params["job_id"]))
                job = self.queue_manager.get_job(job_id)
                if not job:
                    return RenderingDeliveryResponse(
                        success=False,
                        message=f"Render job '{job_id}' not found.",
                    )

                profile = self.profile_registry.get_profile(job.render_profile_id)
                if not profile:
                    return RenderingDeliveryResponse(
                        success=False,
                        message=f"Profile '{job.render_profile_id}' not found.",
                    )

                # Execute rasterization & encoding
                job.status = RenderJobStatus.RUNNING
                self.queue_manager.update_progress(job_id, 25.0)

                output_path = params.get(
                    "output_path",
                    f"storage/deliveries/{project_id}/master_{job_id.hex[:8]}.{profile.container}",
                )

                # Simulated timeline rasterization & transcode
                intermediate_path = f"temp/scratch/intermediate_{job_id.hex[:8]}.mov"
                TimelineAdapter.rasterize_timeline(project_id, {}, intermediate_path)
                self.recovery_manager.record_checkpoint(job_id, "timeline_intermediate", intermediate_path)
                self.queue_manager.update_progress(job_id, 70.0)

                EncodingEngine.execute_transcode(intermediate_path, output_path, profile)
                self.recovery_manager.record_checkpoint(job_id, "distribution_encode", output_path)

                job.output_path = output_path
                job.status = RenderJobStatus.RENDERED
                self.queue_manager.update_progress(job_id, 100.0)

                return RenderingDeliveryResponse(
                    success=True,
                    message="Render execution completed successfully.",
                    data={"render_job": job.model_dump(mode="json")},
                )

            elif action == "package_delivery":
                job_id = UUID(str(params["job_id"]))
                master_file = params["master_file_path"]
                sidecars = params.get("sidecars", [])

                pkg = DeliveryPackageManager.assemble_package(
                    project_id=project_id,
                    render_job_id=job_id,
                    master_file_path=master_file,
                    sidecar_file_paths=sidecars,
                    output_directory=params.get("output_directory"),
                    technical_specs=params.get("technical_specs"),
                    qc_summary=params.get("qc_summary"),
                )

                return RenderingDeliveryResponse(
                    success=True,
                    message="Delivery package assembled successfully.",
                    data={"delivery_package": pkg.model_dump(mode="json")},
                )

            return RenderingDeliveryResponse(
                success=False,
                message=f"Unknown rendering & delivery action: '{action}'.",
            )
        except Exception as e:
            return RenderingDeliveryResponse(
                success=False,
                message=f"Rendering & Delivery error: {str(e)}",
            )

    def health_check(self) -> bool:
        return True
