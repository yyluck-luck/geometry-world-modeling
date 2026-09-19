#!/usr/bin/env python3
"""Post-hoc S31 saved-depth scale/variation decomposition; no optimization.

Preparation may import decompose() only for explicitly synthetic arrays.
Real execution requires a separately frozen contract and an unused output path.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import importlib.util
import io
import json
import math
import os
import time
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
ARMS = ('C2t', 'C2a')
SS_TOL = dict(abs_tol=1e-9, rel_tol=1e-12)
LOG_TOL = dict(atol=1e-12, rtol=1e-12)
METRIC_KEYS = ('absrel', 'rmse_m', 'delta1', 'prediction_invalid_fraction_on_gt')


def utc(): return datetime.now(timezone.utc).isoformat()


def require(ok, why):
    if not ok: raise ValueError(why)


def sha(path):
    with Path(path).open('rb') as f: return hashlib.file_digest(f, 'sha256').hexdigest()


def digest(raw): return hashlib.sha256(raw).hexdigest()


def read(path): return json.loads(Path(path).read_text())


def write(path, value):
    Path(path).write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False)+'\n')


def decompose(initial, final):
    """Prediction-only algebra, all pixels, one scalar for the complete stack.

    Accepts small 3-D arrays for explicitly labelled synthetic checks. The real
    caller separately requires exactly FP32 (4,384,512) stored endpoints.
    """
    import numpy as np
    require(initial.shape == final.shape and initial.ndim == 3 and initial.size > 0, 'Complete equal endpoint grids')
    a = initial.astype(np.float64); b = final.astype(np.float64)
    require(np.isfinite(a).all() and np.isfinite(b).all() and (a > 0).all() and (b > 0).all(), 'Every endpoint pixel must be finite positive; never filter')
    v = np.log(b) - np.log(a)
    mu = float(np.mean(v, dtype=np.float64)); k = math.exp(-mu)
    require(math.isfinite(mu) and math.isfinite(k) and k > 0, 'Finite one global positive multiplier')
    frame_mean = np.mean(v, axis=(1,2), dtype=np.float64)
    offset = frame_mean - mu
    within = v - frame_mean[:,None,None]
    n = int(v.size); frame_n = int(v.shape[1]*v.shape[2])
    ss_total = float(np.sum(v*v, dtype=np.float64))
    ss_common = n*mu*mu
    ss_between = float(frame_n*np.sum(offset*offset, dtype=np.float64))
    ss_within_frames = np.sum(within*within, axis=(1,2), dtype=np.float64)
    ss_within = float(np.sum(ss_within_frames, dtype=np.float64))
    ss_sum = math.fsum([ss_common,ss_between,ss_within])
    centered = v-mu; ss_centered = float(np.sum(centered*centered, dtype=np.float64))
    require(math.isclose(ss_total,ss_sum,**SS_TOL), 'Full sum-of-squares decomposition identity')
    require(math.isclose(ss_centered,math.fsum([ss_between,ss_within]),**SS_TOL), 'Centered sum-of-squares identity')
    normalized = k*b
    require(np.isfinite(normalized).all() and (normalized > 0).all(), 'All normalized pixels finite positive')
    new_log_change = np.log(normalized)-np.log(a)
    log_error = new_log_change-centered
    require(np.allclose(new_log_change,centered,**LOG_TOL), 'Normalized log-change equals v-minus-mu everywhere')
    new_mean = float(np.mean(new_log_change, dtype=np.float64))
    require(abs(new_mean) <= LOG_TOL['atol'], 'Normalized global mean log-change approximately zero')
    components = {name:dict(sum_squares=value,mean_square=value/n,rms_log=math.sqrt(value/n),
        fraction_of_total=value/ss_total if ss_total else None) for name,value in
        [('common_global_mean',ss_common),('between_frame_means',ss_between),('within_frame',ss_within)]}
    rows = [dict(index=i,pixels=frame_n,mean_log_change=float(frame_mean[i]),
        deviation_from_global_mean=float(offset[i]),log_change_min=float(v[i].min()),log_change_max=float(v[i].max()),
        within_frame_sum_squares=float(ss_within_frames[i]),within_frame_rms_log=math.sqrt(float(ss_within_frames[i])/frame_n))
        for i in range(v.shape[0])]
    result = dict(frame_count=int(v.shape[0]),grid_shape=list(v.shape),total_pixels=n,all_pixels_retained=True,
        invalid_initial_pixels=0,invalid_final_pixels=0,mu=mu,k=k,geometric_mean_final_to_initial=math.exp(mu),
        total_sum_squares=ss_total,components=components,per_frame=rows,
        centered_sum_squares=ss_centered,nonuniform_rms_log=math.sqrt(ss_centered/n),
        identities=dict(total_minus_components=ss_total-ss_sum,
            total_relative_residual=abs(ss_total-ss_sum)/ss_total if ss_total else None,
            centered_minus_between_within=ss_centered-math.fsum([ss_between,ss_within]),
            normalized_log_identity_max_abs=float(np.max(np.abs(log_error))),normalized_mean_log_change=new_mean),
        sum_squares_tolerance=SS_TOL,log_identity_tolerance=LOG_TOL,
        scale_source='One full-stack prediction-only mean log(D400)-log(D0); no GT/pose/confidence inputs',
        interpretation='Nonuniform log-depth change, not proof of physical shape damage or optimizer gauge intervention')
    arrays = dict(depth=normalized,log_change=v,frame_mean_log_change=frame_mean,
        mu=np.asarray(mu,dtype=np.float64),k=np.asarray(k,dtype=np.float64))
    return result, arrays


def run(contract_path, expected_sha):
    require(sha(contract_path) == expected_sha, 'Exact caller-frozen S31 contract SHA')
    c = read(contract_path)
    require(c['status'] == 'FROZEN' and c['schema'] == 's31-saved-global-logscale-diagnostic-v1', 'Candidate cannot execute')
    require(c['arms'] == list(ARMS) and c['frame_count'] == 4 and c['depth_shape'] == [4,384,512], 'Fixed full domain')
    require(c['resource'] == dict(cpu_threads=1,wall_seconds=180,rss_bytes=2*1024**3), 'Fixed external caller resource contract')
    require(c['operation'] == dict(log_dtype='float64',scale='exp(-mean_all_pixels(log(D400)-log(D0)))',
        scales_per_arm=1,per_frame_scale=False,shift=False,GT_fit=False,filter_pixels=False,output_dtype='float64'), 'Fixed normalization only')
    require(c['sum_squares_tolerance'] == SS_TOL and c['log_identity_tolerance'] == LOG_TOL, 'Fixed algebra tolerances')
    require(c['identities'][str(Path(__file__).resolve())] == sha(__file__), 'Frozen executing source')
    out = Path(c['output_root']); require(out == ROOT/'results/S31_scale_shape_diagnostic' and not out.exists(), 'No repeat or output overwrite')
    out.mkdir()
    started = utc(); timer = time.perf_counter()
    receipt = dict(status='RUNNING',started_utc=started,contract_sha256=expected_sha,
        sensor_GT_bytes_started=False,new_model=0,new_MST=0,new_GA=0,new_backward=0,new_Adam=0)
    write(out/'receipt.json',receipt)
    try:
        ids = {str(Path(contract_path).resolve()):expected_sha}
        frames = c['gt_depth_frames']; gt_paths = {r['path'] for r in frames}
        require(len(frames) == 4 and len(gt_paths) == 4 and [r['index'] for r in frames] == list(range(4)), 'Original unique ordered four GT identities')
        require(not (gt_paths & set(c['identities'])) and not (gt_paths & set(c['saved_input_sha256'])), 'GT bytes excluded from prediction stage')
        for group in (c['identities'],c['saved_input_sha256']):
            for path,value in group.items():
                require(sha(path) == value, 'Bound source/saved input changed: '+path)
                if path in ids: require(ids[path] == value, 'Conflicting input identity')
                ids[path] = value
        s30 = read(c['s30_contract']); require(ids[c['s30_contract']] == c['s30_contract_sha256'] and s30['status'] == 'FROZEN', 'Frozen S30 parent')
        require(frames == s30['gt_depth_frames'] and c['scoring_policy'] == s30['scoring_policy'], 'Original scoring identities/policy')
        require(c['original_scorer'] == s30['parent_scorer'] and ids[c['original_scorer']] == s30['identities'][c['original_scorer']], 'Same original frozen metric implementation')
        sr = read(c['s30_score_receipt']); ir = read(c['s30_independent_receipt'])
        require(sr['status'] == ir['status'] == 'PASS' and sr['contract_sha256'] == ir['contract_sha256'] == c['s30_contract_sha256'], 'Existing official and independent S30 PASS')
        require(sr['per_frame_rows'] == ir['per_frame_rows'] == 16 and sr['endpoint_groups'] == ir['endpoint_groups'] == 4
                and ir['complete_raw_tensor_comparisons'] == 66 and ir['complete_gradient_records'] == 800, 'Existing complete S30 review domain')
        for arm in ARMS:
            r = read(c['s30_producer_receipts'][arm]); old = read(s30['s29_reference'][arm]['receipt'])
            require(r['status'] == 'PASS' and r['mode'] == arm and r['s30_contract_sha256'] == c['s30_contract_sha256']
                    and r['iterations'] == r['adam_steps'] == 400 and r['clean_calls'] == 1, 'Complete S30 producer')
            require(old['status'] == 'PASS_INITIALIZATION_EXECUTED' and old['arm'] == arm
                    and old['contract_sha256'] == s30['s29_contract_sha256'], 'Own historical zero-step S29 source')
            for endpoint in ('initial','final'):
                item = c['depth_inputs'][arm][endpoint]
                expected_path = s30['s29_reference'][arm]['files']['initial_decoded.npz']['path'] if endpoint == 'initial' else str(Path(s30['output_root'])/arm/'output.npz')
                require(item['path'] == expected_path, 'Exact prescribed endpoint, not another saved depth')
                require(ids[item['path']] == item['sha256'] == sr['input_sha256'][item['path']]
                        == ir['input_identities_before_after'][item['path']], 'Exactly independently reviewed endpoints')
                owner = old if endpoint == 'initial' else r
                require(owner['outputs'][Path(item['path']).name] == item['sha256'], 'Endpoint producer seal')
        for path,value in c['saved_input_sha256'].items():
            if path in sr['input_sha256']: require(sr['input_sha256'][path] == value, 'Same producer input as original S30 scoring')
        require(ids[c['s30_metrics']] == sr['outputs']['metrics.json'] == ir['input_identities_before_after'][c['s30_metrics']], 'Imported original metrics identity')
        write(out/'input_seal.json',dict(status='PASS_BEFORE_PREDICTION_DECODE',utc=utc(),contract_sha256=expected_sha,
            input_sha256=ids,arrays_decoded=False,sensor_GT_bytes_read=False))
        for name in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS','NUMEXPR_NUM_THREADS'): os.environ[name] = '1'
        import numpy as np
        require(np.__version__ == '1.26.4', 'Bound local NumPy version')

        def depth(item):
            raw = Path(item['path']).read_bytes(); require(digest(raw) == ids[item['path']], 'Depth archive changed after seal')
            with np.load(io.BytesIO(raw),allow_pickle=False) as z:
                require(len(z.files) == len(set(z.files)) and 'depth' in z.files, 'Unique saved archive members with depth')
                a = z['depth'].copy()
            require(a.dtype == np.float32 and a.shape == (4,384,512), 'Original FP32 depth endpoints')
            return a

        diagnostic = {}; normalized_ids = {}
        for arm in ARMS:
            initial = depth(c['depth_inputs'][arm]['initial']); final = depth(c['depth_inputs'][arm]['final'])
            result, arrays = decompose(initial,final); diagnostic[arm] = result
            d = out/arm; d.mkdir(); np.savez_compressed(d/'diagnostic_arrays.npz',**arrays)
            write(d/'decomposition.json',result)
            normalized_ids.update({str(p):sha(p) for p in (d/'diagnostic_arrays.npz',d/'decomposition.json')})
            del initial,final,arrays
        write(out/'normalization_seal.json',dict(status='PASS_BOTH_NORMALIZED_OUTPUTS_SEALED_BEFORE_GT',utc=utc(),
            contract_sha256=expected_sha,output_sha256=normalized_ids,scalars={arm:dict(mu=diagnostic[arm]['mu'],k=diagnostic[arm]['k']) for arm in ARMS},
            sensor_GT_bytes_read=False,source='Prediction-only scalar fixed before sensor scoring; researchers already knew S30 scores'))
        for path,value in ids.items(): require(sha(path) == value, 'Inputs changed during normalization')
        for path,value in normalized_ids.items(): require(sha(path) == value, 'Derived outputs changed before GT')
        # The unchanged frozen scorer contains only stdlib imports at module load.
        module_path = c['original_scorer']; require(sha(module_path) == ids[module_path], 'Frozen original scoring mathematics')
        spec = importlib.util.spec_from_file_location('s31_original_frozen_depth_math',module_path)
        p = importlib.util.module_from_spec(spec); spec.loader.exec_module(p)
        receipt.update(sensor_GT_bytes_started=True,sensor_GT_started_utc=utc()); write(out/'receipt.json',receipt)
        for row in frames:
            value = sha(row['path']); require(value == row['sha256'] == sr['input_sha256'][row['path']], 'All four original GT bytes sealed after D*')
            ids[row['path']] = value
        write(out/'pre_GT_decode_seal.json',dict(status='PASS',utc=utc(),normalized_output_sha256=normalized_ids,
            GT_sha256={r['path']:ids[r['path']] for r in frames},sensor_GT_images_decoded=0))
        gt,gt_records,gt_ids = p.load_sensor_depths(frames)
        require(all(ids[path] == value for path,value in gt_ids.items()), 'Original loader reads same GT bytes')
        write(out/'gt_receipt.json',dict(utc=utc(),files=gt_records,role='Scoring only after both prediction-derived scalars/output files sealed',already_seen=True))
        rows = []; means = {}
        for arm in ARMS:
            archive = out/arm/'diagnostic_arrays.npz'; require(sha(archive) == normalized_ids[str(archive)], 'Score sealed D*, not a new fit')
            with np.load(archive,allow_pickle=False) as z: normalized = z['depth'].copy()
            require(normalized.dtype == np.float64 and normalized.shape == (4,384,512), 'Derived depth FP64 full schema')
            selected = [dict(mode=arm,endpoint='global_logscale_normalized_final',index=i,**p.depth_metrics(normalized[i],gt[i])) for i in range(4)]
            rows.extend(selected); means[arm] = p.aggregate(selected,list(range(4)))
        with (out/'per_frame.csv').open('w',newline='') as f:
            writer = csv.DictWriter(f,fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
        # Old endpoints are imported from the exact PASS artifact, never rescored.
        prior = read(c['s30_metrics']); require(prior['contract_sha256'] == c['s30_contract_sha256'], 'Imported scoring contract')
        expected = {(a,e,i) for a in ARMS for e in ('initial','final') for i in range(4)}
        require(len(prior['per_frame']) == 16 and {(r['mode'],r['endpoint'],r['index']) for r in prior['per_frame']} == expected, 'All original rows imported')
        comparisons = {arm:{} for arm in ARMS}
        for arm in ARMS:
            require(set(prior['common4'][arm]) == {'initial','final'}, 'Original four mean groups')
            for endpoint in ('initial','final'):
                group = prior['common4'][arm][endpoint]; require(group['frame_indices'] == list(range(4)) and group['frame_count'] == 4, 'Full imported group')
                comparisons[arm][endpoint] = {key:means[arm][key]-group[key] if means[arm][key] is not None and group[key] is not None else None for key in METRIC_KEYS}
        write(out/'imported_S30_scores.json',dict(source=c['s30_metrics'],sha256=ids[c['s30_metrics']],role='Exact historical JSON import, no repeated endpoint scoring',metrics=prior))
        write(out/'metrics.json',dict(contract_sha256=expected_sha,per_frame=rows,normalized_common4=means,
            normalized_minus_imported_S30=comparisons,normalization='One scalar per complete arm from predictions only; D*=k*D400 in FP64',
            sensor_GT_scale_fit=False,confidence_mask=False,far_depth_cut=False,selected_step=400,
            evidence_scope='Post-hoc output normalization diagnostic on seen common4; not optimizer gauge control, new method, or generated-video improvement'))
        for path,value in {**ids,**normalized_ids}.items(): require(sha(path) == value, 'Input or derived output changed during scoring: '+path)
        receipt.update(status='PASS',completed_utc=utc(),wall_seconds=time.perf_counter()-timer,per_frame_rows=8,endpoint_groups=2,
            total_pixels_per_arm=4*384*512,decomposition_pixel_visits=2*4*384*512,GT_images_decoded=4,
            old_endpoint_rows_imported=16,old_endpoint_scores_recomputed=0,inputs_unchanged=True,input_sha256=ids,
            output_sha256={str(x.relative_to(out)):sha(x) for x in out.rglob('*') if x.is_file() and x.name != 'receipt.json'},
            evidence_scope='Saved-data algebra and post-hoc prediction-only output normalization; no causal optimizer or physical-shape claim')
        write(out/'receipt.json',receipt); print(json.dumps(dict(status='PASS',per_frame_rows=8,endpoint_groups=2,mu_k={a:{k:diagnostic[a][k] for k in ('mu','k')} for a in ARMS})))
    except BaseException as exc:
        receipt.update(status='FAILED',failed_utc=utc(),error=repr(exc),failure_policy='Preserve all partial outputs; no automatic rerun or tolerance change')
        write(out/'receipt.json',receipt); raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--contract',required=True); parser.add_argument('--sha256',required=True)
    args = parser.parse_args(); run(Path(args.contract).resolve(),args.sha256)
