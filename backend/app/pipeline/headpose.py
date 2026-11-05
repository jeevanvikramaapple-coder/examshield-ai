"""Head pose via OpenCV solvePnP on MediaPipe Face Mesh landmarks.

Absolute yaw is meaningless in a hall (camera angle differs per seat), so each
candidate gets a neutral pose captured during the first minutes of the session
and everything afterwards is measured relative to it.
"""
import math

import cv2
import numpy as np

# Generic 3D face model (mm) for nose tip, chin, eye corners, mouth corners.
MODEL_POINTS = np.array([
    (0.0, 0.0, 0.0),
    (0.0, -63.6, -12.5),
    (-43.3, 32.7, -26.0),
    (43.3, 32.7, -26.0),
    (-28.9, -28.9, -24.1),
    (28.9, -28.9, -24.1),
], dtype=np.float64)

# MediaPipe Face Mesh indices matching MODEL_POINTS.
LANDMARK_IDS = (1, 152, 33, 263, 61, 291)


def estimate_pose(landmarks_px: np.ndarray, frame_size: tuple[int, int]):
    """landmarks_px: (468+, 2) pixel coords. Returns (yaw, pitch, roll) in degrees or None."""
    h, w = frame_size
    image_points = np.array([landmarks_px[i] for i in LANDMARK_IDS], dtype=np.float64)
    focal = w
    cam = np.array([[focal, 0, w / 2], [0, focal, h / 2], [0, 0, 1]], dtype=np.float64)
    ok, rvec, _ = cv2.solvePnP(MODEL_POINTS, image_points, cam, np.zeros((4, 1)),
                               flags=cv2.SOLVEPNP_ITERATIVE)
    if not ok:
        return None
    rmat, _ = cv2.Rodrigues(rvec)
    sy = math.sqrt(rmat[0, 0] ** 2 + rmat[1, 0] ** 2)
    pitch = math.degrees(math.atan2(rmat[2, 1], rmat[2, 2]))
    yaw = math.degrees(math.atan2(-rmat[2, 0], sy))
    roll = math.degrees(math.atan2(rmat[1, 0], rmat[0, 0]))
    return yaw, pitch, roll


class NeutralPose:
    """Running calibration of a candidate's neutral (looking-at-paper) pose."""

    def __init__(self, calibration_frames: int = 150):
        self.n, self.target, self.sum = 0, calibration_frames, np.zeros(3)

    @property
    def ready(self) -> bool:
        return self.n >= self.target

    def add(self, pose) -> None:
        if not self.ready:
            self.sum += np.array(pose)
            self.n += 1

    def relative(self, pose) -> np.ndarray:
        return np.array(pose) - self.sum / max(self.n, 1)
