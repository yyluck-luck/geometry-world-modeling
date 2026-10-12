#!/usr/bin/env python3
"""Sealed complete-candidate correspondence diagnostic on fixed RGB-D support."""
import argparse
import datetime as dt
import io
import json
from pathlib import Path
import warnings

import numpy as np
from generate_candidates import (sha_file, sha_bytes, publish_json, require,
                                 validate_manifest)

DIAGONAL = 800.0


def now():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def validate_freeze(freeze_path, expected_sha=None):
    if expected_sha is not None:
        require(sha_file(freeze_path) == expected_sha, 'Freeze checksum mismatch')
    freeze = json.loads(freeze_path.read_text())
    for name, digest in freeze['files'].items():
        require(sha_file(freeze_path.parent / name) == digest, f'Frozen file changed: {name}')
    require(sha_file(__file__) == freeze['files']['score_candidates.py'], 'Running scorer differs from freeze')
    return freeze


def validate_runtime(receipt, freeze, pins):
    code = receipt['code_hashes']
    for key in ('generate_candidates.py', 'kps.py'):
        require(code[key] == freeze['files'][key], f'Unfrozen predictor code: {key}')
    for pin in pins['files']:
        path = pin['path']
        if path.endswith('.pth'):
            require(receipt['weight_sha256'] == pin['sha256'], 'Unpinned model weights')
        elif '/extern/CUT3R/' in path:
            key = 'CUT3R/' + path.split('/extern/CUT3R/', 1)[1]
            require(code[key] == pin['sha256'], 'Unpinned CUT3R source: ' + key)
        elif path.endswith('/kps.py'):
            require(code['kps.py'] == pin['sha256'], 'Unpinned KPS')
    env = receipt['environment']
    for key, expected in {'device': 'cpu', 'dtype': 'float32', 'tf32_matmul': False,
                          'tf32_cudnn': False, 'seed': 0, 'niter': 0, 'known_K': False,
                          'threads': 4, 'interop_threads': 1}.items():
        require(env[key] == expected, 'Runtime protocol mismatch: ' + key)


def check_record(directory, window, candidate, manifest_sha, protocol_sha):
    stem = window['window_id'] + '__' + candidate['candidate_id']
    npz, receipt_path = directory / (stem + '.npz'), directory / (stem + '.json')
    require(npz.is_file() and receipt_path.is_file(), f'Missing candidate {stem}')
    receipt = json.loads(receipt_path.read_text())
    require(receipt['status'] == 'OK' and receipt['window'] == window
            and receipt['candidate'] == candidate, f'Identity/status mismatch {stem}')
    require(receipt['manifest_sha256'] == manifest_sha and
            receipt['protocol_sha256'] == protocol_sha, f'Protocol mismatch {stem}')
    require(receipt['target_data_read'] is False and
            all(not p.endswith('.depth.png') for p in receipt['source_files']), 'Depth leakage')
    require(receipt['candidate_sha256'] == sha_file(npz), f'Checksum mismatch {stem}')
    with np.load(npz, allow_pickle=False) as data:
        require(data['depths'].shape == (4, 384, 512), 'Bad depth shape')
        require(data['source_refs'].tolist() == window['source_refs'], 'Source identity mismatch')
        require(data['candidate_order'].tolist() == candidate['order'], 'Order mismatch')
    return {'npz': npz.name, 'npz_sha256': receipt['candidate_sha256'],
            'receipt': receipt_path.name, 'receipt_sha256': sha_file(receipt_path)}, receipt


def seal(manifest_path, protocol_path, directory, out, freeze_path):
    manifest = json.loads(manifest_path.read_text())
    candidates, windows = validate_manifest(manifest)
    freeze = validate_freeze(freeze_path)
    pins = json.loads((freeze_path.parent / 'PINNED_INPUTS.json').read_text())
    expected_code = json.loads((freeze_path.parent / 'FROZEN_CUT3R_CODE.json').read_text())
    records, common = [], None
    for window in windows:
        source_inputs = None
        for candidate in candidates:
            record, receipt = check_record(directory, window, candidate,
                                           sha_file(manifest_path), sha_file(protocol_path))
            validate_runtime(receipt, freeze, pins)
            require(receipt['code_hashes'] == expected_code, 'Runtime code bundle differs from freeze')
            identity = {k: receipt[k] for k in ('code_hashes', 'weight_sha256', 'environment')}
            if common is None:
                common = identity
            require(identity == common, 'Mixed code/weights/runtime across candidates')
            require(receipt['started_utc'] >= freeze['frozen_utc'], 'Inference preceded freeze')
            if source_inputs is None:
                source_inputs = receipt['source_files']
            require(receipt['source_files'] == source_inputs, 'Mixed source inputs within window')
            records.append(record)
    result = {'sealed_utc': now(), 'manifest_sha256': sha_file(manifest_path),
              'protocol_sha256': sha_file(protocol_path), 'freeze_sha256': sha_file(freeze_path),
              'common': common, 'records': records, 'ground_truth_opened': False}
    publish_json(out, result)
    return result


def verify_seal(seal_path, directory, manifest_path, protocol_path):
    result = json.loads(seal_path.read_text())
    require(result['manifest_sha256'] == sha_file(manifest_path) and
            result['protocol_sha256'] == sha_file(protocol_path), 'Seal protocol mismatch')
    manifest = json.loads(manifest_path.read_text())
    expected = {w['window_id'] + '__' + c['candidate_id'] + '.npz'
                for w in manifest['windows'] for c in manifest['candidates']}
    require(len(result['records']) == len(expected) and
            {r['npz'] for r in result['records']} == expected, 'Incomplete seal')
    for record in result['records']:
        require(sha_file(directory / record['npz']) == record['npz_sha256'] and
                sha_file(directory / record['receipt']) == record['receipt_sha256'],
                'Sealed output changed')
    return result


def sampling_grid(stride=4):
    v, u = np.mgrid[0:480:stride, 0:640:stride]
    x = np.rint(((u + .5) * 1.2 - 96) * 512 / 576 - .5).astype(int)
    y = np.rint((v + .5) * 1.2 * 512 / 576 - 64 - .5).astype(int)
    keep = (x >= 0) & (x < 512) & (y >= 0) & (y < 384)
    return u[keep], v[keep], x[keep], y[keep]


def valid_depth(depth, interior, threshold=.05):
    good = np.isfinite(depth) & (depth > 0) & (depth < 10)
    if not interior:
        return good
    out = np.zeros_like(good)
    center = depth[1:-1, 1:-1]
    inside = good[1:-1, 1:-1].copy()
    for neighbor, valid in ((depth[:-2, 1:-1], good[:-2, 1:-1]),
                            (depth[2:, 1:-1], good[2:, 1:-1]),
                            (depth[1:-1, :-2], good[1:-1, :-2]),
                            (depth[1:-1, 2:], good[1:-1, 2:])):
        inside &= valid & (np.abs(center - neighbor) <= threshold)
    out[1:-1, 1:-1] = inside
    return out


def project(u, v, depth, source_pose, target_pose, K):
    rays = np.stack(((u - K[0, 2]) / K[0, 0],
                     (v - K[1, 2]) / K[1, 1], np.ones_like(u)), axis=-1)
    with np.errstate(invalid='ignore', divide='ignore', over='ignore'):
        world = (rays * depth[..., None]) @ source_pose[:3, :3].T + source_pose[:3, 3]
        target = (world - target_pose[:3, 3]) @ target_pose[:3, :3]
        uv = target[..., :2] / target[..., 2, None] * [K[0, 0], K[1, 1]] + [K[0, 2], K[1, 2]]
    z = target[..., 2]
    inside = np.isfinite(uv).all(axis=-1) & np.isfinite(z) & (z > 0)
    inside &= (uv[..., 0] >= 0) & (uv[..., 0] < 640) & (uv[..., 1] >= 0) & (uv[..., 1] < 480)
    return uv, z, inside


def fixed_support(source_depth, target_depth, source_pose, target_pose, K, grid, interior):
    u, v, _, _ = grid
    uv, z, inside = project(u, v, source_depth[v, u], source_pose, target_pose, K)
    keep = valid_depth(source_depth, interior)[v, u] & inside
    ids = np.flatnonzero(keep)
    pixels = np.rint(uv[ids]).astype(int)
    bounded = (pixels[:, 0] >= 0) & (pixels[:, 0] < 640) & (pixels[:, 1] >= 0) & (pixels[:, 1] < 480)
    ids, pixels = ids[bounded], pixels[bounded]
    tx, ty = pixels[:, 0], pixels[:, 1]
    accepted = valid_depth(target_depth, interior)[ty, tx] & (np.abs(target_depth[ty, tx] - z[ids]) <= .05)
    ids = ids[accepted]
    return ids, uv[ids]


def tuple_losses(depths, ids, gt_uv, source_pose, target_pose, K, grid):
    u, v, _, _ = grid
    selected = depths[..., ids]
    uv, _, inside = project(u[ids], v[ids], selected, source_pose, target_pose, K)
    valid = np.isfinite(selected) & (selected > 0) & inside
    losses = np.ones_like(selected, dtype=np.float64)
    distance = np.linalg.norm(uv - gt_uv, axis=-1) / DIAGONAL
    losses[valid] = np.minimum(distance[valid], 1.0)
    return losses, ~valid


def controls(depths):
    """Source-only controls on model-depth samples, shape [candidate,source,pixel]."""
    valid = np.isfinite(depths) & (depths > 0)
    inverse = np.full_like(depths, np.nan, dtype=float)
    np.divide(1., depths, out=inverse, where=valid)
    with warnings.catch_warnings():
        warnings.simplefilter('ignore', category=RuntimeWarning)
        fused = 1. / np.nanmedian(inverse, axis=0)
    scales = []
    pairwise = np.zeros((len(depths), len(depths)))
    for i in range(len(depths)):
        common = valid[0] & valid[i]
        require(common.any(), 'Scale control undefined: no joint positive source depth')
        scales.append(float(np.exp(np.median(np.log(depths[i][common]) - np.log(depths[0][common])))))
        for j in range(i):
            overlap = valid[i] & valid[j]
            require(overlap.any(), 'Medoid undefined: no joint positive source depth')
            distance = float(np.median(np.abs(np.log(depths[i][overlap]) - np.log(depths[j][overlap]))))
            pairwise[i, j] = pairwise[j, i] = distance
    scales = np.asarray(scales)
    require(np.isfinite(scales).all() and (scales > 0).all(), 'Invalid source-only scales')
    medoid = int(np.argmin(pairwise.mean(axis=1)))
    return {'fusion': fused, 'medoid': depths[medoid], 'medoid_index': medoid,
            'scales': scales, 'pairwise_logdepth': pairwise,
            'scale_family': depths[0][None] * scales[:, None, None],
            'normalized_family': depths / scales[:, None, None]}


def oracle_summary(loss, targets):
    means = loss.mean(axis=1)
    index = int(np.argmin(means))
    target_sum = sum(loss[:, targets == t].mean(axis=1).min() * np.sum(targets == t)
                     for t in np.unique(targets))
    return {'fixed_errors': means.tolist(), 'complete_oracle': float(means[index]),
            'complete_oracle_index': index, 'per_target_oracle': float(target_sum / loss.shape[1]),
            'per_tuple_oracle': float(loss.min(axis=0).mean())}


def read_measurement(data_root, window, ref, provenance):
    from PIL import Image
    seq, frame = ref.split('/')
    base = data_root / window['scene_rel'] / seq / ('frame-' + frame)
    def read(suffix):
        path = Path(str(base) + suffix)
        blob = path.read_bytes()
        provenance[path.relative_to(data_root).as_posix()] = sha_bytes(blob)
        return io.BytesIO(blob)
    with Image.open(read('.depth.png')) as image:
        depth = np.asarray(image).astype(np.float64) / 1000.
    pose = np.loadtxt(read('.pose.txt')).reshape(4, 4)
    require(depth.shape == (480, 640), 'Measurement shape mismatch')
    require(np.isfinite(pose).all() and np.allclose(pose[3], [0, 0, 0, 1]) and
            np.allclose(pose[:3, :3].T @ pose[:3, :3], np.eye(3), atol=1e-5) and
            np.isclose(np.linalg.det(pose[:3, :3]), 1, atol=1e-5), 'Invalid measurement pose')
    return depth, pose


def score_window(window, candidates, directory, data_root, grid, provenance):
    depth_list, K, source_poses = [], None, None
    for candidate in candidates:
        with np.load(directory / (window['window_id'] + '__' + candidate['candidate_id'] + '.npz')) as data:
            depth_list.append(data['depths'][:, grid[3], grid[2]].astype(np.float64))
            if K is None:
                K, source_poses = data['K'], data['poses']
            require(np.array_equal(K, data['K']) and np.array_equal(source_poses, data['poses']), 'Candidate camera mismatch')
    depth_list = np.stack(depth_list)
    nuisance = controls(depth_list)  # No measured depths have been opened yet in this window.
    sources = [read_measurement(data_root, window, ref, provenance) for ref in window['source_refs']]
    targets = [read_measurement(data_root, window, ref, provenance) for ref in window['target_refs']]
    for index, (_, pose) in enumerate(sources):
        require(np.allclose(pose, source_poses[index], atol=1e-6), 'Measured/source pose mismatch')
    row = {'window_id': window['window_id'], 'scene': window['scene'],
           'source_only_scales': nuisance['scales'].tolist(),
           'source_only_medoid_index': nuisance['medoid_index'],
           'source_only_pairwise_logdepth': nuisance['pairwise_logdepth'].tolist()}
    families = {'candidate': depth_list, 'scale': nuisance['scale_family'],
                'normalized': nuisance['normalized_family'],
                'single_controls': np.stack((nuisance['fusion'], nuisance['medoid']))}
    for stratum, interior in (('primary', True), ('secondary', False)):
        losses = {key: [] for key in families}
        invalids = {key: [] for key in families}
        target_ids, counts = [], []
        for si, (sd, sp) in enumerate(sources):
            for ti, (td, tp) in enumerate(targets):
                ids, gt_uv = fixed_support(sd, td, sp, tp, K, grid, interior)
                counts.append({'source': si, 'target': ti, 'tuples': len(ids)})
                target_ids.extend([ti] * len(ids))
                for name, family in families.items():
                    loss, invalid = tuple_losses(family[:, si], ids, gt_uv, sp, tp, K, grid)
                    losses[name].append(loss)
                    invalids[name].append(invalid)
        require(len(target_ids) > 0, f'Empty {stratum} support: {window["window_id"]}')
        target_ids = np.asarray(target_ids)
        values = {'tuple_count': len(target_ids), 'support_counts': counts}
        for name in families:
            loss = np.concatenate(losses[name], axis=1)
            values[name] = oracle_summary(loss, target_ids)
            values[name]['invalid_projection_fraction'] = np.concatenate(invalids[name], axis=1).mean(axis=1).tolist()
        row[stratum] = values
    return row


def relative_gain(baseline, candidate):
    require(np.isfinite(baseline) and baseline > 0, 'Headroom undefined for zero/nonfinite baseline')
    return float(1 - candidate / baseline)


def aggregate(rows, stratum='primary'):
    def mean(family, key):
        return np.mean([row[stratum][family][key] for row in rows], axis=0)
    fixed = mean('candidate', 'fixed_errors')
    oracle = float(mean('candidate', 'complete_oracle'))
    single = mean('single_controls', 'fixed_errors')
    scale = float(mean('scale', 'complete_oracle'))
    normalized = float(mean('normalized', 'complete_oracle'))
    return {'windows': len(rows), 'fixed_errors': fixed.tolist(),
            'fixed_capped_epe_pixels': (fixed * DIAGONAL).tolist(),
            'complete_oracle': oracle, 'complete_oracle_capped_epe_pixels': oracle * DIAGONAL,
            'fusion_error': float(single[0]), 'medoid_error': float(single[1]),
            'scale_oracle': scale, 'normalized_oracle': normalized,
            'per_target_oracle': float(mean('candidate', 'per_target_oracle')),
            'per_tuple_oracle': float(mean('candidate', 'per_tuple_oracle')),
            'headroom_vs_c0': relative_gain(fixed[0], oracle),
            'best_fixed_order_index': int(np.argmin(fixed)),
            'gain_vs_best_fixed_order': relative_gain(fixed.min(), oracle),
            'gain_vs_better_single_control': relative_gain(single.min(), oracle),
            'gain_vs_scale_oracle': relative_gain(scale, oracle),
            'normalized_headroom_vs_c0': relative_gain(fixed[0], normalized)}


def verdict(overall, scenes):
    failures = []
    if overall['headroom_vs_c0'] < .10:
        failures.append('whole_clip_headroom_below_10_percent')
    if any(value['headroom_vs_c0'] <= 0 for value in scenes.values()):
        failures.append('not_positive_in_both_scenes')
    if overall['gain_vs_better_single_control'] < .05:
        failures.append('gain_over_single_controls_below_5_percent')
    if overall['gain_vs_best_fixed_order'] < .05:
        failures.append('gain_over_best_fixed_order_below_5_percent')
    if overall['gain_vs_scale_oracle'] < .05:
        failures.append('gain_over_scale_oracle_below_5_percent')
    if overall['normalized_headroom_vs_c0'] < .10:
        failures.append('normalized_headroom_below_10_percent')
    return ('STOP_TESTED_FAMILY' if failures else 'GO_TO_CONSUMER_PILOT'), failures


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['seal', 'score'])
    for name in ('manifest', 'protocol', 'candidates', 'out'):
        parser.add_argument('--' + name, required=True, type=Path)
    parser.add_argument('--freeze', type=Path)
    parser.add_argument('--seal', type=Path)
    parser.add_argument('--data-root', type=Path)
    args = parser.parse_args()
    if args.action == 'seal':
        require(args.freeze is not None, '--freeze required')
        result = seal(args.manifest, args.protocol, args.candidates, args.out, args.freeze)
        print(json.dumps({'sealed_records': len(result['records']), 'sealed_utc': result['sealed_utc']}))
        return
    require(args.seal is not None and args.data_root is not None, '--seal and --data-root required')
    require(not args.out.exists(), 'Refusing to overwrite score output')
    seal_result = verify_seal(args.seal, args.candidates, args.manifest, args.protocol)
    require(args.freeze is not None, '--freeze required for score')
    validate_freeze(args.freeze, seal_result['freeze_sha256'])
    manifest = json.loads(args.manifest.read_text())
    candidates, windows = validate_manifest(manifest)
    grid = sampling_grid(manifest['scoring']['stride'])
    provenance, rows = {}, []
    for window in windows:
        rows.append(score_window(window, candidates, args.candidates, args.data_root, grid, provenance))
        print('[scored] ' + window['window_id'], flush=True)
    primary = aggregate(rows)
    scenes = {scene: aggregate([r for r in rows if r['scene'] == scene])
              for scene in sorted({r['scene'] for r in rows})}
    decision, reasons = verdict(primary, scenes)
    result = {'status': 'COMPLETE', 'evidence_label': 'MEASURED', 'scored_utc': now(),
              'seal_sha256': sha_file(args.seal), 'sealed_utc': seal_result['sealed_utc'],
              'scorer_sha256': sha_file(__file__), 'protocol_sha256': sha_file(args.protocol),
              'manifest_sha256': sha_file(args.manifest), 'measurement_input_hashes': provenance,
              'primary': primary, 'primary_by_scene': scenes, 'secondary': aggregate(rows, 'secondary'),
              'verdict': decision, 'failed_gates': reasons, 'rows': rows,
              'new_method_validated': False, 'novelty_authorization': 'NONE'}
    publish_json(args.out, result)
    print(json.dumps({'verdict': decision, 'primary': primary, 'failed_gates': reasons}, indent=2))


if __name__ == '__main__':
    main()
