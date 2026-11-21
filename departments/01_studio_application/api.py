"""
REST API and Web Services for the Universal AI Video Production Studio.
Exposes project management, media upload, local import, metadata retrieval,
derivative access, asset role management, and asynchronous job monitoring.
"""
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Dict, List, Optional
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
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field

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
from core.planning.planning_models import (
    ApprovalStatus,
    PlanningEntityType,
    ProductionType,
    PacingStyle
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

@app.get("/api/v1/projects/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: UUID):
    proj = db.get_project(project_id)
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found.")
    return proj

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


