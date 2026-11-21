"""
Archival Film Scratch & Dust Inpainter for Department 16.
Detects vertical line scratches and dust blemishes and removes them via Fast Marching Inpainting (Telea).
"""
import cv2
import numpy as np


class ScratchDustRemover:
    """
    Detects and inpaints physical film scratches and dust artifacts.
    """

    @staticmethod
    def detect_scratches(image_gray: np.ndarray, threshold: int = 40) -> np.ndarray:
        """
        Detects thin vertical scratches using median filtering difference.
        """
        med = cv2.medianBlur(image_gray, 5)
        diff = cv2.absdiff(image_gray, med)
        _, mask = cv2.threshold(diff, threshold, 255, cv2.THRESH_BINARY)
        # Dilate mask slightly to cover scratch boundaries
        mask = cv2.dilate(mask, cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3)))
        return mask

    @classmethod
    def inpaint_scratches(
        cls,
        image: np.ndarray,
        scratch_threshold: int = 35
    ) -> np.ndarray:
        """
        Inpaints detected scratches using Alexandru Telea's Fast Marching Method.
        """
        arr = np.clip(image, 0.0, 1.0).astype(np.float32)
        has_alpha = arr.ndim == 3 and arr.shape[2] == 4
        rgb = arr[:, :, :3] if has_alpha else arr

        # Grayscale uint8 for detection
        img_uint8 = (rgb * 255.0).astype(np.uint8)
        gray = cv2.cvtColor(img_uint8, cv2.COLOR_RGB2GRAY)

        mask = cls.detect_scratches(gray, threshold=scratch_threshold)

        if np.sum(mask) > 10:
            # Telea inpainting on uint8 RGB
            inpainted_uint8 = cv2.inpaint(img_uint8, mask, inpaintRadius=3, flags=cv2.INPAINT_TELEA)
            restored_rgb = inpainted_uint8.astype(np.float32) / 255.0
        else:
            restored_rgb = rgb

        if has_alpha:
            return np.concatenate([restored_rgb, arr[:, :, 3:4]], axis=2)
        return restored_rgb
