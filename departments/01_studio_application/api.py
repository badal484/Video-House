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

# ---------------------------------------------------------
# Lifecycle & Dependency Wiring
# ---------------------------------------------------------
db = AssetDatabase("projects/studio_asset_registry.db")
storage = StorageService("assets", "temp")
job_queue = IngestionJobQueue(db, max_concurrent_workers=4)
ingestion_service = MediaIngestionService(db, storage, job_queue)

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
