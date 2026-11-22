"""
Dynamic module loader for the 22 studio departments.
Maps clean Python attribute names (e.g. media_ingestion, studio_application)
to their numbered directories (e.g. 03_media_ingestion, 01_studio_application).
"""
import importlib
import sys

DEPT_MAP = {
    "studio_application": "01_studio_application",
    "project_management": "02_project_management",
    "media_ingestion": "03_media_ingestion",
    "media_intelligence": "04_media_intelligence",
    "multimodal_providers": "05_multimodal_providers",
    "creative_direction": "06_creative_direction",
    "production_planning": "07_production_planning",
    "video_editing": "08_video_editing",
    "motion_graphics": "09_motion_graphics",
    "animation_2d": "10_animation_2d",
    "animation_3d": "11_animation_3d",
    "character_production": "12_character_production",
    "vfx_compositing": "13_vfx_compositing",
    "audio_production": "14_audio_production",
    "ai_generation": "15_ai_generation",
    "color_restoration": "16_color_restoration",
    "subtitles_dubbing": "17_subtitles_dubbing",
    "quality_control": "18_quality_control",
    "rendering_delivery": "19_rendering_delivery",
    "agent_orchestration": "20_agent_orchestration",
    "storage_asset_management": "21_storage_asset_management",
    "licensing_cost_tracking": "22_licensing_cost_tracking",
}

for alias, folder in DEPT_MAP.items():
    try:
        mod = importlib.import_module(f"departments.{folder}")
        globals()[alias] = mod
        sys.modules[f"departments.{alias}"] = mod
    except Exception:
        pass

# Second pass to resolve any cross-department dependencies
for alias, folder in DEPT_MAP.items():
    if alias not in globals():
        try:
            mod = importlib.import_module(f"departments.{folder}")
            globals()[alias] = mod
            sys.modules[f"departments.{alias}"] = mod
        except Exception:
            pass

__all__ = list(DEPT_MAP.keys())

