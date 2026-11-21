"""
Sprite Sheet Packager
Packs an array of animation frames into a compact 2D sprite sheet atlas PNG
and exports frame coordinate metadata JSON.
"""
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import json
import cv2
import numpy as np


class SpriteSheetPackager:
    """
    Compiles sequences of animation frames into a single texture atlas.
    """

    @staticmethod
    def pack_frames(
        frames: List[np.ndarray],  # List of RGBA frames
        output_png_path: str,
        output_json_path: str,
        columns: int = 4,
    ) -> Dict[str, Any]:
        """
        Packs frames into a grid atlas and saves PNG and JSON atlas coordinate file.
        """
        if not frames:
            raise ValueError("No frames provided for sprite sheet packing.")

        num_frames = len(frames)
        fh, fw = frames[0].shape[:2]
        cols = min(columns, num_frames)
        rows = int(np.ceil(num_frames / float(cols)))

        atlas_w = cols * fw
        atlas_h = rows * fh
        atlas = np.zeros((atlas_h, atlas_w, 4), dtype=np.uint8)

        frame_metadata = []

        for idx, f in enumerate(frames):
            r = idx // cols
            c = idx % cols
            x = c * fw
            y = r * fh
            atlas[y : y + fh, x : x + fw] = f

            frame_metadata.append({
                "frame_index": idx,
                "x": x,
                "y": y,
                "width": fw,
                "height": fh,
            })

        out_img = Path(output_png_path)
        out_img.parent.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(str(out_img), atlas)

        atlas_manifest = {
            "image": out_img.name,
            "resolution": [atlas_w, atlas_h],
            "frame_count": num_frames,
            "frames": frame_metadata,
        }

        out_json = Path(output_json_path)
        out_json.parent.mkdir(parents=True, exist_ok=True)
        out_json.write_text(json.dumps(atlas_manifest, indent=2))

        return atlas_manifest

