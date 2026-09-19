#!/usr/bin/env python3
"""S27 saved-data post-hoc scale diagnostics. prepare never opens arrays/GT/traces."""
from __future__ import annotations
import argparse
import csv
import hashlib
import io
import json
import math
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
SELF = Path(__file__).resolve()
PARENT = ROOT / 'work/S26B_preparation/run_manifest.json'
PARENT_SHA = '147357aa1b24caeb813c01fd822cb96f754c2573437d0db6ac8a05b7cbd4d90c'
BASE = ROOT / 'results/S26B_consumer_baseline'
OUT = ROOT / 'results/S27_saved_scale_diagnostic'
COUNTS = {'common_old': 4, 'cut3r': 8, 'ttt3r': 8, 'filt3r': 8}
FILES = ('output.npz', 'consumed_inputs.npz', 'pairwise_state.npz', 'optimization_trace.jsonl')
H, W = 384, 512
QUANTILES = (0, .01, .05, .25, .5, .75, .95, .99, 1)
QNAMES = ('min', 'p01', 'p05', 'p25', 'p50', 'p75', 'p95', 'p99', 'max')


def utc():
    return datetime.now(timezone.utc).isoformat()


def sha_bytes(raw):
    return hashlib.sha256(raw).hexdigest()


def sha_file(path):
    with Path(path).open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def write_json(path, value):
    Path(path).write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + '\n')


def checked_json(path, expected=None):
    raw = Path(path).read_bytes()
    if expected is not None:
        require(sha_bytes(raw) == expected, f'Identity changed: {path}')
    return json.loads(raw), sha_bytes(raw)


def policy():
    return dict(schema='s27-saved-scale-v1', counts=COUNTS, result_directory=str(OUT),
                hw=[H, W], quantiles=list(QUANTILES), confidence_mask=False, far_cut=False,
                scale_fitting_applied=False, evidence='POST_HOC_SAVED_DATA_DIAGNOSTIC_SEEN_EIGHT_GT',
                metric_rule='S26B_all_valid_GT_invalid_pred_makes_absrel_rmse_null_delta1_failure',
                expected_distribution_rows=132, expected_metric_rows=56, expected_trace_rows=1600,
                expected_aggregate_rows=20, model_runs=0, ga_runs=0)


def prepare():
    target = HERE / 'contract_candidate.json'
    require(not target.exists(), 'Candidate exists; version new work rather than overwrite')
    m, digest = checked_json(PARENT, PARENT_SHA)
    controls = {str(PARENT): digest}
    source_files = [SELF, HERE / 'PROTOCOL.md', ROOT / 'scripts/score_s26b_consumer.py',
                    ROOT / 'scripts/s26b_consumer_baseline.py',
                    ROOT / 'work/S26_consumer_baseline_preparation/saved_heads_adapter.py']
    embedded = ROOT / 'work/S17C_interface_preparation/isolated_vmem_source/extern/CUT3R'
    source_files += [embedded / p for p in ('surfel_inference.py', 'cloud_opt/dust3r_opt/optimizer.py',
                                          'cloud_opt/dust3r_opt/base_opt.py')]
    controls.update({str(p): sha_file(p) for p in source_files})
    datasets, data_ids = {}, {}
    for mode, n in COUNTS.items():
        directory = BASE / mode
        receipt, digest = checked_json(directory / 'receipt.json')
        controls[str(directory / 'receipt.json')] = digest
        require(receipt['status'] == 'PASS' and receipt['manifest_sha256'] == PARENT_SHA,
                f'Producer not complete/bound: {mode}')
        require(receipt['mode'] == mode and receipt['frame_count'] == n, 'Producer domain changed')
        seal, digest = checked_json(directory / 'inputs_seal.json', receipt['inputs_seal_sha256'])
        controls[str(directory / 'inputs_seal.json')] = digest
        require(seal['sensor_depth_used'] is False and seal['manifest_sha256'] == PARENT_SHA, 'Producer GT/parent')
        archive_key = 'common_old_depth_original4' if mode == 'common_old' else mode
        records = m['candidate']['archives'][archive_key]
        require(len(records) == n and [r['index'] for r in records] == list(range(n)), 'Raw domain')
        products = {name: dict(path=str(directory / name), sha256=receipt['outputs'][name]) for name in FILES}
        for r in list(records) + list(products.values()):
            require(Path(r['path']).is_absolute() and len(r['sha256']) == 64, 'Data identity required')
            data_ids[r['path']] = r['sha256']
        datasets[mode] = dict(raw=records, products=products)
    # Byte-equivalence to the preserved original common producer is tested only at run.
    legacy = ROOT / 'results/S26_consumer_baseline/common_old'
    original, digest = checked_json(legacy / 'receipt.json')
    require(original['status'] == 'FAILED', 'Preserve original failed history')
    controls[str(legacy / 'receipt.json')] = digest
    for name in ('output.npz', 'optimization_trace.jsonl'):
        data_ids[str(legacy / name)] = datasets['common_old']['products'][name]['sha256']
    score_receipt, digest = checked_json(BASE / 'scoring/receipt.json')
    require(score_receipt['status'] == 'PASS' and score_receipt['manifest_sha256'] == PARENT_SHA,
            'Existing parent scoring must be complete')
    controls[str(BASE / 'scoring/receipt.json')] = digest
    gt = m['scoring']['gt_depth_frames']
    require(len(gt) == 8 and [r['index'] for r in gt] == list(range(8)), 'All eight GT metadata rows required')
    value = dict(policy=policy(), status='METADATA_CANDIDATE', prepared_utc=utc(),
                 parent_manifest=str(PARENT), parent_sha256=PARENT_SHA,
                 controls=controls, datasets=datasets, data_identities=data_ids, gt=gt,
                 preparation_reads=dict(npz_bytes=0, sensor_png_bytes=0, trace_values=0, model_runs=0, ga_runs=0),
                 known_before_preparation='Root reported common old4 AbsRel 83.3382%, new4 CUT 67.8259%, TTT 93.5431%, FILT 67.5730%; post hoc, not independent verification here.')
    write_json(target, value)
    return dict(status='PREPARED_NOT_RUN', candidate=str(target), sha256=sha_file(target),
                control_count=len(controls), inherited_data_identities=len(data_ids), **value['preparation_reads'])


def verify_identities(identities):
    for p, expected in identities.items():
        require(sha_file(p) == expected, f'File changed: {p}')


def load_npz(record, shapes, dtypes=None):
    import numpy as np
    raw = Path(record['path']).read_bytes()
    require(sha_bytes(raw) == record['sha256'], 'NPZ changed since pre-read seal')
    with np.load(io.BytesIO(raw), allow_pickle=False) as z:
        require(set(z.files) == set(shapes), f'Unexpected archive fields {record["path"]}')
        result = {}
        for k, shape in shapes.items():
            a = z[k]
            dtype = (dtypes or {}).get(k, np.float32)
            require(a.shape == shape and a.dtype == dtype, f'Schema changed: {k} {a.shape} {a.dtype}')
            result[k] = a
    return result


def summary(values):
    import numpy as np
    a = np.asarray(values, dtype=np.float64).ravel()
    finite = np.isfinite(a)
    pos = finite & (a > 0)
    def sub(x):
        if not x.size:
            return dict(count=0, mean=None, quantiles={k: None for k in QNAMES})
        return dict(count=int(x.size), mean=float(x.mean()),
                    quantiles=dict(zip(QNAMES, map(float, np.quantile(x, QUANTILES, method='linear')))))
    return dict(total=int(a.size), finite=int(finite.sum()), nonfinite=int((~finite).sum()),
                positive=int(pos.sum()), zero=int((finite & (a == 0)).sum()), negative=int((finite & (a < 0)).sum()),
                finite_values=sub(a[finite]), positive_values=sub(a[pos]))


def metrics_and_oracle(p, g):
    import numpy as np
    p, g = np.asarray(p, dtype=np.float64), np.asarray(g, dtype=np.float64)
    require(p.shape == (H, W) and g.shape == (H, W), 'Depth grid mismatch')
    v = np.isfinite(g) & (g > 0)
    invalid = (~np.isfinite(p)) | (p <= 0)
    pair = v & ~invalid
    n, ni = int(v.sum()), int((v & invalid).sum())
    ratio = g[pair] / p[pair]
    hits = int((np.maximum(ratio, 1 / ratio) < 1.25).sum())
    row = dict(grid_pixels=int(g.size), gt_valid_pixels=n, gt_invalid_pixels=int(g.size)-n,
               prediction_invalid_all_pixels=int(invalid.sum()), prediction_invalid_on_gt_pixels=ni,
               absrel=None, rmse_m=None, delta1=hits/n if n else None, delta1_success_pixels=hits,
               metric_status='EMPTY_GT' if not n else 'INVALID_PREDICTION' if ni else 'DEFINED',
               oracle_pair_count=int(pair.sum()), oracle_excluded_pixels=int(g.size-pair.sum()),
               sensor_to_prediction_ratio_oracle=summary(ratio), scale_applied=False)
    if n and not ni:
        row.update(absrel=float(np.mean(np.abs(p[v]-g[v])/g[v])),
                   rmse_m=float(np.sqrt(np.mean((p[v]-g[v])**2))))
    return row


def ratio_summary(a, b):
    import numpy as np
    a, b = np.asarray(a, dtype=np.float64), np.asarray(b, dtype=np.float64)
    v = np.isfinite(a) & (a > 0) & np.isfinite(b) & (b > 0)
    return dict(total=int(v.size), valid_pair_count=int(v.sum()), excluded_count=int((~v).sum()),
                ratio=summary(a[v]/b[v]))


def write_csv(path, rows):
    require(rows, 'Refuse empty CSV')
    with Path(path).open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)


def run(contract_path, expected_sha):
    require(not OUT.exists(), 'Output exists; do not overwrite or rerun silently')
    contract_path = Path(contract_path).resolve()
    m, digest = checked_json(contract_path, expected_sha)
    require(m['status'] == 'FROZEN' and m['policy'] == policy(), 'Frozen unchanged diagnostic policy required')
    require(m['parent_manifest'] == str(PARENT) and m['parent_sha256'] == PARENT_SHA, 'Parent changed')
    verify_identities(m['controls'])
    OUT.mkdir()
    receipt = dict(status='RUNNING', started_utc=utc(), contract_sha256=digest,
                   true_npz_decode_started=False, sensor_gt_byte_reads_started=False,
                   model_runs=0, ga_runs=0, evidence=policy()['evidence'])
    write_json(OUT/'receipt.json', receipt)
    try:
        # All saved byte identities (including all traces) verified before any decode/GT.
        verify_identities(m['data_identities'])
        write_json(OUT/'pre_read_seal.json', dict(utc=utc(), contract_sha256=digest,
                   control_identities=m['controls'], data_identities=m['data_identities'],
                   sensor_png_bytes_read_so_far=0, array_decodes_so_far=0))
        import numpy as np
        require(np.__version__ == '1.26.4', 'Use existing NumPy 1.26.4 environment')
        receipt.update(true_npz_decode_started=True, prediction_read_started_utc=utc())
        write_json(OUT/'receipt.json', receipt)
        loaded = {}
        raw_shapes = {'pts3d_in_self_view': (1,H,W,3), 'pts3d_in_other_view': (1,H,W,3),
                      'conf_self': (1,H,W), 'conf': (1,H,W), 'camera_pose': (1,7), 'rgb': (1,H,W,3)}
        for mode, n in COUNTS.items():
            ds = m['datasets'][mode]
            loaded[mode] = dict(raw=[load_npz(r, raw_shapes) for r in ds['raw']],
                output=load_npz(ds['products']['output.npz'], {'depth':(n,H,W),'point_cloud':(n,H,W,3),
                               'conf':(n,H,W),'focal':(n,1),'pp':(n,2),'c2w':(n,4,4)}),
                inputs=load_npz(ds['products']['consumed_inputs.npz'], {'pred_i':(n-1,H*W,3),
                           'pred_j':(n-1,H*W,3),'weight_i':(n-1,H*W),'weight_j':(n-1,H*W),
                           'edge_i':(n-1,),'edge_j':(n-1,)}, {'edge_i':np.int64,'edge_j':np.int64}),
                pair=load_npz(ds['products']['pairwise_state.npz'], {'pw_poses':(n-1,4,4),'adaptors':(n-1,3)}))
            z = loaded[mode]
            require(np.array_equal(z['inputs']['edge_i'], np.zeros(n-1,dtype=np.int64)) and
                    np.array_equal(z['inputs']['edge_j'], np.arange(1,n)), 'Exact star edge mapping required')
            for e in range(n-1):
                require(z['inputs']['pred_i'][e].tobytes() == z['raw'][0]['pts3d_in_self_view'].reshape(-1,3).tobytes(), 'Consumed anchor source differs')
                require(z['inputs']['pred_j'][e].tobytes() == z['raw'][e+1]['pts3d_in_other_view'].reshape(-1,3).tobytes(), 'Consumed other source differs')
        traces = []
        for mode, ds in m['datasets'].items():
            rec = ds['products']['optimization_trace.jsonl']; raw = Path(rec['path']).read_bytes()
            require(sha_bytes(raw) == rec['sha256'], 'Trace changed')
            rows = [json.loads(line) for line in raw.decode().splitlines()]
            require(len(rows) == 400 and [r['iteration'] for r in rows] == list(range(400)), 'Full 400 trace required')
            require(all(math.isfinite(r['loss_before_step']) and math.isfinite(r['lr']) for r in rows), 'Nonfinite trace')
            traces.extend(dict(mode=mode, iteration=r['iteration'], loss_before_step=r['loss_before_step'], lr=r['lr'], historical_utc=r['utc']) for r in rows)
        # The eight GT images are already seen; this is a fresh explicit byte read, not blind evaluation.
        receipt.update(sensor_gt_byte_reads_started=True, sensor_gt_read_started_utc=utc())
        write_json(OUT/'receipt.json', receipt)
        from PIL import Image
        gt, gt_ids = [], {}
        for i, rec in enumerate(m['gt']):
            require(rec['index'] == i, 'GT order changed')
            raw = Path(rec['path']).read_bytes(); require(sha_bytes(raw) == rec['sha256'], 'GT identity changed')
            gt_ids[rec['path']] = rec['sha256']
            with Image.open(io.BytesIO(raw)) as im:
                require(im.format == 'PNG', 'PNG required'); a = np.asarray(im)
            require(a.shape == (480,640) and a.dtype.kind in 'ui' and a.min() >= 0 and a.max() <= 65535, 'Sensor schema')
            yy=((2*np.arange(H)+1)*480)//(2*H); xx=((2*np.arange(W)+1)*640)//(2*W)
            gt.append(a[yy[:,None],xx[None,:]].astype(np.float64)/5000)
        distributions, scores, pairs, summaries, ratio_rows = [], [], [], {}, []
        def add(mode, stage, index, z, edge=None, comparable=True):
            key=dict(mode=mode,stage=stage,index=index,edge=edge)
            distributions.append(dict(**key, coordinate_comparable_to_same_frame_sensor=comparable, distribution=summary(z)))
            if comparable:
                scores.append(dict(**key, **metrics_and_oracle(z,gt[index])))
        for mode,n in COUNTS.items():
            v=loaded[mode]; raw=v['raw']; out=v['output']; inp=v['inputs']; pair=v['pair']
            for i in range(n):
                add(mode,'raw_self_z',i,raw[i]['pts3d_in_self_view'][0,...,2])
                add(mode,'raw_other_z_reference_only',i,raw[i]['pts3d_in_other_view'][0,...,2],comparable=False)
                add(mode,'ga_depth_z',i,out['depth'][i])
                ratio_rows.append(dict(mode=mode,index=i,ga_to_raw_self_ratio=ratio_summary(out['depth'][i],raw[i]['pts3d_in_self_view'][0,...,2])))
            camera_centers=out['c2w'][:,:3,3].astype(np.float64)
            baselines=np.linalg.norm(camera_centers[:,None]-camera_centers[None,:],axis=-1)
            for e,j in enumerate(range(1,n)):
                M=pair['pw_poses'][e].astype(np.float64); a=pair['adaptors'][e].astype(np.float64)
                norms=np.linalg.svd(M[:3,:3],compute_uv=False)
                for side,k,label in [('i',0,'anchor'),('j',j,'other')]:
                    p=inp['pred_'+side][e].reshape(H,W,3).astype(np.float64)
                    add(mode,'consumed_'+label+'_z_reference_only',k,p[...,2],edge=e,comparable=False)
                pairs.append(dict(mode=mode,edge=e,i=0,j=j,
                    scaled_rotation_singular_values=norms.tolist(),
                    stored_scaled_translation=M[:3,3].tolist(),adaptor=a.tolist(),
                    stored_log_weight_anchor=summary(inp['weight_i'][e]),
                    stored_log_weight_other=summary(inp['weight_j'][e])))
            mode_trace=[r for r in traces if r['mode']==mode]
            summaries[mode]=dict(frame_count=n, focal=out['focal'].tolist(), pp=out['pp'].tolist(),
                pairwise_camera_baseline_m=baselines.tolist(), max_camera_baseline_m=float(baselines.max()),
                trace_count=len(mode_trace), first_pre_step_loss=mode_trace[0]['loss_before_step'],
                last_pre_step_loss=mode_trace[-1]['loss_before_step'], minimum_pre_step_loss=min(r['loss_before_step'] for r in mode_trace),
                post_MST_initial_depth='NOT_RECORDED', per_iteration_depth='NOT_RECORDED',
                depth_gradient_or_actual_parameter_updates='NOT_ESTABLISHED_BY_400_STEP_TRACE')
        aggregates=[]
        for mode,n in COUNTS.items():
            groups={'old4':list(range(4))}
            if n==8: groups.update(new4=list(range(4,8)),all8=list(range(8)))
            for stage in ('raw_self_z','ga_depth_z'):
                for group,indices in groups.items():
                    selected=[r for r in scores if r['mode']==mode and r['stage']==stage and r['index'] in indices]
                    require([r['index'] for r in selected]==indices,'Complete aggregation frame list')
                    row=dict(mode=mode,stage=stage,group=group,frame_indices=indices,frame_count=len(indices))
                    for metric in ('absrel','rmse_m','delta1'):
                        vals=[r[metric] for r in selected]
                        row[metric]=math.fsum(vals)/len(vals) if all(x is not None for x in vals) else None
                        row[metric+'_defined_frames']=sum(x is not None for x in vals)
                    row['gt_valid_pixel_sum_descriptive']=sum(r['gt_valid_pixels'] for r in selected)
                    aggregates.append(row)
        require(len(distributions)==132 and len(scores)==56 and len(traces)==1600 and len(aggregates)==20,'Complete planned row counts')
        write_json(OUT/'distributions.json',distributions); write_json(OUT/'metrics_with_oracle_ratios.json',scores)
        write_json(OUT/'pair_diagnostics.json',pairs); write_json(OUT/'ga_raw_ratios.json',ratio_rows)
        write_json(OUT/'summary.json',dict(policy=policy(), modes=summaries, aggregates=aggregates))
        write_csv(OUT/'trace_all.csv',traces)
        scalar_keys=['mode','stage','index','edge','grid_pixels','gt_valid_pixels','gt_invalid_pixels',
                     'prediction_invalid_all_pixels','prediction_invalid_on_gt_pixels','absrel','rmse_m','delta1',
                     'delta1_success_pixels','metric_status','oracle_pair_count','oracle_excluded_pixels','scale_applied']
        write_csv(OUT/'per_frame.csv',[{k:r[k] for k in scalar_keys} for r in scores])
        verify_identities(m['controls']); verify_identities(m['data_identities']); verify_identities(gt_ids)
        require(sha_file(contract_path)==expected_sha,'Contract changed')
        write_json(OUT/'input_identities_before_after.json',dict(unchanged=True,controls=m['controls'],
                   saved_data=m['data_identities'],already_seen_sensor_depth=gt_ids))
        receipt.update(status='PASS', completed_utc=utc(), real_raw_archive_decodes=28, ga_output_decodes=4,
                       consumed_archive_decodes=4,pair_archive_decodes=4,sensor_gt_images_decoded=8,
                       distribution_rows=len(distributions),metric_rows=len(scores),trace_rows=len(traces),
                       aggregate_rows=len(aggregates),inputs_unchanged=True,
                       pass_meaning='Technical saved-data diagnosis completed; no algorithm gain, causal attribution or video result.',
                       outputs={p.name:sha_file(p) for p in sorted(OUT.iterdir()) if p.name!='receipt.json'})
        write_json(OUT/'receipt.json',receipt)
        return receipt
    except Exception as exc:
        receipt.update(status='FAILED', failed_utc=utc(), error=f'{type(exc).__name__}: {exc}')
        write_json(OUT/'receipt.json',receipt)
        raise


def main():
    p=argparse.ArgumentParser(description=__doc__); sub=p.add_subparsers(dest='command',required=True)
    sub.add_parser('prepare'); r=sub.add_parser('run'); r.add_argument('--contract',required=True); r.add_argument('--sha256',required=True)
    a=p.parse_args()
    result=prepare() if a.command=='prepare' else run(a.contract,a.sha256)
    print(json.dumps(result,ensure_ascii=False,allow_nan=False))


if __name__=='__main__':
    main()
