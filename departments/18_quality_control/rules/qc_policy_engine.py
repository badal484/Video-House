"""
QC Policy Engine for Department 18.
Evaluates accumulated defects against profile-specific acceptance policies.
"""
from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from ..core.models import QCDefect, QCPolicy, QCReport, QCSeverity


class QCPolicyEngine:
    """Evaluates defects against quality policy rules and produces the final QCReport."""

    DEFAULT_POLICIES = {
        "STRICT_BROADCAST": QCPolicy(
            policy_id="STRICT_BROADCAST",
            name="Strict Broadcast Acceptance (Zero Error/Critical)",
            target_profile_type="BROADCAST",
            max_allowed_warnings=0,
            strict_mode=True,
        ),
        "STREAMING_STANDARD": QCPolicy(
            policy_id="STREAMING_STANDARD",
            name="Streaming Standard Acceptance",
            target_profile_type="SOCIAL",
            max_allowed_warnings=3,
            strict_mode=False,
        ),
        "ARCHIVAL_PRESERVATION": QCPolicy(
            policy_id="ARCHIVAL_PRESERVATION",
            name="Archival Preservation Strict Mode",
            target_profile_type="ARCHIVAL",
            max_allowed_warnings=1,
            strict_mode=True,
        ),
    }

    @classmethod
    def compile_report(
        cls,
        project_id: UUID,
        asset_id: UUID,
        defects: List[QCDefect],
        policy_name: str = "STREAMING_STANDARD",
        render_job_id: Optional[UUID] = None,
    ) -> QCReport:
        """Compiles defect list into a structured QCReport."""
        policy = cls.DEFAULT_POLICIES.get(policy_name, cls.DEFAULT_POLICIES["STREAMING_STANDARD"])

        critical_count = sum(1 for d in defects if d.severity == QCSeverity.CRITICAL)
        error_count = sum(1 for d in defects if d.severity == QCSeverity.ERROR)
        warning_count = sum(1 for d in defects if d.severity == QCSeverity.WARNING)
        info_count = sum(1 for d in defects if d.severity == QCSeverity.INFO)

        # Pass condition: zero critical, zero error, warnings <= allowed
        passed = (critical_count == 0) and (error_count == 0)
        if policy.strict_mode and warning_count > policy.max_allowed_warnings:
            passed = False

        return QCReport(
            project_id=project_id,
            asset_id=asset_id,
            render_job_id=render_job_id,
            passed=passed,
            total_issues=len(defects),
            critical_count=critical_count,
            error_count=error_count,
            warning_count=warning_count,
            info_count=info_count,
            defects=defects,
        )
