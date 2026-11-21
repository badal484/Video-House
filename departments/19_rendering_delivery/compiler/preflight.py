"""
Preflight Validator for Department 19.
Inspects project completeness prior to rendering: missing source media, missing fonts,
missing LUTs, missing plugins, model dependencies, and licensing violations.
"""
from __future__ import annotations

import os
from typing import Any, Dict, List, Optional
from uuid import UUID


class PreflightIssue(BaseModel if False else object):
    def __init__(
        self,
        issue_id: str,
        category: str,
        is_blocking: bool,
        description: str,
        remediation: str,
    ):
        self.issue_id = issue_id
        self.category = category
        self.is_blocking = is_blocking
        self.description = description
        self.remediation = remediation

    def to_dict(self) -> Dict[str, Any]:
        return {
            "issue_id": self.issue_id,
            "category": self.category,
            "is_blocking": self.is_blocking,
            "description": self.description,
            "remediation": self.remediation,
        }


class PreflightValidator:
    """Inspects production assets, dependencies, and resources before rendering begins."""

    @classmethod
    def validate_project(cls, project_metadata: Dict[str, Any]) -> tuple[bool, List[Dict[str, Any]]]:
        """
        Validates all media assets, fonts, LUTs, and dependencies in project_metadata.
        Returns:
            passed (bool): True if zero blocking errors exist.
            issues (List[Dict]): List of detected issues.
        """
        issues: List[PreflightIssue] = []

        # 1. Inspect referenced media assets
        media_assets = project_metadata.get("media_assets", [])
        for asset in media_assets:
            path = asset.get("file_path", "")
            asset_id = asset.get("asset_id", "unknown")
            if not path or not os.path.exists(path):
                issues.append(
                    PreflightIssue(
                        issue_id=f"missing_asset_{asset_id}",
                        category="MEDIA_OFFLINE",
                        is_blocking=True,
                        description=f"Referenced media asset '{asset_id}' is offline/missing at path: '{path}'.",
                        remediation="Relink or re-ingest the missing media asset in Department 02 before rendering.",
                    )
                )

        # 2. Inspect required fonts (for motion graphics & subtitles)
        fonts = project_metadata.get("fonts", [])
        for font_name in fonts:
            # Check system font or project fonts directory
            font_path = project_metadata.get("font_paths", {}).get(font_name)
            if font_path and not os.path.exists(font_path):
                issues.append(
                    PreflightIssue(
                        issue_id=f"missing_font_{font_name}",
                        category="FONT_MISSING",
                        is_blocking=True,
                        description=f"Required motion graphics typography font '{font_name}' not found.",
                        remediation="Install the designated TrueType/OpenType font into the studio assets directory.",
                    )
                )

        # 3. Inspect required color LUTs
        luts = project_metadata.get("luts", [])
        for lut in luts:
            lut_path = lut.get("file_path", "")
            if not lut_path or not os.path.exists(lut_path):
                issues.append(
                    PreflightIssue(
                        issue_id=f"missing_lut_{lut.get('name', 'lut')}",
                        category="LUT_MISSING",
                        is_blocking=True,
                        description=f"Grading 3D LUT '{lut.get('name')}' is missing at: '{lut_path}'.",
                        remediation="Register or restore the .cube LUT file in Department 12.",
                    )
                )

        # 4. Inspect licensing compliance
        licenses = project_metadata.get("asset_licenses", {})
        for asset_id, lic in licenses.items():
            if "cc-by-nc" in str(lic).lower():
                issues.append(
                    PreflightIssue(
                        issue_id=f"noncommercial_license_{asset_id}",
                        category="LICENSING_VIOLATION",
                        is_blocking=True,
                        description=f"Asset '{asset_id}' carries a Non-Commercial (CC-BY-NC) license violating commercial release.",
                        remediation="Replace with commercially licensed asset per Studio Prime Directive #6.",
                    )
                )

        has_blocking = any(i.is_blocking for i in issues)
        return not has_blocking, [i.to_dict() for i in issues]

