"""
Creative Brief Interpretation and Ingestion Service.
Transforms raw user ideas, prompts, or partial specifications into structured,
schema-validated CreativeBrief instances with explicit assumption tracking.
"""
from datetime import datetime, timezone
import logging
import re
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID, uuid4

from core.planning.planning_models import (
    CreativeBrief,
    PacingStyle,
    ProductionType
)

logger = logging.getLogger("studio.creative_direction.brief")

def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

class CreativeBriefService:
    def __init__(self):
        pass

    def parse_brief(
        self,
        project_id: UUID,
        raw_input: Dict[str, Any]
    ) -> Tuple[CreativeBrief, List[str]]:
        """
        Parses raw text or structured parameters into a validated CreativeBrief.
        Returns the brief and a list of recommended clarification questions if essential data is missing.
        """
        prompt = raw_input.get("prompt", "") or raw_input.get("description", "")
        project_name = raw_input.get("project_name", "Untitled Production")
        if not project_name or project_name == "Untitled Production":
            # Heuristic: Extract first 4 words of prompt
            words = prompt.split()[:4]
            if words:
                project_name = " ".join(words).title()

        assumptions: List[str] = []
        clarification_questions: List[str] = []

        # 1. Infer Production Type
        production_type = self._infer_production_type(prompt, raw_input, assumptions)

        # 2. Target Duration
        duration_sec = self._infer_duration(prompt, raw_input, assumptions)

        # 3. Platform & Technical Specifications
        platform = raw_input.get("intended_platform")
        if not platform:
            if "youtube" in prompt.lower():
                platform = "YouTube"
            elif any(w in prompt.lower() for w in ["tiktok", "reel", "shorts", "vertical"]):
                platform = "TikTok / Instagram Reels"
            else:
                platform = "Web / Broad Commercial"
                assumptions.append("Default platform set to Web / Broad Commercial (16:9 landscape).")

        aspect_ratio = raw_input.get("aspect_ratio")
        if not aspect_ratio:
            if platform in ["TikTok / Instagram Reels", "Shorts"]:
                aspect_ratio = "9:16"
                resolution = "1080x1920"
            else:
                aspect_ratio = "16:9"
                resolution = "1920x1080"
        else:
            resolution = raw_input.get("resolution", "1920x1080")

        # 4. Genre & Tone
        genre = raw_input.get("genre")
        if not genre:
            genre = self._infer_genre(prompt)
            assumptions.append(f"Inferred genre: {genre}")

        # 5. Core Message & Objective
        purpose = raw_input.get("purpose", "")
        if not purpose:
            purpose = f"Produce a compelling {production_type.value.lower().replace('_', ' ')} communicating: {prompt[:120]}"

        # 6. Check for Essential Missing Coverage
        if not raw_input.get("target_duration_sec") and not re.search(r'(\d+)\s*[-]?\s*(?:sec|second|min|minute|s)\b', prompt, re.IGNORECASE):
            clarification_questions.append("What is your desired target duration in seconds (e.g. 15s, 30s, 60s)?")

        if len(prompt.split()) < 10:
            clarification_questions.append("Could you elaborate on the core message, narrative arc, or product hook?")
            clarification_questions.append("Who is your primary target audience and what is the desired emotional takeaway?")
            clarification_questions.append("Do you have specific visual references, color palettes, or pacing preferences?")

        if not prompt and not raw_input.get("core_message"):
            clarification_questions.append("What is the primary message or narrative hook of the video?")

        # 7. Color Palette & Aesthetic Direction
        visual_style = raw_input.get("visual_style", "Cinematic Realism")
        pacing_style = self._infer_pacing_style(prompt, raw_input)

        brief = CreativeBrief(
            brief_id=uuid4(),
            project_id=project_id,
            project_name=project_name,
            production_type=production_type,
            genre=genre,
            target_duration_sec=duration_sec,
            intended_platform=platform,
            aspect_ratio=aspect_ratio,
            resolution=resolution,
            fps=float(raw_input.get("fps", 24.0)),
            language=raw_input.get("language", "en"),
            target_audience=raw_input.get("target_audience", "General audience"),
            purpose=purpose,
            core_message=raw_input.get("core_message", prompt[:200]),
            desired_audience_response=raw_input.get("desired_audience_response", "Engagement and emotional resonance"),
            call_to_action=raw_input.get("call_to_action"),
            emotional_objective=raw_input.get("emotional_objective", "Captivation and trust"),
            narrative_objective=raw_input.get("narrative_objective", "Clear problem-to-solution journey"),
            visual_style=visual_style,
            cinematography=raw_input.get("cinematography", "Dynamic, intentional camera movement"),
            lighting_style=raw_input.get("lighting_style", "High contrast with dramatic rim highlights"),
            color_palette=raw_input.get("color_palette", ["#0D1117", "#161B22", "#58A6FF", "#F0883E"]),
            pacing_style=pacing_style,
            typography_style=raw_input.get("typography_style", "Modern geometric sans-serif"),
            sound_design_notes=raw_input.get("sound_design_notes", "Spatial sound effects with clear dynamic transitions"),
            music_direction=raw_input.get("music_direction", "Cinematic instrumental with driving rhythm"),
            available_footage_ids=[UUID(str(x)) for x in raw_input.get("available_footage_ids", [])],
            reference_asset_ids=[UUID(str(x)) for x in raw_input.get("reference_asset_ids", [])],
            budget_tier=raw_input.get("budget_tier", "STANDARD"),
            model_restrictions=raw_input.get("model_restrictions", []),
            exclusions=raw_input.get("exclusions", []),
            assumptions=assumptions,
            created_at=utc_now_iso(),
            version=1
        )

        return brief, clarification_questions

    def _infer_production_type(
        self, prompt: str, raw_input: Dict[str, Any], assumptions: List[str]
    ) -> ProductionType:
        if raw_input.get("production_type"):
            try:
                return ProductionType(raw_input["production_type"])
            except ValueError:
                pass

        p_lower = prompt.lower()
        if any(w in p_lower for w in ["ad", "advertisement", "commercial", "promo"]):
            return ProductionType.COMMERCIAL
        elif any(w in p_lower for w in ["short film", "cinematic film", "movie"]):
            return ProductionType.SHORT_FILM
        elif any(w in p_lower for w in ["faceless", "reddit", "text-to-video"]):
            return ProductionType.FACELESS_CONTENT
        elif any(w in p_lower for w in ["anime", "manga style"]):
            return ProductionType.ANIME
        elif any(w in p_lower for w in ["2d animation", "cartoon", "grease pencil"]):
            return ProductionType.ANIMATION_2D
        elif any(w in p_lower for w in ["3d animation", "cgi", "blender"]):
            return ProductionType.ANIMATION_3D
        elif any(w in p_lower for w in ["explainer", "saas", "infographic"]):
            return ProductionType.EXPLAINER
        elif any(w in p_lower for w in ["motion graphics", "kinetic typography"]):
            return ProductionType.MOTION_GRAPHICS
        elif any(w in p_lower for w in ["vfx", "cgi composite"]):
            return ProductionType.VFX_SEQUENCE
        elif any(w in p_lower for w in ["music video", "track promo"]):
            return ProductionType.MUSIC_VIDEO

        assumptions.append("Defaulted production type to COMMERCIAL based on project scope.")
        return ProductionType.COMMERCIAL

    def _infer_duration(
        self, prompt: str, raw_input: Dict[str, Any], assumptions: List[str]
    ) -> float:
        if raw_input.get("target_duration_sec"):
            return float(raw_input["target_duration_sec"])

        # Regex scan for patterns like "45-second", "30s", "1 minute"
        match_sec = re.search(r'(\d+)\s*[-]?\s*(?:sec|second|s)\b', prompt, re.IGNORECASE)
        if match_sec:
            return float(match_sec.group(1))

        match_min = re.search(r'(\d+)\s*[-]?\s*(?:min|minute)\b', prompt, re.IGNORECASE)
        if match_min:
            return float(match_min.group(1)) * 60.0

        assumptions.append("Inferred standard target duration: 30.0 seconds.")
        return 30.0

    def _infer_genre(self, prompt: str) -> str:
        p_lower = prompt.lower()
        if any(w in p_lower for w in ["electric car", "automotive", "vehicle", "luxury"]):
            return "Automotive & Luxury"
        elif any(w in p_lower for w in ["tech", "software", "ai", "hardware", "cyber"]):
            return "Technology & Innovation"
        elif any(w in p_lower for w in ["fashion", "apparel", "beauty"]):
            return "Fashion & Lifestyle"
        elif any(w in p_lower for w in ["action", "thriller", "suspense"]):
            return "Action & Thriller"
        elif any(w in p_lower for w in ["comedy", "humor", "funny"]):
            return "Comedy & Entertainment"
        return "Commercial / Editorial"

    def _infer_pacing_style(self, prompt: str, raw_input: Dict[str, Any]) -> PacingStyle:
        if raw_input.get("pacing_style"):
            try:
                return PacingStyle(raw_input["pacing_style"])
            except ValueError:
                pass
        p_lower = prompt.lower()
        if any(w in p_lower for w in ["fast", "rapid", "energetic", "punchy", "tiktok"]):
            return PacingStyle.FAST_PACED
        elif any(w in p_lower for w in ["slow", "contemplative", "ambient", "meditative"]):
            return PacingStyle.CALM_CONTEMPLATIVE
        elif any(w in p_lower for w in ["rhythmic", "beat", "montage"]):
            return PacingStyle.RHYTHMIC_MONTAGE
        return PacingStyle.DYNAMIC_BALANCED
