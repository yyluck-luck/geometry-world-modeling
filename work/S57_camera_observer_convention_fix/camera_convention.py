"""Explicit camera conventions for pure-rotation image homographies.

K is already in OpenCV pixel-index coordinates. This module neither estimates K
nor changes feature matching, calibration, classification, or camera positions.
"""
import numpy as np


def requested_homography(K1, K2, c2w1, c2w2):
    """Pure rotation image1→image2: K2 inv(R2) R1 inv(K1)."""
    R1 = np.asarray(c2w1, dtype=np.float64)[:3, :3]
    R2 = np.asarray(c2w2, dtype=np.float64)[:3, :3]
    H = K2 @ np.linalg.inv(R2) @ R1 @ np.linalg.inv(K1)
    return H / H[2, 2]


def camera_to_opencv(c2w, *, convention):
    """Return a 4x4 copy in the ray consumer's OpenCV camera basis.

    'vmem_stored': pipeline.py:1129 right-multiplies by diag(1,-1,-1,1).
    'opencv': input is already X-right/Y-down/Z-forward; make no axis change.
    Translation is unchanged. Do not pass an already converted camera as stored.
    """
    camera = np.array(c2w, dtype=np.float64, copy=True)
    if camera.shape != (4, 4):
        raise ValueError('Expected one 4x4 camera-to-world matrix')
    if convention == 'vmem_stored':
        camera[:, [1, 2]] *= -1
    elif convention != 'opencv':
        raise ValueError("convention must be 'vmem_stored' or 'opencv'")
    return camera


def requested_homography_with_convention(K1, K2, c2w1, c2w2, *, convention):
    """Construct H after an explicit basis conversion of BOTH cameras.

    Only rotations enter H, as in the original function. Scene-point use requires
    the existing pure-rotation assumption; translation/parallax is not modeled.
    For mixed conventions, convert each camera separately and call the generic
    requested_homography. There is deliberately no guessed/default convention.
    """
    cv1 = camera_to_opencv(c2w1, convention=convention)
    cv2 = camera_to_opencv(c2w2, convention=convention)
    return requested_homography(K1, K2, cv1, cv2)
