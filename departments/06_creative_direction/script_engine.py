"""
Script and Narrative Engine.
Generates structured screenplays and commercial scripts with scene breakdowns,
dialogue entries, voiceover direction, and algorithmic speech duration estimation.
"""
from datetime import datetime, timezone
import logging
import math
import re
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from core.planning.planning_models import (
    CreativeBrief,
    CreativeConcept,
    DialogueEntry,
    DialogueType,
    ProductionScript,
    ScriptScene
)

logger = logging.getLogger("studio.creative_direction.script")

def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

class ScriptAndNarrativeService:
    def __init__(self, default_words_per_minute: float = 140.0):
        # 140 WPM is standard professional broadcast narration speed (~2.33 words/second)
        self.wpm = default_words_per_minute

    def generate_script(
        self,
        brief: CreativeBrief,
        concept: Optional[CreativeConcept] = None
    ) -> ProductionScript:
        """
        Synthesizes a structured screenplay/script aligned with the target duration and concept.
        """
        target_dur = brief.target_duration_sec
        title = brief.project_name
        logline = f"A {brief.genre.lower()} piece capturing '{brief.core_message[:100]}'."

        # Compute optimal number of scenes based on target duration and pacing
        if target_dur <= 15.0:
            scene_count = 2
        elif target_dur <= 30.0:
            scene_count = 3
        elif target_dur <= 60.0:
            scene_count = 4
        else:
            scene_count = max(4, int(target_dur / 18.0))

        sec_per_scene = target_dur / scene_count
        scenes: List[ScriptScene] = []
        script_id = uuid4()

        # Scene 1: The Hook / Opening Intrigue
        sc1_dur = round(sec_per_scene * 0.9, 1)
        sc1 = ScriptScene(
            scene_id=uuid4(),
            script_id=script_id,
            scene_number=1,
            title="The Opening Hook",
            slugline=f"EXT. {brief.genre.upper()} WORLD - NIGHT",
            narrative_purpose="Immediate attention capture; establish mood and central intrigue.",
            location="Atmospheric landscape",
            time_of_day="Night",
            characters_present=["Subject"],
            action_description="Darkness gives way to subtle ambient reflections. A silhouette emerges through rolling mist.",
            dialogue_entries=[
                DialogueEntry(
                    entry_id=uuid4(),
                    speaker="NARRATOR",
                    text=f"Everything changes when silence speaks.",
                    entry_type=DialogueType.VOICEOVER,
                    estimated_duration_sec=self.estimate_speech_duration("Everything changes when silence speaks."),
                    emotional_direction="Quiet authority, low whisper"
                )
            ],
            emotional_tone="Mysterious anticipation",
            estimated_duration_sec=sc1_dur,
            continuity_notes="Initial lighting must remain low-key to allow reveal in Scene 2."
        )
        scenes.append(sc1)

        # Scene 2: The Escalation / Core Reveal
        sc2_dur = round(sec_per_scene * 1.1, 1)
        sc2 = ScriptScene(
            scene_id=uuid4(),
            script_id=script_id,
            scene_number=2,
            title="The Ignition & Reveal",
            slugline=f"EXT. {brief.genre.upper()} HIGHWAY - CONTINUOUS",
            narrative_purpose="Introduce hero subject, demonstrate dynamic power and emotional core.",
            location="Open highway / Dynamic stage",
            time_of_day="Night to Dawn",
            characters_present=["Subject", "Environment"],
            action_description="Headlights slice through darkness. Acceleration pushes forward as precision surfaces catch light.",
            dialogue_entries=[
                DialogueEntry(
                    entry_id=uuid4(),
                    speaker="NARRATOR",
                    text=f"Built without compromise. Designed to move you beyond ordinary boundaries.",
                    entry_type=DialogueType.VOICEOVER,
                    estimated_duration_sec=self.estimate_speech_duration("Built without compromise. Designed to move you beyond ordinary boundaries."),
                    emotional_direction="Confident, inspiring, dynamic"
                )
            ],
            emotional_tone="Exhilarating power",
            estimated_duration_sec=sc2_dur,
            continuity_notes="Vehicle speed and direction must track left-to-right across cuts."
        )
        scenes.append(sc2)

        # Scene 3: Climax & Resolution / Call to Action
        sc3_dur = round(target_dur - (sc1_dur + sc2_dur), 1)
        if scene_count == 3:
            sc3 = ScriptScene(
                scene_id=uuid4(),
                script_id=script_id,
                scene_number=3,
                title="Climax & Call to Action",
                slugline=f"EXT. HORIZON SUMMIT - DAWN",
                narrative_purpose="Resolve narrative journey, deliver memorable brand payoff and CTA.",
                location="Scenic overlook / Horizon",
                time_of_day="Golden Dawn",
                characters_present=["Subject"],
                action_description="Vehicle glides to a stop overlooking a brilliant sunrise. Clean kinetic logo locks into center frame.",
                dialogue_entries=[
                    DialogueEntry(
                        entry_id=uuid4(),
                        speaker="NARRATOR",
                        text=brief.call_to_action or f"The future is here. Experience the new standard.",
                        entry_type=DialogueType.VOICEOVER,
                        estimated_duration_sec=self.estimate_speech_duration(brief.call_to_action or "The future is here. Experience the new standard."),
                        emotional_direction="Triumphant, resonant"
                    )
                ],
                emotional_tone="Aspirational resolution",
                estimated_duration_sec=sc3_dur,
                continuity_notes="Warm golden lighting directly contrasts opening cool shadows."
            )
            scenes.append(sc3)
        else:
            # Handle 4+ scenes for longer productions
            for idx in range(3, scene_count + 1):
                is_last = (idx == scene_count)
                dur = round(sc3_dur / (scene_count - 2), 1)
                sc_extra = ScriptScene(
                    scene_id=uuid4(),
                    script_id=script_id,
                    scene_number=idx,
                    title="Brand Climax & Payoff" if is_last else f"Movement {idx}: Deepening the Core",
                    slugline=f"INT/EXT. {brief.genre.upper()} - SCENE {idx}",
                    narrative_purpose="Deliver closing brand payoff" if is_last else "Showcase interior craftsmanship and human experience.",
                    location="Contemporary architecture / Scenic Vista",
                    time_of_day="Dawn" if is_last else "Daylight",
                    characters_present=["Subject"],
                    action_description="Refined textures and human touchpoints in harmonious motion." if not is_last else "Dynamic hero framing with lockup typography.",
                    dialogue_entries=[
                        DialogueEntry(
                            entry_id=uuid4(),
                            speaker="NARRATOR",
                            text=brief.call_to_action or f"Define your horizon today." if is_last else f"Crafted with perfection in every single detail.",
                            entry_type=DialogueType.VOICEOVER,
                            estimated_duration_sec=self.estimate_speech_duration("Crafted with perfection in every detail."),
                            emotional_direction="Warm, authoritative"
                        )
                    ],
                    emotional_tone="Triumphant" if is_last else "Focus",
                    estimated_duration_sec=dur,
                    continuity_notes="Maintain consistent color palette and character wardrobe."
                )
                scenes.append(sc_extra)

        # Calculate word counts and spoken durations
        all_text = " ".join(d.text for s in scenes for d in s.dialogue_entries)
        total_words = len(re.findall(r'\b\w+\b', all_text))
        total_spoken_sec = sum(d.estimated_duration_sec for s in scenes for d in s.dialogue_entries)

        return ProductionScript(
            script_id=script_id,
            project_id=brief.project_id,
            title=title,
            logline=logline,
            target_duration_sec=target_dur,
            estimated_spoken_duration_sec=round(total_spoken_sec, 2),
            total_words=total_words,
            scenes=scenes,
            version=1,
            created_at=utc_now_iso()
        )

    def estimate_speech_duration(self, text: str) -> float:
        """
        Estimates speaking duration for dialogue or voiceover using WPM heuristics and pause models.
        """
        words = re.findall(r'\b\w+\b', text)
        word_count = len(words)
        if word_count == 0:
            return 0.0

        # Base speech time: words / (WPM / 60)
        base_sec = word_count / (self.wpm / 60.0)

        # Add natural pause time for punctuation marks (commas: 0.25s, periods/colons: 0.45s)
        commas = text.count(',') + text.count(';')
        periods = text.count('.') + text.count('!') + text.count('?')
        pause_sec = (commas * 0.25) + (periods * 0.45)

        return round(base_sec + pause_sec, 2)
