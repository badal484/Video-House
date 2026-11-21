"""
Subtitle Validator for Department 18.
Audits subtitle and caption files for reading speed (CPS), line length (CPL), and overlaps.
"""
from __future__ import annotations

from typing import Any, Dict, List
from ..core.models import QCCheckType, QCDefect, QCSeverity


class SubtitleValidator:
    """Audits subtitle tracks and sidecars against broadcast standards."""

    MAX_CPS_ADULT = 17.0
    MAX_CPL_LATIN = 42

    @classmethod
    def audit_cues(
        cls,
        cues: List[Dict[str, Any]],
        max_cps: float = MAX_CPS_ADULT,
        max_cpl: int = MAX_CPL_LATIN,
    ) -> List[QCDefect]:
        """Audits subtitle cue dictionaries for technical readability defects."""
        defects: List[QCDefect] = []

        for idx, cue in enumerate(cues):
            start_t = float(cue.get("start_time", 0.0))
            end_t = float(cue.get("end_time", 0.0))
            text = str(cue.get("text", ""))
            cue_num = cue.get("cue_index", idx + 1)
            duration = max(0.01, end_t - start_t)

            # 1. Overlap check
            if idx > 0:
                prev_end = float(cues[idx - 1].get("end_time", 0.0))
                if start_t < prev_end:
                    defects.append(
                        QCDefect(
                            check_type=QCCheckType.SUBTITLE,
                            severity=QCSeverity.ERROR,
                            rule_name="subtitle_overlap",
                            description=f"Cue {cue_num} start ({start_t:.2f}s) overlaps with preceding cue end ({prev_end:.2f}s).",
                            timestamp_sec=start_t,
                            remediation_suggestion="Adjust cue start time to maintain minimum 2-frame gap.",
                        )
                    )

            # 2. Duration check
            if duration < 0.833:
                defects.append(
                    QCDefect(
                        check_type=QCCheckType.SUBTITLE,
                        severity=QCSeverity.WARNING,
                        rule_name="subtitle_min_duration",
                        description=f"Cue {cue_num} duration ({duration:.2f}s) is shorter than 0.833s minimum.",
                        timestamp_sec=start_t,
                    )
                )

            # 3. Line length check
            lines = text.split("\n")
            if len(lines) > 2:
                defects.append(
                    QCDefect(
                        check_type=QCCheckType.SUBTITLE,
                        severity=QCSeverity.ERROR,
                        rule_name="subtitle_max_lines",
                        description=f"Cue {cue_num} exceeds 2 lines ({len(lines)} lines detected).",
                        timestamp_sec=start_t,
                    )
                )

            for line in lines:
                if len(line) > max_cpl:
                    defects.append(
                        QCDefect(
                            check_type=QCCheckType.SUBTITLE,
                            severity=QCSeverity.ERROR,
                            rule_name="subtitle_max_cpl",
                            description=f"Cue {cue_num} line length ({len(line)} chars) exceeds maximum {max_cpl}.",
                            timestamp_sec=start_t,
                        )
                    )

            # 4. CPS check
            cps = len(text.replace("\n", " ")) / duration
            if cps > max_cps:
                defects.append(
                    QCDefect(
                        check_type=QCCheckType.SUBTITLE,
                        severity=QCSeverity.WARNING,
                        rule_name="subtitle_reading_speed",
                        description=f"Cue {cue_num} reading speed ({cps:.1f} CPS) exceeds {max_cps} CPS limit.",
                        timestamp_sec=start_t,
                    )
                )

        return defects
