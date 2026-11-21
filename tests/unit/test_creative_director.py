"""
Comprehensive Unit and Integration Test Suite for Part 04:
AI Director, Creative Reasoning & Production Planning Engine.

Tests:
1. CreativeBriefService (interpretation, default inferences, assumptions, questions)
2. ConceptGenerationService (3 distinct concepts, scoring, selection)
3. ScriptAndNarrativeService (screenplay structure, narrative arcs, speech duration estimation)
4. CinematographyShotPlanner (shot decomposition, lenses, camera motion, lighting)
5. StoryboardPlanningService (frame generation, generative prompt crafting, compositions)
6. ReferenceStyleInterpreter (style transfer from Part 03 ReferenceProfile, IP guardrails)
7. ProductionBreakdownService (dependency DAG, task categorization, departmental routing)
8. EditingBlueprintService (Mode B: source footage mapping, exact in/out, coverage gap detection)
9. ProductionFeasibilityService (Apple M4 hardware checks, remote GPU dispatch, cost bounds)
10. WorldContinuityService (characters, environments, continuity rule violation audits)
11. ProductionBlueprintManager (master blueprint assembly, human approval gates)
12. AssetDatabase Planning Persistence (full CRUD across 11 planning tables)
"""
import asyncio
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from uuid import UUID, uuid4

from core.assets.database import (
    AssetDatabase,
    AssetRecord,
    AssetRole,
    MediaType,
    ProcessingStatus
)
from core.assets.intelligence_models import (
    CameraAngle,
    CameraMotionType,
    ReferenceProfile,
    ShotRecord,
    ShotScale,
    TimecodeRange,
    TransitionType
)
from core.planning.planning_models import (
    ApprovalStatus,
    CharacterProfile,
    ComplexityCategory,
    ContinuityRule,
    ContinuityRuleType,
    CreativeApproval,
    CreativeBrief,
    CreativeConcept,
    DialogueEntry,
    DialogueType,
    EditingBlueprint,
    EditShotMapping,
    EnvironmentProfile,
    MissingCoverageItem,
    MissingCoverageSolution,
    PacingStyle,
    PlannedShot,
    PlanningEntityType,
    ProductionBlueprint,
    ProductionBreakdown,
    ProductionFeasibility,
    ProductionScript,
    ProductionTask,
    ProductionTaskType,
    ProductionType,
    PropEntity,
    ScriptScene,
    StoryboardFrame
)

from departments.creative_direction.brief_interpreter import CreativeBriefService
from departments.creative_direction.concept_generator import ConceptGenerationService
from departments.creative_direction.director_service import CreativeDirectorService
from departments.creative_direction.script_engine import ScriptAndNarrativeService
from departments.creative_direction.shot_planner import CinematographyShotPlanner
from departments.creative_direction.storyboard_planner import StoryboardPlanningService
from departments.creative_direction.style_interpreter import (
    ReferenceMatchingDegree,
    ReferenceStyleInterpreter
)

from departments.production_planning.blueprint_manager import ProductionBlueprintManager
from departments.production_planning.edit_planner import EditingBlueprintService
from departments.production_planning.feasibility_evaluator import ProductionFeasibilityService
from departments.production_planning.planning_service import ProductionPlanningService
from departments.production_planning.production_breakdown import ProductionBreakdownService

from departments.character_production.continuity_service import WorldContinuityService


class TestCreativeDirectorEngine(unittest.TestCase):
    """Test suite for Part 04 Creative Director & Production Planning Engine."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="studio_test_p04_")
        self.db_path = Path(self.temp_dir) / "test_planning.db"
        self.db = AssetDatabase(str(self.db_path))
        self.project_id = uuid4()
        self.project_id_str = str(self.project_id)
        self.db.create_project(self.project_id_str, "Test Cinematic Project", "Test Description")

        # Initialize services
        self.brief_service = CreativeBriefService()
        self.concept_service = ConceptGenerationService()
        self.script_service = ScriptAndNarrativeService()
        self.shot_planner = CinematographyShotPlanner()
        self.storyboard_service = StoryboardPlanningService()
        self.style_interpreter = ReferenceStyleInterpreter()
        self.continuity_service = WorldContinuityService(self.db)
        self.breakdown_service = ProductionBreakdownService()
        self.feasibility_service = ProductionFeasibilityService()
        self.edit_planner = EditingBlueprintService()
        self.blueprint_manager = ProductionBlueprintManager(self.db)

        self.director_service = CreativeDirectorService(self.db)
        self.planning_service = ProductionPlanningService(self.db)

    def tearDown(self):
        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)

    def test_01_brief_interpretation_and_assumptions(self):
        """Test parsing unstructured brief, detecting target duration, aspect ratio and assumptions."""
        raw_text = (
            "Create a 45-second commercial for a premium electric car. "
            "Start with a mysterious night-time introduction, reveal the vehicle gradually, "
            "use dramatic lighting with anamorphic lens flares, and finish with a strong logo reveal."
        )
        brief, questions = self.brief_service.parse_brief(
            project_id=self.project_id,
            raw_input={"prompt": raw_text, "target_duration_sec": 45.0}
        )

        self.assertIsNotNone(brief.brief_id)
        self.assertEqual(brief.project_id, self.project_id)
        self.assertEqual(brief.production_type, ProductionType.COMMERCIAL)
        self.assertAlmostEqual(brief.target_duration_sec, 45.0)
        self.assertEqual(brief.aspect_ratio, "16:9")
        self.assertTrue(len(brief.assumptions) > 0)

        # Test incomplete brief generates clarification questions
        vague_brief, vague_questions = self.brief_service.parse_brief(
            project_id=self.project_id,
            raw_input={"prompt": "Make a video for my product."}
        )
        self.assertTrue(len(vague_questions) >= 2)

    def test_02_concept_generation_and_selection(self):
        """Test generating 3 distinct concepts and selecting one."""
        brief, _ = self.brief_service.parse_brief(
            project_id=self.project_id,
            raw_input={"prompt": "30-second luxury perfume commercial in Paris with moody rain.", "target_duration_sec": 30.0}
        )
        concepts = self.concept_service.generate_concepts(brief, count=3)

        self.assertEqual(len(concepts), 3)
        titles = {c.name for c in concepts}
        self.assertEqual(len(titles), 3, "Concepts must have distinct names")

        for c in concepts:
            self.assertEqual(c.project_id, self.project_id)
            self.assertTrue(len(c.creative_premise) > 10)
            self.assertTrue(c.production_complexity in ComplexityCategory)

        # Persistence & selection
        self.db.save_creative_concepts(concepts)
        saved = self.db.get_creative_concepts(self.project_id_str)
        self.assertEqual(len(saved), 3)

        selected_id = str(concepts[1].concept_id)
        self.db.select_concept(self.project_id_str, selected_id)
        updated = self.db.get_creative_concepts(self.project_id_str)
        selected_concepts = [c for c in updated if c["is_selected"]]
        self.assertEqual(len(selected_concepts), 1)
        self.assertEqual(str(selected_concepts[0]["concept_id"]), selected_id)

    def test_03_script_and_speech_duration_estimation(self):
        """Test screenplay generation, scenes, dialogue, and word-per-minute pause heuristic."""
        brief, _ = self.brief_service.parse_brief(
            project_id=self.project_id,
            raw_input={"prompt": "A dramatic 60s documentary teaser on deep sea hydrothermal vents.", "target_duration_sec": 60.0}
        )
        concepts = self.concept_service.generate_concepts(brief)
        selected_concept = concepts[0]

        script = self.script_service.generate_script(brief, selected_concept)
        self.assertIsNotNone(script.script_id)
        self.assertEqual(script.project_id, self.project_id)
        self.assertTrue(len(script.scenes) >= 3)
        self.assertTrue(script.estimated_spoken_duration_sec > 0)

        # Verify speech duration calculation on dialogue
        test_dialogue = "Down here, at four thousand meters beneath the surface, life defies everything we thought we knew."
        calculated_dur = self.script_service.estimate_speech_duration(test_dialogue)
        self.assertGreater(calculated_dur, 6.0)
        self.assertLess(calculated_dur, 10.0)

        # Test script persistence
        self.db.save_script(script)
        retrieved_script = self.db.get_script(self.project_id_str)
        self.assertIsNotNone(retrieved_script)
        self.assertEqual(str(retrieved_script["script_id"]), str(script.script_id))
        self.assertEqual(len(retrieved_script["scenes"]), len(script.scenes))

    def test_04_cinematography_and_shot_planning(self):
        """Test breaking scenes into cinematography-grounded shots."""
        scene = ScriptScene(
            scene_id=uuid4(),
            script_id=uuid4(),
            scene_number=1,
            title="Icelandic Volcanic Desert",
            slugline="EXT. ICELANDIC VOLCANIC DESERT - TWILIGHT",
            narrative_purpose="Establish scale and isolation before vehicle enters.",
            location="Icelandic Volcanic Desert",
            time_of_day="Twilight",
            estimated_duration_sec=9.0
        )

        # Create and save parent script so scene_id is persisted before planned_shots
        script = ProductionScript(
            script_id=scene.script_id,
            project_id=self.project_id,
            title="Icelandic Test",
            logline="Testing shot planning",
            target_duration_sec=9.0,
            estimated_spoken_duration_sec=0.0,
            total_words=0,
            scenes=[scene],
            version=1,
            created_at=datetime.now(timezone.utc).isoformat()
        )
        self.db.save_script(script)

        shots = self.shot_planner.plan_shots_for_scene(
            scene=scene,
            start_index=1,
            visual_style="Cinematic Realism"
        )
        self.assertTrue(len(shots) >= 2)
        total_shot_dur = sum(s.estimated_duration_sec for s in shots)
        self.assertAlmostEqual(total_shot_dur, scene.estimated_duration_sec, places=1)

        # Check technical cinematography parameters
        first_shot = shots[0]
        self.assertIsInstance(first_shot.shot_scale, ShotScale)
        self.assertIsInstance(first_shot.camera_angle, CameraAngle)
        self.assertIsInstance(first_shot.camera_motion, CameraMotionType)
        self.assertIsNotNone(first_shot.lens_focal_length)
        self.assertTrue(len(first_shot.lighting_direction) > 0)
        self.assertIsInstance(first_shot.generation_requirements, ProductionTaskType)

        # Test database persistence
        self.db.save_planned_shots(shots)
        loaded_shots = self.db.get_planned_shots(str(scene.scene_id))
        self.assertEqual(len(loaded_shots), len(shots))

    def test_05_storyboard_frame_generation(self):
        """Test storyboard frame creation, composition guides, and generative AI prompt crafting."""
        scene = ScriptScene(
            scene_id=uuid4(),
            script_id=uuid4(),
            scene_number=1,
            title="Cyberpunk Lab",
            slugline="INT. CYBERPUNK LAB - NIGHT",
            narrative_purpose="Hero operates quantum console.",
            location="Cyberpunk Lab",
            time_of_day="Night",
            estimated_duration_sec=6.0
        )
        script = ProductionScript(
            script_id=scene.script_id,
            project_id=self.project_id,
            title="Cyberpunk Test",
            logline="Testing storyboard frames",
            target_duration_sec=6.0,
            estimated_spoken_duration_sec=0.0,
            total_words=0,
            scenes=[scene],
            version=1,
            created_at=datetime.now(timezone.utc).isoformat()
        )
        self.db.save_script(script)

        shots = self.shot_planner.plan_shots_for_scene(scene, start_index=1, visual_style="Cyberpunk Neo-Noir")
        self.db.save_planned_shots(shots)

        frames = self.storyboard_service.plan_storyboard(shots=shots)

        self.assertEqual(len(frames), len(shots))
        for frame in frames:
            self.assertIsNotNone(frame.frame_id)
            self.assertIn("Cyberpunk Neo-Noir", frame.visual_prompt_spec)
            self.assertTrue(len(frame.camera_composition) > 0)
            self.assertTrue(len(frame.lighting_direction) > 0)

        # Test DB save
        self.db.save_storyboard_frames(frames)
        loaded_frames = self.db.get_storyboard_frames(str(shots[0].shot_id))
        self.assertTrue(len(loaded_frames) > 0)

    def test_06_style_transfer_and_ip_hygiene(self):
        """Test transferring style from Part 03 ReferenceProfile and enforcing IP hygiene."""
        ref_profile = ReferenceProfile(
            profile_id=uuid4(),
            asset_id=uuid4(),
            name="Reference Style Test",
            created_at="2026-11-21T00:00:00Z",
            visual_style={
                "dominant_palette_hex": ["#0A0E17", "#1E2A38", "#3B82F6", "#60A5FA", "#F8FAFC"],
                "dominant_camera_motion": "SLOW_PAN",
                "dominant_shot_scales": ["WIDE", "MEDIUM_CLOSE_UP"]
            },
            editing_style={
                "average_shot_length_sec": 2.5,
                "cut_frequency_cpm": 24.0,
                "pacing": "FAST_PACED"
            },
            motion_graphics={
                "typography_style": "Geometric Sans Serif",
                "text_overlay_frequency": "SPARSE"
            },
            audio_style={
                "estimated_bpm": 120.0,
                "dynamic_range_db": 18.0
            },
            narrative_arc={
                "opening_hook": "Atmospheric reveal",
                "climax": "Dramatic motion",
                "resolution": "Call to action"
            },
            key_moments=[]
        )

        brief, _ = self.brief_service.parse_brief(
            project_id=self.project_id,
            raw_input={"prompt": "Commercial featuring athletic shoes and luxury sports car in Tokyo."}
        )

        # Apply style transfer
        updated_brief = self.style_interpreter.apply_reference_to_brief(
            brief=brief,
            ref_profile=ref_profile,
            matching_degree=ReferenceMatchingDegree.STRONG_MATCHING
        )

        self.assertEqual(len(updated_brief.color_palette), 5)
        self.assertEqual(updated_brief.pacing_style, PacingStyle.FAST_PACED)
        self.assertIn("120.0 BPM", updated_brief.music_direction)
        # IP Hygiene verification: check exclusions
        self.assertTrue(any("trademarked" in e.lower() for e in updated_brief.exclusions))

        # Check cinematography guidelines extraction
        guidelines = self.style_interpreter.extract_cinematography_guidelines(ref_profile)
        self.assertEqual(guidelines["recommended_asl_sec"], 2.5)
        self.assertEqual(guidelines["cuts_per_minute"], 24.0)

    def test_07_world_and_character_continuity(self):
        """Test character tracking, environment registry, and continuity rule violation audits."""
        # Register character
        char = CharacterProfile(
            character_id=uuid4(),
            project_id=self.project_id,
            name="Elena Ramos",
            age_appearance="Mid-30s",
            gender="Female",
            physical_description="Athletic build, cybernetic left ocular implant glowing cyan.",
            costume_wardrobe="Black leather tactical trench coat, charcoal combat boots.",
            personality_traits=["Calculating", "Resolute"],
            continuity_rules=["Must wear black leather tactical trench coat in Server Room"]
        )
        self.continuity_service.register_character(char)

        # Register environment
        env = EnvironmentProfile(
            environment_id=uuid4(),
            project_id=self.project_id,
            name="The Sub-Level Server Room",
            description="Narrow claustrophobic concrete corridor flanked by server racks.",
            location_type="INTERIOR",
            lighting_conditions="Flickering fluorescent fixtures with emergency red ambient pulse",
            time_of_day="Continuous artificial night",
            spatial_layout="Single linear corridor, rack banks left and right"
        )
        self.continuity_service.register_environment(env)

        # Register continuity rule
        rule = self.continuity_service.create_continuity_rule(
            project_id=self.project_id,
            rule_type=ContinuityRuleType.CHARACTER_APPEARANCE,
            description="Character appearance and wardrobe must remain consistent with registered profile."
        )

        # Shot missing continuity requirements
        shot_violating = PlannedShot(
            shot_id=uuid4(),
            scene_id=uuid4(),
            shot_number=1,
            narrative_purpose="Elena hacks terminal",
            shot_scale=ShotScale.MEDIUM,
            camera_angle=CameraAngle.EYE_LEVEL,
            camera_motion=CameraMotionType.STATIC,
            continuity_requirements=[]  # Empty requirements triggers audit warning
        )

        # Shot with proper continuity requirements
        shot_compliant = PlannedShot(
            shot_id=uuid4(),
            scene_id=uuid4(),
            shot_number=2,
            narrative_purpose="Close up on Elena ocular implant",
            shot_scale=ShotScale.CLOSE_UP,
            camera_angle=CameraAngle.EYE_LEVEL,
            camera_motion=CameraMotionType.STATIC,
            continuity_requirements=["Character appearance: Elena black leather trench coat and cyan implant"]
        )

        warnings_violating = self.continuity_service.audit_shot_continuity(shot_violating, [rule])
        self.assertTrue(len(warnings_violating) > 0)
        self.assertIn("character appearance", warnings_violating[0].lower())

        warnings_compliant = self.continuity_service.audit_shot_continuity(shot_compliant, [rule])
        self.assertEqual(len(warnings_compliant), 0)

    def test_08_mode_b_editing_blueprint_and_coverage_gaps(self):
        """Test Mode B: mapping available source shots to target reference and flagging missing coverage."""
        source_asset_id = uuid4()
        source_shots = [
            {
                "asset_id": source_asset_id,
                "shot_id": uuid4(),
                "shot_number": 1,
                "duration_sec": 3.0,
                "start_sec": 0.0,
                "end_sec": 3.0,
                "shot_scale": "WIDE",
                "camera_motion": "STATIC"
            },
            {
                "asset_id": source_asset_id,
                "shot_id": uuid4(),
                "shot_number": 2,
                "duration_sec": 4.0,
                "start_sec": 3.0,
                "end_sec": 7.0,
                "shot_scale": "MEDIUM",
                "camera_motion": "STATIC"
            }
        ]
        # Target duration is 15 seconds, but source footage only provides 7 seconds.
        # This will trigger missing coverage detection for the remaining timeline.
        blueprint = self.edit_planner.create_edit_blueprint(
            project_id=self.project_id,
            target_duration_sec=15.0,
            source_shots=source_shots,
            instructions="Maintain fast tempo"
        )

        self.assertIsNotNone(blueprint.blueprint_id)
        self.assertEqual(len(blueprint.narrative_order), 2)
        self.assertTrue(len(blueprint.missing_coverage) > 0, "Remaining timeline must be flagged as missing coverage")

        gap = blueprint.missing_coverage[0]
        self.assertAlmostEqual(gap.intended_timeline_sec, 6.0)
        self.assertGreater(gap.duration_sec, 0.0)
        self.assertEqual(gap.recommended_solution, MissingCoverageSolution.AI_VIDEO_GENERATION)

        # Verify DB persistence
        self.db.save_editing_blueprint(blueprint)
        loaded = self.db.get_editing_blueprint(self.project_id_str)
        self.assertIsNotNone(loaded)
        self.assertEqual(len(loaded["narrative_order"]), 2)
        self.assertTrue(len(loaded["missing_coverage"]) > 0)

    def test_09_production_breakdown_and_dag(self):
        """Test breaking planned shots into production tasks with dependency DAG."""
        scene_id = uuid4()
        shot1 = PlannedShot(
            shot_id=uuid4(),
            scene_id=scene_id,
            shot_number=1,
            narrative_purpose="Drone establishing shot",
            shot_scale=ShotScale.WIDE,
            camera_angle=CameraAngle.BIRDS_EYE,
            camera_motion=CameraMotionType.DOLLY_IN,
            generation_requirements=ProductionTaskType.AI_VIDEO_GENERATION,
            estimated_duration_sec=4.0
        )
        shot2 = PlannedShot(
            shot_id=uuid4(),
            scene_id=scene_id,
            shot_number=2,
            narrative_purpose="Motion graphics lower third overlay",
            shot_scale=ShotScale.MEDIUM,
            camera_angle=CameraAngle.EYE_LEVEL,
            camera_motion=CameraMotionType.STATIC,
            generation_requirements=ProductionTaskType.MOTION_GRAPHICS_CREATION,
            estimated_duration_sec=3.0
        )

        breakdown = self.breakdown_service.build_breakdown(
            project_id=self.project_id,
            shots=[shot1, shot2]
        )

        self.assertEqual(breakdown.project_id, self.project_id)
        self.assertEqual(breakdown.total_shots, 2)
        self.assertTrue(len(breakdown.tasks) >= 4)  # VO + shot1 + shot2 + conform/master

        # Check task DAG integrity: sound design / mixing task depends on upstream shot tasks
        sound_tasks = [t for t in breakdown.tasks if t.task_type == ProductionTaskType.SOUND_DESIGN]
        self.assertTrue(len(sound_tasks) > 0)
        sound_task = sound_tasks[0]
        self.assertTrue(len(sound_task.dependencies) >= 2)

    def test_10_production_feasibility_and_cost_estimation(self):
        """Test evaluating hardware feasibility on Apple M4 and cost uncertainty bounds."""
        scene_id = uuid4()
        shots = [
            PlannedShot(
                shot_id=uuid4(),
                scene_id=scene_id,
                shot_number=1,
                narrative_purpose="Hero AI video shot",
                shot_scale=ShotScale.WIDE,
                camera_angle=CameraAngle.EYE_LEVEL,
                camera_motion=CameraMotionType.DOLLY_IN,
                generation_requirements=ProductionTaskType.AI_VIDEO_GENERATION,
                estimated_duration_sec=5.0
            ),
            PlannedShot(
                shot_id=uuid4(),
                scene_id=scene_id,
                shot_number=2,
                narrative_purpose="VFX composite shot",
                shot_scale=ShotScale.CLOSE_UP,
                camera_angle=CameraAngle.EYE_LEVEL,
                camera_motion=CameraMotionType.STATIC,
                generation_requirements=ProductionTaskType.VFX_COMPOSITING,
                estimated_duration_sec=4.0
            )
        ]

        breakdown = self.breakdown_service.build_breakdown(
            project_id=self.project_id,
            shots=shots
        )

        feasibility = self.feasibility_service.evaluate_feasibility(
            project_id=self.project_id,
            breakdown=breakdown,
            shots=shots
        )

        self.assertEqual(feasibility.project_id, self.project_id)
        self.assertTrue(len(feasibility.cloud_dependencies) > 0)
        self.assertTrue(any("GPU" in d for d in feasibility.cloud_dependencies))
        self.assertGreaterEqual(feasibility.estimated_cost_range["max_usd"], feasibility.estimated_cost_range["min_usd"])
        self.assertGreater(feasibility.estimated_cost_range["uncertainty_usd"], 0.0)

        # Check local Apple M4 hardware feasibility details
        hw = feasibility.local_hardware_feasibility
        self.assertEqual(hw["workstation"], "Apple M4 (16GB RAM)")
        self.assertTrue(hw["audio_processing_compatible"])
        self.assertTrue(hw["motion_graphics_compatible"])

    def test_11_production_blueprint_and_human_approval_gate(self):
        """Test compiling master ProductionBlueprint and enforcing human approval gate."""
        brief, _ = self.brief_service.parse_brief(
            project_id=self.project_id,
            raw_input={"prompt": "30-second commercial for luxury watches.", "target_duration_sec": 30.0}
        )
        concepts = self.concept_service.generate_concepts(brief)
        selected_concept = concepts[0]
        script = self.script_service.generate_script(brief, selected_concept)
        shots = self.shot_planner.plan_shots_for_scene(script.scenes[0])
        frames = self.storyboard_service.plan_storyboard(shots)
        breakdown = self.breakdown_service.build_breakdown(self.project_id, shots, script)
        feasibility = self.feasibility_service.evaluate_feasibility(self.project_id, breakdown, shots)

        # Assemble master blueprint without prior approvals
        blueprint = self.blueprint_manager.compile_blueprint(
            project_id=self.project_id,
            brief=brief,
            selected_concept=selected_concept,
            script=script,
            planned_shots=shots,
            storyboard=frames,
            breakdown=breakdown,
            feasibility=feasibility
        )

        self.assertFalse(blueprint.is_ready_for_production, "Cannot be ready before approvals are granted")

        # Save to DB
        self.db.save_production_blueprint(blueprint)
        loaded_bp = self.db.get_production_blueprint(self.project_id_str)
        self.assertIsNotNone(loaded_bp)
        self.assertEqual(str(loaded_bp["blueprint_id"]), str(blueprint.blueprint_id))

        # Submit human approval for Script
        self.blueprint_manager.submit_approval(
            project_id=self.project_id,
            entity_type=PlanningEntityType.SCRIPT,
            entity_id=script.script_id,
            version=1,
            status=ApprovalStatus.APPROVED,
            reviewer_notes="Script approved by creative director.",
            approved_by="Executive Producer"
        )

        approvals = self.db.get_creative_approvals(self.project_id_str)
        self.assertEqual(len(approvals), 1)
        self.assertEqual(approvals[0]["status"], ApprovalStatus.APPROVED.value)

        # Re-compile blueprint: with approved script, it should now be ready for production
        updated_bp = self.blueprint_manager.compile_blueprint(
            project_id=self.project_id,
            brief=brief,
            selected_concept=selected_concept,
            script=script,
            planned_shots=shots,
            storyboard=frames,
            breakdown=breakdown,
            feasibility=feasibility
        )
        self.assertTrue(updated_bp.is_ready_for_production)


if __name__ == "__main__":
    unittest.main()
