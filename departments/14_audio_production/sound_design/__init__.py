"""
Sound Design & Music Package Initialization
"""
from .sound_library import SoundLibrary, SFXAssetMetadata
from .procedural_sfx import ProceduralSFXEngine
from .music_engine import MusicEngine

__all__ = [
    "SoundLibrary",
    "SFXAssetMetadata",
    "ProceduralSFXEngine",
    "MusicEngine",
]
