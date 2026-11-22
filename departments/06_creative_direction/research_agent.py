"""
AI Creative Research Agent.
Department: 06_creative_direction
Decomposes video brief, script, and storyboard into multi-query asset research plans.
"""
from typing import Any, Dict, List, Optional
from uuid import UUID

from departments.media_ingestion.discovery.models import (
    AssetResearchPlan, AssetResearchPlanItem, ResourceMediaType, ResourceQuery
)


class CreativeResearchAgent:
    """
    Dedicated AI agent analyzing creative intent to formulate
    scene-by-scene external creative asset acquisition plans.
    """

    def __init__(self):
        pass

    def generate_research_plan(
        self,
        project_id: str,
        topic: str,
        script_scenes: List[Dict[str, Any]],
        visual_style: str = "Cinematic Natural History Documentary",
        target_aspect_ratio: str = "9:16",
        target_fps: float = 30.0
    ) -> AssetResearchPlan:
        """
        Translates script scenes and storyboard requirements into structured search plans.
        """
        plan_items: List[AssetResearchPlanItem] = []

        for idx, scene in enumerate(script_scenes, start=1):
            title = scene.get("title", f"Scene {idx}")
            duration = float(scene.get("duration_seconds", 6.0))
            description = scene.get("description", "")
            media_type = ResourceMediaType(scene.get("required_media_type", "video"))
            intent = scene.get("intent", "visual_foundation")
            subject = scene.get("subject", topic)
            framing = scene.get("framing", "close_up")

            # Generate multi-variant targeted queries
            queries = self._formulate_queries(topic, subject, framing, scene.get("keywords", []))
            taxonomic = self._extract_taxonomic_terms(topic, description)

            plan_items.append(AssetResearchPlanItem(
                scene_index=idx,
                scene_title=title,
                scene_duration_seconds=duration,
                intent=intent,
                required_media_type=media_type,
                queries=queries,
                taxonomic_terms=taxonomic,
                preferred_framing=framing,
                technical_constraints={
                    "aspect_ratio": target_aspect_ratio,
                    "min_resolution": "1080p",
                    "min_framerate": target_fps
                }
            ))

        return AssetResearchPlan(
            project_id=project_id,
            title=topic,
            style_direction=visual_style,
            target_aspect_ratio=target_aspect_ratio,
            target_fps=target_fps,
            total_scenes=len(plan_items),
            items=plan_items
        )

    def _formulate_queries(
        self,
        topic: str,
        subject: str,
        framing: str,
        keywords: List[str]
    ) -> List[str]:
        queries = []
        base = subject if subject else topic

        if framing == "macro":
            queries.append(f"{base} macro close-up underwater")
            queries.append(f"{base} tentacles suckers high resolution")
        elif framing == "wide":
            queries.append(f"{base} swimming open ocean wide")
            queries.append(f"underwater coral reef marine life {base}")
        elif framing == "cutaway" or "anatom" in framing.lower():
            queries.append(f"{base} internal anatomy diagram hearts")
            queries.append(f"cephalopod circulatory system branchial heart")
        else:
            queries.append(f"{base} underwater video footage")
            queries.append(f"{base} natural habitat locomotion")

        for kw in keywords[:2]:
            queries.append(f"{base} {kw}")

        return queries

    def _extract_taxonomic_terms(self, topic: str, description: str) -> List[str]:
        corpus = f"{topic} {description}".lower()
        terms = []
        if "octopus" in corpus or "ऑक्टोपस" in corpus:
            terms.extend(["Octopus vulgaris", "Cephalopoda", "Octopodidae", "Mollusca"])
        if "heart" in corpus or "दिल" in corpus:
            terms.extend(["branchial heart", "systemic heart", "hemocyanin"])
        if "reef" in corpus or "समुद्र" in corpus:
            terms.extend(["coral reef", "benthic zone"])
        return terms
