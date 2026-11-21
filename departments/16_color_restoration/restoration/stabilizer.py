"""
Video Camera Stabilization Engine for Department 16.
Estimates frame-to-frame affine transformations and smoothes camera trajectories.
"""
import cv2
import numpy as np


class VideoStabilizer:
    """
    Stabilizes camera motion using feature tracking and motion compensation.
    """

    @staticmethod
    def stabilize_sequence(frames: list[np.ndarray], smoothness: int = 5) -> list[np.ndarray]:
        """
        Calculates affine transforms between consecutive frames and applies smoothed compensation.
        """
        if len(frames) < 2:
            return frames

        transforms = [] # [dx, dy, da]
        h, w = frames[0].shape[:2]

        # Convert to grayscale uint8 for optical flow / feature tracking
        prev_gray = cv2.cvtColor(np.clip(frames[0] * 255.0, 0, 255).astype(np.uint8), cv2.COLOR_RGB2GRAY)

        for i in range(1, len(frames)):
            curr_gray = cv2.cvtColor(np.clip(frames[i] * 255.0, 0, 255).astype(np.uint8), cv2.COLOR_RGB2GRAY)
            # Find feature points
            prev_pts = cv2.goodFeaturesToTrack(prev_gray, maxCorners=200, qualityLevel=0.01, minDistance=30)

            if prev_pts is not None and len(prev_pts) > 10:
                curr_pts, status, _ = cv2.calcOpticalFlowPyrLK(prev_gray, curr_gray, prev_pts, None)
                idx = np.where(status == 1)[0]
                prev_pts_good = prev_pts[idx]
                curr_pts_good = curr_pts[idx]

                # Estimate affine transform (translation + rotation)
                m, _ = cv2.estimateAffinePartial2D(prev_pts_good, curr_pts_good)
                if m is not None:
                    dx = m[0, 2]
                    dy = m[1, 2]
                    da = np.arctan2(m[1, 0], m[0, 0])
                    transforms.append([dx, dy, da])
                else:
                    transforms.append([0.0, 0.0, 0.0])
            else:
                transforms.append([0.0, 0.0, 0.0])

            prev_gray = curr_gray

        # Compute trajectory & smooth trajectory
        transforms_arr = np.array(transforms)
        trajectory = np.cumsum(transforms_arr, axis=0)

        # Smooth trajectory with moving average
        smoothed_trajectory = trajectory.copy()
        radius = smoothness // 2
        for i in range(len(trajectory)):
            start = max(0, i - radius)
            end = min(len(trajectory), i + radius + 1)
            smoothed_trajectory[i] = np.mean(trajectory[start:end], axis=0)

        diff = smoothed_trajectory - trajectory
        transforms_smooth = transforms_arr + diff

        # Apply smoothed transforms
        stabilized = [frames[0]]
        for i in range(1, len(frames)):
            dx, dy, da = transforms_smooth[i - 1]
            m = np.zeros((2, 3), dtype=np.float32)
            m[0, 0] = np.cos(da)
            m[0, 1] = -np.sin(da)
            m[1, 0] = np.sin(da)
            m[1, 1] = np.cos(da)
            m[0, 2] = dx
            m[1, 2] = dy

            warped = cv2.warpAffine(frames[i], m, (w, h), borderMode=cv2.BORDER_REFLECT)
            stabilized.append(np.clip(warped, 0.0, 1.0))

        return stabilized
