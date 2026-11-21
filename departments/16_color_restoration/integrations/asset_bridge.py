"""
Asset Database Bridge for Department 16.
Registers non-destructive color-graded and restored media derivatives in the Central Asset Database (Part 21).
"""
import json
from typing import Any, Dict, Optional
from uuid import UUID, uuid4
from core.assets.database import AssetDatabase


class AssetStoreBridge:
    """
    Commits restored media outputs to central persistent asset storage.
    """

    def __init__(self, db: Optional[AssetDatabase] = None):
        self.db = db or AssetDatabase()

    def register_restored_derivative(
        self,
        project_id: UUID,
        source_asset_id: UUID,
        derivative_path: str,
        file_size: int,
        checksum: str,
        restoration_metadata: Dict[str, Any]
    ) -> UUID:
        """
        Creates an asset derivative record linking the graded/restored output to its original asset.
        """
        derivative_id = uuid4()
        with self.db.get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO derivatives (
                    derivative_id, asset_id, derivative_type, storage_path,
                    byte_size, mime_type, generation_params_json, created_at, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, ?)
                """,
                (
                    str(derivative_id),
                    str(source_asset_id),
                    "RESTORED_MASTER",
                    derivative_path,
                    file_size,
                    "video/mp4",
                    json.dumps(restoration_metadata),
                    "READY"
                )
            )
        return derivative_id
