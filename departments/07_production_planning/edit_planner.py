"""
Editing Blueprint and Existing Footage Assembly Service (Mode B).
Synthesizes structured editorial blueprints by mapping analyzed source footage moments
(from Part 03 shot boundaries) against reference video pacing and stylistic profiles.
Detects missing footage coverage and specifies generative or motion graphics remedies.
"""
from datetime import datetime, timezone
import logging
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from core.assets.intelligence_models import (
    ReferenceProfile,
    ShotRecord,
    TransitionType
)
from core.planning.planning_models import (
    EditShotMapping,
    EditingBlueprint,
    MissingCoverageItem,
    MissingCoverageSolution,
    PacingStyle
)

logger = logging.getLogger("studio.production_planning.edit_planner")

def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

class EditingBlueprintService:
    def __init__(self):
        pass

    def create_edit_blueprint(
        self,
        project_id: UUID,
        target_duration_sec: float,
        source_shots: List[Dict[str, Any]],
        ref_profile: Optional[ReferenceProfile] = None,
        instructions: str = ""
    ) -> EditingBlueprint:
        """
        Maps available source footage shots to the timeline according to reference rhythm,
        identifying exact source in/out timestamps and flagging missing coverage gaps.
        """
        # Determine pacing from reference or default
        if ref_profile:
            asl = ref_profile.editing_style.get("average_shot_length_sec", 2.5)
            pacing_name = ref_profile.editing_style.get("pacing", "DYNAMIC_BALANCED")
            try:
                pacing = PacingStyle(pacing_name)
            except ValueError:
                pacing = PacingStyle.FAST_PACED if asl <= 2.0 else PacingStyle.DYNAMIC_BALANCED
        else:
            asl = 2.5
            pacing = PacingStyle.DYNAMIC_BALANCED

        timeline_pos = 0.0
        mappings: List[EditShotMapping] = []
        missing_coverage: List[MissingCoverageItem] = []

        # Iterate over source shots and map to timeline
        for idx, shot in enumerate(source_shots):
            if timeline_pos >= target_duration_sec:
                break

            start_t = float(shot.get("start_sec", shot.get("start_time_sec", 0.0)))
            end_t = float(shot.get("end_sec", shot.get("end_time_sec", start_t + float(shot.get("duration_sec", 3.0)))))
            s_dur = max(0.1, end_t - start_t)
            # Clip duration to reference ASL window
            take_dur = min(s_dur, round(asl * 1.2, 2))
            if timeline_pos + take_dur > target_duration_sec:
                take_dur = round(target_duration_sec - timeline_pos, 2)

            t_in = round(timeline_pos, 2)
            t_out = round(timeline_pos + take_dur, 2)

            src_in = start_t
            src_out = round(src_in + take_dur, 2)

            mapping = EditShotMapping(
                mapping_id=uuid4(),
                timeline_in_sec=t_in,
                timeline_out_sec=t_out,
                source_asset_id=UUID(str(shot["asset_id"])),
                source_in_sec=src_in,
                source_out_sec=src_out,
                shot_purpose=f"Cut {idx + 1}: Dynamic action beat derived from Shot {shot.get('shot_number', idx + 1)}",
                transition_in=TransitionType.HARD_CUT if idx > 0 else TransitionType.FADE_FROM_BLACK,
                transition_out=TransitionType.HARD_CUT,
                color_treatment="Color grade matched to reference dominant palette",
                speed_ratio=1.0
            )
            mappings.append(mapping)
            timeline_pos = t_out

        # Detect Missing Coverage if source footage is insufficient for target duration
        if timeline_pos < target_duration_sec:
            gap_dur = round(target_duration_sec - timeline_pos, 2)
            missing = MissingCoverageItem(
                item_id=uuid4(),
                intended_timeline_sec=round(timeline_pos, 2),
                duration_sec=gap_dur,
                description=f"Coverage deficit of {gap_dur:.1f}s at end of timeline. Source footage exhausted.",
                recommended_solution=MissingCoverageSolution.AI_VIDEO_GENERATION,
                suggested_prompt="Cinematic closing hero shot matching lighting and mood of preceding footage."
            )
            missing_coverage.append(missing)

        # Plan audio, music, and motion graphics layers
        music_placement = [{
            "track_type": "MUSIC_BED",
            "start_timeline_sec": 0.0,
            "end_timeline_sec": target_duration_sec,
            "tempo_bpm": ref_profile.audio_style.get("estimated_bpm", 120.0) if ref_profile else 120.0,
            "volume_db": -12.0,
            "fade_in_sec": 0.5,
            "fade_out_sec": 1.5
        }]

        motion_graphics = [{
            "overlay_type": "LOWER_THIRD_TITLE",
            "start_timeline_sec": 1.0,
            "duration_sec": 3.5,
            "style": ref_profile.motion_graphics.get("typography_style", "Clean Minimal") if ref_profile else "Clean Minimal"
        }]

        return EditingBlueprint(
            blueprint_id=uuid4(),
            project_id=project_id,
            target_duration_sec=target_duration_sec,
            narrative_order=mappings,
            pacing_style=pacing,
            transitions=[{"type": "HARD_CUT", "count": max(0, len(mappings) - 1)}],
            music_placement=music_placement,
            dialogue_placement=[],
            sound_effects=[{"type": "TRANSITION_WHOOSH", "timeline_sec": 0.0}],
            motion_graphics=motion_graphics,
            missing_coverage=missing_coverage,
            version=1,
            created_at=utc_now_iso()
        )
