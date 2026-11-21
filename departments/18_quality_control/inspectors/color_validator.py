"""
Color and HDR Validator for Department 18.
Verifies NCLX metadata tags, transfer characteristics, and HDR MaxCLL/MaxFALL values.
"""
from __future__ import annotations

from typing import List, Optional
from ..core.models import QCCheckType, QCDefect, QCSeverity


class ColorValidator:
    """Validates color primaries, transfer functions, and HDR mastering metadata."""

    @classmethod
    def validate_color_metadata(
        cls,
        actual_primaries: str,
        actual_transfer: str,
        actual_matrix: str,
        expected_primaries: str = "bt709",
        expected_transfer: str = "bt709",
        expected_matrix: str = "bt709",
    ) -> List[QCDefect]:
        """Validates NCLX color metadata tags."""
        defects: List[QCDefect] = []

        if actual_primaries.lower() != expected_primaries.lower():
            defects.append(
                QCDefect(
                    check_type=QCCheckType.COLOR,
                    severity=QCSeverity.ERROR,
                    rule_name="color_primaries_conformance",
                    description=f"Color primaries tag '{actual_primaries}' does not match expected '{expected_primaries}'.",
                    remediation_suggestion=f"Re-tag container with: -color_primaries {expected_primaries}.",
                )
            )

        if actual_transfer.lower() != expected_transfer.lower():
            defects.append(
                QCDefect(
                    check_type=QCCheckType.COLOR,
                    severity=QCSeverity.ERROR,
                    rule_name="transfer_characteristics_conformance",
                    description=f"Transfer curve '{actual_transfer}' does not match expected '{expected_transfer}'.",
                    remediation_suggestion=f"Re-tag container with: -color_trc {expected_transfer}.",
                )
            )

        return defects

    @classmethod
    def validate_hdr_metadata(
        cls,
        is_hdr: bool,
        max_cll: Optional[int] = None,
        max_fall: Optional[int] = None,
        max_permitted_cll: int = 1000,
    ) -> List[QCDefect]:
        """Validates HDR10 mastering and content light levels."""
        defects: List[QCDefect] = []
        if not is_hdr:
            return defects

        if max_cll is None or max_fall is None:
            defects.append(
                QCDefect(
                    check_type=QCCheckType.COLOR,
                    severity=QCSeverity.WARNING,
                    rule_name="hdr_metadata_present",
                    description="HDR stream missing MaxCLL / MaxFALL content light level metadata.",
                    remediation_suggestion="Inject mastering display metadata via x265 or MP4Box tags.",
                )
            )
        elif max_cll > max_permitted_cll:
            defects.append(
                QCDefect(
                    check_type=QCCheckType.COLOR,
                    severity=QCSeverity.WARNING,
                    rule_name="max_cll_limit",
                    description=f"MaxCLL ({max_cll} nits) exceeds mastering target ({max_permitted_cll} nits).",
                    remediation_suggestion="Apply highlight roll-off or tone-mapping curve in Department 12.",
                )
            )

        return defects
