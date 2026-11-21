"""
REST API and Web Services for the Universal AI Video Production Studio.
Exposes project management, media upload, local import, metadata retrieval,
derivative access, asset role management, and asynchronous job monitoring.
"""
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID, uuid4

from fastapi import (
    FastAPI,
    File,
    Form,
    HTTPException,
    Query,
    UploadFile,
    status
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, Response
import mimetypes
from pydantic import BaseModel, Field

import departments
from departments.project_management.service import ProjectManagementService, STANDARD_TEMPLATES
from departments.project_management.models import ProjectTemplateType
from departments.studio_application.service import StudioApplicationService

from core.assets.database import (
    AssetDatabase,
    AssetRecord,
    AssetRole,
    DerivativeRecord,
    DerivativeType,
    MediaType,
    ProcessingStatus,
    TechnicalMetadata
)
from core.orchestration.job_queue import IngestionJobQueue
from core.storage.storage_service import StorageService
from departments.media_ingestion.service import MediaIngestionService
from core.assets.intelligence_models import (
    AnalysisProfile,
    ReferenceProfile
)
from departments.media_intelligence.service import MediaIntelligenceService
from departments.multimodal_providers.router import MultimodalProviderRouter
from departments.creative_direction.director_service import CreativeDirectorService
from departments.production_planning.planning_service import ProductionPlanningService
from departments.character_production.continuity_service import WorldContinuityService
from departments.video_editing.service import VideoEditingService
from core.planning.planning_models import (
    ApprovalStatus,
    PlanningEntityType,
    ProductionType,
    PacingStyle
)
from core.timeline import (
    Clip,
    EditMode,
    EffectType,
    OTIOAdapter,
    RationalTime,
    Timeline,
    TrackType,
    TransitionType
)

# ---------------------------------------------------------
# Lifecycle & Dependency Wiring
# ---------------------------------------------------------
db = AssetDatabase("projects/studio_asset_registry.db")
storage = StorageService("assets", "temp")
job_queue = IngestionJobQueue(db, max_concurrent_workers=4)
ingestion_service = MediaIngestionService(db, storage, job_queue)
intelligence_service = MediaIntelligenceService(db)
provider_router = MultimodalProviderRouter()
creative_director = CreativeDirectorService(db)
production_planner = ProductionPlanningService(db)
continuity_service = WorldContinuityService(db)
video_editor = VideoEditingService(db)
project_manager = ProjectManagementService(db)
studio_app = StudioApplicationService(db)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Start background workers
    await job_queue.start()
    yield
    # Shutdown: Stop workers cleanly
    await job_queue.stop()

app = FastAPI(
    title="Universal AI Video Production Studio - Media Engine",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------
# Pydantic Schemas for Requests & Responses
# ---------------------------------------------------------

class CreateProjectRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    settings: Dict[str, Any] = Field(default_factory=dict)

class UpdateProjectRequest(BaseModel):
    name: Optional[str] = None
    settings: Optional[Dict[str, Any]] = None

class SaveVersionRequest(BaseModel):
    version_name: str
    notes: Optional[str] = None

class SaveLayoutRequest(BaseModel):
    layout: Dict[str, Any]

class ProjectResponse(BaseModel):
    project_id: UUID
    name: str
    created_at: str
    updated_at: str
    settings: Dict[str, Any]

class ImportLocalFileRequest(BaseModel):
    file_path: str = Field(..., description="Absolute or relative path to local media file")
    display_name: Optional[str] = None
    roles: List[AssetRole] = Field(default_factory=lambda: [AssetRole.SOURCE_FOOTAGE])

class AnalyzeAssetRequest(BaseModel):
    profile: AnalysisProfile = Field(default=AnalysisProfile.STANDARD)

class CompareAssetsRequest(BaseModel):
    source_asset_id: UUID
    reference_asset_id: UUID

class SearchMediaRequest(BaseModel):
    query: str = Field(..., min_length=1)
    limit: int = Field(default=20, ge=1, le=100)

class CreateBriefRequest(BaseModel):
    prompt: str = Field(..., min_length=1)
    project_name: Optional[str] = None
    production_type: Optional[str] = None
    target_duration_sec: Optional[float] = None
    intended_platform: Optional[str] = None
    genre: Optional[str] = None
    visual_style: Optional[str] = None
    aspect_ratio: Optional[str] = None

class CreateScriptRequest(BaseModel):
    selected_concept_id: Optional[UUID] = None
    notes: Optional[str] = None

class PlanShotsRequest(BaseModel):
    visual_style: Optional[str] = "Cinematic Realism"

class CreateEditPlanRequest(BaseModel):
    target_duration_sec: float = Field(..., gt=0.0)
    source_asset_ids: List[UUID] = Field(default_factory=list)
    reference_asset_id: Optional[UUID] = None
    instructions: Optional[str] = ""

class SubmitApprovalRequest(BaseModel):
    entity_type: PlanningEntityType
    entity_id: UUID
    version: int = 1
    status: ApprovalStatus
    reviewer_notes: Optional[str] = ""
    approved_by: Optional[str] = "human_director"

class AnalyzeAssetRequest(BaseModel):
    profile: AnalysisProfile = Field(default=AnalysisProfile.STANDARD)

class CompareAssetsRequest(BaseModel):
    source_asset_id: UUID
    reference_asset_id: UUID

class SearchMediaRequest(BaseModel):
    query: str = Field(..., min_length=1)
    limit: int = Field(default=20, ge=1, le=100)

class CreateBriefRequest(BaseModel):
    prompt: str = Field(..., min_length=1)
    project_name: Optional[str] = None
    production_type: Optional[str] = None
    target_duration_sec: Optional[float] = None
    intended_platform: Optional[str] = None
    genre: Optional[str] = None
    visual_style: Optional[str] = None
    aspect_ratio: Optional[str] = None

class CreateScriptRequest(BaseModel):
    selected_concept_id: Optional[UUID] = None
    notes: Optional[str] = None

class PlanShotsRequest(BaseModel):
    visual_style: Optional[str] = "Cinematic Realism"

class CreateEditPlanRequest(BaseModel):
    target_duration_sec: float = Field(..., gt=0.0)
    source_asset_ids: List[UUID] = Field(default_factory=list)
    reference_asset_id: Optional[UUID] = None
    instructions: Optional[str] = ""

class SubmitApprovalRequest(BaseModel):
    entity_type: PlanningEntityType
    entity_id: UUID
    version: int = 1
    status: ApprovalStatus
    reviewer_notes: Optional[str] = ""
    approved_by: Optional[str] = "human_director"

class UpdateAssetRequest(BaseModel):
    display_name: Optional[str] = None
    add_roles: Optional[List[AssetRole]] = None
    remove_roles: Optional[List[AssetRole]] = None

class AssetDetailResponse(BaseModel):
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
    error_message: Optional[str]
    version: int
    source_type: str
    license_info: Optional[str]
    roles: List[AssetRole]
    technical_metadata: Optional[Dict[str, Any]] = None
    derivatives: List[Dict[str, Any]] = Field(default_factory=list)

# ---------------------------------------------------------
# Project Management Endpoints
# ---------------------------------------------------------

@app.post("/api/v1/projects", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(req: CreateProjectRequest):
    project_id = uuid4()
    db.create_project(project_id, req.name, req.settings)
    proj = db.get_project(project_id)
    if not proj:
        raise HTTPException(status_code=500, detail="Failed to create project.")
    return proj

@app.get("/api/v1/projects")
async def list_projects_endpoint(limit: int = 100, offset: int = 0):
    return {"projects": project_manager.list_projects(limit=limit, offset=offset)}

@app.get("/api/v1/projects/templates")
async def list_project_templates():
    return {"templates": [t.model_dump(mode="json") for t in project_manager.get_templates()]}

@app.get("/api/v1/projects/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: UUID):
    proj = db.get_project(project_id)
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found.")
    return proj

@app.patch("/api/v1/projects/{project_id}")
async def update_project_endpoint(project_id: UUID, req: UpdateProjectRequest):
    updated = project_manager.update_project(project_id, name=req.name, settings=req.settings)
    if not updated:
        raise HTTPException(status_code=404, detail="Project not found.")
    return updated

@app.delete("/api/v1/projects/{project_id}")
async def delete_project_endpoint(project_id: UUID):
    success = project_manager.delete_project(project_id)
    if not success:
        raise HTTPException(status_code=404, detail="Project not found.")
    return {"success": True, "message": f"Project {project_id} deleted."}

@app.post("/api/v1/projects/{project_id}/versions")
async def save_project_version_endpoint(project_id: UUID, req: SaveVersionRequest):
    try:
        ver = project_manager.save_version(project_id, req.version_name, req.notes)
        return ver
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.get("/api/v1/projects/{project_id}/versions")
async def list_project_versions_endpoint(project_id: UUID):
    return {"versions": project_manager.list_versions(project_id)}

@app.post("/api/v1/projects/{project_id}/versions/{version_id}/restore")
async def restore_project_version_endpoint(project_id: UUID, version_id: str):
    try:
        return project_manager.restore_version(project_id, version_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

# ---------------------------------------------------------
# Media Ingestion & Upload Endpoints
# ---------------------------------------------------------

@app.post("/api/v1/projects/{project_id}/assets/upload", status_code=status.HTTP_202_ACCEPTED)
async def upload_asset(
    project_id: UUID,
    file: UploadFile = File(...),
    display_name: Optional[str] = Form(None),
    role: Optional[AssetRole] = Form(AssetRole.SOURCE_FOOTAGE)
):
    """
    Streams multipart file upload directly to project storage, validates contents,
    registers the asset, and triggers non-blocking background derivative generation.
    """
    proj = db.get_project(project_id)
    if not proj:
        raise HTTPException(status_code=404, detail=f"Project {project_id} does not exist.")

    try:
        asset_record = await ingestion_service.import_stream(
            project_id=project_id,
            stream=file.file,
            filename=file.filename or "uploaded_media.bin",
            display_name=display_name,
            roles=[role] if role else [AssetRole.SOURCE_FOOTAGE]
        )
        return {
            "success": True,
            "message": "Asset uploaded and queued for processing.",
            "asset_id": asset_record.asset_id,
            "status": asset_record.processing_status
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/v1/projects/{project_id}/assets/import-local", status_code=status.HTTP_202_ACCEPTED)
async def import_local_file(project_id: UUID, req: ImportLocalFileRequest):
    """
    Imports a local file by path, preserves original, validates content,
    and enqueues background processing.
    """
    proj = db.get_project(project_id)
    if not proj:
        raise HTTPException(status_code=404, detail=f"Project {project_id} does not exist.")

    source_path = Path(req.file_path)
    try:
        asset_record = await ingestion_service.import_local_file(
            project_id=project_id,
            source_path=source_path,
            display_name=req.display_name,
            roles=req.roles
        )
        return {
            "success": True,
            "message": "Local file imported and queued for processing.",
            "asset_id": asset_record.asset_id,
            "status": asset_record.processing_status
        }
    except FileNotFoundError as fnf:
        raise HTTPException(status_code=404, detail=str(fnf))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ---------------------------------------------------------
# Asset Query & Metadata Endpoints
# ---------------------------------------------------------

@app.get("/api/v1/projects/{project_id}/assets")
async def list_assets(
    project_id: UUID,
    media_type: Optional[MediaType] = Query(None),
    role: Optional[AssetRole] = Query(None),
    status_filter: Optional[ProcessingStatus] = Query(None, alias="status"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0)
):
    assets = db.list_project_assets(
        project_id=project_id,
        media_type=media_type,
        role=role,
        status=status_filter,
        limit=limit,
        offset=offset
    )
    return {
        "project_id": project_id,
        "count": len(assets),
        "limit": limit,
        "offset": offset,
        "assets": assets
    }

@app.get("/api/v1/projects/{project_id}/assets/{asset_id}", response_model=AssetDetailResponse)
async def get_asset_details(project_id: UUID, asset_id: UUID):
    asset = db.get_asset(asset_id)
    if not asset or asset.project_id != project_id:
        raise HTTPException(status_code=404, detail="Asset not found in project.")

    meta = db.get_technical_metadata(asset_id)
    derivatives = db.get_derivatives(asset_id)

    meta_dict = None
    if meta:
        meta_dict = {
            "width": meta.width,
            "height": meta.height,
            "duration_seconds": meta.duration_seconds,
            "frame_rate": meta.frame_rate,
            "avg_frame_rate": meta.avg_frame_rate,
            "is_vfr": meta.is_vfr,
            "video_codec": meta.video_codec,
            "audio_codec": meta.audio_codec,
            "pixel_format": meta.pixel_format,
            "bit_depth": meta.bit_depth,
            "aspect_ratio": meta.aspect_ratio,
            "color_primaries": meta.color_primaries,
            "color_transfer": meta.color_transfer,
            "color_space": meta.color_space,
            "is_hdr": meta.is_hdr,
            "rotation": meta.rotation,
            "timecode": meta.timecode,
            "audio_sample_rate": meta.audio_sample_rate,
            "audio_channels": meta.audio_channels,
            "audio_channel_layout": meta.audio_channel_layout,
            "stream_count": meta.stream_count,
            "bitrate_bps": meta.bitrate_bps,
            "raw_probe": meta.raw_probe
        }

    deriv_list = [
        {
            "derivative_id": d.derivative_id,
            "derivative_type": d.derivative_type.value,
            "storage_path": d.storage_path,
            "byte_size": d.byte_size,
            "mime_type": d.mime_type,
            "generation_params": d.generation_params,
            "created_at": d.created_at,
            "status": d.status.value
        }
        for d in derivatives
    ]

    return AssetDetailResponse(
        asset_id=asset.asset_id,
        project_id=asset.project_id,
        original_filename=asset.original_filename,
        display_name=asset.display_name,
        media_type=asset.media_type,
        detected_format=asset.detected_format,
        mime_type=asset.mime_type,
        byte_size=asset.byte_size,
        checksum_sha256=asset.checksum_sha256,
        storage_path=asset.storage_path,
        import_timestamp=asset.import_timestamp,
        processing_status=asset.processing_status,
        metadata_status=asset.metadata_status,
        derivative_status=asset.derivative_status,
        error_message=asset.error_message,
        version=asset.version,
        source_type=asset.source_type,
        license_info=asset.license_info,
        roles=asset.roles,
        technical_metadata=meta_dict,
        derivatives=deriv_list
    )

@app.patch("/api/v1/projects/{project_id}/assets/{asset_id}")
async def update_asset(project_id: UUID, asset_id: UUID, req: UpdateAssetRequest):
    asset = db.get_asset(asset_id)
    if not asset or asset.project_id != project_id:
        raise HTTPException(status_code=404, detail="Asset not found.")

    if req.display_name is not None:
        db.update_display_name(asset_id, req.display_name)
    if req.add_roles:
        for r in req.add_roles:
            db.add_asset_role(asset_id, r)
    if req.remove_roles:
        for r in req.remove_roles:
            db.remove_asset_role(asset_id, r)

    return {"success": True, "asset": db.get_asset(asset_id)}

@app.delete("/api/v1/projects/{project_id}/assets/{asset_id}")
async def delete_asset(project_id: UUID, asset_id: UUID):
    asset = db.get_asset(asset_id)
    if not asset or asset.project_id != project_id:
        raise HTTPException(status_code=404, detail="Asset not found.")

    deleted = ingestion_service.delete_asset(asset_id)
    if not deleted:
        raise HTTPException(
            status_code=409,
            detail="Asset cannot be deleted because other assets or timelines depend on it."
        )

    return {"success": True, "message": f"Asset {asset_id} deleted successfully."}

@app.post("/api/v1/projects/{project_id}/assets/{asset_id}/retry")
async def retry_asset_processing(project_id: UUID, asset_id: UUID):
    asset = db.get_asset(asset_id)
    if not asset or asset.project_id != project_id:
        raise HTTPException(status_code=404, detail="Asset not found.")

    job_id = await ingestion_service.retry_processing(asset_id)
    return {"success": True, "job_id": job_id, "message": "Reprocessing enqueued."}

# ---------------------------------------------------------
# Job Monitoring & Media Delivery
# ---------------------------------------------------------

@app.get("/api/v1/projects/{project_id}/jobs/{job_id}")
async def get_job_status(project_id: UUID, job_id: UUID):
    job = job_queue.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")
    return job

@app.get("/api/v1/media/stream/{asset_id}")
async def stream_media_file(asset_id: UUID):
    asset = db.get_asset(asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found.")
    path = Path(asset.storage_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Physical media file missing on disk.")
    return FileResponse(path, media_type=asset.mime_type, filename=asset.original_filename)

@app.get("/api/v1/media/derivative/{derivative_id}")
async def get_derivative_file(derivative_id: UUID):
    with db.get_connection() as conn:
        row = conn.execute("SELECT * FROM derivatives WHERE derivative_id = ?", (str(derivative_id),)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Derivative not found.")
        path = Path(row["storage_path"])
        if not path.exists():
            raise HTTPException(status_code=404, detail="Derivative file missing on disk.")
        return FileResponse(path, media_type=row["mime_type"])

# ---------------------------------------------------------
# Department 04 & 05: Multimodal Intelligence Endpoints
# ---------------------------------------------------------

@app.post("/api/v1/projects/{project_id}/assets/{asset_id}/analyze")
async def analyze_asset(project_id: UUID, asset_id: UUID, req: AnalyzeAssetRequest):
    asset = db.get_asset(asset_id)
    if not asset or asset.project_id != project_id:
        raise HTTPException(status_code=404, detail="Asset not found.")
    
    result = await intelligence_service.analyze_asset(asset_id, profile=req.profile)
    return {"success": True, "asset_id": str(asset_id), "manifest": result}

@app.get("/api/v1/projects/{project_id}/assets/{asset_id}/analysis")
async def get_asset_analysis(project_id: UUID, asset_id: UUID):
    asset = db.get_asset(asset_id)
    if not asset or asset.project_id != project_id:
        raise HTTPException(status_code=404, detail="Asset not found.")
    
    shots = db.get_shots(asset_id)
    transcripts = db.get_transcripts(asset_id)
    audio_events = db.get_audio_events(asset_id)
    camera_motions = db.get_camera_movements(asset_id)
    ocr_obs = db.get_ocr_observations(asset_id)
    ref_profile = db.get_reference_profile(asset_id)
    
    return {
        "success": True,
        "asset_id": str(asset_id),
        "shots_count": len(shots),
        "transcripts_count": len(transcripts),
        "audio_events_count": len(audio_events),
        "camera_movements_count": len(camera_motions),
        "ocr_count": len(ocr_obs),
        "has_reference_profile": ref_profile is not None
    }

@app.get("/api/v1/projects/{project_id}/assets/{asset_id}/shots")
async def get_asset_shots(project_id: UUID, asset_id: UUID):
    asset = db.get_asset(asset_id)
    if not asset or asset.project_id != project_id:
        raise HTTPException(status_code=404, detail="Asset not found.")
    shots = db.get_shots(asset_id)
    return {"success": True, "asset_id": str(asset_id), "shots": shots}

@app.get("/api/v1/projects/{project_id}/assets/{asset_id}/transcript")
async def get_asset_transcript(project_id: UUID, asset_id: UUID):
    asset = db.get_asset(asset_id)
    if not asset or asset.project_id != project_id:
        raise HTTPException(status_code=404, detail="Asset not found.")
    transcripts = db.get_transcripts(asset_id)
    return {"success": True, "asset_id": str(asset_id), "transcripts": transcripts}

@app.get("/api/v1/projects/{project_id}/assets/{asset_id}/audio-events")
async def get_asset_audio_events(project_id: UUID, asset_id: UUID):
    asset = db.get_asset(asset_id)
    if not asset or asset.project_id != project_id:
        raise HTTPException(status_code=404, detail="Asset not found.")
    events = db.get_audio_events(asset_id)
    music = db.get_music_segments(asset_id)
    return {"success": True, "asset_id": str(asset_id), "audio_events": events, "music_segments": music}

@app.get("/api/v1/projects/{project_id}/assets/{asset_id}/camera-motion")
async def get_asset_camera_motion(project_id: UUID, asset_id: UUID):
    asset = db.get_asset(asset_id)
    if not asset or asset.project_id != project_id:
        raise HTTPException(status_code=404, detail="Asset not found.")
    motions = db.get_camera_movements(asset_id)
    return {"success": True, "asset_id": str(asset_id), "camera_motions": motions}

@app.get("/api/v1/projects/{project_id}/assets/{asset_id}/ocr")
async def get_asset_ocr(project_id: UUID, asset_id: UUID):
    asset = db.get_asset(asset_id)
    if not asset or asset.project_id != project_id:
        raise HTTPException(status_code=404, detail="Asset not found.")
    ocr_obs = db.get_ocr_observations(asset_id)
    return {"success": True, "asset_id": str(asset_id), "ocr_observations": ocr_obs}

@app.post("/api/v1/projects/{project_id}/assets/{asset_id}/reference-profile")
async def generate_reference_profile(project_id: UUID, asset_id: UUID):
    asset = db.get_asset(asset_id)
    if not asset or asset.project_id != project_id:
        raise HTTPException(status_code=404, detail="Asset not found.")
    
    result = await intelligence_service.analyze_asset(asset_id, profile=AnalysisProfile.REFERENCE_ANALYSIS)
    profile = db.get_reference_profile(asset_id)
    return {"success": True, "asset_id": str(asset_id), "reference_profile": profile}

@app.get("/api/v1/projects/{project_id}/assets/{asset_id}/reference-profile")
async def get_reference_profile_endpoint(project_id: UUID, asset_id: UUID):
    asset = db.get_asset(asset_id)
    if not asset or asset.project_id != project_id:
        raise HTTPException(status_code=404, detail="Asset not found.")
    profile = db.get_reference_profile(asset_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Reference profile not found for this asset.")
    return {"success": True, "asset_id": str(asset_id), "reference_profile": profile}

@app.post("/api/v1/projects/{project_id}/compare")
async def compare_assets_endpoint(project_id: UUID, req: CompareAssetsRequest):
    src = db.get_asset(req.source_asset_id)
    ref = db.get_asset(req.reference_asset_id)
    if not src or src.project_id != project_id or not ref or ref.project_id != project_id:
        raise HTTPException(status_code=404, detail="One or both assets not found in project.")
    
    try:
        comparison = intelligence_service.compare_assets(req.source_asset_id, req.reference_asset_id)
        return {"success": True, "comparison": comparison}
    except FileNotFoundError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/v1/projects/{project_id}/search")
async def search_media_endpoint(project_id: UUID, req: SearchMediaRequest):
    results = intelligence_service.search(project_id, req.query, limit=req.limit)
    return {"success": True, "query": req.query, "results_count": len(results), "results": results}

# ---------------------------------------------------------
# Part 04: AI Director & Creative Production Planning
# ---------------------------------------------------------

@app.post("/api/v1/projects/{project_id}/creative/brief")
async def create_or_parse_brief(project_id: UUID, req: CreateBriefRequest):
    proj = db.get_project(project_id)
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found.")
    raw_dict = req.model_dump()
    brief, questions = creative_director.parse_brief(project_id, raw_dict)
    return {
        "success": True,
        "brief_id": str(brief.brief_id),
        "project_name": brief.project_name,
        "production_type": brief.production_type.value,
        "target_duration_sec": brief.target_duration_sec,
        "assumptions": brief.assumptions,
        "clarification_questions": questions
    }

@app.get("/api/v1/projects/{project_id}/creative/brief")
async def get_creative_brief_endpoint(project_id: UUID):
    brief_dict = db.get_creative_brief(project_id)
    if not brief_dict:
        raise HTTPException(status_code=404, detail="Creative brief not found for this project.")
    return {"success": True, "brief": brief_dict}

@app.post("/api/v1/projects/{project_id}/creative/concepts")
async def generate_creative_concepts(project_id: UUID):
    brief_dict = db.get_creative_brief(project_id)
    if not brief_dict:
        raise HTTPException(status_code=400, detail="Please create a creative brief first.")
    from core.planning.planning_models import CreativeBrief, PacingStyle, ProductionType
    brief, _ = creative_director.brief_service.parse_brief(project_id, brief_dict)
    concepts = creative_director.generate_concepts(brief, count=3)
    return {"success": True, "concepts_count": len(concepts), "concepts": [
        {"concept_id": str(c.concept_id), "name": c.name, "premise": c.creative_premise, "complexity": c.production_complexity.value, "is_selected": c.is_selected}
        for c in concepts
    ]}

@app.get("/api/v1/projects/{project_id}/creative/concepts")
async def get_creative_concepts_endpoint(project_id: UUID):
    concepts = db.get_creative_concepts(project_id)
    return {"success": True, "concepts": concepts}

@app.post("/api/v1/projects/{project_id}/creative/concepts/{concept_id}/select")
async def select_concept_endpoint(project_id: UUID, concept_id: UUID):
    db.select_concept(project_id, concept_id)
    return {"success": True, "message": f"Concept {concept_id} selected as active direction."}

@app.post("/api/v1/projects/{project_id}/creative/script")
async def develop_script_endpoint(project_id: UUID, req: CreateScriptRequest):
    brief_dict = db.get_creative_brief(project_id)
    if not brief_dict:
        raise HTTPException(status_code=400, detail="Creative brief required before script generation.")
    brief, _ = creative_director.brief_service.parse_brief(project_id, brief_dict)
    
    selected_concept = None
    if req.selected_concept_id:
        concepts = db.get_creative_concepts(project_id)
        matching = [c for c in concepts if c["concept_id"] == req.selected_concept_id]
        if matching:
            from core.planning.planning_models import CreativeConcept, ComplexityCategory
            m = matching[0]
            selected_concept = CreativeConcept(
                concept_id=m["concept_id"], project_id=project_id, name=m["name"],
                creative_premise=m["creative_premise"], narrative_approach=m["narrative_approach"],
                visual_treatment=m["visual_treatment"], cinematography_style=m["cinematography_style"],
                color_direction=m["color_direction"], sound_direction=m["sound_direction"],
                editing_rhythm=m["editing_rhythm"], motion_graphics_style=m["motion_graphics_style"],
                production_complexity=ComplexityCategory(m["production_complexity"]), is_selected=True
            )
    
    script = creative_director.develop_script(brief, selected_concept)
    return {
        "success": True,
        "script_id": str(script.script_id),
        "title": script.title,
        "scenes_count": len(script.scenes),
        "estimated_spoken_duration_sec": script.estimated_spoken_duration_sec,
        "total_words": script.total_words
    }

@app.get("/api/v1/projects/{project_id}/creative/script")
async def get_script_endpoint(project_id: UUID):
    script = db.get_script(project_id)
    if not script:
        raise HTTPException(status_code=404, detail="Script not found for this project.")
    return {"success": True, "script": script}

@app.post("/api/v1/projects/{project_id}/creative/shots")
async def plan_shots_endpoint(project_id: UUID, req: PlanShotsRequest):
    script_dict = db.get_script(project_id)
    if not script_dict:
        raise HTTPException(status_code=400, detail="Script required before shot planning.")
    
    from core.planning.planning_models import ProductionScript, ScriptScene, DialogueEntry, DialogueType
    scenes = []
    for sc in script_dict["scenes"]:
        diag = [DialogueEntry(
            entry_id=UUID(d["entry_id"]), speaker=d["speaker"], text=d["text"],
            entry_type=DialogueType(d["entry_type"]), estimated_duration_sec=d["estimated_duration_sec"]
        ) for d in sc["dialogue_entries"]]
        scenes.append(ScriptScene(
            scene_id=sc["scene_id"], script_id=sc["script_id"], scene_number=sc["scene_number"],
            title=sc["title"], slugline=sc["slugline"], narrative_purpose=sc["narrative_purpose"],
            location=sc["location"], time_of_day=sc["time_of_day"], characters_present=sc["characters_present"],
            action_description=sc["action_description"], dialogue_entries=diag,
            emotional_tone=sc["emotional_tone"], estimated_duration_sec=sc["estimated_duration_sec"]
        ))
    script = ProductionScript(
        script_id=script_dict["script_id"], project_id=project_id, title=script_dict["title"],
        logline=script_dict["logline"], target_duration_sec=script_dict["target_duration_sec"],
        estimated_spoken_duration_sec=script_dict["estimated_spoken_duration_sec"],
        total_words=script_dict["total_words"], scenes=scenes
    )
    shots = creative_director.plan_shots(script, visual_style=req.visual_style or "Cinematic Realism")
    return {"success": True, "planned_shots_count": len(shots), "shots": [
        {"shot_number": s.shot_number, "scale": s.shot_scale.value, "camera_motion": s.camera_motion.value, "duration_sec": s.estimated_duration_sec}
        for s in shots
    ]}

@app.get("/api/v1/projects/{project_id}/creative/shots")
async def get_planned_shots_endpoint(project_id: UUID):
    shots = db.get_planned_shots()
    return {"success": True, "shots": shots}

@app.post("/api/v1/projects/{project_id}/creative/storyboard")
async def plan_storyboard_endpoint(project_id: UUID):
    shot_dicts = db.get_planned_shots()
    if not shot_dicts:
        raise HTTPException(status_code=400, detail="Planned shots required before storyboard generation.")
    from core.planning.planning_models import PlannedShot
    from core.assets.intelligence_models import ShotScale, CameraAngle, CameraMotionType
    from core.planning.planning_models import ProductionTaskType
    shots = []
    for s in shot_dicts:
        shots.append(PlannedShot(
            shot_id=s["shot_id"], scene_id=s["scene_id"], shot_number=s["shot_number"],
            narrative_purpose=s["narrative_purpose"], shot_scale=ShotScale(s["shot_scale"]),
            camera_angle=CameraAngle(s["camera_angle"]), camera_motion=CameraMotionType(s["camera_motion"]),
            lens_focal_length=s["lens_focal_length"], camera_position=s["camera_position"],
            subject_action=s["subject_action"], environment_description=s["environment_description"],
            lighting_direction=s["lighting_direction"], composition_notes=s["composition_notes"],
            depth_of_field=s["depth_of_field"], focus_behavior=s["focus_behavior"],
            motion_characteristics=s["motion_characteristics"], start_state=s["start_state"],
            end_state=s["end_state"], estimated_duration_sec=s["estimated_duration_sec"],
            aspect_ratio=s["aspect_ratio"], visual_style=s["visual_style"],
            continuity_requirements=s["continuity_requirements"], required_source_assets=s["required_source_assets"],
            generation_requirements=ProductionTaskType(s["generation_requirements"])
        ))
    frames = creative_director.plan_storyboard(shots)
    return {"success": True, "frames_count": len(frames), "frames": [
        {"frame_order": f.frame_order, "prompt_spec": f.visual_prompt_spec, "approval_status": f.approval_status.value}
        for f in frames
    ]}

@app.get("/api/v1/projects/{project_id}/creative/storyboard")
async def get_storyboard_endpoint(project_id: UUID):
    frames = db.get_storyboard_frames()
    return {"success": True, "storyboard_frames": frames}

@app.post("/api/v1/projects/{project_id}/creative/edit-plan")
async def create_edit_plan_endpoint(project_id: UUID, req: CreateEditPlanRequest):
    # Retrieve shots from source assets
    source_shots = []
    for aid in req.source_asset_ids:
        s_list = db.get_shots(aid)
        source_shots.extend(s_list)
    
    ref_profile = None
    if req.reference_asset_id:
        rp_dict = db.get_reference_profile(req.reference_asset_id)
        if rp_dict:
            from core.assets.intelligence_models import ReferenceProfile
            ref_profile = ReferenceProfile(**rp_dict)
            
    blueprint = production_planner.create_edit_blueprint(
        project_id=project_id,
        target_duration_sec=req.target_duration_sec,
        source_shots=source_shots,
        ref_profile=ref_profile,
        instructions=req.instructions or ""
    )
    return {
        "success": True,
        "blueprint_id": str(blueprint.blueprint_id),
        "target_duration_sec": blueprint.target_duration_sec,
        "cuts_count": len(blueprint.narrative_order),
        "missing_coverage_count": len(blueprint.missing_coverage),
        "missing_coverage": [{"duration_sec": m.duration_sec, "solution": m.recommended_solution.value} for m in blueprint.missing_coverage]
    }

@app.get("/api/v1/projects/{project_id}/creative/edit-plan")
async def get_edit_plan_endpoint(project_id: UUID):
    plan = db.get_editing_blueprint(project_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Editing blueprint not found.")
    return {"success": True, "editing_blueprint": plan}

@app.post("/api/v1/projects/{project_id}/creative/blueprint")
async def compile_production_blueprint_endpoint(project_id: UUID):
    brief_dict = db.get_creative_brief(project_id)
    if not brief_dict:
        raise HTTPException(status_code=400, detail="Creative brief required.")
    from core.planning.planning_models import CreativeBrief
    brief, _ = creative_director.brief_service.parse_brief(project_id, brief_dict)
    
    blueprint = production_planner.compile_blueprint(project_id=project_id, brief=brief)
    return {
        "success": True,
        "blueprint_id": str(blueprint.blueprint_id),
        "version": blueprint.version,
        "is_ready_for_production": blueprint.is_ready_for_production,
        "approvals_count": len(blueprint.approvals)
    }

@app.get("/api/v1/projects/{project_id}/creative/blueprint")
async def get_production_blueprint_endpoint(project_id: UUID):
    bp = db.get_production_blueprint(project_id)
    if not bp:
        raise HTTPException(status_code=404, detail="Production blueprint not found.")
    return {"success": True, "production_blueprint": bp}

@app.post("/api/v1/projects/{project_id}/creative/approve")
async def submit_creative_approval(project_id: UUID, req: SubmitApprovalRequest):
    approval = production_planner.submit_approval(
        project_id=project_id,
        entity_type=req.entity_type,
        entity_id=req.entity_id,
        version=req.version,
        status=req.status,
        reviewer_notes=req.reviewer_notes or "",
        approved_by=req.approved_by or "human_director"
    )
    return {
        "success": True,
        "approval_id": str(approval.approval_id),
        "status": approval.status.value,
        "entity_type": approval.entity_type.value
    }

@app.get("/api/v1/projects/{project_id}/creative/approvals")
async def get_creative_approvals_endpoint(project_id: UUID):
    approvals = db.get_creative_approvals(project_id)
    return {"success": True, "approvals": approvals}


# ---------------------------------------------------------
# Part 05 Non-Linear Video Editing Endpoints
# ---------------------------------------------------------

class CreateTimelineRequest(BaseModel):
    name: str = "Master Timeline"
    fps: float = 24.0
    resolution_width: int = 1920
    resolution_height: int = 1080
    sample_rate: int = 48000

class AddTrackRequest(BaseModel):
    track_type: str = "VIDEO"
    name: str = "V1"

class AddClipRequest(BaseModel):
    track_id: UUID
    asset_id: UUID
    timeline_start_sec: float
    duration_sec: float
    source_in_sec: float = 0.0
    speed: float = 1.0
    mode: str = "OVERWRITE"
    name: str = "Clip"

class SplitClipRequest(BaseModel):
    split_time_sec: float

class TrimClipRequest(BaseModel):
    new_start_sec: Optional[float] = None
    new_end_sec: Optional[float] = None

class AddTransitionRequest(BaseModel):
    track_id: UUID
    transition_type: str = "CROSS_DISSOLVE"
    start_time_sec: float
    duration_sec: float = 1.0
    from_clip_id: Optional[UUID] = None
    to_clip_id: Optional[UUID] = None
    parameters: Dict[str, Any] = Field(default_factory=dict)

class AddEffectRequest(BaseModel):
    effect_type: str = "OPACITY"
    parameters: Dict[str, Any] = Field(default_factory=dict)

class RenderTimelineRequest(BaseModel):
    output_path: Optional[str] = None
    is_preview: bool = False
    format_preset: str = "H264_1080P"

class ExecuteBlueprintRequest(BaseModel):
    blueprint_id: Optional[UUID] = None
    timeline_name: str = "Blueprint Timeline"
    fps: float = 24.0


@app.post("/api/v1/editing/projects/{project_id}/timelines")
async def create_timeline_endpoint(project_id: UUID, req: CreateTimelineRequest):
    tl = video_editor.manager.create_timeline(
        project_id=project_id,
        name=req.name,
        fps=req.fps,
        resolution_width=req.resolution_width,
        resolution_height=req.resolution_height,
        sample_rate=req.sample_rate
    )
    return {"success": True, "timeline": tl.to_dict()}

@app.get("/api/v1/editing/timelines/{timeline_id}")
async def get_timeline_endpoint(timeline_id: UUID):
    tl = video_editor.manager.get_timeline(timeline_id)
    if not tl:
        raise HTTPException(status_code=404, detail="Timeline not found.")
    return {"success": True, "timeline": tl.to_dict()}

@app.post("/api/v1/editing/timelines/{timeline_id}/tracks")
async def add_track_endpoint(timeline_id: UUID, req: AddTrackRequest):
    try:
        t_type = TrackType(req.track_type)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid track type {req.track_type}")
    track = video_editor.manager.add_track(timeline_id, t_type, req.name)
    return {"success": True, "track": track.to_dict()}

@app.post("/api/v1/editing/timelines/{timeline_id}/clips")
async def add_clip_endpoint(timeline_id: UUID, req: AddClipRequest):
    try:
        e_mode = EditMode(req.mode)
    except ValueError:
        e_mode = EditMode.OVERWRITE
    clip = video_editor.manager.add_clip_to_track(
        timeline_id=timeline_id,
        track_id=req.track_id,
        asset_id=req.asset_id,
        timeline_start_sec=req.timeline_start_sec,
        duration_sec=req.duration_sec,
        source_in_sec=req.source_in_sec,
        speed=req.speed,
        mode=e_mode,
        name=req.name
    )
    return {"success": True, "clip": clip.to_dict()}

@app.post("/api/v1/editing/timelines/{timeline_id}/clips/{clip_id}/split")
async def split_clip_endpoint(timeline_id: UUID, clip_id: UUID, req: SplitClipRequest):
    try:
        c1, c2 = video_editor.manager.split_clip(timeline_id, clip_id, req.split_time_sec)
        return {"success": True, "left_clip": c1.to_dict(), "right_clip": c2.to_dict()}
    except (ValueError, KeyError) as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.post("/api/v1/editing/timelines/{timeline_id}/clips/{clip_id}/trim")
async def trim_clip_endpoint(timeline_id: UUID, clip_id: UUID, req: TrimClipRequest):
    try:
        clip = video_editor.manager.trim_clip(timeline_id, clip_id, req.new_start_sec, req.new_end_sec)
        return {"success": True, "clip": clip.to_dict()}
    except (ValueError, KeyError) as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.post("/api/v1/editing/timelines/{timeline_id}/clips/{clip_id}/ripple-delete")
async def ripple_delete_endpoint(timeline_id: UUID, clip_id: UUID):
    try:
        removed = video_editor.manager.ripple_delete_clip(timeline_id, clip_id)
        if not removed:
            raise HTTPException(status_code=404, detail="Clip not found.")
        return {"success": True, "removed_clip": removed.to_dict()}
    except (ValueError, KeyError) as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.post("/api/v1/editing/timelines/{timeline_id}/transitions")
async def add_transition_endpoint(timeline_id: UUID, req: AddTransitionRequest):
    try:
        t_type = TransitionType(req.transition_type)
    except ValueError:
        t_type = TransitionType.CROSS_DISSOLVE
    trans = video_editor.manager.add_transition(
        timeline_id=timeline_id,
        track_id=req.track_id,
        transition_type=t_type,
        start_time_sec=req.start_time_sec,
        duration_sec=req.duration_sec,
        from_clip_id=req.from_clip_id,
        to_clip_id=req.to_clip_id,
        parameters=req.parameters
    )
    return {"success": True, "transition": trans.to_dict()}

@app.post("/api/v1/editing/timelines/{timeline_id}/clips/{clip_id}/effects")
async def add_effect_endpoint(timeline_id: UUID, clip_id: UUID, req: AddEffectRequest):
    try:
        eff_type = EffectType(req.effect_type)
    except ValueError:
        eff_type = EffectType.OPACITY
    eff = video_editor.manager.add_effect_to_clip(
        timeline_id=timeline_id,
        clip_id=clip_id,
        effect_type=eff_type,
        parameters=req.parameters
    )
    return {"success": True, "effect": eff.to_dict()}

@app.post("/api/v1/editing/timelines/{timeline_id}/undo")
async def undo_endpoint(timeline_id: UUID):
    restored = video_editor.manager.undo(timeline_id)
    if not restored:
        raise HTTPException(status_code=400, detail="No undo actions available.")
    return {"success": True, "timeline": restored.to_dict()}

@app.post("/api/v1/editing/timelines/{timeline_id}/redo")
async def redo_endpoint(timeline_id: UUID):
    restored = video_editor.manager.redo(timeline_id)
    if not restored:
        raise HTTPException(status_code=400, detail="No redo actions available.")
    return {"success": True, "timeline": restored.to_dict()}

@app.post("/api/v1/editing/projects/{project_id}/execute-blueprint")
async def execute_blueprint_endpoint(project_id: UUID, req: ExecuteBlueprintRequest):
    bp_data = None
    if req.blueprint_id:
        bp_dict = db.get_editing_blueprint(project_id)
        if bp_dict:
            bp_data = bp_dict
    if not bp_data:
        bp_data = db.get_editing_blueprint(project_id)
    if not bp_data:
        raise HTTPException(status_code=404, detail="Editing blueprint not found for project.")

    tl = video_editor.executor.execute_blueprint(
        project_id=project_id,
        blueprint_data=bp_data,
        timeline_name=req.timeline_name,
        fps=req.fps
    )
    return {"success": True, "timeline": tl.to_dict()}

@app.post("/api/v1/editing/timelines/{timeline_id}/render-preview")
async def render_preview_endpoint(timeline_id: UUID):
    tl = video_editor.manager.get_timeline(timeline_id)
    if not tl:
        raise HTTPException(status_code=404, detail="Timeline not found.")
    job = video_editor.previewer.generate_timeline_preview(tl)
    return {"success": True, "render_job": job.__dict__}

@app.post("/api/v1/editing/timelines/{timeline_id}/render-final")
async def render_final_endpoint(timeline_id: UUID, req: RenderTimelineRequest):
    tl = video_editor.manager.get_timeline(timeline_id)
    if not tl:
        raise HTTPException(status_code=404, detail="Timeline not found.")
    out_path = req.output_path or f"temp/renders/{timeline_id}_master.mp4"
    job = video_editor.renderer.render_timeline(
        timeline=tl,
        output_path=out_path,
        is_preview=False,
        format_preset=req.format_preset
    )
    return {"success": True, "render_job": job.__dict__}

@app.get("/api/v1/editing/renders/{render_id}")
async def get_render_job_endpoint(render_id: UUID):
    job = db.get_render_job(render_id)
    if not job:
        raise HTTPException(status_code=404, detail="Render job not found.")
    return {"success": True, "render_job": job}

@app.post("/api/v1/editing/renders/{render_id}/cancel")
async def cancel_render_endpoint(render_id: UUID):
    success = video_editor.renderer.cancel_render(render_id)
    return {"success": success, "message": "Render cancelled." if success else "Render process not active."}

@app.get("/api/v1/editing/timelines/{timeline_id}/export-otio")
async def export_otio_endpoint(timeline_id: UUID):
    tl = video_editor.manager.get_timeline(timeline_id)
    if not tl:
        raise HTTPException(status_code=404, detail="Timeline not found.")
    out_dir = Path("temp/interchange")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = str(out_dir / f"{timeline_id}.otio")
    OTIOAdapter.export_otio_json(tl, out_path)
    return FileResponse(out_path, media_type="application/json", filename=f"{timeline_id}.otio")


# ============================================================================
# 5. DEPARTMENT 09: MOTION GRAPHICS & TYPOGRAPHY ENDPOINTS
# ============================================================================

from departments.motion_graphics.service import MotionGraphicsService
from departments.motion_graphics.core.composition_models import MotionComposition
from departments.motion_graphics.core.design_validator import DesignValidator

motion_service = MotionGraphicsService(db, storage)


class InstantiatePresetRequest(BaseModel):
    project_id: UUID = Field(..., description="Target project ID")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Preset configuration parameters")


class SaveCompositionRequest(BaseModel):
    composition: Dict[str, Any] = Field(..., description="Canonical motion composition dictionary")


class RenderCompositionRequest(BaseModel):
    codec: str = Field(default="prores_ks", description="Target video codec: 'prores_ks' or 'libvpx-vp9'")


class InsertToTimelineRequest(BaseModel):
    timeline_id: UUID = Field(..., description="Target timeline ID")
    track_name: str = Field(default="V3 - Graphics", description="Target video track name")
    timeline_in_sec: Optional[float] = Field(default=None, description="Timeline in-point in seconds")
    codec: str = Field(default="prores_ks", description="Target video codec")


@app.get("/api/v1/motion-graphics/presets")
async def list_motion_presets_endpoint(category: Optional[str] = None):
    presets = motion_service.presets.list_presets(category)
    return {
        "success": True,
        "presets": [
            {
                "preset_id": p.preset_id,
                "name": p.name,
                "category": p.category,
                "description": p.description,
                "default_duration_sec": p.default_duration.to_seconds(),
                "supported_aspect_ratios": p.supported_aspect_ratios,
                "parameters_schema": p.parameters_schema
            }
            for p in presets
        ]
    }


@app.get("/api/v1/motion-graphics/presets/{preset_id}")
async def get_motion_preset_endpoint(preset_id: str):
    p = motion_service.presets.get(preset_id)
    if not p:
        raise HTTPException(status_code=404, detail=f"Preset '{preset_id}' not found.")
    return {
        "success": True,
        "preset": {
            "preset_id": p.preset_id,
            "name": p.name,
            "category": p.category,
            "description": p.description,
            "default_duration_sec": p.default_duration.to_seconds(),
            "supported_aspect_ratios": p.supported_aspect_ratios,
            "parameters_schema": p.parameters_schema
        }
    }


@app.post("/api/v1/motion-graphics/presets/{preset_id}/instantiate")
async def instantiate_motion_preset_endpoint(preset_id: str, req: InstantiatePresetRequest):
    p = motion_service.presets.get(preset_id)
    if not p:
        raise HTTPException(status_code=404, detail=f"Preset '{preset_id}' not found.")

    params = req.parameters.copy()
    params["project_id"] = str(req.project_id)
    comp = motion_service.presets.instantiate(preset_id, params)
    comp.project_id = str(req.project_id)
    db.save_motion_composition(comp)
    val = DesignValidator.validate_composition(comp)

    return {
        "success": True,
        "composition": comp.to_dict(),
        "validation": val
    }


@app.post("/api/v1/motion-graphics/compositions")
async def save_motion_composition_endpoint(req: SaveCompositionRequest):
    comp = MotionComposition.from_dict(req.composition)
    db.save_motion_composition(comp)
    return {"success": True, "composition_id": comp.composition_id}


@app.get("/api/v1/motion-graphics/compositions/{composition_id}")
async def get_motion_composition_endpoint(composition_id: str):
    comp_dict = db.get_motion_composition(composition_id)
    if not comp_dict:
        raise HTTPException(status_code=404, detail=f"Motion composition '{composition_id}' not found.")
    return {"success": True, "composition": comp_dict}


@app.post("/api/v1/motion-graphics/compositions/{composition_id}/validate")
async def validate_motion_composition_endpoint(composition_id: str):
    comp_dict = db.get_motion_composition(composition_id)
    if not comp_dict:
        raise HTTPException(status_code=404, detail=f"Motion composition '{composition_id}' not found.")
    comp = MotionComposition.from_dict(comp_dict)
    val = DesignValidator.validate_composition(comp)
    return {"success": True, "validation": val}


@app.post("/api/v1/motion-graphics/compositions/{composition_id}/render")
async def render_motion_composition_endpoint(composition_id: str, req: RenderCompositionRequest):
    comp_dict = db.get_motion_composition(composition_id)
    if not comp_dict:
        raise HTTPException(status_code=404, detail=f"Motion composition '{composition_id}' not found.")
    comp = MotionComposition.from_dict(comp_dict)

    ext = "mov" if req.codec == "prores_ks" else "webm"
    out_dir = Path("temp/motion_graphics")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = str(out_dir / f"{comp.composition_id}.{ext}")

    rendered = motion_service.router.render(comp, out_path)
    return {"success": True, "output_path": rendered}


@app.post("/api/v1/motion-graphics/compositions/{composition_id}/insert-to-timeline")
async def insert_motion_composition_to_timeline_endpoint(composition_id: str, req: InsertToTimelineRequest):
    comp_dict = db.get_motion_composition(composition_id)
    if not comp_dict:
        raise HTTPException(status_code=404, detail=f"Motion composition '{composition_id}' not found.")
    comp = MotionComposition.from_dict(comp_dict)

    from core.timeline.time_model import RationalTime
    t_in = RationalTime(int(round(req.timeline_in_sec * comp.fps)), comp.fps) if req.timeline_in_sec is not None else None

    clip = motion_service.timeline_adapter.render_and_insert_to_timeline(
        composition=comp,
        timeline_id=str(req.timeline_id),
        target_track_name=req.track_name,
        timeline_in=t_in,
        codec=req.codec
    )
    return {"success": True, "clip_id": clip.clip_id, "asset_id": clip.asset_id}


# =========================================================================
# Department 13: VFX & Compositing API Endpoints
# =========================================================================

class VFXProjectCreateRequest(BaseModel):
    project_id: str
    name: str
    resolution_w: int = 1920
    resolution_h: int = 1080
    fps: float = 24.0
    metadata: Dict[str, Any] = Field(default_factory=dict)


class VFXTaskCreateRequest(BaseModel):
    project_id: str
    shot_id: str
    name: str
    vfx_type: str
    description: str = ""
    input_assets: List[str] = Field(default_factory=list)
    compositing_graph: Optional[Dict[str, Any]] = None


class VFXGraphEvaluateRequest(BaseModel):
    graph: Dict[str, Any]
    frame_index: int = 0


@app.post("/api/v1/vfx/projects")
async def create_vfx_project_endpoint(req: VFXProjectCreateRequest):
    from departments.vfx_compositing.core.vfx_project_models import VFXProject
    vfx_proj = VFXProject(
        vfx_project_id=str(uuid4()),
        project_id=req.project_id,
        name=req.name,
        resolution_w=req.resolution_w,
        resolution_h=req.resolution_h,
        fps=req.fps,
        metadata=req.metadata,
    )
    db.save_vfx_project(vfx_proj)
    return {"success": True, "vfx_project": vfx_proj.to_dict()}


@app.get("/api/v1/vfx/projects/{project_id}")
async def list_vfx_projects_endpoint(project_id: str):
    projects = db.list_vfx_projects(project_id)
    return {"project_id": project_id, "vfx_projects": projects}


@app.post("/api/v1/vfx/shots/tasks")
async def create_vfx_task_endpoint(req: VFXTaskCreateRequest):
    from departments.vfx_compositing.core.vfx_project_models import VFXShotTask, VFXType, VFXTaskStatus
    task = VFXShotTask(
        task_id=str(uuid4()),
        project_id=req.project_id,
        shot_id=req.shot_id,
        name=req.name,
        vfx_type=VFXType(req.vfx_type),
        description=req.description,
        status=VFXTaskStatus.PENDING,
        input_assets=req.input_assets,
        compositing_graph_id=req.compositing_graph.get("graph_id") if req.compositing_graph else None,
    )
    db.save_vfx_shot_task(task)
    return {"success": True, "task": task.to_dict()}


@app.get("/api/v1/vfx/shots/tasks/{task_id}")
async def get_vfx_task_endpoint(task_id: str):
    task = db.get_vfx_shot_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"VFX Task '{task_id}' not found.")
    return {"task": task}


@app.post("/api/v1/vfx/evaluate-graph")
async def evaluate_vfx_graph_endpoint(req: VFXGraphEvaluateRequest):
    from departments.vfx_compositing.core.graph_models import CompositingGraph
    from departments.vfx_compositing.engines.local_compositor import LocalCompositorEngine
    graph = CompositingGraph.from_dict(req.graph)
    engine = LocalCompositorEngine()
    frame = engine.evaluate_frame(graph, frame_index=req.frame_index)
    return {
        "success": True,
        "graph_id": graph.graph_id,
        "frame_shape": list(frame.shape),
        "dtype": str(frame.dtype),
    }


# =========================================================================
# Department 10 & 12: 2D Animation, Anime & Character Studio API Endpoints
# =========================================================================

class CharacterConceptCreateRequest(BaseModel):
    project_id: str
    name: str
    brief: str
    head_ratio: float = 7.0
    visual_style: str = "ANIME_CEL"
    custom_palette: Optional[Dict[str, str]] = None


class AnimationProjectCreateRequest(BaseModel):
    project_id: str
    name: str
    resolution_w: int = 1920
    resolution_h: int = 1080
    fps: float = 24.0


class AnimationBackgroundRenderRequest(BaseModel):
    resolution: Tuple[int, int] = (1080, 1920)
    camera_offset_x: float = 0.0
    time_of_day: str = "SUNSET"


@app.post("/api/v1/animation/characters")
async def create_character_concept_endpoint(req: CharacterConceptCreateRequest):
    from departments.animation_2d.characters.character_generator import CharacterGenerator
    char = CharacterGenerator.create_character_concept(
        project_id=req.project_id,
        name=req.name,
        brief_text=req.brief,
        head_ratio=req.head_ratio,
        visual_style=req.visual_style,
        custom_palette=req.custom_palette,
    )
    db.save_character_identity(char)
    sheet, _ = CharacterGenerator.generate_turnaround_model_sheet(char)
    return {
        "success": True,
        "character": char.to_dict(),
        "model_sheet": sheet.to_dict(),
    }


@app.get("/api/v1/animation/characters/{character_id}")
async def get_character_identity_endpoint(character_id: str):
    char = db.get_character_identity(character_id)
    if not char:
        raise HTTPException(status_code=404, detail=f"Character '{character_id}' not found.")
    return {"character": char}


@app.get("/api/v1/animation/projects/{project_id}/characters")
async def list_character_identities_endpoint(project_id: str):
    chars = db.list_character_identities(project_id)
    return {"project_id": project_id, "characters": chars}


@app.post("/api/v1/animation/projects")
async def create_animation_project_endpoint(req: AnimationProjectCreateRequest):
    from departments.animation_2d.core.models import AnimationProject
    proj = AnimationProject(
        project_id=req.project_id,
        name=req.name,
        resolution_w=req.resolution_w,
        resolution_h=req.resolution_h,
        fps=req.fps,
    )
    db.save_animation_project(proj)
    return {"success": True, "animation_project": proj.to_dict()}


@app.get("/api/v1/animation/projects/{project_id}")
async def list_animation_projects_endpoint(project_id: str):
    projects = db.list_animation_projects(project_id)
    return {"project_id": project_id, "animation_projects": projects}


@app.post("/api/v1/animation/scenes/render-background")
async def render_animation_background_endpoint(req: AnimationBackgroundRenderRequest):
    from departments.animation_2d.anime_pipeline.multiplane_background import MultiplaneBackgroundEngine
    bg = MultiplaneBackgroundEngine.render_parallax_frame(
        canvas_shape=req.resolution,
        camera_offset_x=req.camera_offset_x,
        time_of_day=req.time_of_day,
    )
    return {
        "success": True,
        "resolution": list(req.resolution),
        "time_of_day": req.time_of_day,
        "frame_shape": list(bg.shape),
    }


# =========================================================================
# Department 14: Audio Production Endpoints
# =========================================================================

class AudioSessionCreateRequest(BaseModel):
    project_id: str
    name: str = "Multitrack Session"
    sample_rate: int = 48000
    tempo_bpm: float = 120.0

class AudioTrackCreateRequest(BaseModel):
    name: str
    track_type: str = "DIALOGUE"
    gain_db: float = 0.0
    pan: float = 0.0

class AudioClipCreateRequest(BaseModel):
    name: str = "Clip"
    start_time_sec: float = 0.0
    duration_sec: float = 1.0
    gain_db: float = 0.0
    file_path: Optional[str] = None

class AudioMasterRequest(BaseModel):
    standard: str = "YOUTUBE"
    export_stems: bool = True

class AudioSFXGenerateRequest(BaseModel):
    sfx_type: str = "impact"
    duration_sec: float = 2.0


@app.post("/api/v1/audio/sessions")
async def create_audio_session_endpoint(req: AudioSessionCreateRequest):
    from departments.audio_production.core.session_models import AudioSession
    session = AudioSession(
        project_id=req.project_id,
        name=req.name,
        sample_rate=req.sample_rate,
        tempo_bpm=req.tempo_bpm,
    )
    db.save_audio_session(session)
    return {"success": True, "session": session.to_dict()}


@app.get("/api/v1/audio/sessions/{session_id}")
async def get_audio_session_endpoint(session_id: str):
    sess = db.get_audio_session(session_id)
    if not sess:
        raise HTTPException(status_code=404, detail=f"AudioSession '{session_id}' not found.")
    return {"session": sess}


@app.get("/api/v1/audio/projects/{project_id}/sessions")
async def list_audio_sessions_endpoint(project_id: str):
    sessions = db.list_audio_sessions(project_id)
    return {"project_id": project_id, "sessions": sessions}


@app.post("/api/v1/audio/sessions/{session_id}/tracks")
async def add_audio_track_endpoint(session_id: str, req: AudioTrackCreateRequest):
    from departments.audio_production.core.session_models import AudioSession, AudioTrackType
    sess_dict = db.get_audio_session(session_id)
    if not sess_dict:
        raise HTTPException(status_code=404, detail=f"AudioSession '{session_id}' not found.")
    session = AudioSession.from_dict(sess_dict["data"])
    ttype = AudioTrackType[req.track_type.upper()] if req.track_type.upper() in AudioTrackType.__members__ else AudioTrackType.DIALOGUE
    track = session.add_track(name=req.name, track_type=ttype, gain_db=req.gain_db, pan=req.pan)
    db.save_audio_session(session)
    return {"success": True, "track": track.to_dict()}


@app.post("/api/v1/audio/sessions/{session_id}/tracks/{track_id}/clips")
async def add_audio_clip_endpoint(session_id: str, track_id: str, req: AudioClipCreateRequest):
    from departments.audio_production.core.session_models import AudioSession, AudioClip
    sess_dict = db.get_audio_session(session_id)
    if not sess_dict:
        raise HTTPException(status_code=404, detail=f"AudioSession '{session_id}' not found.")
    session = AudioSession.from_dict(sess_dict["data"])
    track = session.get_track(track_id)
    if not track:
        raise HTTPException(status_code=404, detail=f"AudioTrack '{track_id}' not found.")
    clip = AudioClip(
        track_id=track_id,
        name=req.name,
        start_time_sec=req.start_time_sec,
        duration_sec=req.duration_sec,
        gain_db=req.gain_db,
        file_path=req.file_path,
    )
    track.add_clip(clip)
    db.save_audio_session(session)
    return {"success": True, "clip": clip.to_dict()}


@app.post("/api/v1/audio/sessions/{session_id}/master")
async def master_audio_session_endpoint(session_id: str, req: AudioMasterRequest):
    from departments.audio_production.core.session_models import AudioSession, LoudnessStandard
    from departments.audio_production.mixing.mastering_engine import MasteringEngine
    sess_dict = db.get_audio_session(session_id)
    if not sess_dict:
        raise HTTPException(status_code=404, detail=f"AudioSession '{session_id}' not found.")
    session = AudioSession.from_dict(sess_dict["data"])
    std = LoudnessStandard[req.standard.upper()] if req.standard.upper() in LoudnessStandard.__members__ else LoudnessStandard.YOUTUBE
    out_dir = f"temp/audio_scratch/{session_id}"
    res = MasteringEngine.master_session(session, out_dir, standard=std, export_stems=req.export_stems)
    return {"success": True, "mastering_result": res}


@app.post("/api/v1/audio/sfx/generate")
async def generate_procedural_sfx_endpoint(req: AudioSFXGenerateRequest):
    from departments.audio_production.sound_design.procedural_sfx import ProceduralSFXEngine
    from departments.audio_production.mixing.mastering_engine import MasteringEngine
    st = req.sfx_type.lower()
    if st == "impact":
        audio = ProceduralSFXEngine.generate_cinematic_impact(duration_sec=req.duration_sec)
    elif st == "whoosh":
        audio = ProceduralSFXEngine.generate_whoosh_transition(duration_sec=req.duration_sec)
    elif st == "riser":
        audio = ProceduralSFXEngine.generate_tension_riser(duration_sec=req.duration_sec)
    else:
        audio = ProceduralSFXEngine.generate_ambient_drone(duration_sec=req.duration_sec)

    import os
    os.makedirs("temp/audio_scratch", exist_ok=True)
    out_path = f"temp/audio_scratch/sfx_{uuid4().hex[:8]}.wav"
    MasteringEngine.export_wav(audio, 48000, out_path)
    return {
        "success": True,
        "sfx_type": req.sfx_type,
        "duration_sec": req.duration_sec,
        "output_path": out_path,
    }


# =========================================================================
# Department 15: AI Generation Studio Endpoints
# =========================================================================

class GenerationJobSubmitRequest(BaseModel):
    project_id: str
    shot_id: Optional[str] = None
    modality: str = "TEXT_TO_IMAGE"
    prompt: str
    preferred_provider: Optional[str] = None
    duration_sec: float = 5.0
    aspect_ratio: str = "16:9"

class CompilePromptRequest(BaseModel):
    dimensions: Dict[str, Any]
    provider_id: str = "runway_gen3"

class CharacterProfileCreateRequest(BaseModel):
    project_id: str
    name: str
    style_description: str = "cinematic photorealism"
    distinguishing_features: List[str] = Field(default_factory=list)


@app.post("/api/v1/generation/jobs")
async def submit_generation_job_endpoint(req: GenerationJobSubmitRequest):
    import departments
    from departments.ai_generation.service import AIGenerationService
    from departments.ai_generation.interface import AIGenerationRequest
    svc = AIGenerationService()
    resp = await svc.execute(AIGenerationRequest(
        project_id=uuid.UUID(req.project_id) if len(req.project_id) == 36 else uuid.uuid4(),
        parameters={
            "action": "submit_job",
            "modality": req.modality,
            "prompt": req.prompt,
            "shot_id": req.shot_id,
            "preferred_provider": req.preferred_provider,
            "duration_sec": req.duration_sec,
            "aspect_ratio": req.aspect_ratio,
        },
    ))
    return {"success": resp.success, "message": resp.message, "data": resp.data}


@app.get("/api/v1/generation/jobs/{job_id}")
async def get_generation_job_endpoint(job_id: str):
    job = db.get_generation_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Generation job '{job_id}' not found.")
    return {"job": job}


@app.get("/api/v1/generation/projects/{project_id}/jobs")
async def list_generation_jobs_endpoint(project_id: str):
    jobs = db.list_generation_jobs(project_id)
    return {"project_id": project_id, "jobs": jobs}


@app.post("/api/v1/generation/compile-prompt")
async def compile_prompt_endpoint(req: CompilePromptRequest):
    from departments.ai_generation.prompts.prompt_compiler import PromptCompiler, StructuredPromptDimensions
    dims = StructuredPromptDimensions(**req.dimensions)
    pos, neg = PromptCompiler.compile_for_provider(dims, req.provider_id)
    return {
        "success": True,
        "compiled_positive_prompt": pos,
        "compiled_negative_prompt": neg,
    }


@app.post("/api/v1/generation/characters")
async def create_character_profile_endpoint(req: CharacterProfileCreateRequest):
    from departments.ai_generation.core.character_profile import CharacterReferenceProfile
    prof = CharacterReferenceProfile(
        project_id=req.project_id,
        name=req.name,
        style_description=req.style_description,
        distinguishing_features=req.distinguishing_features,
    )
    db.save_generation_character_profile(prof)
    return {"success": True, "character_profile": prof.to_dict()}


@app.get("/api/v1/generation/characters/{character_id}")
async def get_character_profile_endpoint(character_id: str):
    prof = db.get_generation_character_profile(character_id)
    if not prof:
        raise HTTPException(status_code=404, detail=f"Character profile '{character_id}' not found.")
    return {"character_profile": prof}


@app.get("/api/v1/generation/providers")
async def list_generation_providers_endpoint():
    import departments
    from departments.ai_generation.providers.registry import ProviderRegistry
    reg = ProviderRegistry()
    return {"providers": [p.model_dump() for p in reg.list_providers()]}




# ---------------------------------------------------------------------------
# Department 16: Color Grading & Video Restoration Endpoints
# ---------------------------------------------------------------------------

class ColorGradeSaveRequest(BaseModel):
    project_id: UUID
    name: str = "Master Grade"
    clip_id: Optional[str] = None
    working_color_space: str = "acescg"
    display_color_space: str = "rec709"
    nodes: List[Dict[str, Any]] = Field(default_factory=list)
    version: int = 1
    description: Optional[str] = None


class RecommendGradeRequest(BaseModel):
    project_id: UUID
    creative_intent: Optional[str] = None
    mean_luminance: float = 0.18
    color_temperature_k: float = 6500.0


class RestorationJobSubmitRequest(BaseModel):
    project_id: UUID
    asset_id: UUID
    restoration_types: List[str]
    parameters: Dict[str, Any] = Field(default_factory=dict)


@app.post("/api/v1/color/grades", status_code=status.HTTP_201_CREATED)
async def save_color_grade_endpoint(req: ColorGradeSaveRequest):
    import departments
    from departments.color_restoration.core.models import GradingGraph, ColorSpace
    graph = GradingGraph(
        project_id=req.project_id,
        name=req.name,
        clip_id=req.clip_id,
        working_color_space=ColorSpace(req.working_color_space),
        display_color_space=ColorSpace(req.display_color_space),
        version=req.version,
        description=req.description
    )
    db.save_color_grade(graph)
    return {"success": True, "grade_id": str(graph.id), "name": graph.name}


@app.get("/api/v1/color/grades/{grade_id}")
async def get_color_grade_endpoint(grade_id: str):
    grade = db.get_color_grade(grade_id)
    if not grade:
        raise HTTPException(status_code=404, detail=f"Color grade '{grade_id}' not found.")
    return {"grade": grade}


@app.get("/api/v1/color/projects/{project_id}/grades")
async def list_color_grades_endpoint(project_id: str):
    grades = db.list_color_grades(project_id)
    return {"project_id": project_id, "grades": grades}


@app.post("/api/v1/color/recommend-grade")
async def recommend_grade_endpoint(req: RecommendGradeRequest):
    import departments
    from departments.color_restoration.ai_colorist.ai_colorist_assistant import AIColoristAssistant
    import numpy as np

    # Synthetic sample frame matching requested luminance and temp
    sample = np.ones((64, 64, 3), dtype=np.float32) * req.mean_luminance
    if req.color_temperature_k < 5500.0:
        sample[:, :, 0] *= 1.2 # warm
    elif req.color_temperature_k > 7000.0:
        sample[:, :, 2] *= 1.2 # cool

    graph, explanations = AIColoristAssistant.recommend_grade(
        sample, project_id=req.project_id, creative_intent=req.creative_intent
    )
    return {
        "success": True,
        "recommended_graph": graph.model_dump(mode="json"),
        "explanations": explanations
    }


@app.post("/api/v1/restoration/jobs", status_code=status.HTTP_202_ACCEPTED)
async def submit_restoration_job_endpoint(req: RestorationJobSubmitRequest):
    import departments
    from departments.color_restoration.core.models import RestorationJob, RestorationType
    types = [RestorationType(t) for t in req.restoration_types]
    job = RestorationJob(
        project_id=req.project_id,
        asset_id=req.asset_id,
        restoration_types=types,
        parameters=req.parameters,
        status="PROCESSING"
    )
    db.save_restoration_job(job)
    return {
        "success": True,
        "job_id": str(job.id),
        "status": job.status,
        "restoration_types": [t.value for t in types]
    }


@app.get("/api/v1/restoration/jobs/{job_id}")
async def get_restoration_job_endpoint(job_id: str):
    job = db.get_restoration_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Restoration job '{job_id}' not found.")
    return {"job": job}


@app.get("/api/v1/restoration/projects/{project_id}/jobs")
async def list_restoration_jobs_endpoint(project_id: str):
    jobs = db.list_restoration_jobs(project_id)
    return {"project_id": project_id, "jobs": jobs}


# ==============================================================================
# Part 13 — Subtitles, Dubbing & Localization Endpoints
# ==============================================================================

class LocalizationTranscribeRequest(BaseModel):
    project_id: UUID
    media_asset_id: UUID
    language: Optional[str] = None
    simulated_text: Optional[str] = None

class LocalizationTranslateRequest(BaseModel):
    project_id: UUID
    text: str
    target_language: str
    source_language: str = "en"

class LocalizationSubtitlesRequest(BaseModel):
    project_id: UUID
    text: Optional[str] = None
    format: str = "srt"
    style_preset: str = "cinematic"
    max_cpl: int = 42

class LocalizationDubbingRequest(BaseModel):
    project_id: UUID
    target_language: str
    text: Optional[str] = None
    preserve_background: bool = True
    voice_mappings: Optional[Dict[str, str]] = None

class LocalizationLipSyncRequest(BaseModel):
    project_id: UUID
    video_asset_id: UUID
    audio_asset_id: UUID
    provider: str = "synclabs"

class LocalizationQCAuditRequest(BaseModel):
    project_id: UUID
    measured_lufs: float = -23.0
    true_peak_db: float = -1.2


@app.post("/api/v1/localization/transcribe")
async def transcribe_endpoint(req: LocalizationTranscribeRequest):
    import departments
    from departments.subtitles_dubbing.service import SubtitlesDubbingService
    from departments.subtitles_dubbing.interface import SubtitlesDubbingRequest
    svc = SubtitlesDubbingService()
    resp = await svc.execute(SubtitlesDubbingRequest(
        project_id=req.project_id,
        parameters={
            "action": "transcribe",
            "media_asset_id": req.media_asset_id,
            "language": req.language,
            "simulated_text": req.simulated_text,
        }
    ))
    return resp.model_dump(mode="json")


@app.post("/api/v1/localization/translate")
async def translate_endpoint(req: LocalizationTranslateRequest):
    import departments
    from departments.subtitles_dubbing.translation.translator import MultilingualTranslator
    from departments.subtitles_dubbing.core.models import TranscriptSegment
    translator = MultilingualTranslator()
    seg = TranscriptSegment(start_time=0.0, end_time=3.0, text=req.text)
    record = translator.translate_segment(
        segment=seg,
        project_id=req.project_id,
        target_language=req.target_language,
        source_language=req.source_language,
    )
    return {"success": True, "translation": record.model_dump(mode="json")}


@app.post("/api/v1/localization/subtitles")
async def subtitles_endpoint(req: LocalizationSubtitlesRequest):
    import departments
    from departments.subtitles_dubbing.service import SubtitlesDubbingService
    from departments.subtitles_dubbing.interface import SubtitlesDubbingRequest
    svc = SubtitlesDubbingService()
    resp = await svc.execute(SubtitlesDubbingRequest(
        project_id=req.project_id,
        parameters={
            "action": "generate_subtitles",
            "text": req.text,
            "format": req.format,
            "style_preset": req.style_preset,
            "max_cpl": req.max_cpl,
        }
    ))
    return resp.model_dump(mode="json")


@app.post("/api/v1/localization/dubbing", status_code=status.HTTP_202_ACCEPTED)
async def dubbing_endpoint(req: LocalizationDubbingRequest):
    import departments
    from departments.subtitles_dubbing.service import SubtitlesDubbingService
    from departments.subtitles_dubbing.interface import SubtitlesDubbingRequest
    svc = SubtitlesDubbingService()
    resp = await svc.execute(SubtitlesDubbingRequest(
        project_id=req.project_id,
        parameters={
            "action": "orchestrate_dubbing",
            "target_language": req.target_language,
            "text": req.text,
            "preserve_background": req.preserve_background,
            "voice_mappings": req.voice_mappings,
        }
    ))
    if resp.success and "dubbing_job" in resp.data:
        job_data = resp.data["dubbing_job"]
        db.save_localization_job(
            job_id=job_data["job_id"],
            project_id=str(req.project_id),
            job_type="dubbing",
            target_language=req.target_language,
            status=job_data["status"],
            output_asset_id=job_data.get("output_audio_asset_id"),
            details=job_data,
        )
    return resp.model_dump(mode="json")


@app.post("/api/v1/localization/lipsync", status_code=status.HTTP_202_ACCEPTED)
async def lipsync_endpoint(req: LocalizationLipSyncRequest):
    import departments
    from departments.subtitles_dubbing.service import SubtitlesDubbingService
    from departments.subtitles_dubbing.interface import SubtitlesDubbingRequest
    svc = SubtitlesDubbingService()
    resp = await svc.execute(SubtitlesDubbingRequest(
        project_id=req.project_id,
        parameters={
            "action": "process_lipsync",
            "video_asset_id": req.video_asset_id,
            "audio_asset_id": req.audio_asset_id,
            "provider": req.provider,
        }
    ))
    if resp.success and "lipsync_job" in resp.data:
        job_data = resp.data["lipsync_job"]
        db.save_localization_job(
            job_id=job_data["job_id"],
            project_id=str(req.project_id),
            job_type="lipsync",
            target_language="visual_sync",
            status=job_data["status"],
            output_asset_id=job_data.get("output_video_asset_id"),
            details=job_data,
        )
    return resp.model_dump(mode="json")


@app.post("/api/v1/localization/qc")
async def localization_qc_endpoint(req: LocalizationQCAuditRequest):
    import departments
    from departments.subtitles_dubbing.qc.quality_controller import LocalizationQualityController
    report = LocalizationQualityController.audit_audio_loudness(
        project_id=req.project_id,
        measured_lufs=req.measured_lufs,
        true_peak_db=req.true_peak_db,
    )
    return {"success": True, "qc_report": report.model_dump(mode="json")}


@app.get("/api/v1/localization/projects/{project_id}/jobs")
async def list_localization_jobs_endpoint(project_id: str):
    jobs = db.list_localization_jobs(project_id)
    return {"project_id": project_id, "jobs": jobs}


# ==============================================================================
# Part 14 — Quality Control, Rendering & Delivery Endpoints
# ==============================================================================

class RenderPlanCompileRequest(BaseModel):
    project_id: UUID
    render_profile_id: str = "youtube_1080p"
    project_metadata: Dict[str, Any] = Field(default_factory=dict)
    timeline_id: Optional[UUID] = None

class RenderJobSubmitRequest(BaseModel):
    project_id: UUID
    render_profile_id: str
    priority: int = 5
    sequence_id: Optional[UUID] = None
    idempotency_key: Optional[str] = None

class DeliveryPackageCreateRequest(BaseModel):
    project_id: UUID
    render_job_id: UUID
    master_file_path: str
    sidecars: List[Dict[str, str]] = Field(default_factory=list)
    output_directory: Optional[str] = None
    technical_specs: Optional[Dict[str, Any]] = None
    qc_summary: Optional[Dict[str, Any]] = None

class MediaQCAuditRequest(BaseModel):
    project_id: UUID
    file_path: str
    asset_id: Optional[UUID] = None
    policy_name: str = "STREAMING_STANDARD"
    expected_checksum: Optional[str] = None
    video: Optional[Dict[str, Any]] = None
    audio: Optional[Dict[str, Any]] = None


@app.post("/api/v1/rendering/plan")
async def compile_render_plan_endpoint(req: RenderPlanCompileRequest):
    import departments
    from departments.rendering_delivery.service import RenderingDeliveryService
    from departments.rendering_delivery.interface import RenderingDeliveryRequest
    svc = RenderingDeliveryService()
    resp = await svc.execute(RenderingDeliveryRequest(
        project_id=req.project_id,
        parameters={
            "action": "compile_render_plan",
            "render_profile_id": req.render_profile_id,
            "project_metadata": req.project_metadata,
            "timeline_id": req.timeline_id,
        }
    ))
    if resp.success and "render_plan" in resp.data:
        plan = resp.data["render_plan"]
        db.save_render_plan(
            plan_id=plan["plan_id"],
            project_id=str(req.project_id),
            render_profile_id=req.render_profile_id,
            stages=plan["stages"],
            estimated_duration_sec=plan["estimated_duration_sec"],
            estimated_cost_usd=plan["estimated_cost_usd"],
            timeline_id=str(req.timeline_id) if req.timeline_id else None,
        )
    return resp.model_dump(mode="json")


@app.post("/api/v1/rendering/jobs", status_code=status.HTTP_202_ACCEPTED)
async def submit_render_job_endpoint(req: RenderJobSubmitRequest):
    import departments
    from departments.rendering_delivery.service import RenderingDeliveryService
    from departments.rendering_delivery.interface import RenderingDeliveryRequest
    svc = RenderingDeliveryService()
    resp = await svc.execute(RenderingDeliveryRequest(
        project_id=req.project_id,
        parameters={
            "action": "submit_render_job",
            "render_profile_id": req.render_profile_id,
            "priority": req.priority,
            "sequence_id": req.sequence_id,
            "idempotency_key": req.idempotency_key,
        }
    ))
    return resp.model_dump(mode="json")


@app.get("/api/v1/rendering/profiles")
async def list_render_profiles_endpoint():
    import departments
    from departments.rendering_delivery.profiles.profile_registry import RenderProfileRegistry
    profiles = RenderProfileRegistry.list_profiles()
    return {"profiles": [p.model_dump(mode="json") for p in profiles]}


@app.post("/api/v1/rendering/delivery/package", status_code=status.HTTP_201_CREATED)
async def create_delivery_package_endpoint(req: DeliveryPackageCreateRequest):
    import departments
    from departments.rendering_delivery.service import RenderingDeliveryService
    from departments.rendering_delivery.interface import RenderingDeliveryRequest
    svc = RenderingDeliveryService()
    resp = await svc.execute(RenderingDeliveryRequest(
        project_id=req.project_id,
        parameters={
            "action": "package_delivery",
            "job_id": req.render_job_id,
            "master_file_path": req.master_file_path,
            "sidecars": req.sidecars,
            "output_directory": req.output_directory,
            "technical_specs": req.technical_specs,
            "qc_summary": req.qc_summary,
        }
    ))
    if resp.success and "delivery_package" in resp.data:
        pkg = resp.data["delivery_package"]
        db.save_delivery_package(
            package_id=pkg["package_id"],
            delivery_id=pkg["delivery_id"],
            project_id=str(req.project_id),
            render_job_id=str(req.render_job_id),
            master_file_path=pkg["master_file_path"],
            manifest_path=pkg["manifest_path"],
            sidecars=pkg["sidecar_files"],
            total_size_bytes=pkg["total_size_bytes"],
        )
    return resp.model_dump(mode="json")


@app.post("/api/v1/qc/audit")
async def media_qc_audit_endpoint(req: MediaQCAuditRequest):
    import departments
    from departments.quality_control.service import QualityControlService
    from departments.quality_control.interface import QualityControlRequest
    svc = QualityControlService()
    resp = await svc.execute(QualityControlRequest(
        project_id=req.project_id,
        parameters={
            "action": "audit_media_file",
            "file_path": req.file_path,
            "asset_id": req.asset_id,
            "policy_name": req.policy_name,
            "expected_checksum": req.expected_checksum,
            "video": req.video,
            "audio": req.audio,
        }
    ))
    if resp.success and "qc_report" in resp.data:
        rep = resp.data["qc_report"]
        db.save_qc_report(
            report_id=rep["report_id"],
            project_id=str(req.project_id),
            asset_id=rep["asset_id"],
            passed=rep["passed"],
            defects=rep["defects"],
            critical_count=rep["critical_count"],
            error_count=rep["error_count"],
            warning_count=rep["warning_count"],
            metrics=rep["metrics"],
        )
    return resp.model_dump(mode="json")


@app.get("/api/v1/qc/reports/{report_id}")
async def get_qc_report_endpoint(report_id: str):
    rep = db.get_qc_report(report_id)
    if not rep:
        raise HTTPException(status_code=404, detail=f"QC report '{report_id}' not found.")
    return {"qc_report": rep}


# ---------------------------------------------------------
# System Telemetry & Workspace Layout Endpoints
# ---------------------------------------------------------

@app.get("/api/v1/system/telemetry")
async def get_system_telemetry():
    return studio_app.get_system_telemetry()

@app.get("/api/v1/system/layout/{workspace_id}")
async def get_workspace_layout_endpoint(workspace_id: str):
    return {"workspace_id": workspace_id, "layout": studio_app.get_workspace_layout(workspace_id)}

@app.post("/api/v1/system/layout/{workspace_id}")
async def save_workspace_layout_endpoint(workspace_id: str, req: SaveLayoutRequest):
    studio_app.save_workspace_layout(workspace_id, req.layout)
    return {"success": True, "workspace_id": workspace_id, "layout": req.layout}

# ---------------------------------------------------------
# Studio UI Static Web Application Serving
# ---------------------------------------------------------

UI_DIR = Path(__file__).parent / "ui"

@app.get("/")
async def serve_index():
    index_file = UI_DIR / "index.html"
    if not index_file.exists():
        raise HTTPException(status_code=404, detail="UI index.html not found.")
    return HTMLResponse(content=index_file.read_text(encoding="utf-8"))

@app.get("/ui")
@app.get("/ui/{file_path:path}")
async def serve_ui_file(file_path: str = ""):
    if not file_path or file_path.endswith("/"):
        target = UI_DIR / "index.html"
    else:
        target = (UI_DIR / file_path).resolve()

    # Path traversal protection
    if not str(target).startswith(str(UI_DIR.resolve())):
        raise HTTPException(status_code=403, detail="Forbidden: Path traversal blocked")

    if target.is_dir() or not target.exists():
        target = UI_DIR / "index.html"

    mime_type, _ = mimetypes.guess_type(str(target))
    if str(target).endswith(".css"):
        mime_type = "text/css"
    elif str(target).endswith(".js"):
        mime_type = "application/javascript"
    elif str(target).endswith(".html"):
        mime_type = "text/html"
    elif str(target).endswith(".svg"):
        mime_type = "image/svg+xml"
    elif str(target).endswith(".json"):
        mime_type = "application/json"

    return Response(content=target.read_bytes(), media_type=mime_type or "application/octet-stream")

