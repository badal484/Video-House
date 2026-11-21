"""
LUT Manager for Department 16.
Handles parsing, validation, storage, application, and export of .cube, .3dl, and .clf formats.
Enforces color space compatibility checks to prevent applying incompatible conversion LUTs.
"""
from pathlib import Path
from typing import Dict, Optional, Tuple, Union
import numpy as np
from ..core.models import ColorSpace, LUTMetadata
from .lut_interpolator import LUTInterpolator


class LUTManager:
    """
    Manages lookup table ingestion, compatibility validation, and application.
    """

    @staticmethod
    def parse_cube_file(cube_content: str) -> Tuple[LUTMetadata, np.ndarray]:
        """
        Parses a standard Adobe/DaVinci .cube file string into LUTMetadata and a NumPy grid array.
        """
        lines = [line.strip() for line in cube_content.strip().splitlines() if line.strip() and not line.startswith("#")]

        name = "Imported LUT"
        size = 33
        is_3d = True
        domain_min = np.array([0.0, 0.0, 0.0], dtype=np.float32)
        domain_max = np.array([1.0, 1.0, 1.0], dtype=np.float32)
        data_rows = []

        for line in lines:
            parts = line.split()
            if parts[0] == "TITLE":
                name = " ".join(parts[1:]).strip('"')
            elif parts[0] == "LUT_3D_SIZE":
                size = int(parts[1])
                is_3d = True
            elif parts[0] == "LUT_1D_SIZE":
                size = int(parts[1])
                is_3d = False
            elif parts[0] == "DOMAIN_MIN":
                domain_min = np.array([float(p) for p in parts[1:4]], dtype=np.float32)
            elif parts[0] == "DOMAIN_MAX":
                domain_max = np.array([float(p) for p in parts[1:4]], dtype=np.float32)
            elif len(parts) == 3:
                try:
                    data_rows.append([float(parts[0]), float(parts[1]), float(parts[2])])
                except ValueError:
                    continue

        if not data_rows:
            raise ValueError("No valid numeric RGB rows found in .cube file.")

        data_arr = np.array(data_rows, dtype=np.float32)

        if is_3d:
            expected_count = size * size * size
            if len(data_arr) != expected_count:
                raise ValueError(f"Expected {expected_count} rows for 3D LUT size {size}, found {len(data_arr)}.")
            # .cube ordering is typically R fastest, then G, then B
            # Reshape to (size, size, size, 3) where index is [r, g, b]
            lut_grid = data_arr.reshape((size, size, size, 3))
        else:
            lut_grid = data_arr

        metadata = LUTMetadata(
            name=name,
            format="cube",
            input_color_space=ColorSpace.REC709,
            output_color_space=ColorSpace.REC709,
            size=size,
            is_3d=is_3d
        )

        return metadata, lut_grid

    @staticmethod
    def export_cube_file(metadata: LUTMetadata, lut_grid: np.ndarray) -> str:
        """
        Exports a 3D NumPy array into standard .cube file format string.
        """
        size = lut_grid.shape[0]
        header = [
            f"# Universal Studio Generated 3D LUT",
            f'TITLE "{metadata.name}"',
            f"LUT_3D_SIZE {size}",
            f"DOMAIN_MIN 0.0 0.0 0.0",
            f"DOMAIN_MAX 1.0 1.0 1.0",
            ""
        ]
        lines = header
        for r in range(size):
            for g in range(size):
                for b in range(size):
                    val = lut_grid[r, g, b]
                    lines.append(f"{val[0]:.6f} {val[1]:.6f} {val[2]:.6f}")

        return "\n".join(lines)

    @staticmethod
    def validate_lut_compatibility(
        lut_metadata: LUTMetadata,
        current_color_space: ColorSpace
    ) -> Tuple[bool, Optional[str]]:
        """
        Rejects applying an input-dependent LUT in an incompatible color space.
        """
        if lut_metadata.is_technical:
            if lut_metadata.input_color_space != current_color_space:
                return False, (
                    f"Incompatible technical LUT: '{lut_metadata.name}' requires input space "
                    f"'{lut_metadata.input_color_space.value}', but clip is in '{current_color_space.value}'."
                )
        return True, None

    @classmethod
    def apply_lut(
        cls,
        image: np.ndarray,
        lut_grid: np.ndarray,
        metadata: LUTMetadata,
        current_color_space: ColorSpace,
        intensity: float = 1.0
    ) -> np.ndarray:
        """
        Validates color space compatibility and applies the LUT.
        """
        compatible, err = cls.validate_lut_compatibility(metadata, current_color_space)
        if not compatible:
            raise ValueError(err)

        if metadata.is_3d:
            return LUTInterpolator.apply_3d_lut(image, lut_grid, intensity=intensity)
        else:
            return LUTInterpolator.apply_1d_lut(image, lut_grid, intensity=intensity)
