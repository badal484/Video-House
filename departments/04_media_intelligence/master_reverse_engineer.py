"""
Master Multimodal Video Reverse Engineering Service.
Coordinates:
- Multi-resolution temporal sampling (5-pass engine).
- Shot detection and transition classification (20+ transition types).
- Cinematography, composition geometry, and 6-DoF camera motion.
- Motion graphics and kinetic typography tracking.
- Animation medium, cadence, and VFX layer decomposition.
- Advanced tri-band audio, beat grid, and SFX transient classification.
- Color grading, palette extraction, and vignette/LUT analysis.
- 5-phase narrative arc synthesis.
- Construction of the Unified Temporal Event Graph.
- Generation of the structured Reference Reconstruction Manifest.
"""
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID, uuid4

import cv2
import numpy as np

from core.assets.database import AssetDatabase
from core.assets.intelligence_models import (
    AnalysisProfile,
    CameraMotionType,
    EvidenceRecord,
    ReferenceProfile,
    ShotRecord,
    TimecodeRange,
    TransitionType
)
from core.intelligence.event_graph import (
    EventGraphNode,
    GraphEdgeType,
    GraphNodeType,
    TemporalEventGraph
)

from .animation_vfx import AnimationAndVFXIntelligenceEngine, VisualMediumAnalysis
from .audio_intelligence_v2 import AdvancedAudioIntelligenceEngine, AudioMasterIntelligenceResult
from .cinematography import CinematographyIntelligenceEngine, ShotCinematographyAnalysis
from .color_grading_intelligence import ColorGradingIntelligenceEngine, ColorGradingProfile
from .editing_intelligence import EditingIntelligenceEngine, EditorialRhythmProfile, TransitionDetail
from .motion_graphics_intelligence import MotionGraphicsReverseEngineeringEngine, TrackedGraphicElement
from .narrative_intelligence import NarrativePhase, StorytellingIntelligenceEngine, StorytellingProfile
from .shot_detector import ShotDetectionService
from .temporal_engine.normalization import MediaNormalizationService
from .temporal_engine.sampling_engine import HighResolutionTemporalSamplingEngine, MultiResolutionTimeline

logger = logging.getLogger("studio.master_reverse_engineer")

def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

@dataclass
class ReferenceReconstructionManifest:
    manifest_id: UUID = field(default_factory=uuid4)
    asset_id: UUID = field(default_factory=uuid4)
    video_title: str = "Reference Video"
    total_duration_sec: float = 0.0
    fps: float = 30.0
    aspect_ratio: str = "16:9"
    created_at: str = field(default_factory=utc_now_iso)
    visual_medium: VisualMediumAnalysis = field(default_factory=VisualMediumAnalysis)
    editorial_rhythm: EditorialRhythmProfile = field(default_factory=EditorialRhythmProfile)
    cinematography_shots: List[ShotCinematographyAnalysis] = field(default_factory=list)
    transitions: List[TransitionDetail] = field(default_factory=list)
    motion_graphics_elements: List[TrackedGraphicElement] = field(default_factory=list)
    audio_intelligence: AudioMasterIntelligenceResult = field(default_factory=AudioMasterIntelligenceResult)
    color_grading: ColorGradingProfile = field(default_factory=ColorGradingProfile)
    storytelling: StorytellingProfile = field(default_factory=StorytellingProfile)
    contradictions_detected: List[str] = field(default_factory=list)
    overall_confidence: float = 0.95
    event_graph_summary: Dict[str, Any] = field(default_factory=dict)

class MasterVideoReverseEngineeringService:
    def __init__(
        self,
        db: Optional[AssetDatabase] = None,
        normalizer: Optional[MediaNormalizationService] = None,
        sampling_engine: Optional[HighResolutionTemporalSamplingEngine] = None,
        shot_detector: Optional[ShotDetectionService] = None,
        cinematography: Optional[CinematographyIntelligenceEngine] = None,
        editing_engine: Optional[EditingIntelligenceEngine] = None,
        motion_graphics: Optional[MotionGraphicsReverseEngineeringEngine] = None,
        animation_vfx: Optional[AnimationAndVFXIntelligenceEngine] = None,
        audio_engine: Optional[AdvancedAudioIntelligenceEngine] = None,
        color_engine: Optional[ColorGradingIntelligenceEngine] = None,
        narrative_engine: Optional[StorytellingIntelligenceEngine] = None
    ):
        self.db = db
        self.normalizer = normalizer or MediaNormalizationService()
        self.sampling_engine = sampling_engine or HighResolutionTemporalSamplingEngine(self.normalizer)
        self.shot_detector = shot_detector or ShotDetectionService()
        self.cinematography = cinematography or CinematographyIntelligenceEngine()
        self.editing_engine = editing_engine or EditingIntelligenceEngine()
        self.motion_graphics = motion_graphics or MotionGraphicsReverseEngineeringEngine()
        self.animation_vfx = animation_vfx or AnimationAndVFXIntelligenceEngine()
        self.audio_engine = audio_engine or AdvancedAudioIntelligenceEngine()
        self.color_engine = color_engine or ColorGradingIntelligenceEngine()
        self.narrative_engine = narrative_engine or StorytellingIntelligenceEngine()

    def reverse_engineer_video(
        self,
        video_path: Path,
        asset_id: UUID,
        video_title: str = "Reference Video"
    ) -> Tuple[ReferenceReconstructionManifest, TemporalEventGraph]:
        """
        Executes deep end-to-end multimodal video reverse engineering.
        Produces the ReferenceReconstructionManifest and the Unified Temporal Event Graph.
        """
        video_path = video_path.resolve()
        if not video_path.exists():
            raise FileNotFoundError(f"Video file not found: {video_path}")

        logger.info(f"Initiating Master Reverse Engineering on {video_path.name} (asset {asset_id})...")

        # 1. Media Normalization & Probing
        media_info = self.normalizer.probe_media(video_path)
        fps = media_info["fps"]
        duration = media_info["duration_seconds"]

        # 2. Shot and Cut Boundary Detection
        shots = self.shot_detector.detect_shots(video_path, asset_id, fps=fps)
        cut_timestamps = [s.timecode_range.start_seconds for s in shots[1:]]

        # 3. High-Resolution Temporal Sampling (5-pass engine)
        timeline = self.sampling_engine.execute_multi_pass_analysis(
            video_path, asset_id, known_cut_timestamps=cut_timestamps
        )

        # 4. Audio Extraction & Signal Intelligence
        audio_path = self.normalizer.extract_analysis_audio(video_path)
        if audio_path and audio_path.exists():
            audio_intel = self.audio_engine.analyze_audio_stream(
                audio_path, asset_id, video_cut_timestamps=cut_timestamps
            )
            self.normalizer.cleanup_artifacts(audio_path)
        else:
            audio_intel = AudioMasterIntelligenceResult()

        # 5. Editing Rhythm & Transition Classification
        cap = cv2.VideoCapture(str(video_path))
        transitions: List[TransitionDetail] = []
        if cap.isOpened():
            for i, shot in enumerate(shots[:-1]):
                next_shot = shots[i + 1]
                cut_frame = next_shot.timecode_range.start_frame
                tr_detail = self.editing_engine.classify_transition(cap, cut_frame, fps)
                tr_detail.from_shot_number = shot.shot_number
                tr_detail.to_shot_number = next_shot.shot_number
                transitions.append(tr_detail)
            cap.release()

        editorial_rhythm = self.editing_engine.analyze_editorial_rhythm(
            shots=shots,
            total_duration_sec=duration,
            music_beat_timestamps=audio_intel.beat_timestamps
        )

        # 6. Cinematography Intelligence (Per Shot Keyframe)
        cinematography_shots: List[ShotCinematographyAnalysis] = []
        for shot in shots:
            mid_sec = (shot.timecode_range.start_seconds + shot.timecode_range.end_seconds) / 2.0
            mid_frame = int(round(mid_sec * fps))

            # Retrieve inspected keyframe from Pass D or extract frame
            kf_path = timeline.inspected_keyframe_paths.get(mid_frame)
            if kf_path and Path(kf_path).exists():
                kf_img = cv2.imread(kf_path)
            else:
                cap_temp = cv2.VideoCapture(str(video_path))
                cap_temp.set(cv2.CAP_PROP_POS_FRAMES, mid_frame)
                ret, kf_img = cap_temp.read()
                cap_temp.release()
                if not ret:
                    kf_img = np.zeros((360, 640, 3), dtype=np.uint8)

            c_analysis = self.cinematography.analyze_shot_cinematography(
                keyframe=kf_img,
                shot_number=shot.shot_number,
                timecode_range=shot.timecode_range
            )
            cinematography_shots.append(c_analysis)

        # 7. Motion Graphics & Kinetic Typography Reverse Engineering
        motion_graphics_elements = self.motion_graphics.track_and_reconstruct_elements(
            video_path, fps=fps, sample_step=max(2, int(round(fps * 0.15)))
        )

        # 8. Animation Medium & VFX Layer Decomposition
        visual_medium = self.animation_vfx.analyze_visual_medium_and_vfx(video_path, fps=fps)

        # 9. Color Grading & Finishing Profile
        color_grading = self.color_engine.analyze_color_finish(video_path)

        # 10. Storytelling Narrative Arc Synthesis
        storytelling = self.narrative_engine.analyze_narrative_arc(
            duration_sec=duration,
            shots_count=len(shots),
            asl_sec=editorial_rhythm.average_shot_length_sec
        )

        # 11. Build Unified Temporal Event Graph
        event_graph = TemporalEventGraph(asset_id=asset_id, title=f"Event Graph - {video_title}")

        # Add Video Root Node
        root_node = EventGraphNode(
            node_id=f"video_root_{asset_id}",
            node_type=GraphNodeType.VIDEO,
            label=f"Video Root: {video_title}",
            start_seconds=0.0,
            end_seconds=duration,
            attributes={
                "fps": fps,
                "duration": duration,
                "aspect_ratio": media_info["aspect_ratio"],
                "visual_medium": visual_medium.visual_medium
            },
            evidence_provider="master_reverse_engineer"
        )
        event_graph.add_node(root_node)

        # Add Narrative Phase Nodes
        for p_idx, phase in enumerate(storytelling.narrative_phases, start=1):
            p_node = EventGraphNode(
                node_id=f"narrative_phase_{p_idx}_{asset_id}",
                node_type=GraphNodeType.NARRATIVE_EVENT,
                label=f"Narrative: {phase.phase_name}",
                start_seconds=phase.timecode_range.start_seconds,
                end_seconds=phase.timecode_range.end_seconds,
                attributes={
                    "role": phase.narrative_role,
                    "intensity": phase.emotional_intensity,
                    "retention_hook": phase.retention_hook
                },
                evidence_provider="StorytellingIntelligenceEngine"
            )
            event_graph.add_node(p_node)
            event_graph.add_edge(root_node.node_id, p_node.node_id, GraphEdgeType.CONTAINS)

        # Add Shot Nodes & Cinematography
        for s_idx, (shot, c_shot) in enumerate(zip(shots, cinematography_shots), start=1):
            s_node = EventGraphNode(
                node_id=f"shot_{s_idx}_{asset_id}",
                node_type=GraphNodeType.SHOT,
                label=f"Shot {shot.shot_number} [{c_shot.shot_scale.value}]",
                start_seconds=shot.timecode_range.start_seconds,
                end_seconds=shot.timecode_range.end_seconds,
                attributes={
                    "shot_scale": c_shot.shot_scale.value,
                    "camera_angle": c_shot.camera_angle.value,
                    "camera_motion": c_shot.camera_motion.value,
                    "rot_adherence": c_shot.composition.rule_of_thirds_adherence,
                    "symmetry": c_shot.composition.symmetry_score,
                    "lighting_style": c_shot.lighting.lighting_style,
                    "color_temperature_k": c_shot.lighting.estimated_color_temperature_kelvin
                },
                evidence_provider="CinematographyIntelligenceEngine"
            )
            event_graph.add_node(s_node)
            event_graph.add_edge(root_node.node_id, s_node.node_id, GraphEdgeType.CONTAINS)

        # Add Transition Nodes
        for t_idx, tr in enumerate(transitions, start=1):
            t_node = EventGraphNode(
                node_id=f"transition_{t_idx}_{asset_id}",
                node_type=GraphNodeType.TRANSITION,
                label=f"Transition: {tr.transition_type}",
                start_seconds=tr.start_seconds,
                end_seconds=tr.end_seconds,
                attributes={
                    "type": tr.transition_type,
                    "duration_sec": tr.duration_seconds,
                    "from_shot": tr.from_shot_number,
                    "to_shot": tr.to_shot_number
                },
                evidence_provider="EditingIntelligenceEngine"
            )
            event_graph.add_node(t_node)
            event_graph.add_edge(root_node.node_id, t_node.node_id, GraphEdgeType.CONTAINS)

        # Add Graphic & Typography Nodes
        for g_idx, elem in enumerate(motion_graphics_elements, start=1):
            g_node = EventGraphNode(
                node_id=f"graphic_{g_idx}_{asset_id}",
                node_type=GraphNodeType.GRAPHIC_ELEMENT,
                label=f"Graphic: {elem.element_type} ({elem.typography.text_hierarchy})",
                start_seconds=elem.timecode_range.start_seconds,
                end_seconds=elem.timecode_range.end_seconds,
                attributes={
                    "element_type": elem.element_type,
                    "entry_animation": elem.motion_behavior.entry_animation,
                    "easing": elem.motion_behavior.easing_curve,
                    "primary_color": elem.typography.primary_color_hex,
                    "font_class": elem.typography.font_family_class,
                    "weight": elem.typography.estimated_weight,
                    "initial_box": asdict(elem.initial_bounding_box)
                },
                evidence_provider="MotionGraphicsReverseEngineeringEngine"
            )
            event_graph.add_node(g_node)
            event_graph.add_edge(root_node.node_id, g_node.node_id, GraphEdgeType.CONTAINS)

        # Add Audio Event Nodes (Music, SFX)
        for sfx_idx, sfx in enumerate(audio_intel.detected_sfx, start=1):
            a_node = EventGraphNode(
                node_id=f"audio_sfx_{sfx_idx}_{asset_id}",
                node_type=GraphNodeType.AUDIO_EVENT,
                label=f"SFX: {sfx.sfx_type}",
                start_seconds=sfx.start_seconds,
                end_seconds=sfx.end_seconds,
                attributes={
                    "sfx_type": sfx.sfx_type,
                    "intensity": sfx.intensity,
                    "coincides_with_cut": sfx.coincides_with_video_cut
                },
                evidence_provider="AdvancedAudioIntelligenceEngine"
            )
            event_graph.add_node(a_node)
            event_graph.add_edge(root_node.node_id, a_node.node_id, GraphEdgeType.CONTAINS)

        # Compute cross-modal edges (PRECEDES, OVERLAPS, SYNCHRONIZED_WITH)
        event_graph.auto_connect_temporal_edges()

        # Audit contradictions between models
        contradictions = []
        if visual_medium.is_vector_flat_art and color_grading.film_grain_level == "HEAVY_16MM":
            contradictions.append("Contradiction: Flat vector artwork classified alongside heavy 16mm film grain.")
        if editorial_rhythm.average_shot_length_sec < 1.0 and editorial_rhythm.editorial_grammar == "SLOW_CINEMATIC":
            contradictions.append("Contradiction: Rapid ASL <1.0s conflicting with SLOW_CINEMATIC editorial classification.")

        # Build Manifest
        manifest = ReferenceReconstructionManifest(
            manifest_id=uuid4(),
            asset_id=asset_id,
            video_title=video_title,
            total_duration_sec=round(duration, 2),
            fps=fps,
            aspect_ratio=media_info["aspect_ratio"],
            visual_medium=visual_medium,
            editorial_rhythm=editorial_rhythm,
            cinematography_shots=cinematography_shots,
            transitions=transitions,
            motion_graphics_elements=motion_graphics_elements,
            audio_intelligence=audio_intel,
            color_grading=color_grading,
            storytelling=storytelling,
            contradictions_detected=contradictions,
            overall_confidence=0.95 if not contradictions else 0.88,
            event_graph_summary=event_graph.to_dict()
        )

        # Persist into database if available
        if self.db:
            try:
                self.db.save_shots(shots)
                ref_profile = ReferenceProfile(
                    profile_id=uuid4(),
                    asset_id=asset_id,
                    name=video_title,
                    created_at=utc_now_iso(),
                    visual_style={
                        "dominant_palette_hex": color_grading.dominant_palette_hex,
                        "color_harmony": color_grading.color_harmony_type,
                        "lighting": cinematography_shots[0].lighting.lighting_style if cinematography_shots else "BALANCED",
                        "lut": color_grading.recommended_lut
                    },
                    editing_style={
                        "average_shot_length_sec": float(editorial_rhythm.average_shot_length_sec),
                        "cut_frequency_cpm": float(editorial_rhythm.cuts_per_minute),
                        "pacing": str(editorial_rhythm.cutting_pace_category),
                        "grammar": str(editorial_rhythm.editorial_grammar)
                    },
                    motion_graphics={
                        "tracked_elements_count": int(len(motion_graphics_elements)),
                        "palette": [str(x) for x in color_grading.dominant_palette_hex[:3]]
                    },
                    audio_style={
                        "tempo_bpm": float(audio_intel.tempo_bpm),
                        "integrated_lufs": float(audio_intel.energy_profile.integrated_lufs)
                    },
                    narrative_arc={
                        "structure": str(storytelling.story_structure),
                        "hook_duration_sec": float(storytelling.hook_duration_sec)
                    },
                    key_moments=[
                        {
                            "shot_number": s.shot_number,
                            "timestamp": s.timecode_range.start_time,
                            "scale": s.shot_scale.value
                        }
                        for s in cinematography_shots[:8]
                    ]
                )
                self.db.save_reference_profile(ref_profile)
            except Exception as e:
                logger.warning(f"Could not persist reference profile to DB: {e}")

        logger.info(f"Master Reverse Engineering completed for {video_title} with {len(event_graph.nodes)} graph nodes.")
        return manifest, event_graph
