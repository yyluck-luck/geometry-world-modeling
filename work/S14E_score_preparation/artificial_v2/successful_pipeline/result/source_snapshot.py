#!/usr/bin/env python3
"""Score four known-camera S14E predictions only after a root-bound combined seal.

No model, target RGB, scale fitting, smoothing, confidence gating or query selection.
"""
from __future__ import annotations
import argparse
import csv
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import sys
import traceback

METHODS = ['ray', 'history_zbuffer', 'history_constant']
QUERIES = [20, 21, 22, 23]
ERROR_KEYS = ['mae_m', 'abs_rel', 'rmse_m']
AVERAGE_KEYS = ['delta1_all_gt', 'coverage'] + [p + k for p in ['own_', 'common_'] for k in ERROR_KEYS]
BASELINE_KEYS = ['history_zbuffer_m', 'history_constant_m']


def utc():
    return datetime.now(timezone.utc).isoformat()


def require(ok, message):
    if not ok:
        raise ValueError(message)


def timestamp(value):
    result = datetime.fromisoformat(value)
    require(result.tzinfo is not None and result.utcoffset() is not None, 'Timestamp requires timezone')
    return result


def canonical(value):
    p = Path(value)
    require(p.is_absolute() and str(p.resolve()) == value, 'Canonical absolute path required: ' + value)
    return p


def sha(path):
    with Path(path).open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def write(path, value):
    Path(path).write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')


def validate_identity_map(identities):
    require(isinstance(identities, dict) and identities, 'Nonempty identity map required')
    for p, digest in identities.items():
        canonical(p)
        require(isinstance(digest, str) and re.fullmatch('[0-9a-f]{64}', digest), 'Invalid SHA256: ' + p)


def error_metrics(pred, gt, mask):
    """Fixed-domain errors; explicit empty/overflow status, never fill missing with zero."""
    import numpy as np
    n = int(mask.sum())
    if not n:
        return dict(status='EMPTY_DOMAIN', **{k: None for k in ERROR_KEYS})
    with np.errstate(over='ignore', invalid='ignore', divide='ignore'):
        residual = pred[mask].astype(np.float64) - gt[mask]
        absolute = np.abs(residual)
        largest = float(np.max(absolute))
        # The scaled form avoids needless squaring/summing overflow for large errors.
        mae = largest * float(np.mean(absolute / largest)) if largest else 0.0
        rmse = largest * math.sqrt(float(np.mean((absolute / largest) ** 2))) if largest else 0.0
        relative = absolute / gt[mask]
        rmax = float(np.max(relative))
        absrel = rmax * float(np.mean(relative / rmax)) if rmax else 0.0
    values = dict(mae_m=mae, abs_rel=absrel, rmse_m=rmse)
    finite = all(math.isfinite(v) for v in values.values())
    return dict(status='OK' if finite else 'NONFINITE_ARITHMETIC',
                **{k: v if math.isfinite(v) else None for k, v in values.items()})


def compute_metrics(gt, predictions, query_index, target_index):
    """Pure numeric boundary used by synthetic tests and the real scorer."""
    import numpy as np
    gt = np.asarray(gt, dtype=np.float64)
    predictions = np.asarray(predictions, dtype=np.float64)
    require(gt.ndim == 2 and predictions.shape == (3,) + gt.shape, 'No metric broadcasting permitted')
    g = np.isfinite(gt) & (gt > 0)
    positive = np.isfinite(predictions) & (predictions > 0)
    own = positive & g[None]
    common = g & positive.all(axis=0)
    success = np.zeros_like(own)
    rows = []
    for mi, method in enumerate(METHODS):
        valid = own[mi]
        with np.errstate(over='ignore', invalid='ignore', divide='ignore'):
            success[mi, valid] = np.maximum(predictions[mi, valid] / gt[valid],
                                           gt[valid] / predictions[mi, valid]) < 1.25
        total, count, succeeded = int(g.sum()), int(valid.sum()), int(success[mi].sum())
        own_errors = error_metrics(predictions[mi], gt, valid)
        common_errors = error_metrics(predictions[mi], gt, common)
        row = dict(query_index=query_index, target_index=target_index, model_call=target_index + 1,
                   method=method, gt_valid_count=total,
                   prediction_positive_finite_count=int(positive[mi].sum()), own_valid_count=count,
                   common_valid_count=int(common.sum()), delta1_success_count=succeeded,
                   delta1_all_gt=succeeded / total if total else None,
                   coverage=count / total if total else None,
                   gt_domain_status='OK' if total else 'EMPTY_GT_DOMAIN',
                   own_error_status=own_errors.pop('status'), common_error_status=common_errors.pop('status'))
        row.update({'own_' + k: v for k, v in own_errors.items()})
        row.update({'common_' + k: v for k, v in common_errors.items()})
        rows.append(row)
    arrays = dict(gt_depth_m=gt, prediction_depth_m=predictions, gt_valid_mask=g,
                  prediction_positive_finite_mask=positive, own_valid_mask=own,
                  common_valid_mask=common, delta1_success_mask=success)
    return rows, arrays


def equal_query_means(rows):
    result = []
    for method in METHODS:
        part = [r for r in rows if r['method'] == method]
        require([r['query_index'] for r in part] == QUERIES, 'Keep all four ordered queries')
        means, counts = {}, {}
        for key in AVERAGE_KEYS:
            values = [r[key] for r in part if r[key] is not None]
            counts[key] = len(values)
            means[key] = math.fsum(v / len(values) for v in values) if values else None
        result.append(dict(method=method, query_count=4, means=means, contributing_query_counts=counts,
                           gt_valid_pixel_visits=sum(r['gt_valid_count'] for r in part),
                           interpretation='Equal-query descriptive means; no independent-scene inference'))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--prediction-seal', type=Path, required=True)
    parser.add_argument('--prediction-seal-sha256', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    require(not args.output.exists(), 'Preserve prior output: use a fresh directory')
    args.output.mkdir(parents=True)
    report = dict(schema='s14e-depth-score-run-v1', status='RUNNING', started_utc=utc(),
                  python=sys.version, executable=sys.executable, reads=[], identity_hashes=[],
                  counters=dict(json_decode_attempts=0, json_decoded=0, identity_hash_attempts=0,
                                identity_hash_successes=0, npz_open_attempts=0, npz_opened=0,
                                npz_array_decode_attempts=0, npz_arrays_decoded=0,
                                depth_open_attempts=0, depth_opened=0, depth_decode_attempts=0,
                                depths_decoded=0, target_rgb_decoded=0, model_calls=0),
                  target_results=[], known_camera_pose_is_shared_input=True,
                  new_model_trained=False, new_scene=False, video_generated=False)

    def phase(name):
        report.update(phase=name, updated_utc=utc())
        write(args.output / 'run_metadata.json', report)
        print(json.dumps(dict(utc=utc(), phase=name)), flush=True)

    def read_json(path, role):
        entry = dict(path=str(path), role=role, format='json', attempted_utc=utc(), completed=False)
        report['reads'].append(entry)
        report['counters']['json_decode_attempts'] += 1
        value = json.loads(Path(path).read_text())
        entry.update(completed=True, completed_utc=utc())
        report['counters']['json_decoded'] += 1
        return value

    def hash_check(path, expected, role):
        entry = dict(path=str(path), role=role, attempted_utc=utc(), completed=False)
        report['identity_hashes'].append(entry)
        report['counters']['identity_hash_attempts'] += 1
        digest = sha(path)
        entry.update(completed=True, sha256=digest, completed_utc=utc())
        require(digest == expected, 'Identity mismatch: ' + str(path))
        report['counters']['identity_hash_successes'] += 1

    try:
        phase('read_static_manifest')
        manifest = read_json(args.manifest, 'static pre-run scoring contract')
        require(manifest['schema'] == 's14e-score-manifest-v1', 'Static manifest schema')
        require(canonical(manifest['runner']) == Path(__file__).resolve(), 'Scorer path')
        require(os.path.realpath(sys.executable) == os.path.realpath(manifest['python']), 'Python identity')
        identities = manifest['identities']
        validate_identity_map(identities)
        require(manifest['runner'] in identities, 'Scorer missing from static freeze')
        hash_check(manifest['runner'], identities[manifest['runner']], 'scorer source before seal')
        targets = manifest['targets']
        require(len(targets) == 4 and [x['query_index'] for x in targets] == QUERIES, 'Four fixed ordered targets')
        depth_paths = [str(canonical(x['depth_path'])) for x in targets]
        require(len(set(depth_paths)) == 4, 'Distinct four target depths required')
        for target in targets:
            require(identities.get(target['depth_path']) == target['depth_sha256'], 'GT identity not pre-frozen')
        model_dir = canonical(manifest['model_result_dir'])
        prepare_dir = canonical(manifest['prepare_result_dir'])
        require(model_dir != prepare_dir, 'Separate model/prepare outputs required')
        report['manifest_sha256'] = sha(args.manifest)
        report['static_frozen_utc'] = manifest['frozen_utc']
        phase('verify_combined_prediction_seal_before_any_gt_file_access')
        hash_check(args.prediction_seal, args.prediction_seal_sha256, 'externally root-bound combined seal')
        seal = read_json(args.prediction_seal, 'combined prediction seal')
        require(seal['schema'] == 's14e-combined-prediction-seal-v1', 'Combined seal schema')
        prediction_ids = seal['identities']
        validate_identity_map(prediction_ids)
        require(not set(depth_paths) & set(prediction_ids), 'GT is not a prediction-seal payload')
        for p, digest in prediction_ids.items():
            hash_check(p, digest, 'combined prediction payload')
        for directory in [model_dir, prepare_dir]:
            require(directory.is_dir(), 'Prediction directory missing')
            members = [p for p in directory.rglob('*') if p.is_file()]
            require(members, 'Empty prediction directory')
            for p in members:
                require(str(p.resolve()) in prediction_ids, 'Unsealed prediction directory member: ' + str(p))
        model_meta = read_json(model_dir / 'run_metadata.json', 'sealed model metadata')
        prep_meta = read_json(prepare_dir / 'run_metadata.json', 'sealed prepare metadata')
        require(model_meta['schema'] == 's14e-state-reuse-queries-v1' and model_meta['status'] == 'SUCCESS', 'Successful model schema/status')
        require(prep_meta['schema'] == 's14e-known-camera-prepare-v1' and prep_meta['status'] == 'SUCCESS', 'Successful prepare schema/status')
        require(model_meta['parity_all_six_outputs_exact'] is True, 'Restored-state parity did not pass')
        require(model_meta['counters']['query_calls'] == 5 and model_meta['counters']['query_image_encoder_batches'] == 0,
                'Model call / target RGB boundary')
        calls = model_meta['query_runs']
        require([x['call'] for x in calls] == [0, 1, 2, 3, 4] and all(x['status'] == 'PASS' for x in calls), 'Complete ordered five model calls')
        for directory, metadata in [(model_dir, model_meta), (prepare_dir, prep_meta)]:
            require(metadata.get('output_sha256'), 'Prediction metadata lacks output identities')
            for name, digest in metadata['output_sha256'].items():
                p = (directory / name).resolve()
                require(p.is_relative_to(directory) and prediction_ids.get(str(p)) == digest, 'Metadata/seal payload mismatch: ' + name)
            require(timestamp(manifest['frozen_utc']) < timestamp(metadata['started_utc']) <= timestamp(metadata['completed_utc'])
                    < timestamp(seal['sealed_utc']) < timestamp(report['started_utc']), 'Freeze/run/seal/score time order')
        for name in ['alignment.json', 'baselines.npz', 'condition.npz', 'condition_seal.json']:
            require(str(prepare_dir / name) in prediction_ids, 'Required prepared payload absent: ' + name)
        for i in range(5):
            require(str(model_dir / f'query_call_{i}.npz') in prediction_ids, 'Missing sealed query call')
        # Two successful directories are not enough: bind the exact consumed conditions
        # to this prepare result, hence to this history-only scale and these baselines.
        model_manifest_path = model_dir / 'frozen_manifest.json'
        prepare_manifest_path = prepare_dir / 'frozen_manifest.json'
        require(model_meta['manifest_sha256'] == prediction_ids.get(str(model_manifest_path)), 'Model manifest provenance')
        require(prep_meta['manifest_sha256'] == prediction_ids.get(str(prepare_manifest_path)), 'Prepare manifest provenance')
        model_manifest = read_json(model_manifest_path, 'sealed model condition provenance')
        require(model_manifest['schema'] == 's14e-state-reuse-manifest-v1', 'Consumed model manifest schema')
        for role, name in [('condition_npz', 'condition.npz'), ('condition_seal', 'condition_seal.json')]:
            expected_path = str(prepare_dir / name)
            require(model_manifest[role] == expected_path and
                    model_manifest['identities'].get(expected_path) == prediction_ids[expected_path],
                    'Model consumed a different prepare condition: ' + role)
        condition_seal = read_json(prepare_dir / 'condition_seal.json', 'sealed prepare-to-model binding')
        require(condition_seal['schema'] == 's14e-condition-seal-v1' and
                condition_seal['condition_npz_sha256'] == prediction_ids[str(prepare_dir / 'condition.npz')],
                'Condition-seal array binding')
        require(condition_seal['prepare_manifest_sha256'] == prep_meta['manifest_sha256'], 'Condition-seal prepare provenance')
        payload = condition_seal['payload_sha256']
        expected_payload = {str(p.relative_to(prepare_dir)) for p in prepare_dir.rglob('*')
                            if p.is_file() and p != prepare_dir / 'condition_seal.json'}
        require(set(payload) == expected_payload, 'Complete prepare payload seal required')
        for name, digest in payload.items():
            require(prediction_ids.get(str((prepare_dir / name).resolve())) == digest, 'Prepare payload/combined-seal mismatch')
        require(timestamp(prep_meta['completed_utc']) <= timestamp(condition_seal['sealed_utc'])
                <= timestamp(model_meta['started_utc']), 'Prepare / condition seal / model start order')
        report.update(seal_verified_utc=utc(), prediction_seal_sha256=args.prediction_seal_sha256,
                      prediction_sealed_utc=seal['sealed_utc'], model_completed_utc=model_meta['completed_utc'],
                      prepare_completed_utc=prep_meta['completed_utc'], combined_prediction_file_count=len(prediction_ids))
        phase('combined_seal_verified')
        for p, digest in identities.items():
            if p in depth_paths and 'first_target_depth_hash_utc' not in report:
                report['first_target_depth_hash_utc'] = utc()
            hash_check(p, digest, 'static identity after prediction-seal verification')
        import numpy as np
        from PIL import Image
        report['numpy_version'] = np.__version__
        report['pillow_version'] = Image.__version__
        alignment = read_json(prepare_dir / 'alignment.json', 'sealed history-only scale')
        require(alignment['schema'] == 's14e-history-alignment-v1', 'Alignment schema')
        scale = alignment['s_model_per_metric']
        require(isinstance(scale, (float, int)) and not isinstance(scale, bool) and math.isfinite(scale) and scale > 0,
                'Finite positive model-per-meter scale required')
        report['s_model_per_metric'] = scale

        def read_npz(path, keys, role, strict_keys=False):
            entry = dict(path=str(path), role=role, format='npz', attempted_utc=utc(), completed=False, arrays=[])
            report['reads'].append(entry)
            report['counters']['npz_open_attempts'] += 1
            with np.load(path, allow_pickle=False) as source:
                report['counters']['npz_opened'] += 1
                if strict_keys:
                    require(set(source.files) == set(keys), 'NPZ complete key domain: ' + role)
                values = {}
                for key in keys:
                    item = dict(key=key, attempted_utc=utc(), completed=False)
                    entry['arrays'].append(item)
                    report['counters']['npz_array_decode_attempts'] += 1
                    values[key] = source[key].copy()
                    item.update(completed=True, completed_utc=utc(), shape=list(values[key].shape), dtype=str(values[key].dtype))
                    report['counters']['npz_arrays_decoded'] += 1
                entry.update(completed=True, completed_utc=utc())
                return values

        phase('read_only_sealed_scale_and_prediction_arrays')
        baseline = read_npz(prepare_dir / 'baselines.npz', BASELINE_KEYS, 'two fixed baseline predictions', True)
        for key in BASELINE_KEYS:
            require(baseline[key].shape == (4, 224, 224) and baseline[key].dtype == np.float64, 'Baseline schema: ' + key)
        rays = []
        for call in range(1, 5):
            value = read_npz(model_dir / f'query_call_{call}.npz', ['pts3d_in_self_view'], 'new target self pointmap')['pts3d_in_self_view']
            require(value.shape == (1, 224, 224, 3) and value.dtype == np.float32, 'Self pointmap schema')
            with np.errstate(over='ignore', invalid='ignore', divide='ignore'):
                rays.append(value[0, ..., 2].astype(np.float64) / scale)
        predictions = np.stack([np.stack(rays), baseline[BASELINE_KEYS[0]], baseline[BASELINE_KEYS[1]]], axis=1)
        shutil.copy2(args.manifest, args.output / 'frozen_manifest.json')
        shutil.copy2(args.prediction_seal, args.output / 'combined_prediction_seal.json')
        shutil.copy2(__file__, args.output / 'source_snapshot.py')
        (args.output / 'per_query_arrays').mkdir()
        rows, all_arrays = [], []
        for i, target in enumerate(targets):
            entry = dict(path=target['depth_path'], role='sealed-prediction target-depth scoring', format='png',
                         query_index=target['query_index'], attempted_utc=utc(), opened=False, decoded=False)
            report['reads'].append(entry)
            report['counters']['depth_open_attempts'] += 1
            report.setdefault('first_depth_open_attempt_utc', entry['attempted_utc'])
            require(timestamp(report['seal_verified_utc']) < timestamp(entry['attempted_utc']), 'GT open before seal verification')
            phase('first_or_next_target_depth_open_' + str(target['query_index']))
            with Image.open(target['depth_path']) as image:
                entry.update(opened=True, opened_utc=utc(), pil_format=image.format, pil_mode=image.mode)
                report['counters']['depth_opened'] += 1
                require(image.format == 'PNG' and image.size == (640, 480), 'Depth PNG/size contract')
                report['counters']['depth_decode_attempts'] += 1
                image.load()
                entry.update(decoded=True, decoded_utc=utc())
                report['counters']['depths_decoded'] += 1
                raw = np.asarray(image)
                require(raw.shape == (480, 640) and raw.dtype == np.uint16, 'Native uint16 depth contract')
                gt = np.asarray(image.resize((299, 224), Image.Resampling.NEAREST).crop((37, 0, 261, 224)), dtype=np.float64) / 5000.0
                entry.update(native_shape=list(raw.shape), native_dtype=str(raw.dtype), native_nonzero_count=int(np.count_nonzero(raw)))
            new_rows, arrays = compute_metrics(gt, predictions[i], target['query_index'], i)
            rows.extend(new_rows)
            all_arrays.append(arrays)
            np.savez_compressed(args.output / 'per_query_arrays' / f'query{target["query_index"]}.npz', **arrays)
            entry.update(completed=True, completed_utc=utc())
            report['target_results'].append(dict(query_index=target['query_index'], rows=new_rows))
            phase('target_depth_scored_' + str(target['query_index']))
        require(len(rows) == 12 and report['counters']['depths_decoded'] == 4, 'All 12 results required')
        np.savez_compressed(args.output / 'arrays.npz', **{k: np.stack([a[k] for a in all_arrays]) for k in all_arrays[0]})
        summary = dict(schema='s14e-depth-metrics-v1', method_order=METHODS, query_order=QUERIES, rows=rows,
                       equal_query_means=equal_query_means(rows), s_model_per_metric=scale,
                       contract=dict(primary='delta1_all_gt', delta1='max(pred/gt,gt/pred)<1.25; missing fails',
                                     scale='self_z_model / s_model_per_metric; no target fitting',
                                     depth_divisor=5000, resize=[299, 224], crop=[37, 0, 261, 224],
                                     gt_domain='all cropped nonzero measured depth', confidence_filter=False,
                                     smooth_mask=False, independent_scene_count=0),
                       source_seal_sha256=args.prediction_seal_sha256)
        write(args.output / 'metrics.json', summary)
        with (args.output / 'metrics.csv').open('w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
        phase('post_score_identity')
        for p, digest in prediction_ids.items():
            hash_check(p, digest, 'post-score prediction identity')
        for p, digest in identities.items():
            hash_check(p, digest, 'post-score static identity')
        hash_check(args.prediction_seal, args.prediction_seal_sha256, 'post-score seal identity')
        hash_check(args.manifest, report['manifest_sha256'], 'post-score manifest identity')
        report['output_sha256'] = {str(p.relative_to(args.output)): sha(p) for p in sorted(args.output.rglob('*'))
                                  if p.is_file() and p != args.output / 'run_metadata.json'}
        report.update(status='SUCCESS', completed_utc=utc(), phase='complete', result_rows=12,
                      before_after_identity_pass=True, methods=METHODS, queries=QUERIES)
        write(args.output / 'run_metadata.json', report)
        print(json.dumps(dict(status='SUCCESS', result_rows=12, target_depths_decoded=4)), flush=True)
    except BaseException as error:
        report.update(status='FAILED', completed_utc=utc(), error=repr(error), traceback=traceback.format_exc())
        write(args.output / 'run_metadata.json', report)
        print(report['traceback'], file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
