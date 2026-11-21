"""
Structured Prompt Compiler & Provider Adapters
Department 15: 15_ai_generation
"""
from __future__ import annotations

import re
from typing import Dict, List, Optional, Tuple
from pydantic import BaseModel, Field

from ..core.generation_models import GenerationModality


class StructuredPromptDimensions(BaseModel):
    subject: str
    character_identity: Optional[str] = None
    environment: Optional[str] = None
    action: Optional[str] = None
    composition: Optional[str] = None
    camera_movement: Optional[str] = None
    lens: Optional[str] = None
    lighting: Optional[str] = None
    visual_style: Optional[str] = None
    mood: Optional[str] = None
    color_palette: Optional[str] = None
    time_of_day: Optional[str] = None
    weather: Optional[str] = None
    aspect_ratio: str = "16:9"
    negative_constraints: Optional[str] = None


class PromptCompiler:
    """Compiles structured creative dimensions into provider-optimized prompt payloads."""

    DEFAULT_NEGATIVE_VIDEO = "blurry, low quality, warped anatomy, extra limbs, distorted face, flickering, watermark, bad hands"
    DEFAULT_NEGATIVE_IMAGE = "low resolution, deformed, bad anatomy, bad hands, missing fingers, extra digits, text, watermark, signature"

    @classmethod
    def compile_for_provider(
        cls,
        dimensions: StructuredPromptDimensions,
        provider_id: str,
        modality: GenerationModality = GenerationModality.TEXT_TO_VIDEO,
    ) -> Tuple[str, str]:
        """
        Compiles dimensions into provider-specific (positive_prompt, negative_prompt).
        """
        p_id = provider_id.lower()

        # 1. Runway Gen-3 Syntax
        if "runway" in p_id:
            positive = cls._compile_runway(dimensions, modality)
            negative = dimensions.negative_constraints or cls.DEFAULT_NEGATIVE_VIDEO
            return positive, negative

        # 2. Kling AI Syntax
        elif "kling" in p_id:
            positive = cls._compile_kling(dimensions, modality)
            negative = dimensions.negative_constraints or cls.DEFAULT_NEGATIVE_VIDEO
            return positive, negative

        # 3. FLUX.1 Natural Prose Syntax
        elif "flux" in p_id:
            positive = cls._compile_flux(dimensions)
            negative = dimensions.negative_constraints or cls.DEFAULT_NEGATIVE_IMAGE
            return positive, negative

        # 4. Midjourney Style Syntax
        elif "midjourney" in p_id:
            positive = cls._compile_midjourney(dimensions)
            negative = dimensions.negative_constraints or "--no blurry, deformed, watermark"
            return positive, negative

        # 5. Audio / Music / Speech
        elif modality in (GenerationModality.TEXT_TO_SPEECH, GenerationModality.TEXT_TO_SOUND, GenerationModality.TEXT_TO_MUSIC):
            positive = cls._compile_audio(dimensions, modality)
            return positive, ""

        # Generic Default
        positive = cls._compile_generic(dimensions)
        negative = dimensions.negative_constraints or cls.DEFAULT_NEGATIVE_VIDEO
        return positive, negative

    @staticmethod
    def _compile_runway(d: StructuredPromptDimensions, modality: GenerationModality) -> str:
        parts = []
        # Camera Bracket
        cam_elements = []
        if d.camera_movement:
            cam_elements.append(d.camera_movement)
        if d.composition:
            cam_elements.append(d.composition)
        if d.lens:
            cam_elements.append(d.lens)
        if cam_elements:
            parts.append(f"[Camera: {', '.join(cam_elements)}]")

        # Subject and Identity
        subject_str = d.subject
        if d.character_identity:
            subject_str = f"{d.subject} ({d.character_identity})"
        parts.append(subject_str)

        # Action & Environment
        if d.action:
            parts.append(d.action)
        if d.environment:
            env_full = d.environment
            if d.time_of_day:
                env_full += f", {d.time_of_day}"
            if d.weather:
                env_full += f", {d.weather}"
            parts.append(f"in {env_full}")

        # Lighting & Style
        if d.lighting:
            parts.append(f"Lighting: {d.lighting}")
        if d.visual_style:
            parts.append(d.visual_style)
        if d.color_palette:
            parts.append(f"{d.color_palette} color grade")

        return ". ".join(parts) + "."

    @staticmethod
    def _compile_kling(d: StructuredPromptDimensions, modality: GenerationModality) -> str:
        parts = []
        # Subject & Action
        subj = f"{d.subject} {d.character_identity or ''}".strip()
        if d.action:
            parts.append(f"{subj} is {d.action}")
        else:
            parts.append(f"A clear cinematic shot of {subj}")

        if d.environment:
            parts.append(f"set in {d.environment}")
        if d.composition:
            parts.append(d.composition)
        if d.camera_movement:
            parts.append(f"camera {d.camera_movement}")
        if d.lighting:
            parts.append(f"illuminated with {d.lighting}")
        if d.visual_style:
            parts.append(d.visual_style)

        return ", ".join(parts)

    @staticmethod
    def _compile_flux(d: StructuredPromptDimensions) -> str:
        prose = []
        subj = f"{d.subject}"
        if d.character_identity:
            subj += f", featuring {d.character_identity}"
        prose.append(f"A high-fidelity photograph of {subj}")

        if d.action:
            prose.append(f"{d.action}")
        if d.environment:
            env = d.environment
            if d.time_of_day:
                env += f" during {d.time_of_day}"
            if d.weather:
                env += f" with {d.weather}"
            prose.append(f"in {env}")

        if d.composition or d.lens:
            shot_desc = ", ".join(filter(None, [d.composition, d.lens]))
            prose.append(f"Captured in a {shot_desc}")

        if d.lighting:
            prose.append(f"The scene features {d.lighting}")
        if d.color_palette or d.visual_style:
            style = ", ".join(filter(None, [d.visual_style, d.color_palette]))
            prose.append(f"Rendered in {style}")

        return ". ".join(prose) + "."

    @staticmethod
    def _compile_midjourney(d: StructuredPromptDimensions) -> str:
        tokens = [d.subject]
        if d.character_identity:
            tokens.append(d.character_identity)
        if d.action:
            tokens.append(d.action)
        if d.environment:
            tokens.append(d.environment)
        if d.composition:
            tokens.append(d.composition)
        if d.lens:
            tokens.append(d.lens)
        if d.lighting:
            tokens.append(d.lighting)
        if d.visual_style:
            tokens.append(d.visual_style)
        if d.color_palette:
            tokens.append(d.color_palette)
        
        ar_param = f"--ar {d.aspect_ratio}" if d.aspect_ratio else "--ar 16:9"
        return f"{', '.join(tokens)} {ar_param} --v 6.1 --style raw"

    @staticmethod
    def _compile_audio(d: StructuredPromptDimensions, modality: GenerationModality) -> str:
        if modality == GenerationModality.TEXT_TO_MUSIC:
            return f"Musical score: {d.subject}. Mood: {d.mood or 'cinematic'}. Style: {d.visual_style or 'orchestral'}."
        elif modality == GenerationModality.TEXT_TO_SOUND:
            return f"Sound effect of {d.subject}, {d.action or ''}".strip()
        return d.subject

    @staticmethod
    def _compile_generic(d: StructuredPromptDimensions) -> str:
        elements = [d.subject, d.action, d.environment, d.composition, d.lighting, d.visual_style]
        return ", ".join(filter(None, elements))

    @classmethod
    def parse_freeform_prompt(cls, raw_text: str) -> StructuredPromptDimensions:
        """Heuristic extractor parsing natural language text into structured dimensions."""
        # Detect camera movements
        cam_match = re.search(r"\b(pan|tilt|zoom|dolly|tracking|orbit|close[- ]up|wide shot|medium shot)\b", raw_text, re.IGNORECASE)
        cam = cam_match.group(0) if cam_match else None

        # Detect time of day
        tod_match = re.search(r"\b(day|night|dusk|dawn|sunset|sunrise|midnight|afternoon)\b", raw_text, re.IGNORECASE)
        tod = tod_match.group(0) if tod_match else None

        # Clean subject
        subject = raw_text.strip()
        return StructuredPromptDimensions(
            subject=subject,
            camera_movement=cam,
            time_of_day=tod,
        )
