"""
Production Feasibility and Compute Cost Evaluation Engine.
Analyzes requested visual complexity, local hardware capabilities (Apple M4, 16GB RAM),
and cloud provider compute pricing with explicit uncertainty bounds.
"""
from datetime import datetime, timezone
import logging
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from core.planning.planning_models import (
    ComplexityCategory,
    PlannedShot,
    ProductionBreakdown,
    ProductionFeasibility,
    ProductionTaskType
)

logger = logging.getLogger("studio.production_planning.feasibility")

class ProductionFeasibilityService:
    def __init__(self):
        # Local workstation constraints (Apple M4, 16GB Unified RAM, ~41GB disk)
        self.max_local_model_weight_gb = 2.0
        self.available_ram_gb = 16.0
        self.available_disk_gb = 41.0

    def evaluate_feasibility(
        self,
        project_id: UUID,
        breakdown: ProductionBreakdown,
        shots: List[PlannedShot]
    ) -> ProductionFeasibility:
        """
        Evaluates production feasibility, computing cost ranges, local hardware compatibility,
        and flagging technical risks with actionable alternatives.
        """
        total_shots = len(shots)
        total_duration = sum(s.estimated_duration_sec for s in shots)
        ai_video_shots = breakdown.shots_by_type.get(ProductionTaskType.AI_VIDEO_GENERATION.value, 0)
        vfx_shots = breakdown.shots_by_type.get(ProductionTaskType.VFX_COMPOSITING.value, 0)
        mograph_shots = breakdown.shots_by_type.get(ProductionTaskType.MOTION_GRAPHICS_CREATION.value, 0)

        # 1. Complexity Categorization
        if total_shots > 20 or ai_video_shots > 12 or vfx_shots > 4:
            complexity = ComplexityCategory.HIGH
            feasibility_score = 0.75
        elif total_shots > 10 or ai_video_shots > 6:
            complexity = ComplexityCategory.MEDIUM
            feasibility_score = 0.88
        else:
            complexity = ComplexityCategory.LOW
            feasibility_score = 0.96

        # 2. Local Hardware Feasibility (Apple M4 Audit)
        local_feasibility = {
            "workstation": "Apple M4 (16GB RAM)",
            "audio_processing_compatible": True,  # faster-whisper int8 + SciPy < 500MB RAM
            "motion_graphics_compatible": True,   # Motion Canvas headless < 800MB RAM
            "video_cut_detection_compatible": True, # PySceneDetect < 300MB RAM
            "local_heavy_diffusion_permitted": False, # Exceeds 2GB disk limit
            "routing_recommendation": "Route heavy video diffusion (Wan2.1 / Kling / Runway) to Cloud APIs."
        }

        # 3. Cost Estimation with Uncertainty Intervals
        # Known costs: LLM creative planning tokens (~$0.01)
        known_cost = 0.01
        # Estimated costs: AI video generation ($0.035 - $0.055 per second)
        video_gen_sec = sum(
            s.estimated_duration_sec for s in shots
            if s.generation_requirements == ProductionTaskType.AI_VIDEO_GENERATION
        )
        min_video_cost = round(video_gen_sec * 0.035, 2)
        max_video_cost = round(video_gen_sec * 0.055, 2)
        uncertainty = round((max_video_cost - min_video_cost) * 0.5, 2)

        cost_range = {
            "min_usd": round(known_cost + min_video_cost, 2),
            "max_usd": round(known_cost + max_video_cost, 2),
            "known_cost_usd": round(known_cost, 2),
            "uncertainty_usd": uncertainty
        }

        # 4. Cloud Dependencies
        cloud_deps = []
        if ai_video_shots > 0:
            cloud_deps.append("Remote Cloud GPU Cluster (Runway Gen-3 / Kling 1.5 / Google Imagen Video API)")
        if any(s.narrative_purpose.lower().count("voice") for s in shots):
            cloud_deps.append("ElevenLabs Speech Synthesis API")

        # 5. Technical Risks & Recommended Alternatives
        risks = []
        alternatives = []
        if ai_video_shots > 8:
            risks.append(f"Generating {ai_video_shots} separate AI video shots increases risk of character/wardrobe drift.")
            alternatives.append("Consolidate adjacent shots into continuous camera takes or incorporate motion graphics overlays.")

        if total_duration > 90.0:
            risks.append("Long-form video generation (>90s) without live-action B-roll leads to high cloud compute expenditure.")
            alternatives.append("Interleave curated stock footage or interview talking heads with generative inserts.")

        return ProductionFeasibility(
            feasibility_id=uuid4(),
            project_id=project_id,
            overall_feasibility_score=feasibility_score,
            complexity_category=complexity,
            estimated_cost_range=cost_range,
            cloud_dependencies=cloud_deps,
            local_hardware_feasibility=local_feasibility,
            technical_risks=risks,
            recommended_alternatives=alternatives
        )
