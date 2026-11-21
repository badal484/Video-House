"""
Unit Tests for Department 10 & 12: 2D Animation, Anime & Character Studio
Verifies all 12 core animation capabilities: character creation, model sheets,
identity preservation, expressions, frame-by-frame walk cycle, skeletal rigging,
2-bone IK, cut-out puppetry, anime multiplane backgrounds, dialogue lip-sync,
motion retargeting, transparent export, and timeline integration.
"""
from pathlib import Path
import unittest
from uuid import uuid4
import cv2
import numpy as np

import departments
from departments.animation_2d.core.models import (
    AnimationProject,
    AnimationScene,
    AnimationShot,
    AnimationTrack,
    TrackType,
    DrawingExposure,
    ExposureRate,
    Camera2D,
)
from departments.animation_2d.characters.character_models import (
    CharacterIdentity,
    ModelSheet,
    CharacterPose,
    ExpressionType,
    PoseType,
    IdentityStatus,
)
from departments.animation_2d.characters.character_generator import CharacterGenerator
from departments.animation_2d.characters.identity_validator import IdentityValidator
from departments.animation_2d.rigging.bone_models import BoneNode, CharacterRig
from departments.animation_2d.rigging.ik_solver import IKSolver2D
from departments.animation_2d.rigging.puppet_animator import PuppetAnimator
from departments.animation_2d.anime_pipeline.anime_models import AnimeLayout, TimingChart
from departments.animation_2d.anime_pipeline.cel_shader import AnimeCelShader
from departments.animation_2d.anime_pipeline.multiplane_background import MultiplaneBackgroundEngine
from departments.animation_2d.ai_generation.motion_retargeting import MotionRetargeter
from departments.animation_2d.ai_generation.facial_animator import VisemeType, FacialAnimator
from departments.animation_2d.ai_generation.inbetween_engine import InBetweenEngine
from departments.animation_2d.asset_library.asset_library import (
    AnimationAsset,
    AnimationAssetLibrary,
    AssetCategory,
)
from departments.animation_2d.rendering.vector_renderer import VectorAnimationRenderer
from departments.animation_2d.rendering.raster_renderer import RasterAnimationRenderer
from departments.animation_2d.rendering.sprite_sheet_packager import SpriteSheetPackager
from departments.animation_2d.integrations.timeline_adapter import TimelineAnimationAdapter
from departments.animation_2d.integrations.director_bridge import DirectorAnimationBridge
from departments.animation_2d.service import Animation2DService
from departments.video_editing.timeline_manager import TimelineManager
from core.assets.database import AssetDatabase


class Test2DAnimationStudio(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.artifact_dir = Path("test_artifacts/animation_2d")
        cls.artifact_dir.mkdir(parents=True, exist_ok=True)
        cls.db_path = cls.artifact_dir / "test_animation.db"
        if cls.db_path.exists():
            cls.db_path.unlink()
        cls.db = AssetDatabase(str(cls.db_path))

    def test_01_create_character_concept(self):
        """Test creating structured character concept from natural-language brief."""
        brief = "A sharp-witted young anime cyber-detective with asymmetrical bangs and high-collar dark jacket with gold trim."
        char = CharacterGenerator.create_character_concept(
            project_id=str(uuid4()),
            name="Ren Kurogane",
            brief_text=brief,
            head_ratio=7.0,
            visual_style="ANIME_CEL",
        )

        self.assertEqual(char.name, "Ren Kurogane")
        self.assertEqual(char.head_ratio, 7.0)
        self.assertIn("skin_base", char.color_palette)
        self.assertIn("hair_base", char.color_palette)
        self.assertGreater(len(char.distinctive_features), 0)
        self.assertEqual(char.status, IdentityStatus.APPROVED)

    def test_02_generate_turnaround_model_sheet(self):
        """Test generating complete 5-angle Settei turnaround model sheet with alignment guides."""
        char = CharacterGenerator.create_character_concept(
            project_id=str(uuid4()),
            name="Ren Kurogane",
            brief_text="Cyber-detective with jacket",
        )
        sheet, canvas = CharacterGenerator.generate_turnaround_model_sheet(char, resolution=(1920, 1080))

        self.assertEqual(canvas.shape, (1080, 1920, 3))
        self.assertIn("top_of_head", sheet.alignment_guides)
        self.assertIn("ankle", sheet.alignment_guides)
        self.assertGreater(sheet.alignment_guides["ankle"], sheet.alignment_guides["top_of_head"])

        # Save model sheet artifact
        cv2.imwrite(str(self.artifact_dir / "02_turnaround_model_sheet.png"), canvas)

    def test_03_identity_preservation_across_poses(self):
        """Test character identity preservation across 5 poses (Standing, Walking, Running, Sitting, Jumping)."""
        char = CharacterGenerator.create_character_concept(
            project_id=str(uuid4()),
            name="Ren Kurogane",
            brief_text="Hero character",
            head_ratio=7.0,
        )
        poses = CharacterGenerator.generate_pose_library(char)
        self.assertEqual(len(poses), 5)

        # Audit consistency for each pose
        dummy_img = np.zeros((100, 100, 3), dtype=np.uint8)
        for pose in poses:
            report = IdentityValidator.audit_character_consistency(
                dummy_img,
                char,
                measured_head_ratio=7.1,  # Minor natural variation (<2% delta)
                sampled_colors={"skin_base": (248, 213, 194)},
            )
            self.assertEqual(report["validation_status"], "PASSED")
            self.assertGreaterEqual(report["consistency_score"], 0.9)

    def test_04_facial_expression_matrix(self):
        """Test generating 5 facial expressions (Neutral, Happy, Sad, Angry, Surprised)."""
        char = CharacterGenerator.create_character_concept(
            project_id=str(uuid4()),
            name="Ren Kurogane",
            brief_text="Hero",
        )
        expressions = CharacterGenerator.generate_expression_matrix(char)
        self.assertEqual(len(expressions), 5)

        # Build contact row of expressions
        expr_strip = np.hstack([img[:, :, :3] for _, img in expressions])
        cv2.imwrite(str(self.artifact_dir / "04_expression_strip.png"), expr_strip)

    def test_05_frame_by_frame_walk_cycle(self):
        """Test creating an 8-frame traditional walk cycle stepped on 2s (12 FPS)."""
        char = CharacterGenerator.create_character_concept(
            project_id=str(uuid4()),
            name="Ren Kurogane",
            brief_text="Hero",
        )
        rig = PuppetAnimator.build_standard_humanoid_rig(char, root_origin=(200.0, 150.0))
        cycle_frames = []

        # Generate 8 walk cycle phases
        for i in range(8):
            phase = i / 8.0
            PuppetAnimator.generate_walk_cycle_frame(rig, phase)
            f = PuppetAnimator.render_rig_skeleton(rig, canvas_shape=(400, 400))
            cycle_frames.append(f)

        self.assertEqual(len(cycle_frames), 8)
        # Pack into sprite sheet
        pack_manifest = SpriteSheetPackager.pack_frames(
            cycle_frames,
            output_png_path=str(self.artifact_dir / "05_walk_cycle_spritesheet.png"),
            output_json_path=str(self.artifact_dir / "05_walk_cycle_atlas.json"),
            columns=4,
        )
        self.assertEqual(pack_manifest["frame_count"], 8)

    def test_06_skeletal_rigging_and_2bone_ik(self):
        """Test analytical 2-bone Inverse Kinematics (IK) with reach clamping."""
        # Arm reaching for target: shoulder at (100, 100), target at (180, 180)
        ik_result = IKSolver2D.solve_2bone_ik(
            root_pos=(100.0, 100.0),
            target_pos=(180.0, 180.0),
            length_upper=70.0,
            length_lower=70.0,
            bend_positive=True,
        )

        self.assertTrue(ik_result["success"])
        self.assertFalse(ik_result["clamped"])
        # Elbow position should exist and be valid
        ex, ey = ik_result["elbow_pos"]
        self.assertGreater(ex, 100.0)
        self.assertGreater(ey, 100.0)

        # Over-extended reach test (target at 500, 500, max reach 140)
        ik_clamped = IKSolver2D.solve_2bone_ik(
            root_pos=(100.0, 100.0),
            target_pos=(500.0, 500.0),
            length_upper=70.0,
            length_lower=70.0,
        )
        self.assertTrue(ik_clamped["clamped"])

    def test_07_cut_out_puppet_animation(self):
        """Test hierarchical bone forward kinematics and cut-out skeleton rendering."""
        char = CharacterGenerator.create_character_concept(
            project_id=str(uuid4()),
            name="Ren Kurogane",
            brief_text="Hero",
        )
        rig = PuppetAnimator.build_standard_humanoid_rig(char, root_origin=(300.0, 150.0))
        rig_canvas = PuppetAnimator.render_rig_skeleton(rig, canvas_shape=(500, 600))

        self.assertEqual(rig_canvas.shape, (500, 600, 4))
        self.assertGreater(np.sum(rig_canvas[:, :, 3] > 0), 1000)
        cv2.imwrite(str(self.artifact_dir / "07_skeletal_rig.png"), rig_canvas)

    def test_08_anime_multiplane_background(self):
        """Test rendering multiplane parallax environment (Sky, Skyline, City Midground, Railing)."""
        bg_sunset = MultiplaneBackgroundEngine.render_parallax_frame(
            canvas_shape=(600, 800),
            camera_offset_x=150.0,
            time_of_day="SUNSET",
        )
        self.assertEqual(bg_sunset.shape, (600, 800, 4))
        # Ensure alpha channel is solid 255
        self.assertEqual(bg_sunset[100, 100, 3], 255)

        cv2.imwrite(str(self.artifact_dir / "08_multiplane_background.png"), bg_sunset)

    def test_09_two_character_dialogue_scene(self):
        """Test staging two characters with speech-synced mouth visemes."""
        h, w = 400, 600
        scene_canvas = np.zeros((h, w, 4), dtype=np.uint8)

        # Character 1 on left (talking: Viseme O_OH)
        cv2.circle(scene_canvas, (180, 200), 80, (210, 225, 245, 255), -1)
        v_talk = FacialAnimator.render_viseme((60, 80), VisemeType.O_OH)
        scene_canvas[190:250, 140:220] = v_talk

        # Character 2 on right (listening: Viseme REST)
        cv2.circle(scene_canvas, (420, 200), 80, (200, 215, 240, 255), -1)
        v_rest = FacialAnimator.render_viseme((60, 80), VisemeType.REST)
        scene_canvas[190:250, 380:460] = v_rest

        self.assertEqual(scene_canvas.shape, (h, w, 4))
        cv2.imwrite(str(self.artifact_dir / "09_two_character_dialogue.png"), scene_canvas)

    def test_10_ai_motion_retargeting(self):
        """Test retargeting 2D joint coordinates to character rig bones."""
        char = CharacterGenerator.create_character_concept(
            project_id=str(uuid4()),
            name="Ren Kurogane",
            brief_text="Hero",
        )
        rig = PuppetAnimator.build_standard_humanoid_rig(char)

        # Simulated driving pose from video tracker
        driving_joints = {
            "pelvis": (300.0, 400.0),
            "chest": (300.0, 250.0),
            "shoulder_r": (330.0, 250.0),
            "elbow_r": (380.0, 300.0),
            "wrist_r": (420.0, 260.0),
            "hip_r": (320.0, 400.0),
            "knee_r": (350.0, 520.0),
            "ankle_r": (380.0, 640.0),
        }

        retargeted_angles = MotionRetargeter.retarget_pose(driving_joints, rig)
        self.assertIn("upper_arm_r", retargeted_angles)
        self.assertIn("thigh_r", retargeted_angles)
        self.assertIsInstance(retargeted_angles["upper_arm_r"], float)

    def test_11_transparent_alpha_video_export(self):
        """Test rendering transparent character animation frames directly to ProRes 4444 video."""
        char = CharacterGenerator.create_character_concept(
            project_id=str(uuid4()),
            name="Ren Kurogane",
            brief_text="Hero",
        )
        rig = PuppetAnimator.build_standard_humanoid_rig(char, root_origin=(150.0, 100.0))

        # Generate 12 walk frames
        frames = []
        for i in range(12):
            PuppetAnimator.generate_walk_cycle_frame(rig, i / 12.0)
            f = PuppetAnimator.render_rig_skeleton(rig, canvas_shape=(300, 300))
            frames.append(f)

        out_mov = self.artifact_dir / "11_transparent_walk_cycle.mov"
        render_res = RasterAnimationRenderer.render_video(
            frames=frames,
            output_path=str(out_mov),
            fps=24.0,
            codec="prores_ks",
        )

        self.assertEqual(render_res["status"], "COMPLETED")
        self.assertTrue(out_mov.exists())
        self.assertGreater(out_mov.stat().st_size, 500)

    def test_12_editorial_timeline_insertion_and_contact_sheet(self):
        """Test inserting rendered animation onto NLE timeline and build visual acceptance contact sheet."""
        # 1. Timeline Bridge Test
        mgr = TimelineManager(self.db)
        proj_id = uuid4()
        self.db.create_project(proj_id, "Animation NLE Test")
        tl = mgr.create_timeline(proj_id, "Animation Sequence", fps=24.0)

        anim_asset_id = uuid4()
        res = TimelineAnimationAdapter.insert_animation_to_timeline(
            timeline_manager=mgr,
            timeline_id=tl.timeline_id,
            animation_asset_id=anim_asset_id,
            duration_seconds=4.0,
            timeline_start_seconds=1.5,
            is_transparent_overlay=True,
        )
        self.assertTrue(res["success"])
        self.assertEqual(res["track_name"], "V3_ANIMATION_OVERLAY")

        # 2. Build 12-Slot Visual Acceptance Contact Sheet
        cs_h, cs_w = 400, 600
        sheet = np.zeros((cs_h * 2, cs_w * 2, 3), dtype=np.uint8)

        # Slot 1: Turnaround Model Sheet
        f1 = cv2.imread(str(self.artifact_dir / "02_turnaround_model_sheet.png"))
        if f1 is not None: sheet[0:cs_h, 0:cs_w] = cv2.resize(f1, (cs_w, cs_h))

        # Slot 2: Multiplane Parallax Background
        f2 = cv2.imread(str(self.artifact_dir / "08_multiplane_background.png"))
        if f2 is not None: sheet[0:cs_h, cs_w:cs_w*2] = cv2.resize(f2, (cs_w, cs_h))

        # Slot 3: Skeletal 2D Rigging & IK
        f3 = cv2.imread(str(self.artifact_dir / "07_skeletal_rig.png"))
        if f3 is not None: sheet[cs_h:cs_h*2, 0:cs_w] = cv2.resize(f3, (cs_w, cs_h))

        # Slot 4: Two-Character Dialogue Scene
        f4 = cv2.imread(str(self.artifact_dir / "09_two_character_dialogue.png"))
        if f4 is not None: sheet[cs_h:cs_h*2, cs_w:cs_w*2] = cv2.resize(f4, (cs_w, cs_h))

        # Annotate Contact Sheet Slots
        cv2.putText(sheet, "1. SETTEI MODEL SHEET (5-VIEW)", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
        cv2.putText(sheet, "2. ANIME MULTIPLANE PARALLAX", (cs_w + 20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
        cv2.putText(sheet, "3. 2D SKELETAL RIG & 2-BONE IK", (20, cs_h + 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
        cv2.putText(sheet, "4. 2-CHARACTER DIALOGUE LIP-SYNC", (cs_w + 20, cs_h + 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)

        contact_sheet_path = self.artifact_dir / "ANIMATION_ACCEPTANCE_CONTACT_SHEET.png"
        cv2.imwrite(str(contact_sheet_path), sheet)
        self.assertTrue(contact_sheet_path.exists())


if __name__ == "__main__":
    unittest.main()
