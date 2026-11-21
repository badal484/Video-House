"""
Universal Media Ingestion Service.
Orchestrates validation, cryptographic hashing, storage preservation,
metadata extraction, asynchronous derivative generation, and asset registration.
"""
import asyncio
from datetime import datetime, timezone
import logging
from pathlib import Path
from typing import BinaryIO, Dict, List, Optional
from uuid import UUID, uuid4

from core.assets.database import (
    AssetDatabase,
    AssetRecord,
    AssetRole,
    MediaType,
    ProcessingStatus,
    TechnicalMetadata
)

def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
from core.media_validator import FormatDetectionResult, MediaValidator
from core.orchestration.job_queue import IngestionJobQueue
from core.security import MediaSecurityPolicy, SecurityError
from core.storage.storage_service import StorageService
from .derivative_generator import DerivativeGenerator
from .metadata_extractor import MetadataExtractor

logger = logging.getLogger("studio.ingestion_service")

class MediaIngestionService:
    def __init__(
        self,
        db: AssetDatabase,
        storage: StorageService,
        job_queue: IngestionJobQueue,
        extractor: Optional[MetadataExtractor] = None,
        generator: Optional[DerivativeGenerator] = None
    ):
        self.db = db
        self.storage = storage
        self.job_queue = job_queue
        self.extractor = extractor or MetadataExtractor()
        self.generator = generator or DerivativeGenerator(storage)

    async def import_local_file(
        self,
        project_id: UUID,
        source_path: Path,
        display_name: Optional[str] = None,
        roles: Optional[List[AssetRole]] = None,
        source_type: str = "LOCAL_IMPORT"
    ) -> AssetRecord:
        """
        Imports an existing local file into the project asset registry.
        Preserves original file safely, validates content, and enqueues async derivative generation.
        """
        source_path = source_path.resolve()
        if not source_path.exists() or not source_path.is_file():
            raise FileNotFoundError(f"Source file {source_path} does not exist.")

        filename = source_path.name
        safe_filename = MediaSecurityPolicy.sanitize_filename(filename)
        
        # 1. Content and Magic Signature Validation
        detection = MediaValidator.inspect_file(source_path, safe_filename)
        if not detection.is_valid:
            raise ValueError(f"File validation failed: {detection.validation_error}")

        # 2. Size limit validation
        byte_size = source_path.stat().st_size
        MediaSecurityPolicy.validate_file_size(byte_size, detection.media_type.value)

        # 3. Check for existing identical file in project
        prelim_hash, _ = self.storage.calculate_checksum_and_size(source_path)
        existing = self.db.find_by_checksum(project_id, prelim_hash)
        if existing:
            # If identical asset already exists, return existing
            logger.info(f"Duplicate asset detected with checksum {prelim_hash}. Returning existing asset {existing.asset_id}.")
            if roles:
                for r in roles:
                    self.db.add_asset_role(existing.asset_id, r)
            return self.db.get_asset(existing.asset_id) or existing

        # 4. Generate asset UUID and store original copy
        asset_id = uuid4()
        dest_path, checksum, final_size = self.storage.store_original_file(
            project_id=project_id,
            asset_id=asset_id,
            source_path=source_path,
            filename=safe_filename
        )

        # 5. Register in Database
        now = utc_now_iso()
        asset_record = AssetRecord(
            asset_id=asset_id,
            project_id=project_id,
            original_filename=filename,
            display_name=display_name or filename,
            media_type=detection.media_type,
            detected_format=detection.detected_format,
            mime_type=detection.mime_type,
            byte_size=final_size,
            checksum_sha256=checksum,
            storage_path=str(dest_path),
            import_timestamp=now,
            processing_status=ProcessingStatus.QUEUED,
            metadata_status=ProcessingStatus.QUEUED,
            derivative_status=ProcessingStatus.QUEUED,
            version=1,
            source_type=source_type,
            roles=roles or [AssetRole.SOURCE_FOOTAGE]
        )
        self.db.register_asset(asset_record)

        # 6. Enqueue Asynchronous Background Processing
        await self.job_queue.enqueue_job(
            asset_id=asset_id,
            job_type="INGESTION_DERIVATIVES",
            task_coro_fn=lambda: self.process_asset_derivatives(asset_id)
        )

        return asset_record

    async def import_stream(
        self,
        project_id: UUID,
        stream: BinaryIO,
        filename: str,
        display_name: Optional[str] = None,
        roles: Optional[List[AssetRole]] = None
    ) -> AssetRecord:
        """
        Streams uploaded binary data directly into project storage, then validates and processes.
        """
        safe_filename = MediaSecurityPolicy.sanitize_filename(filename)
        asset_id = uuid4()

        # 1. Stream write to project originals
        dest_path, checksum, byte_size = self.storage.store_stream_to_original(
            project_id=project_id,
            asset_id=asset_id,
            stream=stream,
            filename=safe_filename
        )

        # 2. Content validation
        detection = MediaValidator.inspect_file(dest_path, safe_filename)
        if not detection.is_valid:
            # Delete invalid file
            self.storage.delete_asset_files(project_id, asset_id, str(dest_path))
            raise ValueError(f"Uploaded file failed content inspection: {detection.validation_error}")

        # 3. Size validation
        try:
            MediaSecurityPolicy.validate_file_size(byte_size, detection.media_type.value)
        except SecurityError as se:
            self.storage.delete_asset_files(project_id, asset_id, str(dest_path))
            raise se

        # 4. Check for duplicate in project
        existing = self.db.find_by_checksum(project_id, checksum)
        if existing:
            self.storage.delete_asset_files(project_id, asset_id, str(dest_path))
            if roles:
                for r in roles:
                    self.db.add_asset_role(existing.asset_id, r)
            return self.db.get_asset(existing.asset_id) or existing

        # 5. Register in Database
        now = utc_now_iso()
        asset_record = AssetRecord(
            asset_id=asset_id,
            project_id=project_id,
            original_filename=filename,
            display_name=display_name or filename,
            media_type=detection.media_type,
            detected_format=detection.detected_format,
            mime_type=detection.mime_type,
            byte_size=byte_size,
            checksum_sha256=checksum,
            storage_path=str(dest_path),
            import_timestamp=now,
            processing_status=ProcessingStatus.QUEUED,
            metadata_status=ProcessingStatus.QUEUED,
            derivative_status=ProcessingStatus.QUEUED,
            version=1,
            source_type="UPLOAD",
            roles=roles or [AssetRole.SOURCE_FOOTAGE]
        )
        self.db.register_asset(asset_record)

        # 6. Enqueue Background Processing
        await self.job_queue.enqueue_job(
            asset_id=asset_id,
            job_type="INGESTION_DERIVATIVES",
            task_coro_fn=lambda: self.process_asset_derivatives(asset_id)
        )

        return asset_record

    async def process_asset_derivatives(self, asset_id: UUID) -> None:
        """
        Executes metadata extraction and derivative generation for an asset.
        Executed by the background worker.
        """
        asset = self.db.get_asset(asset_id)
        if not asset:
            logger.error(f"Asset {asset_id} not found for derivative processing.")
            return

        self.db.update_asset_status(
            asset_id=asset_id,
            processing_status=ProcessingStatus.PROCESSING,
            metadata_status=ProcessingStatus.PROCESSING,
            derivative_status=ProcessingStatus.PROCESSING
        )

        try:
            # 1. Metadata Extraction
            file_path = Path(asset.storage_path)
            meta = self.extractor.extract(file_path, asset.asset_id, asset.media_type)
            self.db.set_technical_metadata(meta)
            self.db.update_asset_status(asset_id=asset_id, metadata_status=ProcessingStatus.COMPLETED)

            # 2. Derivative Generation
            derivatives = self.generator.generate_derivatives(asset, meta)
            for d in derivatives:
                self.db.add_derivative(d)

            self.db.update_asset_status(
                asset_id=asset_id,
                processing_status=ProcessingStatus.COMPLETED,
                derivative_status=ProcessingStatus.COMPLETED
            )
            logger.info(f"Successfully processed {len(derivatives)} derivatives for asset {asset_id}.")

        except Exception as e:
            logger.error(f"Failed processing derivatives for asset {asset_id}: {e}", exc_info=True)
            self.db.update_asset_status(
                asset_id=asset_id,
                processing_status=ProcessingStatus.FAILED,
                error_message=str(e)
            )
            raise e

    async def retry_processing(self, asset_id: UUID) -> UUID:
        """Manually re-enqueues processing for an asset."""
        asset = self.db.get_asset(asset_id)
        if not asset:
            raise FileNotFoundError(f"Asset {asset_id} not found.")

        job_id = await self.job_queue.enqueue_job(
            asset_id=asset_id,
            job_type="INGESTION_DERIVATIVES_RETRY",
            task_coro_fn=lambda: self.process_asset_derivatives(asset_id)
        )
        return job_id

    def delete_asset(self, asset_id: UUID) -> bool:
        """
        Safely deletes an asset and its physical files if not locked by dependencies.
        """
        asset = self.db.get_asset(asset_id)
        if not asset:
            return False

        # Attempt DB deletion (enforcing foreign keys and dependency checks)
        deleted = self.db.delete_asset(asset_id)
        if deleted:
            # Delete physical files
            self.storage.delete_asset_files(asset.project_id, asset_id, asset.storage_path)
            return True
        return False
