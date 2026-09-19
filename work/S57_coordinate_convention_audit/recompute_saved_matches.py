"""Post-exposure observer correction; JSON correspondences only, no pixels/models."""
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter
import hashlib
import json
import time
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
META = ROOT / 'work/S57_camera_observer_calibration/CAMERA_METADATA_BINDING.json'
SAVED = ROOT / 'results/S57_B0_C1_camera_observer_exploration/ALL_30_PAIRS.json'
CAL = ROOT / 'work/S57_camera_observer_calibration/CALIBRATION.json'
PIPE = ROOT / 'work/S20_environment/isolated_vmem_source/modeling/pipeline.py'
UTIL = ROOT / 'work/S20_environment/isolated_vmem_source/utils/util.py'
NAV = ROOT / 'work/S20_environment/isolated_vmem_source/navigation.py'
OBS = ROOT / 'work/S57_camera_observer_calibration/observer.py'


def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def project(H, p):
    z = (H @ np.concatenate([p, np.ones((len(p), 1))], axis=1).T).T
    assert np.isfinite(z).all() and (np.abs(z[:, 2]) > 1e-12).all()
    return z[:, :2] / z[:, 2:]


def residual(H, p, q, h, w):
    forward = np.linalg.norm(project(H, p) - q, axis=1)
    backward = np.linalg.norm(project(np.linalg.solve(H, np.eye(3)), q) - p, axis=1)
    r = (forward + backward) / 2
    x = np.clip((p[:, 0] * 4 / w).astype(int), 0, 3)
    y = np.clip((p[:, 1] * 4 / h).astype(int), 0, 3)
    cells = y * 4 + x
    med = [float(np.median(r[cells == c])) if np.any(cells == c) else None for c in range(16)]
    return {'cell_balanced_median_px': float(np.median([v for v in med if v is not None])),
            'median_px': float(np.median(r)), 'p90_px': float(np.quantile(r, .9)),
            'per_cell_median_px': med, 'all_match_symmetric_px': r.tolist()}


def classify(m, req, displacement, t):
    # Same frozen matching/coverage/coherence gate and decision boundaries.
    if m['status'] != 'MEASURED_UNCLASSIFIED':
        return 'UNKNOWN_MATCHING'
    if (m['match_count'] < t['min_matches']
        or m['source_coverage']['supported'] < t['min_supported_source_cells']
        or m['target_coverage']['supported'] < t['min_supported_target_cells']
        or m['fitted_forward_inlier_fraction'] < t['min_fitted_inlier_fraction']
        or m['fitted']['cell_balanced_median_px'] > t['residual_limit_px']):
        return 'UNKNOWN_COVERAGE_OR_MATCH_COHERENCE'
    identity = m['identity']['cell_balanced_median_px']
    if displacement <= 2*t['residual_limit_px']:
        return 'IDENTITY_ENDPOINT_ONLY' if identity <= t['residual_limit_px'] else 'UNKNOWN_SUBRESOLUTION_REQUEST'
    if req <= t['residual_limit_px'] and identity-req >= t['separation_margin_px']:
        return 'CONSISTENT_WITH_CORRECTED_NOMINAL_REQUEST'
    if identity <= t['residual_limit_px'] and req-identity >= t['separation_margin_px']:
        return 'STATIC_LIKE_MATCHED_SUPPORT'
    if req > t['residual_limit_px'] and req-m['fitted']['cell_balanced_median_px'] >= t['separation_margin_px']:
        return 'INCONSISTENT_WITH_CORRECTED_REQUEST_ON_MATCHED_SUPPORT'
    return 'UNKNOWN_AMBIGUOUS'


def main():
    start = datetime.now(timezone.utc).isoformat(); timer = time.monotonic()
    inputs = {str(p.relative_to(ROOT)): digest(p) for p in [META, SAVED, CAL, PIPE, UTIL, NAV, OBS]}
    metadata = json.loads(META.read_text()); saved = json.loads(SAVED.read_text()); cal = json.loads(CAL.read_text())
    assert saved['pair_denominator'] == 30
    assert cal['status'] == 'CALIBRATED_ON_SINGLE_SYNTHETIC_TEXTURE_ONLY'
    assert digest(CAL) == saved['calibration_sha256']
    source_binding = {}
    for row, v in metadata['rows'].items():
        mp = Path(v['generation_manifest_path'])
        assert digest(mp) == v['generation_manifest_sha256']
        sources = json.loads(mp.read_text())['source_identities']
        source_binding[row] = {str(p.relative_to(ROOT)): {'actual': digest(p), 'bound': sources[str(p)]}
                               for p in [PIPE, UTIL, NAV]}
        assert all(vv['actual'] == vv['bound'] for vv in source_binding[row].values())
    D = np.diag([1., -1., -1.]); reports = {}; original_max_error = 0.; point_count = 0
    for row, v in saved['rows'].items():
        reports[row] = []
        frames = metadata['rows'][row]['frames']
        for old in v['pairs']:
            i, j = old['pair']; m = old['measurement']
            p = np.asarray(m['points1']); q = np.asarray(m['points2']); point_count += len(p)
            Ki = np.asarray(frames[i]['K_opencv_index']); Kj = np.asarray(frames[j]['K_opencv_index'])
            Ri = np.asarray(frames[i]['c2w'])[:3, :3]; Rj = np.asarray(frames[j]['c2w'])[:3, :3]
            # Source-derived local basis change at pipeline.py:1129, applied to ALL c2ws.
            H = Kj @ np.linalg.solve(Rj @ D, Ri @ D) @ np.linalg.solve(Ki, np.eye(3))
            H /= H[2, 2]
            h, w = m['shape1'][:2]
            old_check = residual(np.asarray(m['requested_H']), p, q, h, w)
            original_max_error = max(original_max_error, abs(old_check['cell_balanced_median_px'] - m['requested']['cell_balanced_median_px']))
            corrected = residual(H, p, q, h, w)
            flow = project(H, p) - p
            displacement = float(np.median(np.linalg.norm(flow, axis=1)))
            denom = float(np.sum(flow**2))
            flow_projection = float(np.sum((q-p)*flow)/denom) if denom > 1e-12 else None
            verdict = classify(m, corrected['cell_balanced_median_px'], displacement, cal['thresholds'])
            if old['verdict'] == 'UNKNOWN_COVERAGE_OR_MATCH_COHERENCE':
                assert verdict == old['verdict']
            reports[row].append({'pair': old['pair'], 'match_count': m['match_count'],
                                 'original_verdict': old['verdict'], 'corrected_verdict': verdict,
                                 'source_supported_cells': m['source_coverage']['supported'],
                                 'target_supported_cells': m['target_coverage']['supported'],
                                 'old_requested_residual_px': m['requested']['cell_balanced_median_px'],
                                 'identity_residual_px': m['identity']['cell_balanced_median_px'],
                                 'fitted_residual_px': m['fitted']['cell_balanced_median_px'],
                                 'corrected_requested_H': H.tolist(), 'corrected_requested_residual': corrected,
                                 'corrected_requested_median_displacement_px': displacement,
                                 'corrected_observed_flow_projection_on_request': flow_projection})
    assert sum(len(v) for v in reports.values()) == 30
    after = {str(p.relative_to(ROOT)): digest(p) for p in [META, SAVED, CAL, PIPE, UTIL, NAV, OBS]}
    assert inputs == after
    result = {'schema': 's57-post-exposure-source-derived-coordinate-correction-v1',
              'started_utc': start, 'completed_utc': datetime.now(timezone.utc).isoformat(),
              'elapsed_seconds': time.monotonic()-timer, 'numpy_version': np.__version__,
              'evidence_kind': 'SAVED_CORRESPONDENCE_RECOMPUTATION_NOT_NEW_GENERATION_OR_PIXEL_READ',
              'source_derived_D': D.tolist(), 'corrected_formula': 'Kj inv(Rj D) (Ri D) inv(Ki)',
              'source_binding': source_binding, 'input_sha256_before_and_after_equal': inputs,
              'original_residual_independent_max_error_px': original_max_error,
              'pair_denominator': 30, 'saved_correspondence_count': point_count,
              'thresholds_unchanged': cal['thresholds'], 'rows': reports,
              'counts': {k: dict(Counter(p['corrected_verdict'] for p in v)) for k, v in reports.items()},
              'pixels_read': 0, 'models_loaded': 0, 'new_model_calls': 0, 'C2_reads': 0,
              'new_method_validated': False, 'novelty_authorization': 'NONE',
              'scope': 'Correct observer convention, retain all original matches and unknown coverage; no baseline improvement or calibrated physical camera claim'}
    target = OUT / 'ALL_30_SOURCE_D_CORRECTION.json'
    with target.open('x') as f: json.dump(result, f, ensure_ascii=False, indent=2, allow_nan=False); f.write('\n')
    print(json.dumps({'output': str(target), 'sha256': digest(target), 'counts': result['counts'],
                      'original_residual_max_error_px': original_max_error,
                      'pairs': {k: [{'pair': p['pair'], 'old': p['old_requested_residual_px'],
                                     'new': p['corrected_requested_residual']['cell_balanced_median_px'],
                                     'projection': p['corrected_observed_flow_projection_on_request'],
                                     'verdict': p['corrected_verdict']} for p in v] for k, v in reports.items()}}, indent=2))


if __name__ == '__main__':
    main()
