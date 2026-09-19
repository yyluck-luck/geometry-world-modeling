#!/usr/bin/env python3
"""Independent exact-arithmetic reference cases. No S81 implementation or real inputs.

This tests the mathematical expectations below, not a production runner.
Run once to write SYNTHETIC_REVIEW.json beside this file.
"""
from fractions import Fraction as Q
from pathlib import Path
import datetime
import hashlib
import json
import math
import sys


def as_q(value):
    return value if isinstance(value, Q) else Q(value)


def matvec(matrix, vector):
    return tuple(sum((as_q(a) * as_q(b) for a, b in zip(row, vector)), Q(0)) for row in matrix)


def transpose(matrix):
    return tuple(zip(*matrix))


def camera_transform(point, source_rotation, source_center, target_rotation, target_center):
    world_offset = tuple(a + as_q(b) - as_q(c) for a, b, c in zip(
        matvec(source_rotation, point), source_center, target_center))
    return matvec(transpose(target_rotation), world_offset)


def project(point, fx=1, fy=1, cx=0, cy=0, z_epsilon=Q(1, 10**9)):
    x, y, z = map(as_q, point)
    if z <= z_epsilon:
        return None
    return (as_q(fx) * x / z + as_q(cx), as_q(fy) * y / z + as_q(cy))


def unproject_z(xy, z, fx=1, fy=1, cx=0, cy=0):
    u, v = map(as_q, xy)
    z = as_q(z)
    return ((u - as_q(cx)) * z / as_q(fx), (v - as_q(cy)) * z / as_q(fy), z)


def inverse_nominal_crop(xy):
    # Frozen old-K convention: no new half-pixel correction.
    u, v = map(as_q, xy)
    return ((u + 96) / Q(6, 5), v / Q(6, 5))


def forward_nominal_crop(xy):
    u, v = map(as_q, xy)
    return (u * Q(6, 5) - 96, v * Q(6, 5))


def nearest_half_up(value):
    # Exact floor(v+0.5), deliberately not Python round (ties to even).
    value = as_q(value) + Q(1, 2)
    return value.numerator // value.denominator


def sample_address(xy, width, height):
    u, v = map(as_q, xy)
    if not (0 <= u < width and 0 <= v < height):
        return {'status': 'CONTINUOUS_OUTSIDE', 'index': None}
    index = (nearest_half_up(u), nearest_half_up(v))
    if not (0 <= index[0] < width and 0 <= index[1] < height):
        return {'status': 'ROUNDED_INDEX_OUTSIDE', 'index': index}
    return {'status': 'VALID_ADDRESS', 'index': index}


def valid_depth(value):
    return math.isfinite(float(value)) and value > 0


def json_value(value):
    if isinstance(value, Q):
        return {'exact': str(value), 'float': float(value)}
    if isinstance(value, tuple):
        return [json_value(v) for v in value]
    if isinstance(value, dict):
        return {k: json_value(v) for k, v in value.items()}
    return value


def main():
    started = datetime.datetime.now(datetime.timezone.utc).isoformat()
    checks = []

    def expect(case, actual, expected, reason):
        checks.append({'case': case, 'passed': actual == expected,
                       'actual': json_value(actual), 'expected': json_value(expected),
                       'reason': reason})

    identity = ((1, 0, 0), (0, 1, 0), (0, 0, 1))
    origin = (0, 0, 0)
    # 1. Identity camera: projection recovers a subpixel feature exactly.
    xy = (Q(241, 4), Q(163, 4))
    point = unproject_z(xy, 2, fx=100, fy=100, cx=50, cy=40)
    expect('zero_motion_subpixel_identity', project(camera_transform(point, identity, origin, identity, origin),
            fx=100, fy=100, cx=50, cy=40), xy, 'No motion; no rounding of the feature ray.')

    # 2. Camera moves right by 1/2 m: fixed point shifts left by 25 px at Z=2 m.
    moved = camera_transform((0, 0, 2), identity, origin, identity, (Q(1, 2), 0, 0))
    expect('known_translation_camera_space', moved, (Q(-1, 2), Q(0), Q(2)), 'Use Rj.T*(Ri*Xs+ci-cj), not ci+cj.')
    expect('known_translation_pixel_direction', project(moved, fx=100, fy=100, cx=50, cy=40),
           (Q(25), Q(40)), 'Right-moving camera gives left-moving fixed point.')

    # 3. Z and range differ along q=(3/4,0,1), whose norm is exactly 5/4.
    ray = (Q(3, 4), Q(0), Q(1))
    expect('ray_norm_squared', sum(x*x for x in ray), Q(25, 16), 'Exact norm is 5/4, not 1.')
    range_point = tuple(Q(10) * x / Q(5, 4) for x in ray)
    z_point = unproject_z((Q(3, 4), 0), 10)
    expect('range_10m_point', range_point, (Q(6), Q(0), Q(8)), 'Range 10 m corresponds to optical Z 8 m.')
    expect('z_10m_point', z_point, (Q(15, 2), Q(0), Q(10)), 'Optical Z 10 m is not range 10 m.')
    expect('range_target_projection', project(camera_transform(range_point, identity, origin, identity, (2, 0, 0))),
           (Q(1, 2), Q(0)), 'Range-correct target coordinate.')
    expect('z_target_projection', project(camera_transform(z_point, identity, origin, identity, (2, 0, 0))),
           (Q(11, 20), Q(0)), 'Mistaking range for Z changes the expected target coordinate.')

    # 4. Old geometric K convention and inverse crop, no payload resampling.
    expect('inverse_crop_top_left', inverse_nominal_crop((0, 0)), (Q(80), Q(0)), '576 x=0 maps to original x=80.')
    expect('inverse_crop_bottom_right', inverse_nominal_crop((575, 575)),
           (Q(3355, 6), Q(2875, 6)), 'Last feature coordinates are subpixel native addresses.')
    native_xy = (Q(651, 2), Q(501, 2))
    expect('crop_round_trip', inverse_nominal_crop(forward_nominal_crop(native_xy)), native_xy,
           'Pure affine coordinate round trip; not a claim of RGB pixel identity under area interpolation.')

    # 5. Half-up ties and explicit continuous/index bounds.
    for value, expected in [(Q(1, 2), 1), (Q(5, 2), 3), (Q(2499, 1000), 2), (Q(-1, 2), 0), (Q(-3, 2), -1)]:
        expect('floor_half_up_' + str(value), nearest_half_up(value), expected, 'floor(x+0.5), including exact ties.')
    expect('negative_source_coordinate', sample_address((Q(-1, 10), 0), 640, 480),
           {'status': 'CONTINUOUS_OUTSIDE', 'index': None}, 'Do not clip negative coordinates into pixel zero.')
    expect('continuous_right_boundary', sample_address((640, 100), 640, 480),
           {'status': 'CONTINUOUS_OUTSIDE', 'index': None}, 'Right boundary is excluded.')
    expect('rounding_beyond_right_boundary', sample_address((Q(6396, 10), 100), 640, 480),
           {'status': 'ROUNDED_INDEX_OUTSIDE', 'index': (640, 100)}, 'In continuous domain, but rounded address is invalid.')
    expect('last_valid_depth_address', sample_address(inverse_nominal_crop((575, 575)), 640, 480),
           {'status': 'VALID_ADDRESS', 'index': (559, 479)}, 'Do not resize or fill depth in this reference case.')

    # 6. Zero/negative/nonfinite depth must be unknown, not a zero error.
    for label, value, expected in [('zero', 0, False), ('negative', -1, False),
                                  ('nan', float('nan'), False), ('infinity', float('inf'), False),
                                  ('positive', Q(1, 5000), True)]:
        expect('depth_' + label, valid_depth(value), expected,
               '1/5000 is only a synthetic positive number, not a verified data encoding factor.')

    # 7. In front but outside the target FOV still has a finite descriptive error.
    outside_point = (6, 0, 1)
    outside_xy = project(outside_point, fx=100, fy=100, cx=50, cy=40)
    expect('outside_target_fov_projection', outside_xy, (Q(650), Q(40)), 'Projected location exists outside width 576.')
    expect('outside_target_fov_flag', 0 <= outside_xy[0] < 576 and 0 <= outside_xy[1] < 576,
           False, 'Out of FOV is not inferred occlusion.')
    expect('outside_target_error_squared', (outside_xy[0]-Q(550))**2 + (outside_xy[1]-Q(40))**2,
           Q(10000), '100 px error remains defined; do not remove it from all-valid summary.')

    # 8. Point behind/on the camera cannot be divided into a valid visible projection.
    behind = camera_transform((0, 0, 2), identity, origin, identity, (0, 0, 3))
    expect('behind_camera_coordinates', behind, (Q(0), Q(0), Q(-1)), 'Target camera passes the source point.')
    expect('behind_camera_projection', project(behind), None, 'No e=0 substitute.')
    expect('camera_plane_projection', project((1, 0, 0)), None, 'Z=0 cannot be divided.')
    expect('at_z_epsilon', project((0, 0, Q(1, 10**9))), None, 'Strict Z>epsilon required.')
    flipped = camera_transform((0, 0, 2), identity, origin,
                               ((-1, 0, 0), (0, 1, 0), (0, 0, -1)), origin)
    expect('rotation_180_y_behind', flipped, (Q(0), Q(0), Q(-2)), 'Do not add a consumer-axis flip to optical c2w.')

    # Additional exact metric counterexample: point-to-line and point-to-point differ.
    expected_target, accepted_target = (Q(25), Q(40)), (Q(55), Q(40))
    expect('same_epipolar_line_but_30px_error',
           ((accepted_target[0]-expected_target[0])**2 + (accepted_target[1]-expected_target[1])**2,
            abs(accepted_target[1]-expected_target[1])),
           (Q(900), Q(0)), 'Along-line displacement is invisible to target point-to-line distance.')

    source = Path(__file__).resolve()
    receipt = {'schema': 'S81_INDEPENDENT_PURE_MATH_REFERENCE_V1',
               'started_at_utc': started,
               'completed_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
               'status': 'REFERENCE_CASES_PASS' if all(c['passed'] for c in checks) else 'REFERENCE_CASES_FAILED',
               'source_path': str(source), 'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
               'arithmetic': 'Python standard-library Fraction; exact expected values. No numpy/model imports.',
               'checks_count': len(checks), 'checks_passed': sum(c['passed'] for c in checks),
               'checks': checks,
               'scope': {'candidate_implementation_read': False, 'candidate_implementation_executed': False,
                         'real_rgb_reads': 0, 'real_depth_reads': 0, 'real_camera_or_npz_reads': 0,
                         'network_calls': 0, 'model_calls': 0, 'new_method_validated': False},
               'limits': 'PASS validates these reference calculations only. Does not approve future S81 code, data alignment, depth semantics, actual experiment or physical correspondence truth.'}
    destination = source.with_name('SYNTHETIC_REVIEW.json')
    with destination.open('x', encoding='utf-8') as handle:
        json.dump(receipt, handle, ensure_ascii=False, indent=2)
        handle.write('\n')
    print(json.dumps({k: receipt[k] for k in ['status','checks_count','checks_passed','source_sha256']}))
    return 0 if receipt['status'] == 'REFERENCE_CASES_PASS' else 1


if __name__ == '__main__':
    sys.exit(main())
