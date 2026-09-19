"""One finite numerical check; existing JSON and source text only, no pixels."""
from pathlib import Path
from datetime import datetime, timezone
import ast
import hashlib
import json
import sys
import time
import numpy as np
from camera_convention import (camera_to_opencv, requested_homography,
                               requested_homography_with_convention)

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
TOLERANCE_PX = 1e-9
TOLERANCE_H = 1e-11


def project(H, points):
    p = H @ np.column_stack([points, np.ones(len(points))]).T
    return (p[:2] / p[2]).T


def direct_source_rays(Ci, Cj, anchor, Ki_pixel_center, Kj_pixel_center,
                       points, *, stored):
    # Independent literal pipeline column operation, not the helper under test.
    cameras = np.array([anchor, Ci, Cj], dtype=np.float64, copy=True)
    if stored:
        cameras[:, :, [1, 2]] *= -1
    extrinsics = np.linalg.inv(cameras)
    # util.py:154-158: E_relative = E_i @ inverse(E_anchor).
    relative = extrinsics @ np.linalg.inv(extrinsics[0])
    p_center = np.column_stack([points + .5, np.ones(len(points))]).T
    camera_grid = np.linalg.solve(Ki_pixel_center, p_center)
    # util.py:78-97: inverse-pose transform of points minus camera center.
    pose_inverse = np.linalg.inv(relative[1])
    grid_anchor = pose_inverse @ np.vstack([camera_grid, np.ones(len(points))])
    center_anchor = pose_inverse @ np.array([0., 0., 0., 1.])
    rays_anchor = grid_anchor[:3] - center_anchor[:3, None]
    rays_anchor /= np.linalg.norm(rays_anchor, axis=0)
    rays_target = relative[2, :3, :3] @ rays_anchor
    pixel_center = Kj_pixel_center @ rays_target
    return (pixel_center[:2] / pixel_center[2]).T - .5


def camera(yaw, pitch, roll, position):
    y, p, r = np.deg2rad([yaw, pitch, roll])
    Ry = np.array([[np.cos(y), 0., np.sin(y)], [0., 1., 0.],
                   [-np.sin(y), 0., np.cos(y)]])
    Rx = np.array([[1., 0., 0.], [0., np.cos(p), -np.sin(p)],
                   [0., np.sin(p), np.cos(p)]])
    Rz = np.array([[np.cos(r), -np.sin(r), 0.],
                   [np.sin(r), np.cos(r), 0.], [0., 0., 1.]])
    C = np.eye(4); C[:3, :3] = Rz @ Ry @ Rx; C[:3, 3] = position
    return C


def main():
    start = datetime.now(timezone.utc).isoformat(); timer = time.monotonic()
    pins = json.loads((HERE / 'SOURCE_PINS.json').read_text())['files']
    for name, expected in pins.items():
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == expected, name
    old_text = (ROOT / 'work/S57_camera_observer_calibration/observer.py').read_text()
    new_text = (HERE / 'camera_convention.py').read_text()
    def generic_ast(text):
        return ast.dump(next(n for n in ast.parse(text).body
                             if isinstance(n, ast.FunctionDef)
                             and n.name == 'requested_homography'))
    assert generic_ast(old_text) == generic_ast(new_text)

    # Explicit artificial parameters, unrelated to TUM or generated-image K.
    Ki = np.array([[520., 7., 301.25], [0., 610., 220.75], [0., 0., 1.]])
    Kj = np.array([[690., -3., 250.5], [0., 570., 310.25], [0., 0., 1.]])
    center_to_index = np.array([[1., 0., -.5], [0., 1., -.5], [0., 0., 1.]])
    Kii, Kji = center_to_index @ Ki, center_to_index @ Kj
    Ci = camera(7., 4., -3., [.4, -.2, .7])
    Cj = camera(-5., -6., 9., [.4, -.2, .7])
    anchor = camera(23., -17., 11., [-.3, .8, .1])
    points = np.array([[0., 0.], [639., 0.], [0., 479.], [639., 479.],
                       [319.5, 239.5], [111.25, 87.75], [500.5, 330.25]])
    Ci_before, Cj_before = Ci.copy(), Cj.copy()
    arbitrary = {}
    for convention in ('vmem_stored', 'opencv'):
        H = requested_homography_with_convention(Kii, Kji, Ci, Cj,
                                                 convention=convention)
        expected = direct_source_rays(Ci, Cj, anchor, Ki, Kj, points,
                                      stored=(convention == 'vmem_stored'))
        err = float(np.max(np.abs(project(H, points) - expected)))
        assert err < TOLERANCE_PX
        identity = requested_homography_with_convention(Kii, Kii, Ci, Ci,
                                                        convention=convention)
        identity_error = float(np.max(np.abs(identity - np.eye(3))))
        assert identity_error < TOLERANCE_H
        arbitrary[convention] = dict(max_ray_difference_px=err,
                                      same_camera_identity_error=identity_error)
    np.testing.assert_array_equal(Ci, Ci_before)
    np.testing.assert_array_equal(Cj, Cj_before)
    cv_copy = camera_to_opencv(Ci, convention='opencv')
    np.testing.assert_array_equal(cv_copy, Ci)
    assert not np.shares_memory(cv_copy, Ci)
    converted = camera_to_opencv(Ci, convention='vmem_stored')
    np.testing.assert_array_equal(converted[:, 3], Ci[:, 3])
    np.testing.assert_array_equal(converted[:, 0], Ci[:, 0])
    generic = requested_homography(Kii, Kji, Ci, Cj)
    cv = requested_homography_with_convention(Kii, Kji, Ci, Cj, convention='opencv')
    np.testing.assert_array_equal(generic, cv)
    wrong = requested_homography_with_convention(Kii, Kji, Ci, Cj,
                                                 convention='vmem_stored')
    sensitivity = float(np.max(np.abs(project(wrong, points) - project(cv, points))))
    assert sensitivity > 1., 'Chosen finite example must expose indiscriminate flipping'

    metadata = json.loads((ROOT / 'work/S57_camera_observer_calibration/CAMERA_METADATA_BINDING.json').read_text())
    audit = json.loads((ROOT / 'work/S57_coordinate_convention_audit/ALL_30_SOURCE_D_CORRECTION.json').read_text())
    expected_pairs = sorted(set([(i, i + 1) for i in range(8)]
                                + [(0, j) for j in range(1, 9)]))
    checks = []
    for row in ('B0', 'C1'):
        assert [tuple(x['pair']) for x in audit['rows'][row]] == expected_pairs
        frames = metadata['rows'][row]['frames']
        for entry in audit['rows'][row]:
            i, j = entry['pair']; fi, fj = frames[i], frames[j]
            H = requested_homography_with_convention(
                np.asarray(fi['K_opencv_index']), np.asarray(fj['K_opencv_index']),
                fi['c2w'], fj['c2w'], convention='vmem_stored')
            err = float(np.max(np.abs(H - np.asarray(entry['corrected_requested_H']))))
            assert err < TOLERANCE_H
            endpoint_error = float(np.max(np.abs(H - np.eye(3)))) if (i, j) == (0, 8) else None
            if endpoint_error is not None:
                assert endpoint_error < TOLERANCE_H
            checks.append(dict(row=row, pair=[i, j], max_H_difference=err,
                               identity_endpoint_error=endpoint_error))
    assert len(checks) == 30
    for name, expected in pins.items():
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == expected, name
    receipt = dict(status='PASS_FINITE_CONVENTION_CHECK_ONLY', started_utc=start,
                   completed_utc=datetime.now(timezone.utc).isoformat(),
                   elapsed_seconds=time.monotonic()-timer, python=sys.version,
                   python_executable=sys.executable, numpy=np.__version__,
                   tolerance_px=TOLERANCE_PX, tolerance_H=TOLERANCE_H,
                   generic_function_AST_unchanged=True, arbitrary_rotation=arbitrary,
                   test_parameters=dict(rotation_composition='Rz(roll) Ry(yaw) Rx(pitch)',
                       Ci_yaw_pitch_roll=[7., 4., -3.], Cj_yaw_pitch_roll=[-5., -6., 9.],
                       anchor_yaw_pitch_roll=[23., -17., 11.], Ki_center=Ki.tolist(),
                       Kj_center=Kj.tolist(), points_index=points.tolist(),
                       calibration_status='ARTIFICIAL_NUMERICAL_PARAMETERS_ONLY'),
                   indiscriminate_flip_difference_px=sensitivity, all_30_H_checks=checks,
                   sources_unchanged=True, pixel_reads=0, model_loads=0,
                   feature_extractions=0, calibration_runs=0, C2_reads=0)
    with (HERE / 'CHECK_RECEIPT.json').open('x') as f:
        json.dump(receipt, f, indent=2, allow_nan=False); f.write('\n')
    print(json.dumps({k: v for k, v in receipt.items()
                      if k not in ('test_parameters', 'all_30_H_checks')}, indent=2))


if __name__ == '__main__':
    main()
