"""
2D Bone Node & Rigging Data Models
Defines hierarchical 2D bone trees, parent-child coordinate spaces, and cut-out sprite attachments.
"""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4
import numpy as np


@dataclass
class BoneNode:
    bone_id: str
    parent_id: Optional[str]
    name: str
    length: float = 50.0
    local_position: Tuple[float, float] = (0.0, 0.0)
    local_rotation: float = 0.0  # Degrees
    local_scale: Tuple[float, float] = (1.0, 1.0)
    pivot_point: Tuple[float, float] = (0.0, 0.0)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "bone_id": self.bone_id,
            "parent_id": self.parent_id,
            "name": self.name,
            "length": self.length,
            "local_position": list(self.local_position),
            "local_rotation": self.local_rotation,
            "local_scale": list(self.local_scale),
            "pivot_point": list(self.pivot_point),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BoneNode":
        return cls(
            bone_id=data["bone_id"],
            parent_id=data.get("parent_id"),
            name=data["name"],
            length=float(data.get("length", 50.0)),
            local_position=tuple(data.get("local_position", [0.0, 0.0])),
            local_rotation=float(data.get("local_rotation", 0.0)),
            local_scale=tuple(data.get("local_scale", [1.0, 1.0])),
            pivot_point=tuple(data.get("pivot_point", [0.0, 0.0])),
        )


@dataclass
class CharacterRig:
    rig_id: str
    character_id: str
    name: str
    root_bone_id: str = "root"
    bones: Dict[str, BoneNode] = field(default_factory=dict)
    sprite_attachments: Dict[str, str] = field(default_factory=dict)  # Bone ID -> Sprite asset/layer name
    draw_order: List[str] = field(default_factory=list)  # Back-to-front rendering order

    def add_bone(self, bone: BoneNode) -> None:
        self.bones[bone.bone_id] = bone
        if bone.bone_id not in self.draw_order:
            self.draw_order.append(bone.bone_id)

    def get_bone(self, bone_id: str) -> Optional[BoneNode]:
        return self.bones.get(bone_id)

    def compute_world_transforms(self) -> Dict[str, Dict[str, Any]]:
        """
        Recursively evaluates world-space position, rotation, and tip coordinates for all bones.
        Returns dict: bone_id -> {'start': (x, y), 'end': (x, y), 'rotation': deg, 'matrix': 3x3}
        """
        transforms: Dict[str, Dict[str, Any]] = {}

        def get_local_matrix(b: BoneNode) -> np.ndarray:
            rad = np.radians(b.local_rotation)
            c, s = np.cos(rad), np.sin(rad)
            # Translation * Rotation * Scale
            T = np.array([
                [c * b.local_scale[0], -s * b.local_scale[1], b.local_position[0]],
                [s * b.local_scale[0],  c * b.local_scale[1], b.local_position[1]],
                [0.0,                  0.0,                  1.0]
            ], dtype=np.float32)
            return T

        def evaluate_bone(b_id: str) -> None:
            if b_id in transforms:
                return
            bone = self.bones[b_id]
            local_mat = get_local_matrix(bone)

            if bone.parent_id and bone.parent_id in self.bones:
                evaluate_bone(bone.parent_id)
                parent_world_mat = transforms[bone.parent_id]["matrix"]
                world_mat = parent_world_mat @ local_mat
                world_rot = (transforms[bone.parent_id]["rotation"] + bone.local_rotation) % 360.0
            else:
                world_mat = local_mat
                world_rot = bone.local_rotation % 360.0

            start_pos = (float(world_mat[0, 2]), float(world_mat[1, 2]))
            # Bone tip extends along its local X-axis by bone.length
            tip_local = np.array([bone.length, 0.0, 1.0], dtype=np.float32)
            tip_world = world_mat @ tip_local
            end_pos = (float(tip_world[0]), float(tip_world[1]))

            transforms[b_id] = {
                "start": start_pos,
                "end": end_pos,
                "rotation": world_rot,
                "matrix": world_mat,
            }

        for b_id in self.bones:
            evaluate_bone(b_id)

        return transforms

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rig_id": self.rig_id,
            "character_id": self.character_id,
            "name": self.name,
            "root_bone_id": self.root_bone_id,
            "bones": {k: v.to_dict() for k, v in self.bones.items()},
            "sprite_attachments": self.sprite_attachments,
            "draw_order": self.draw_order,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CharacterRig":
        rig = cls(
            rig_id=data["rig_id"],
            character_id=data["character_id"],
            name=data["name"],
            root_bone_id=data.get("root_bone_id", "root"),
            sprite_attachments=data.get("sprite_attachments", {}),
            draw_order=data.get("draw_order", []),
        )
        for b_id, b_data in data.get("bones", {}).items():
            rig.add_bone(BoneNode.from_dict(b_data))
        return rig
