#!/usr/bin/env python3
"""Author-side S14E scorer boundary checks on generated arrays/files only."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import numpy as np
from PIL import Image


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    assert not args.output.exists()
    args.output.mkdir(parents=True)
    source = Path(__file__).with_name('score_s14e_depth.py').resolve()
    spec = importlib.util.spec_from_file_location('s14e_score_under_test', source)
    score = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(score)
    record = dict(schema='s14e-score-artificial-check-v1', started_utc=datetime.now(timezone.utc).isoformat(),
                  kind='Author synthetic tests, not independent audit or real experiment', checks=[],
                  real_npz_arrays_decoded=0, real_png_images_decoded=0, model_calls=0, source_sha256=score.sha(source))

    def check(ok, name):
        record['checks'].append(dict(name=name, passed=bool(ok)))
        assert ok, name

    gt = np.array([[1., 2., 0., np.nan], [4., 8., np.inf, 16.]])
    pred = np.broadcast_to(gt, (3,) + gt.shape).copy()
    rows, arrays = score.compute_metrics(gt, pred, 20, 0)
    check(len(rows) == 3 and rows[0]['gt_valid_count'] == 5, 'GT domain is all five finite positive values')
    check(all(r['delta1_all_gt'] == 1 and r['coverage'] == 1 for r in rows), 'Correct predictions full success')
    check(all(r['own_mae_m'] == r['own_abs_rel'] == r['own_rmse_m'] == 0 for r in rows), 'Correct predictions zero errors')
    check(arrays['gt_valid_mask'].dtype == bool and arrays['common_valid_mask'].sum() == 5, 'Boolean GT/common masks')
    pred[0, 0, 0] = np.nan
    pred[1, 0, 1] = 0
    pred[2, 1, 0] = -1
    rows, arrays = score.compute_metrics(gt, pred, 20, 0)
    check(all(r['delta1_all_gt'] == .8 and r['coverage'] == .8 for r in rows), 'NaN/zero/negative predictions fail full GT domain')
    check(all(r['common_valid_count'] == 2 for r in rows), 'Common domain is intersection of all three methods')
    check(all(r['own_mae_m'] == 0 and r['common_mae_m'] == 0 for r in rows), 'Missing predictions not silently zero-filled into errors')
    one = np.ones((1, 4))
    threshold = np.array([[[1.25, .8, np.nextafter(1.25, 0), 1.]], [[1, 1, 1, 1]], [[np.inf, 1, 1, 1]]])
    rows, arrays = score.compute_metrics(one, threshold, 20, 0)
    check(rows[0]['delta1_success_count'] == 2, 'Strict 1.25 boundary excludes exact 1.25 and inverse .8')
    check(rows[2]['delta1_success_count'] == 3 and rows[2]['coverage'] == .75, 'Infinity is missing prediction')
    zero = np.zeros((2, 2))
    rows, _ = score.compute_metrics(zero, np.ones((3, 2, 2)), 20, 0)
    check(all(r['delta1_all_gt'] is None and r['coverage'] is None for r in rows), 'Empty GT gives null primary/coverage')
    check(all(r['own_mae_m'] is None and r['common_mae_m'] is None for r in rows), 'Empty domains give null errors')
    check(all(r['gt_domain_status'] == 'EMPTY_GT_DOMAIN' for r in rows), 'Empty GT status retained')
    pred = np.ones((3, 2, 2)); pred[1] = np.nan
    rows, _ = score.compute_metrics(np.ones((2, 2)), pred, 20, 0)
    check(rows[1]['coverage'] == rows[1]['delta1_all_gt'] == 0, 'All-missing method scores zero primary not null')
    check(rows[1]['own_mae_m'] is None and rows[0]['own_mae_m'] == 0, 'Own domains remain separate')
    check(all(r['common_mae_m'] is None and r['common_valid_count'] == 0 for r in rows), 'Empty common domain all methods null')
    uneven = []
    for qi in range(4):
        g = np.ones((1, qi + 1)); values = np.ones((3, 1, qi + 1)) * (1 if qi % 2 == 0 else 2)
        r, _ = score.compute_metrics(g, values, 20 + qi, qi); uneven += r
    means = score.equal_query_means(uneven)
    check(all(m['means']['delta1_all_gt'] == .5 for m in means), 'Equal-query mean not pixel-weighted')
    check(all(m['contributing_query_counts']['delta1_all_gt'] == 4 for m in means), 'Four contributors explicitly reported')
    try:
        score.compute_metrics(np.ones((2, 2)), np.ones((3, 1, 2)), 20, 0)
    except ValueError:
        check(True, 'Metric broadcasting rejected')
    else:
        check(False, 'Metric broadcasting rejected')
    # An independent index formula checks PIL's exact nearest resize/crop grid.
    y, x = np.mgrid[:480, :640]
    native = ((x + 7 * y) % 65535).astype(np.uint16)
    pil = np.asarray(Image.fromarray(native).resize((299, 224), Image.Resampling.NEAREST).crop((37, 0, 261, 224)))
    sx = np.floor((np.arange(224) + 37 + .5) * 640 / 299).astype(int)
    sy = np.floor((np.arange(224) + .5) * 480 / 224).astype(int)
    check(np.array_equal(pil, native[sy[:, None], sx[None, :]]), 'All 50176 nearest pixel mappings independently matched')

    def fixture(name, mode):
        base = (args.output / name).resolve(); base.mkdir()
        model = base / 'model'; prepare = base / 'prepare'; model.mkdir(); prepare.mkdir()
        for call in range(5):
            pts = np.zeros((1, 224, 224, 3), dtype=np.float32); pts[..., 2] = 2
            np.savez_compressed(model / f'query_call_{call}.npz', pts3d_in_self_view=pts)
        model_outputs = {v.name: score.sha(v) for v in model.iterdir()}
        model_meta = dict(schema='s14e-state-reuse-queries-v1', status='SUCCESS',
                          started_utc='2021-01-01T00:00:00+00:00', completed_utc='2021-01-01T00:00:01+00:00',
                          parity_all_six_outputs_exact=True, counters=dict(query_calls=5, query_image_encoder_batches=0),
                          query_runs=[dict(call=i, status='PASS') for i in range(5)], output_sha256=model_outputs)
        score.write(model / 'run_metadata.json', model_meta)
        z = np.ones((4, 224, 224), dtype=np.float64); z[:, :, 0] = np.nan
        np.savez_compressed(prepare / 'baselines.npz', history_zbuffer_m=z, history_constant_m=np.ones_like(z))
        np.savez_compressed(prepare / 'condition.npz', artificial_only=np.array([1]))
        score.write(prepare / 'alignment.json', dict(schema='s14e-history-alignment-v1', s_model_per_metric=2.))
        score.write(prepare / 'frozen_manifest.json', dict(artificial_only=True))
        prep_outputs = {v.name: score.sha(v) for v in prepare.iterdir()}
        prep_meta = dict(schema='s14e-known-camera-prepare-v1', status='SUCCESS',
                         started_utc='2020-06-01T00:00:00+00:00', completed_utc='2020-06-01T00:00:01+00:00',
                         output_sha256=prep_outputs, manifest_sha256=score.sha(prepare / 'frozen_manifest.json'))
        score.write(prepare / 'run_metadata.json', prep_meta)
        condition_payload = {v.name: score.sha(v) for v in prepare.iterdir()}
        score.write(prepare / 'condition_seal.json', dict(schema='s14e-condition-seal-v1',
                    sealed_utc='2020-06-01T00:00:02+00:00', condition_npz_sha256=score.sha(prepare / 'condition.npz'),
                    payload_sha256=condition_payload, prepare_manifest_sha256=prep_meta['manifest_sha256']))
        consumed = dict(schema='s14e-state-reuse-manifest-v1', condition_npz=str(prepare / 'condition.npz'),
                        condition_seal=str(prepare / 'condition_seal.json'),
                        identities={str(prepare / v): score.sha(prepare / v) for v in ['condition.npz', 'condition_seal.json']})
        if mode == 'bad_condition_binding': consumed['condition_npz'] = str(base / 'some_other_condition.npz')
        score.write(model / 'frozen_manifest.json', consumed)
        model_meta['manifest_sha256'] = score.sha(model / 'frozen_manifest.json')
        model_meta['output_sha256'] = {v.name: score.sha(v) for v in model.iterdir() if v.name != 'run_metadata.json'}
        score.write(model / 'run_metadata.json', model_meta)
        targets = []
        for i in range(4):
            dp = base / f'generated_depth{i}.png'
            Image.fromarray(np.full((480, 640), 0 if i == 1 else 5000, dtype=np.uint16)).save(dp)
            targets.append(dict(query_index=i + 20, depth_path=str(dp), depth_sha256=score.sha(dp)))
        ids = {str(source): score.sha(source), **{t['depth_path']: t['depth_sha256'] for t in targets}}
        manifest = dict(schema='s14e-score-manifest-v1', frozen_utc='2020-01-01T00:00:00+00:00',
                        runner=str(source), python=sys.executable, identities=ids, model_result_dir=str(model),
                        prepare_result_dir=str(prepare), targets=targets)
        mf = base / 'manifest.json'; score.write(mf, manifest)
        seal = dict(schema='s14e-combined-prediction-seal-v1', sealed_utc='2022-01-01T00:00:00+00:00',
                    identities={str(v): score.sha(v) for d in [model, prepare] for v in d.iterdir()})
        if mode == 'bad_order': seal['sealed_utc'] = '2020-01-01T00:00:00+00:00'
        if mode == 'missing_payload': del seal['identities'][str(prepare / 'condition.npz')]
        sf = base / 'seal.json'; score.write(sf, seal)
        digest = score.sha(sf)
        if mode == 'bad_seal_sha': digest = '0' * 64
        command = [sys.executable, str(source), '--manifest', str(mf), '--prediction-seal', str(sf),
                   '--prediction-seal-sha256', digest, '--output', str(base / 'result')]
        done = subprocess.run(command, text=True, capture_output=True, timeout=60)
        (base / 'stdout.txt').write_text(done.stdout); (base / 'stderr.txt').write_text(done.stderr)
        metadata = json.loads((base / 'result' / 'run_metadata.json').read_text())
        score.write(base / 'caller_receipt.json', dict(command=command, returncode=done.returncode))
        for entry in metadata['reads']:
            require_path = Path(entry['path']).resolve()
            check(require_path.is_relative_to(base), name + ' only generated fixtures decoded: ' + entry['role'])
        return base, done.returncode, metadata

    base, code, meta = fixture('successful_pipeline', 'success')
    check(code == 0 and meta['status'] == 'SUCCESS', 'Synthetic full CLI pipeline succeeds')
    check(meta['counters']['depths_decoded'] == 4 and meta['result_rows'] == 12, 'Four generated depths and all 12 rows')
    check(meta['counters']['npz_arrays_decoded'] == 6, 'Only two baselines and four self arrays decoded')
    check(score.timestamp(meta['seal_verified_utc']) < score.timestamp(meta['first_target_depth_hash_utc'])
          < score.timestamp(meta['first_depth_open_attempt_utc']), 'Actual seal then GT hash then depth open order')
    data = json.loads((base / 'result' / 'metrics.json').read_text())
    check(len(data['rows']) == 12 and all(r['delta1_all_gt'] is None for r in data['rows'][3:6]), 'Empty second query preserved in full output')
    check(data['rows'][0]['delta1_all_gt'] == 1 and data['rows'][1]['coverage'] == 223 / 224, 'Scale is division and sparse column costs coverage')
    with np.load(base / 'result' / 'arrays.npz', allow_pickle=False) as a:
        check(a['prediction_depth_m'].shape == (4, 3, 224, 224), 'Saved complete prediction shape')
        check(a['gt_valid_mask'][1].sum() == 0, 'Saved empty GT mask')
    for mode in ['bad_seal_sha', 'bad_order', 'missing_payload', 'bad_condition_binding']:
        _, code, meta = fixture(mode, mode)
        check(code != 0 and meta['status'] == 'FAILED', mode + ' fails closed')
        check(meta['counters']['depth_open_attempts'] == 0 and 'first_target_depth_hash_utc' not in meta,
              mode + ' zero GT open/hash before valid seal')
    record.update(status='PASS', completed_utc=datetime.now(timezone.utc).isoformat(), check_count=len(record['checks']))
    score.write(args.output / 'receipt.json', record)
    print(json.dumps(dict(status='PASS', check_count=len(record['checks']), source_sha256=record['source_sha256'])))


if __name__ == '__main__':
    main()
