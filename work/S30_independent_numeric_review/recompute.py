#!/usr/bin/env python3
"""S30 saved-data review adapter; explicit execution only, no model or optimizer.

Reuses the byte-frozen S28 independent numerical implementation unchanged.
All selected saved inputs and four GT byte seals precede every archive/PNG decode.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import importlib.util
import json
import math
import time
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
BASE = ROOT / 'results/S30_scale_optimization'
HELPER = ROOT / 'work/S28_independent_numeric_review/recompute.py'
HELPER_SHA = '2bef151226649a87b5c8cc29e6bd5173b2ece63900837f100dbf4338006d40f2'
CANDIDATE = ROOT / 'work/S30_scale_optimization_preparation/contract_candidate.json'
CANDIDATE_SHA = 'd5e7326875cffaf314fadd48e7b5f43e4fd63d7afda3f7d3a63498bd8e04c86f'
ARMS = ('C2t', 'C2a')
ENDPOINTS = ('initial', 'final')


def utc(): return datetime.now(timezone.utc).isoformat()


def require(ok, message):
    if not ok: raise ValueError(message)


def sha(path):
    with Path(path).open('rb') as f: return hashlib.file_digest(f, 'sha256').hexdigest()


def read(path): return json.loads(Path(path).read_text())


def write(name, value):
    (HERE / name).write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + '\n')


def main(args):
    require(not (HERE/'attempt.json').exists() and not (HERE/'receipt.json').exists(), 'Preserve prior attempts; no overwrite or automatic retry')
    require(sha(__file__) == args.script_sha256, 'Caller must bind reviewed adapter')
    require(sha(HERE/'protocol.md') == args.protocol_sha256, 'Caller must bind reviewed protocol')
    require(args.helper_sha256 == HELPER_SHA == sha(HELPER), 'Only the executed frozen S28 helper')
    started = utc(); timer = time.perf_counter()
    write('attempt.json', dict(status='STARTED', started_utc=started, contract_sha256=args.sha256,
        script_sha256=args.script_sha256, protocol_sha256=args.protocol_sha256, helper_sha256=HELPER_SHA,
        arrays_decoded=False, sensor_GT_bytes_read=False))
    try:
        # The helper has only stdlib top-level imports and an explicit __main__ guard.
        spec = importlib.util.spec_from_file_location('s30_frozen_s28_independent_helper', HELPER)
        h = importlib.util.module_from_spec(spec); spec.loader.exec_module(h)
        h.BASE = BASE  # Only path routing changes; no function/AST/formula is replaced.
        require(h.TOL == dict(abs_tol=1e-12, rel_tol=1e-10), 'Original independent tolerance')
        cp = Path(args.contract).resolve()
        require(sha(cp) == args.sha256 and sha(CANDIDATE) == CANDIDATE_SHA, 'Frozen contract and reviewed candidate identities')
        c = read(cp); candidate = read(CANDIDATE)
        require(c['status'] == 'FROZEN' and c['schema'] == 's30-s29-initialized-400-v1', 'No candidate execution')
        for key, value in candidate.items():
            if key == 'status': continue
            if key == 'identities':
                require(all(c[key].get(p) == v for p, v in value.items()), 'Candidate source identity changed at freeze')
            else: require(c[key] == value, 'Candidate condition changed at freeze: ' + key)
        require(c['arms'] == list(ARMS) and c['scoring_endpoints'] == list(ENDPOINTS), 'Fixed two arms and endpoints')
        require(c['steps_per_arm'] == 400 and c['endpoint_frame_count'] == 4 and c['per_frame_score_rows'] == 16
                and c['complete_raw_reference_count'] == 33, 'Complete prespecified domain')
        require(c['output_root'] == str(BASE), 'Explicit fixed S30 output root')
        ids = {str(cp): args.sha256, str(Path(__file__).resolve()): args.script_sha256,
               str(HERE/'protocol.md'): args.protocol_sha256, str(HELPER): HELPER_SHA,
               str(CANDIDATE): CANDIDATE_SHA}
        frames = c['gt_depth_frames']
        require(len(frames) == 4 and [r['index'] for r in frames] == list(range(4))
                and len({r['path'] for r in frames}) == 4, 'Four unique ordered GT identities')
        require(not ({r['path'] for r in frames} & set(c['identities'])), 'GT bytes reserved for final seal stage')
        for path, value in c['identities'].items():
            require(sha(path) == value, 'Frozen direct source/receipt identity: ' + path); ids[path] = value
        parent = Path(c['parent_manifest'])
        require(ids[str(parent)] == c['parent_manifest_sha256'], 'Parent manifest exact')
        pm = read(parent)
        require(frames == pm['scoring']['gt_depth_frames'][:4], 'Same existing GT domain')
        policy = dict(prediction_shape_hw=[384,512], sensor_shape_hw=[480,640], sensor_depth_divisor=5000,
            nearest_mapping='floor((2*target_index+1)*source_size/(2*target_size))',
            gt_valid='finite_and_positive_on_target_grid', prediction_invalid='nonfinite_or_nonpositive',
            invalid_policy='any_invalid_on_valid_gt_makes_frame_absrel_rmse_null;delta1_invalid_is_failure',
            aggregation='equal_frame_mean_only_if_all_prespecified_frames_defined', gt_scale_fit=False,
            confidence_mask=False, far_depth_cut=False, delta1_threshold=1.25, delta1_comparison='strict_less_than')
        require(c['scoring_policy'] == policy == {k: pm['scoring'][k] for k in policy}, 'Complete unchanged scoring policy')

        def bind_json(path, expected=None):
            path = Path(path); raw = path.read_bytes(); value = h.digest(raw)
            if expected is not None: require(value == expected, 'JSON hash mismatch: ' + str(path))
            if str(path) in ids: require(ids[str(path)] == value, 'Existing JSON binding changed')
            ids[str(path)] = value
            return json.loads(raw)

        # Read all readiness receipts before any producer archive or GT byte read.
        sr = bind_json(BASE/'scoring/receipt.json')
        require(sr['status'] == 'PASS' and sr['contract_sha256'] == args.sha256, 'Official S30 scorer must PASS first')
        require(sr['sensor_depth_images_decoded'] == 4 and sr['per_frame_rows'] == 16 and sr['endpoint_groups'] == 4, 'Complete official scoring')
        scored = sr['input_sha256']; producers = {}; refs = {}
        for arm in ARMS:
            d = BASE/arm; r = bind_json(d/'receipt.json'); producers[arm] = r
            require(r['status'] == 'PASS' and r['s30_contract_sha256'] == args.sha256
                    and r['manifest_sha256'] == c['parent_manifest_sha256'], 'Both producers must PASS/bind')
            require(r['mode'] == arm and r['frame_count'] == 4 and r['iterations'] == r['adam_steps'] == 400
                    and r['clean_calls'] == 1 and r['parent_identities_rechecked'] is True, 'Full original 400 steps/clean')
            ob = r['observer']; init = ob['s30_initialization']
            require(ob['s30_gradient_steps'] == 400 and ob['s30_alignment_calls'] == 1
                    and len(ob['pnp_calls']) == 3, 'Complete recorded observer path')
            require(all(init[k] is True for k in ('reference_S29_raw_exact','getter_forward_bytes_exact','getter_repair_active')), 'Own S29 starting gate')
            require(set(h.REQUIRED_PRODUCTS) | {'s29_reference_gate.json', 'controlled_alignment.npz'} <= set(r['outputs']), 'Complete saved products required')
            ref = c['s29_reference'][arm]; old = bind_json(ref['receipt'], c['identities'][ref['receipt']]); refs[arm] = old
            require(old['status'] == 'PASS_INITIALIZATION_EXECUTED' and old['arm'] == arm
                    and old['contract_sha256'] == c['s29_contract_sha256'], 'Own S29 zero-step source')
            require(old['counts'] == dict(MST=1,PnP=3,alignment=1,objective=1,backward=0,Adam=0,clean=0,model=0,GT=0), 'Historical start has zero optimizer steps')
            require(set(ref['files']) == {'initial_raw.npz','initial_raw_metadata.json','initial_decoded.npz','alignment.npz'}, 'Complete fixed S29 references')
        for arm, r in producers.items():
            d = BASE/arm
            for name, value in r['outputs'].items():
                require(Path(name).name == name, 'No product path traversal')
                p = d/name; require(sha(p) == value == scored[str(p)], 'Producer product must match original scorer seal: ' + str(p)); ids[str(p)] = value
            require(ids[str(d/'receipt.json')] == scored[str(d/'receipt.json')], 'Same scored producer receipt')
            seal = bind_json(d/'inputs_seal.json', r['inputs_seal_sha256'])
            require(seal['s30_contract_sha256'] == args.sha256 and seal['manifest_sha256'] == c['parent_manifest_sha256']
                    and seal['mode'] == arm and seal['frame_count'] == 4 and seal['sensor_depth_used'] is False, 'All original producer input seals')
            gate = bind_json(d/'s29_reference_gate.json')
            require(gate['status'] == 'PASS' and gate['arm'] == arm and gate['s30_contract_sha256'] == args.sha256
                    and gate['complete_raw_tensor_count'] == 33
                    and all(gate[k] is True for k in ('raw_exact','objective_exact','alignment_exact'))
                    and gate['s29_receipt_sha256'] == ids[c['s29_reference'][arm]['receipt']], 'Sealed S29 producer starting gate')
            ref = c['s29_reference'][arm]
            require(scored[ref['receipt']] == ids[ref['receipt']], 'Same S29 receipt as official scoring')
            for name, item in ref['files'].items():
                require(Path(item['path']).name == name and sha(item['path']) == item['sha256']
                        == refs[arm]['outputs'][name] == scored[item['path']], 'Same full saved S29 reference: ' + name)
                ids[item['path']] = item['sha256']
        require({'metrics.json','per_frame.csv','pre_score_seal.json'} <= set(sr['outputs']), 'Complete scored outputs')
        for name, value in sr['outputs'].items():
            require(Path(name).name == name, 'No score path traversal')
            p = BASE/'scoring'/name; require(sha(p) == value, 'Scorer output changed'); ids[str(p)] = value
        pre = bind_json(BASE/'scoring/pre_score_seal.json')
        require(pre['status'] == 'PASS' and pre['contract_sha256'] == args.sha256
                and pre['both_final_producers_complete'] is True and pre['both_saved_S29_starts_bound'] is True
                and pre['scoring_arrays_decoded'] is False and pre['sensor_GT_bytes_read'] is False, 'Original pre-score seal declarations')
        require(all(scored.get(p) == value for p,value in pre['input_sha256'].items()), 'Pre-score identities preserved through official scoring')
        for path, value in c['identities'].items(): require(scored[path] == value, 'Official scoring direct identity mismatch')
        # All four GT byte images are sealed together BEFORE any NPZ or PNG decode.
        write('progress.json', dict(stage='GT_BYTE_SEAL_STARTED', utc=utc(), arrays_decoded=False, sensor_depth_decoded=False))
        gt_bytes = []
        for row in frames:
            raw = Path(row['path']).read_bytes(); value = h.digest(raw)
            require(value == row['sha256'] == scored[row['path']], 'GT must equal the original scored bytes')
            ids[row['path']] = value; gt_bytes.append(raw)
        write('input_seal.json', dict(status='PASS_ALL_SAVED_AND_GT_BYTES_SEALED_BEFORE_DECODE', utc=utc(),
            contract_sha256=args.sha256, identities=ids, arrays_decoded=False, sensor_GT_images_decoded=0,
            sensor_GT_byte_images_read=4, scope='All direct frozen identities, producer/scorer products and own S29 references; no large dependency inventory repeat'))

        import numpy as np
        import cv2
        require(np.__version__ == '1.26.4', 'Existing NumPy 1.26.4 required'); cv2.setNumThreads(1)
        write('progress.json', dict(stage='SAVED_DATA_DECODING', utc=utc(), input_seal_sha256=sha(HERE/'input_seal.json')))
        gt = [cv2.imdecode(np.frombuffer(raw,np.uint8),cv2.IMREAD_UNCHANGED) for raw in gt_bytes]
        require(all(x is not None and x.shape == (480,640) and x.dtype == np.uint16 for x in gt), 'Original sensor PNG shape/dtype')
        final_shapes = dict(depth=(4,384,512),point_cloud=(4,384,512,3),conf=(4,384,512),focal=(4,1),pp=(4,2),c2w=(4,4,4))
        initial_shapes = {k:v for k,v in final_shapes.items() if k != 'conf'}
        initial_shapes.update(pw_scale=(3,),pw_poses=(3,4,4),adaptors=(3,3),objective=())
        # S29 adds prelog_depth and scalar norm_scale; the latter may be float64.
        expected_s29_keys = set(initial_shapes) | {'prelog_depth','norm_scale'}
        endpoints = {}; initial_reviews = {}; trace_summaries = []; trace_rows = []
        for arm in ARMS:
            d = BASE/arm; ref = c['s29_reference'][arm]['files']
            raw = h.load_archive(d/'initial_raw.npz',ids); meta = read(d/'initial_raw_metadata.json')
            old_raw = h.load_archive(Path(ref['initial_raw.npz']['path']),ids); old_meta = read(ref['initial_raw_metadata.json']['path'])
            h.validate_raw(raw,meta,arm+'/S30'); h.validate_raw(old_raw,old_meta,arm+'/S29')
            require(len(raw) == len(old_raw) == 33 and meta == old_meta, 'Own full 33 initial metadata entries exact')
            comparisons = []
            for name, a in raw.items():
                b = old_raw[name]; require(a.shape == b.shape and a.dtype == b.dtype and a.tobytes() == b.tobytes(), 'Own S29 initial tensor bytes: ' + name)
                comparisons.append(dict(name=name,shape=list(a.shape),dtype=str(a.dtype),elements=int(a.size),
                    requires_grad=meta[name]['requires_grad'],sha256=h.digest(a.tobytes()),bitwise_equal=True))
            new = h.load_archive(d/'initial_decoded.npz',ids,initial_shapes)
            old = h.load_archive(Path(ref['initial_decoded.npz']['path']),ids)
            require(set(old) == expected_s29_keys, 'Complete source-inspected S29 decoded schema')
            for name, shape in initial_shapes.items(): require(old[name].shape == shape and old[name].dtype == np.float32, 'S29 comparable FP32 decoded field: ' + name)
            require(old['prelog_depth'].shape == (4,384,512) and old['prelog_depth'].dtype == np.float32 and old['norm_scale'].shape == (), 'S29 additional decoded schema')
            compared = {k: old[k].tobytes() == new[k].tobytes() for k in initial_shapes}
            require(compared['depth'] and compared['objective'], 'Own exact S29 scored starting depth/objective')
            final_raw = h.load_archive(d/'final_raw_before_clean.npz',ids); final_meta = read(d/'final_raw_metadata.json')
            h.validate_raw(final_raw,final_meta,arm+'/final')
            require(set(final_meta) == set(meta) and all(all(final_meta[k][f] == meta[k][f] for f in ('shape','dtype','requires_grad')) for k in meta), 'Stable complete final tensor schema/flags')
            endpoints[arm] = dict(initial=old['depth'], final=h.load_archive(d/'output.npz',ids,final_shapes)['depth'])
            summary, steps = h.trace_review(arm,meta,ids)
            require(all(x['present_steps'] == 400 and x['none_steps'] == 0 for x in summary['counts'].values()), 'All six recorded trained gradients present finite; zero is allowed')
            trace_summaries.append(summary); trace_rows.extend(steps)
            initial_reviews[arm] = dict(raw_tensor_count=33,raw_comparison=comparisons,raw_and_metadata_exact=True,
                initial_decoded_byte_comparison=compared,required_depth_objective_exact=True,
                final_raw_schema_flags_valid=True,alignment_scope='Producer alignment gate verified as a sealed record; alignment arrays not numerically recomputed here')
            del raw,old_raw,final_raw,new,old

        metrics = read(BASE/'scoring/metrics.json')
        require(metrics['contract_sha256'] == args.sha256 and metrics['scale_fit'] is False
                and metrics['confidence_mask'] is False and metrics['far_depth_cut'] is False, 'Official metric policy')
        reported = metrics['per_frame']; expected = {(a,e,i) for a in ARMS for e in ENDPOINTS for i in range(4)}
        require(len(reported) == 16 and {(r['mode'],r['endpoint'],r['index']) for r in reported} == expected, 'All 16 official rows once')
        require(set(metrics['common4']) == set(ARMS) and set(metrics['final_minus_initial']) == set(ARMS), 'All group and change arms')
        lookup = {(r['mode'],r['endpoint'],r['index']):r for r in reported}; rows = []; differences = {}
        for arm in ARMS:
            for endpoint in ENDPOINTS:
                for i in range(4):
                    row = dict(mode=arm,endpoint=endpoint,index=i,**h.independent_frame(endpoints[arm][endpoint][i],gt[i]))
                    target = lookup[arm,endpoint,i]
                    for key in h.COUNT_KEYS + ('metric_status',): require(row[key] == target[key], f'Count/status mismatch {arm}/{endpoint}/{i}/{key}')
                    for key in h.FLOAT_KEYS: h.metric_match(row[key],target[key],f'{arm}/{endpoint}/{i}/{key}',differences)
                    rows.append(row)
        means = {}; changes = {}; aggregate_checks = 0
        for arm in ARMS:
            require(set(metrics['common4'][arm]) == set(ENDPOINTS), 'Two complete endpoint mean groups')
            means[arm] = {}
            for endpoint in ENDPOINTS:
                selected = [r for r in rows if r['mode'] == arm and r['endpoint'] == endpoint]
                target = metrics['common4'][arm][endpoint]
                group = dict(frame_indices=list(range(4)),frame_count=4,aggregation='equal_frame_mean;no_available_frame_or_pixel_pooled_substitution')
                for k,v in group.items(): require(target[k] == v, 'Complete ordered equal-frame aggregation')
                for key in h.FLOAT_KEYS:
                    vals = [r[key] for r in selected]; value = math.fsum(vals)/4 if all(v is not None for v in vals) else None
                    h.metric_match(value,target[key],f'{arm}/{endpoint}/mean/{key}',differences); aggregate_checks += 1
                    group[key] = value; group[key+'_defined_frames'] = sum(v is not None for v in vals)
                    require(target[key+'_defined_frames'] == group[key+'_defined_frames'], 'Exact defined-frame count')
                for key in h.SUM_KEYS:
                    group[key+'_sum_descriptive'] = sum(r[key] for r in selected)
                    require(target[key+'_sum_descriptive'] == group[key+'_sum_descriptive'], 'Complete denominator sums')
                group['empty_gt_frames'] = [r['index'] for r in selected if r['gt_valid_pixels'] == 0]
                group['invalid_prediction_frames'] = [r['index'] for r in selected if r['prediction_invalid_on_gt_pixels'] > 0]
                for key in ('empty_gt_frames','invalid_prediction_frames'): require(target[key] == group[key], 'Complete exception frame list')
                means[arm][endpoint] = group
            require(set(metrics['final_minus_initial'][arm]) == set(h.FLOAT_KEYS), 'All four endpoint differences')
            changes[arm] = {}
            for key in h.FLOAT_KEYS:
                a,b = means[arm]['initial'][key],means[arm]['final'][key]; value = b-a if a is not None and b is not None else None
                h.metric_match(value,metrics['final_minus_initial'][arm][key],f'{arm}/change/{key}',differences); changes[arm][key] = value
        with (BASE/'scoring/per_frame.csv').open() as f: csv_rows = list(csv.DictReader(f))
        require(len(csv_rows) == 16 and {(r['mode'],r['endpoint'],int(r['index'])) for r in csv_rows} == expected, 'All CSV rows once')
        for row in csv_rows:
            target = lookup[row['mode'],row['endpoint'],int(row['index'])]
            for key in h.COUNT_KEYS: require(int(row[key]) == target[key], 'CSV integer exact')
            require(row['metric_status'] == target['metric_status'], 'CSV status exact')
            for key in h.FLOAT_KEYS: h.metric_match(float(row[key]) if row[key] else None,target[key],'csv/'+key,differences)
        for path, value in ids.items(): require(sha(path) == value, 'Input changed during review: ' + path)
        write('recomputed_metrics.json', dict(per_frame=rows,common4=means,final_minus_initial=changes,tolerance=h.TOL,maximum_difference=differences))
        write('initial_review.json', dict(arms=initial_reviews,complete_raw_tensor_comparisons=66,
            scope='Each fresh S30 arm versus its OWN S29 start; no cross-arm equality requirement or recreated historical objects'))
        write('trace_review.json', dict(total_actual_step_records=800,arms=trace_summaries,per_step=trace_rows,
            scope='Complete saved ordinary/gradient record audit; no backward or independent gradient-norm recomputation'))
        names = ('recomputed_metrics.json','initial_review.json','trace_review.json','input_seal.json')
        write('receipt.json', dict(status='PASS',started_utc=started,completed_utc=utc(),wall_seconds=time.perf_counter()-timer,
            contract_sha256=args.sha256,candidate_sha256=CANDIDATE_SHA,script_sha256=args.script_sha256,
            protocol_sha256=args.protocol_sha256,helper_sha256=HELPER_SHA,per_frame_rows=16,endpoint_groups=4,
            aggregate_numeric_checks=aggregate_checks,endpoint_difference_checks=8,full_grid_pixel_visits=16*384*512,
            valid_GT_pixel_visits=sum(r['gt_valid_pixels'] for r in rows),maximum_metric_difference=differences,
            complete_raw_tensor_comparisons=66,complete_gradient_records=800,GT_images_decoded=4,
            inputs_unchanged=True,input_identities_before_after=ids,outputs={n:sha(HERE/n) for n in names},
            new_model_runs=0,new_GA_runs=0,new_MST_runs=0,new_backward_calls=0,
            evidence_scope='Different author from S30 producer/scorer; frozen S28 OpenCV/rowwise independent formula reused. Previously seen common4, saved record audit, not fresh replication or new method evidence'))
        print(json.dumps(dict(status='PASS',per_frame_rows=16,endpoint_groups=4,raw_tensor_comparisons=66,gradient_records=800,maximum_difference=differences)))
    except BaseException as exc:
        write('receipt.json', dict(status='FAILED',started_utc=started,failed_utc=utc(),error=repr(exc),
            contract_sha256=args.sha256,script_sha256=args.script_sha256,helper_sha256=HELPER_SHA,
            evidence_scope='Incomplete independent review; preserve attempt, no automatic retry or tolerance change'))
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('contract','sha256','script-sha256','protocol-sha256','helper-sha256'): parser.add_argument('--'+name,required=True)
    main(parser.parse_args())
