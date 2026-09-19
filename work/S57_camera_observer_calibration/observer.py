"""Small SIFT/homography observer; no camera estimation or model imports."""
from pathlib import Path
import hashlib
import json
import cv2
import numpy as np

PARAMETERS = dict(sift_nfeatures=5000, sift_nOctaveLayers=3,
                  sift_contrastThreshold=0.04, sift_edgeThreshold=10,
                  sift_sigma=1.6, ratio=0.75, grid_rows=4, grid_cols=4,
                  cell_min_matches=3, ransac_threshold_px=3.0,
                  ransac_max_iters=2000, ransac_confidence=0.995,
                  random_seed=57, cpu_threads=1)
PAIRS = sorted(set([(i, i + 1) for i in range(8)] + [(0, j) for j in range(1, 9)]))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_json(path, obj):
    with Path(path).open('x') as stream:
        json.dump(obj, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')


def configure():
    cv2.setNumThreads(PARAMETERS['cpu_threads'])
    cv2.setRNGSeed(PARAMETERS['random_seed'])


def rotation_y(degrees):
    angle = np.deg2rad(degrees)
    c, s = np.cos(angle), np.sin(angle)
    return np.array([[c, 0., s], [0., 1., 0.], [-s, 0., c]])


def normalized_K_to_index(K, width, height):
    """VMem uses image grid index+0.5; OpenCV keypoint index starts at 0."""
    scale = np.diag([width, height, 1.])
    center = np.array([[1., 0., -.5], [0., 1., -.5], [0., 0., 1.]])
    return center @ scale @ np.asarray(K, dtype=np.float64)


def requested_homography(K1, K2, c2w1, c2w2):
    """Pure rotation image1→image2: K2 inv(R2) R1 inv(K1)."""
    R1 = np.asarray(c2w1, dtype=np.float64)[:3, :3]
    R2 = np.asarray(c2w2, dtype=np.float64)[:3, :3]
    H = K2 @ np.linalg.inv(R2) @ R1 @ np.linalg.inv(K1)
    return H / H[2, 2]


def project(H, points):
    p = np.column_stack([points, np.ones(len(points))]) @ H.T
    if not np.all(np.isfinite(p)) or np.any(np.abs(p[:, 2]) < 1e-12):
        raise ValueError('Undefined projection')
    return p[:, :2] / p[:, 2:3]


def features(rgb):
    if rgb.dtype != np.uint8 or rgb.ndim != 3 or rgb.shape[2] != 3:
        raise ValueError('Expected uint8 RGB')
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    sift = cv2.SIFT_create(nfeatures=PARAMETERS['sift_nfeatures'],
                          nOctaveLayers=PARAMETERS['sift_nOctaveLayers'],
                          contrastThreshold=PARAMETERS['sift_contrastThreshold'],
                          edgeThreshold=PARAMETERS['sift_edgeThreshold'],
                          sigma=PARAMETERS['sift_sigma'])
    keypoints, descriptors = sift.detectAndCompute(gray, None)
    points = np.array([k.pt for k in keypoints], dtype=np.float64).reshape(-1, 2)
    return points, descriptors


def grid_ids(points, shape):
    height, width = shape[:2]
    cols, rows = PARAMETERS['grid_cols'], PARAMETERS['grid_rows']
    x = np.clip((points[:, 0] * cols / width).astype(int), 0, cols - 1)
    y = np.clip((points[:, 1] * rows / height).astype(int), 0, rows - 1)
    return y * cols + x


def coverage(points, shape):
    counts = np.bincount(grid_ids(points, shape), minlength=16)
    return dict(counts=counts.tolist(), occupied=int(np.count_nonzero(counts)),
                supported=int(np.count_nonzero(counts >= PARAMETERS['cell_min_matches'])))


def residual(H, p, q, shape):
    forward = np.linalg.norm(project(H, p) - q, axis=1)
    backward = np.linalg.norm(project(np.linalg.inv(H), q) - p, axis=1)
    symmetric = (forward + backward) / 2.
    cells = grid_ids(p, shape)
    medians = [float(np.median(symmetric[cells == i])) if np.any(cells == i) else None
               for i in range(16)]
    # Every occupied source cell receives one vote; zero-coverage cells remain explicit.
    balanced = float(np.median([x for x in medians if x is not None]))
    return dict(cell_balanced_median_px=balanced, median_px=float(np.median(symmetric)),
                p90_px=float(np.quantile(symmetric, .9)), per_cell_median_px=medians,
                all_match_symmetric_px=symmetric.tolist())


def observe(rgb1, rgb2, H_requested, cached1=None, cached2=None):
    """Measure all mutual ratio matches; never filter primary points by requested H."""
    f1 = features(rgb1) if cached1 is None else cached1
    f2 = features(rgb2) if cached2 is None else cached2
    points1, d1 = f1; points2, d2 = f2
    result = dict(status='UNKNOWN', keypoints=[len(points1), len(points2)],
                  shape1=list(rgb1.shape), shape2=list(rgb2.shape), match_count=0,
                  keypoint_coverage1=coverage(points1, rgb1.shape),
                  keypoint_coverage2=coverage(points2, rgb2.shape))
    if d1 is None or d2 is None or min(len(d1), len(d2)) < 2:
        return dict(result, reason='Insufficient descriptors')
    matcher = cv2.BFMatcher(cv2.NORM_L2)
    def selected(a, b):
        return {pair[0].queryIdx: pair[0].trainIdx for pair in matcher.knnMatch(a, b, k=2)
                if len(pair) == 2 and pair[0].distance < PARAMETERS['ratio'] * pair[1].distance}
    forward, reverse = selected(d1, d2), selected(d2, d1)
    indices = sorted((i, j) for i, j in forward.items() if reverse.get(j) == i)
    if not indices:
        return dict(result, reason='No mutual ratio matches')
    p = points1[[i for i, _ in indices]]; q = points2[[j for _, j in indices]]
    result.update(match_count=len(p), match_fraction_of_source_keypoints=len(p)/len(points1),
                  unmatched_source_keypoint_fraction=1.-len(p)/len(points1),
                  source_coverage=coverage(p, rgb1.shape), target_coverage=coverage(q, rgb2.shape),
                  points1=p.tolist(), points2=q.tolist(), requested_H=H_requested.tolist())
    if len(p) < 4:
        return dict(result, reason='Fewer than four matches; homography unidentified')
    result['requested'] = residual(H_requested, p, q, rgb1.shape)
    result['identity'] = residual(np.eye(3), p, q, rgb1.shape)
    requested_flow = project(H_requested, p) - p
    observed_flow = q - p
    denominator = float(np.sum(requested_flow**2))
    result['observed_flow_projection_on_request'] = (
        float(np.sum(observed_flow * requested_flow)/denominator) if denominator > 1e-12 else None)
    result['requested_median_displacement_px'] = float(np.median(np.linalg.norm(requested_flow, axis=1)))
    cv2.setRNGSeed(PARAMETERS['random_seed'])
    H, _ = cv2.findHomography(p, q, cv2.RANSAC, PARAMETERS['ransac_threshold_px'],
                             maxIters=PARAMETERS['ransac_max_iters'],
                             confidence=PARAMETERS['ransac_confidence'])
    if H is None or not np.all(np.isfinite(H)) or abs(np.linalg.det(H)) < 1e-12:
        return dict(result, reason='Fitted homography absent or singular')
    try:
        result['fitted'] = residual(H, p, q, rgb1.shape)
    except (ValueError, np.linalg.LinAlgError):
        return dict(result, reason='Fitted homography projection undefined')
    # Independently recompute membership; do not trust an opaque RANSAC mask.
    forward_error = np.linalg.norm(project(H, p) - q, axis=1)
    result.update(status='MEASURED_UNCLASSIFIED', fitted_H=H.tolist(),
                  fitted_forward_inlier_fraction=float(np.mean(forward_error <= PARAMETERS['ransac_threshold_px'])))
    return result


def classify(measurement, calibration):
    if calibration.get('status') != 'CALIBRATED_ON_SINGLE_SYNTHETIC_TEXTURE_ONLY':
        return 'UNKNOWN_CALIBRATION_FAILED'
    if measurement['status'] != 'MEASURED_UNCLASSIFIED':
        return 'UNKNOWN_MATCHING'
    t = calibration['thresholds']
    if (measurement['match_count'] < t['min_matches']
        or measurement['source_coverage']['supported'] < t['min_supported_source_cells']
        or measurement['target_coverage']['supported'] < t['min_supported_target_cells']
        or measurement['fitted_forward_inlier_fraction'] < t['min_fitted_inlier_fraction']
        or measurement['fitted']['cell_balanced_median_px'] > t['residual_limit_px']):
        return 'UNKNOWN_COVERAGE_OR_MATCH_COHERENCE'
    req = measurement['requested']['cell_balanced_median_px']
    identity = measurement['identity']['cell_balanced_median_px']
    if measurement['requested_median_displacement_px'] <= 2*t['residual_limit_px']:
        return 'IDENTITY_ENDPOINT_ONLY' if identity <= t['residual_limit_px'] else 'UNKNOWN_SUBRESOLUTION_REQUEST'
    if req <= t['residual_limit_px'] and identity-req >= t['separation_margin_px']:
        return 'CONSISTENT_WITH_RECORDED_NOMINAL_REQUEST'
    if identity <= t['residual_limit_px'] and req-identity >= t['separation_margin_px']:
        return 'STATIC_LIKE_MATCHED_SUPPORT'
    if req > t['residual_limit_px'] and req-measurement['fitted']['cell_balanced_median_px'] >= t['separation_margin_px']:
        return 'INCONSISTENT_WITH_REQUEST_ON_MATCHED_SUPPORT'
    return 'UNKNOWN_AMBIGUOUS'
