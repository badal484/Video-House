"""
Creative Concept Development Service.
Generates multiple materially distinct, high-level creative directions from a CreativeBrief,
allowing users to compare, select, or combine stylistic and narrative paradigms.
"""
from datetime import datetime, timezone
import logging
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from core.planning.planning_models import (
    ComplexityCategory,
    CreativeBrief,
    CreativeConcept,
    ProductionType
)

logger = logging.getLogger("studio.creative_direction.concepts")

def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

class ConceptGenerationService:
    def __init__(self):
        pass

    def generate_concepts(
        self,
        brief: CreativeBrief,
        count: int = 3
    ) -> List[CreativeConcept]:
        """
        Produces at least 3 distinct creative concepts tailored to the brief's objectives and constraints.
        """
        concepts: List[CreativeConcept] = []
        name_prefix = brief.project_name

        # Concept 1: Cinematic Dramatic Storytelling
        c1 = CreativeConcept(
            concept_id=uuid4(),
            project_id=brief.project_id,
            name=f"{name_prefix}: The Cinematic Journey",
            creative_premise=(
                f"An evocative narrative centering on atmosphere, emotional build-up, and a dramatic reveal. "
                f"Focuses on sensory details and character connection to highlight: {brief.core_message[:80]}."
            ),
            narrative_approach="Three-act micro-narrative: Atmospheric mystery, inciting discovery, breathtaking climax.",
            visual_treatment="Anamorphic widescreen bokeh, low-key moody chiaroscuro lighting, deep shadows with warm rim highlights.",
            cinematography_style="Slow deliberate dolly push-ins, majestic crane reveals, shallow depth of field (f/1.4).",
            color_direction="Cool teal and charcoal environment contrasted by rich amber and gold practical lights.",
            sound_direction="Sparse ambient soundscape building into a swelling hybrid orchestral score with low brass crescendos.",
            editing_rhythm="Paced, deliberate cutting (ASL ~3.5s) allowing visual atmosphere to breathe.",
            motion_graphics_style="Minimalist tracking titles integrated seamlessly into 3D camera space.",
            production_complexity=ComplexityCategory.MEDIUM,
            estimated_generation_requirements={
                "video_generation_shots": 6,
                "image_generation_frames": 2,
                "vfx_compositing_shots": 1,
                "audio_tracks": 3
            },
            risks_and_limitations=[
                "Requires high visual fidelity in low-light shadow rendering.",
                "Pacing must not feel sluggish during the opening 5 seconds."
            ],
            is_selected=True,  # Default recommended concept
            created_at=utc_now_iso()
        )
        concepts.append(c1)

        # Concept 2: High-Energy Kinetic Commercial / Rhythmic Montage
        c2 = CreativeConcept(
            concept_id=uuid4(),
            project_id=brief.project_id,
            name=f"{name_prefix}: Kinetic Velocity",
            creative_premise=(
                f"A relentless, high-octane sensory assault. Slices of extreme action, dynamic speed-ramps, "
                f"and bold typography synchronize directly to a heavy rhythmic pulse."
            ),
            narrative_approach="Montage of impact: Immediate hook, rhythmic escalation, sensory crescendo, punchy CTA.",
            visual_treatment="High-saturation commercial finish, lens flares, motion blur, and sharp high-frequency textures.",
            cinematography_style="Fast whip pans, dynamic tracking vehicle cams, Dutch tilts, and rapid macro close-ups.",
            color_direction="Punchy high-contrast grade, electric blue highlights with fiery magenta accents.",
            sound_direction="Heavy percussion, rhythmic riser sweeps, sub-bass drops, and sharp foley impacts.",
            editing_rhythm="Rapid-fire sync-to-beat cutting (ASL ~1.2s) with speed ramps and whip transitions.",
            motion_graphics_style="Bold kinetic typography with glitch accents, animated text masking, and metric badges.",
            production_complexity=ComplexityCategory.HIGH,
            estimated_generation_requirements={
                "video_generation_shots": 12,
                "motion_graphics_layers": 8,
                "vfx_compositing_shots": 4,
                "audio_tracks": 5
            },
            risks_and_limitations=[
                "Dense cut frequency requires tight audio-visual synchronization.",
                "Can overwhelm viewers if core messaging is not clearly grounded."
            ],
            is_selected=False,
            created_at=utc_now_iso()
        )
        concepts.append(c2)

        # Concept 3: Minimalist Technical Precision / Architectural Elegance
        c3 = CreativeConcept(
            concept_id=uuid4(),
            project_id=brief.project_id,
            name=f"{name_prefix}: Engineered Perfection",
            creative_premise=(
                f"Sleek architectural deconstruction emphasizing craft, engineering tolerances, and refined luxury. "
                f"Every frame is treated as a high-art design exhibition."
            ),
            narrative_approach="Curated gallery showcase: Macro craftsmanship, structural elegance, refined holistic reveal.",
            visual_treatment="Clean studio lighting, soft diffused reflections, geometric balance, pristine surfaces.",
            cinematography_style="Orthographic sliding axes, slow rotational turntable movements, locked macro inspection.",
            color_direction="Monochrome matte graphite and titanium base with singular vibrant accent color.",
            sound_direction="Refined acoustic foley: mechanical clicks, smooth motor hums, and crisp ASMR foley.",
            editing_rhythm="Smooth mathematical transitions (ASL ~4.0s) matching continuous geometric lines.",
            motion_graphics_style="Precision technical blueprint overlays, fine HUD lines, and measured callouts.",
            production_complexity=ComplexityCategory.LOW,
            estimated_generation_requirements={
                "video_generation_shots": 5,
                "motion_graphics_layers": 4,
                "3d_animation_passes": 2,
                "audio_tracks": 2
            },
            risks_and_limitations=[
                "Demands pristine edge sharpness and reflection cleanliness.",
                "Requires careful pacing to maintain emotional warmth."
            ],
            is_selected=False,
            created_at=utc_now_iso()
        )
        concepts.append(c3)

        return concepts[:count]

