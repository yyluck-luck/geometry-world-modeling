#!/usr/bin/env python3
"""S15C: sealed observed-view depth calibration and evaluation; never model inference."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import csv
import hashlib
import json
import math
import os
from pathlib import Path
import re
import resource
import shutil
import signal
import sys
import threading
import time
import traceback

METHODS = ('model', 'constant')
CALIBRATION_INDICES = list(range(4))
EVALUATION_INDICES = list(range(4, 20))
EXPECTED_CONTRACT = dict(device='cpu', wall_seconds=600, max_rss_bytes=8589934592,
    resize=[299, 224], crop=[37, 0, 261, 224], depth_divisor=5000,
    calibration_indices=CALIBRATION_INDICES, evaluation_indices=EVALUATION_INDICES)
ERROR_KEYS = ('mae_m', 'abs_rel', 'rmse_m')
AVERAGE_KEYS = ('delta1_all_gt', 'coverage') + tuple(p+k for p in ('own_', 'common_') for k in ERROR_KEYS)


def utc():
    return datetime.now(timezone.utc).isoformat()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def timestamp(value):
    t = datetime.fromisoformat(value)
    require(t.tzinfo is not None and t.utcoffset() is not None, 'Timezone required')
    return t


def canonical(value):
    require(isinstance(value, str), 'Path must be string')
    p = Path(value)
    require(p.is_absolute() and str(p.resolve()) == value, 'Canonical absolute path required: '+value)
    return p


def sha(path):
    with Path(path).open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def write_json(path, value):
    Path(path).write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False)+'\n')


def identity_map(ids):
    require(isinstance(ids, dict) and len(ids) > 0, 'Identity map required')
    for p, h in ids.items():
        canonical(p)
        require(isinstance(h, str) and re.fullmatch('[0-9a-f]{64}', h), 'Invalid SHA256: '+p)


def validate_manifest(m):
    require(m['schema'] == 's15c-observed-depth-manifest-v1', 'Manifest schema')
    for k, v in EXPECTED_CONTRACT.items():
        require(m['contract'].get(k) == v, 'Fixed contract: '+k)
    for k in ('runner', 'history_seal', 'history_predictions', 'history_metadata'):
        canonical(m[k])
    require(canonical(m['runner']) == Path(__file__).resolve(), 'This exact runner required')
    require(Path(m['python']).is_absolute(), 'Absolute Python path')
    ids = m['identities']; identity_map(ids)
    controls = m['controls']
    require(isinstance(controls, list) and len(controls) == len(set(controls)), 'Distinct controls')
    for p in controls:
        canonical(p)
        require(Path(p).suffix in ('.md', '.py', '.json'), 'Control type restriction')
    samples = m['samples']
    require(len(samples) == 20 and [s['index'] for s in samples] == list(range(20)), 'All twenty fixed ordered samples')
    for kind in ('rgb_path', 'depth_path'):
        require(len(set(s[kind] for s in samples)) == 20, 'Distinct sample paths: '+kind)
        for s in samples:
            canonical(s[kind])
            require(Path(s[kind]).suffix.lower() == '.png', 'PNG only')
    rgb_paths = {s['rgb_path'] for s in samples}; depth_paths = {s['depth_path'] for s in samples}
    require(not rgb_paths & depth_paths, 'RGB/depth disjoint')
    for s in samples:
        for name in ('rgb_timestamp', 'depth_timestamp'):
            require(isinstance(s[name], (int, float)) and not isinstance(s[name], bool)
                    and math.isfinite(s[name]), 'Finite numeric timestamp')
        require(abs(s['rgb_timestamp'] - s['depth_timestamp']) <= .025, 'Frozen RGB-depth time gate')
        require(ids.get(s['depth_path']) == s['depth_sha256'], 'Depth identity binding')
        require(isinstance(s['rgb_sha256'], str) and re.fullmatch('[0-9a-f]{64}', s['rgb_sha256']), 'RGB SHA format')
    require(all(samples[i]['rgb_timestamp'] < samples[i+1]['rgb_timestamp'] and
                samples[i]['depth_timestamp'] < samples[i+1]['depth_timestamp'] for i in range(19)), 'Ordered unique timestamps')
    allowed = set(controls) | depth_paths | {m['runner'], m['history_seal']}
    require(set(ids) == allowed, 'Only declared controls, runner, history seal, twenty depth identities')
    require(not (set(controls) & (rgb_paths | depth_paths)), 'No images disguised as controls')
    require(ids[m['history_seal']] == m['history_seal_sha256'], 'S15A seal hash binding')
    timestamp(m['frozen_utc'])
    return samples


def calibration_values(prediction, gt):
    """Pure small-array test boundary. Production caller separately requires 4 x 224 x 224."""
    import numpy as np
    prediction = np.asarray(prediction, dtype=np.float64)
    gt = np.asarray(gt, dtype=np.float64)
    require(prediction.ndim == 3 and prediction.shape == gt.shape and prediction.shape[0] == 4,
            'Four matching calibration frame arrays')
    gt_valid = np.isfinite(gt) & (gt > 0)
    pairs = gt_valid & np.isfinite(prediction) & (prediction > 0)
    frame_counts = [int(p.sum()) for p in pairs]
    require(all(n > 0 for n in frame_counts), 'Every calibration frame needs a positive finite prediction/GT pair')
    with np.errstate(over='ignore', invalid='ignore', divide='ignore'):
        ratios = prediction[pairs] / gt[pairs]
    require(np.isfinite(ratios).all() and (ratios > 0).all(), 'Calibration ratio arithmetic finite positive')
    scale = float(np.median(ratios))
    constant = float(np.median(gt[gt_valid]))
    require(math.isfinite(scale) and scale > 0 and math.isfinite(constant) and constant > 0,
            'Positive finite pooled calibration and constant')
    return dict(s_model_per_meter=scale, constant_depth_m=constant,
                ratio_count=int(ratios.size), positive_gt_count=int(gt_valid.sum()),
                frame_pair_counts=frame_counts,
                frame_positive_gt_counts=[int(v.sum()) for v in gt_valid],
                median_even_rule='arithmetic mean of two middle sorted values')


def error_metrics(prediction, gt, mask):
    import numpy as np
    n = int(mask.sum())
    if not n:
        return dict(status='EMPTY_DOMAIN', **{k: None for k in ERROR_KEYS})
    with np.errstate(over='ignore', invalid='ignore', divide='ignore'):
        error = np.abs(prediction[mask].astype(np.float64) - gt[mask])
        peak = float(np.max(error))
        mae = peak * float(np.mean(error / peak)) if peak else 0.0
        rmse = peak * math.sqrt(float(np.mean((error / peak)**2))) if peak else 0.0
        relative = error / gt[mask]
        maximum = float(np.max(relative))
        abs_rel = maximum * float(np.mean(relative / maximum)) if maximum else 0.0
    result = dict(mae_m=mae, abs_rel=abs_rel, rmse_m=rmse)
    return dict(status='OK' if all(math.isfinite(x) for x in result.values()) else 'NONFINITE_ARITHMETIC',
                **{k: v if math.isfinite(v) else None for k, v in result.items()})


def compute_metrics(gt, predictions, index):
    import numpy as np
    gt = np.asarray(gt, dtype=np.float64); predictions = np.asarray(predictions, dtype=np.float64)
    require(gt.ndim == 2 and predictions.shape == (2,) + gt.shape, 'Exact two-method metric dimensions')
    valid_gt = np.isfinite(gt) & (gt > 0)
    positive = np.isfinite(predictions) & (predictions > 0)
    own = positive & valid_gt[None]
    common = valid_gt & positive.all(axis=0)
    success = np.zeros_like(own)
    rows = []
    for j, method in enumerate(METHODS):
        mask = own[j]
        with np.errstate(over='ignore', invalid='ignore', divide='ignore'):
            success[j, mask] = np.maximum(predictions[j, mask]/gt[mask], gt[mask]/predictions[j, mask]) < 1.25
        total, count, hits = int(valid_gt.sum()), int(mask.sum()), int(success[j].sum())
        own_errors = error_metrics(predictions[j], gt, mask)
        common_errors = error_metrics(predictions[j], gt, common)
        row = dict(index=index, method=method, gt_valid_count=total,
                   prediction_positive_finite_count=int(positive[j].sum()), own_valid_count=count,
                   common_valid_count=int(common.sum()), delta1_success_count=hits,
                   delta1_all_gt=hits/total if total else None, coverage=count/total if total else None,
                   gt_domain_status='OK' if total else 'EMPTY_GT_DOMAIN',
                   own_error_status=own_errors.pop('status'), common_error_status=common_errors.pop('status'))
        row.update({'own_'+k: v for k, v in own_errors.items()})
        row.update({'common_'+k: v for k, v in common_errors.items()})
        rows.append(row)
    return rows, dict(gt_depth_m=gt, prediction_depth_m=predictions, gt_valid_mask=valid_gt,
        prediction_positive_finite_mask=positive, own_valid_mask=own,
        common_valid_mask=common, delta1_success_mask=success)


def equal_frame_means(rows):
    result = []
    for method in METHODS:
        selected = [r for r in rows if r['method'] == method]
        require([r['index'] for r in selected] == EVALUATION_INDICES, 'Keep all sixteen ordered frames')
        means, counts, available = {}, {}, {}
        for key in AVERAGE_KEYS:
            values = [r[key] for r in selected if r[key] is not None]
            counts[key] = len(values)
            available[key] = math.fsum(v / len(values) for v in values) if values else None
            # A missing frame invalidates the primary 16-frame average; do not silently drop it.
            means[key] = available[key] if len(values) == 16 else None
        result.append(dict(method=method, frame_count=16, means=means,
            contributing_frame_counts=counts, available_frame_descriptive_means=available,
            gt_valid_pixel_visits=sum(r['gt_valid_count'] for r in selected),
            interpretation='Equal-frame descriptive means; one correlated source sequence; no independent-scene inference'))
    return result


class Recorder:
    def __init__(self, out, mode):
        self.out = out
        self.report = dict(schema='s15c-observed-depth-run-v1', mode=mode, status='RUNNING', started_utc=utc(),
            executable=sys.executable, python=sys.version, reads=[], identity_hashes=[],
            counters={k: 0 for k in ('identity_hash_attempts','identity_hash_successes','json_decode_attempts','json_decoded',
                'npz_open_attempts','npz_opened','npz_array_decode_attempts','npz_arrays_decoded',
                'depth_open_attempts','depth_opened','depth_decode_attempts','depths_decoded','rgb_decodes','trajectory_decodes','model_calls')},
            observed_rgb_is_model_input=True, new_method_test=False, novel_view=False, video_generated=False)
    def flush(self):
        write_json(self.out/'run_metadata.json', self.report)
    def phase(self, value):
        self.report.update(phase=value, updated_utc=utc()); self.flush()
        print(json.dumps(dict(utc=utc(), phase=value)), flush=True)
    def hash_check(self, path, digest, role):
        entry=dict(path=str(path), role=role, attempted_utc=utc(), completed=False)
        self.report['identity_hashes'].append(entry);self.report['counters']['identity_hash_attempts']+=1
        actual=sha(path);entry.update(completed=True, completed_utc=utc(), sha256=actual)
        require(actual == digest, 'SHA256 mismatch: '+str(path))
        self.report['counters']['identity_hash_successes']+=1
    def json(self, path, role):
        entry=dict(path=str(path), role=role, format='json', attempted_utc=utc(), completed=False)
        self.report['reads'].append(entry);self.report['counters']['json_decode_attempts']+=1
        value=json.loads(Path(path).read_text());entry.update(completed=True, completed_utc=utc())
        self.report['counters']['json_decoded']+=1;return value
    def npz(self, path, keys, role, exact=False):
        import numpy as np
        entry=dict(path=str(path), role=role, format='npz', attempted_utc=utc(), completed=False, arrays=[])
        self.report['reads'].append(entry);self.report['counters']['npz_open_attempts']+=1
        with np.load(path, allow_pickle=False) as source:
            self.report['counters']['npz_opened']+=1
            if exact:require(set(source.files)==set(keys), 'Exact NPZ key schema')
            values={}
            for key in keys:
                a=dict(key=key, attempted_utc=utc(), completed=False);entry['arrays'].append(a)
                self.report['counters']['npz_array_decode_attempts']+=1
                values[key]=source[key].copy();a.update(completed=True,completed_utc=utc(),shape=list(values[key].shape),dtype=str(values[key].dtype))
                self.report['counters']['npz_arrays_decoded']+=1
        entry.update(completed=True, completed_utc=utc());return values
    def depth(self, sample):
        import numpy as np
        from PIL import Image
        role='calibration depth' if sample['index']<4 else 'evaluation depth after sealed prediction'
        entry=dict(path=sample['depth_path'],index=sample['index'],role=role,format='png',attempted_utc=utc(),opened=False,decoded=False)
        self.report['reads'].append(entry);self.report['counters']['depth_open_attempts']+=1
        self.report.setdefault('first_depth_open_attempt_utc',entry['attempted_utc'])
        with Image.open(sample['depth_path']) as im:
            entry.update(opened=True,opened_utc=utc(),pil_format=im.format,pil_mode=im.mode)
            self.report['counters']['depth_opened']+=1
            require(im.format=='PNG' and im.size==(640,480), 'Native PNG 640x480 required')
            self.report['counters']['depth_decode_attempts']+=1;im.load()
            entry.update(decoded=True,decoded_utc=utc());self.report['counters']['depths_decoded']+=1
            raw=np.asarray(im)
            require(raw.dtype==np.uint16 and raw.shape==(480,640), 'Native uint16 required')
            gt=np.asarray(im.resize((299,224),Image.Resampling.NEAREST).crop((37,0,261,224)),dtype=np.float64)/5000.0
            entry.update(native_shape=list(raw.shape),native_dtype=str(raw.dtype),native_positive_count=int(np.count_nonzero(raw)),resized_shape=list(gt.shape))
        entry.update(completed=True,completed_utc=utc());return gt


def verify_history(m, rec):
    """Authenticate history source before any current-stage depth access."""
    rec.phase('verify_s15a_history_seal')
    rec.hash_check(m['history_seal'],m['history_seal_sha256'],'externally frozen S15A seal')
    seal=rec.json(m['history_seal'],'S15A combined history seal')
    require(seal['schema']=='s15a-history-combined-seal-v1','S15A seal schema')
    ids=seal['identities'];identity_map(ids)
    depth_paths={s['depth_path'] for s in m['samples']}
    require(not depth_paths & set(ids),'Current sensor depth cannot be in old history seal')
    for p,h in ids.items():rec.hash_check(p,h,'S15A sealed input/output identity; bytes may include RGB and weights')
    for key in ('history_predictions','history_metadata'):
        require(m[key] in ids,'History role not sealed: '+key)
    run=canonical(seal['run_dir'])
    require(canonical(m['history_predictions'])==run/'predictions.npz' and canonical(m['history_metadata'])==run/'run_metadata.json','Exact history output roles')
    for p in run.rglob('*'):
        if p.is_file():require(str(p.resolve()) in ids,'Unsealed history run file')
    require(seal['manifest'] in ids,'Original history manifest must be sealed')
    history_manifest=rec.json(seal['manifest'],'Original twenty RGB identity/order')
    require(history_manifest['schema']=='s15-history-manifest-v1','History manifest schema')
    require(len(history_manifest['history_images'])==20,'History count')
    for s,old in zip(m['samples'],history_manifest['history_images']):
        require((old['index'],old['path'],old['sha256'])==(s['index'],s['rgb_path'],s['rgb_sha256']), 'Current sample does not match actual S15A RGB')
        require(ids.get(s['rgb_path'])==s['rgb_sha256'],'History RGB seal binding')
    meta=rec.json(m['history_metadata'],'Successful original model metadata')
    require(meta['schema']=='s15-history-run-v1' and meta['status']=='SUCCESS','Successful S15A run required')
    require(meta['manifest_sha256']==ids[seal['manifest']],'Model manifest provenance')
    require(meta['output_sha256']['predictions.npz']==ids[m['history_predictions']],'Prediction SHA provenance')
    require(timestamp(meta['completed_utc'])<=timestamp(seal['sealed_utc'])<timestamp(m['frozen_utc'])<timestamp(rec.report['started_utc']),'History completion/seal/new freeze/start order')
    rec.report.update(history_seal_verified_utc=utc(),history_sealed_file_count=len(ids),history_seal_sha256=m['history_seal_sha256'])


def verify_prediction_seal(args, m, rec):
    require(args.prediction_seal and args.prediction_seal_sha256,'Score requires an external root-bound calibration seal')
    rec.phase('verify_s15c_calibrated_prediction_seal_before_eval_depth')
    rec.hash_check(args.prediction_seal,args.prediction_seal_sha256,'external calibrated prediction seal')
    seal=rec.json(args.prediction_seal,'S15C calibrated prediction seal')
    require(seal['schema']=='s15c-calibrated-prediction-seal-v1','Calibration seal schema')
    require(seal['manifest']==str(args.manifest.resolve()) and seal['manifest_sha256']==args.manifest_sha256,'Exact same pre-calibration manifest required')
    ids=seal['identities'];identity_map(ids)
    require(not {s['depth_path'] for s in m['samples']} & set(ids),'New raw sensor depths excluded from calibrated output seal')
    directory=canonical(seal['calibration_dir'])
    require(directory.is_dir(),'Calibration output directory must exist')
    members={str(p.resolve()) for p in directory.rglob('*') if p.is_file()}
    require(members and set(ids)==members,'Prediction seal must contain exactly the calibration directory files; no outside identities')
    require(all(Path(p).is_relative_to(directory) for p in ids),'No symlink escape in calibration outputs')
    for p,h in ids.items():rec.hash_check(p,h,'S15C sealed calibration output')
    for name in ('calibration.json','calibrated_predictions.npz','calibration_gt.npz','run_metadata.json','frozen_manifest.json','source_snapshot.py'):
        require(str(directory/name) in ids,'Required calibrated output missing: '+name)
    for p in directory.rglob('*'):
        if p.is_file():require(str(p.resolve()) in ids,'Unsealed calibration output file')
    meta=rec.json(directory/'run_metadata.json','Successful prior calibration run')
    require(meta['schema']=='s15c-observed-depth-run-v1' and meta['mode']=='calibrate' and meta['status']=='SUCCESS','Successful calibration required')
    require(meta['manifest_sha256']==args.manifest_sha256 and ids[str(directory/'frozen_manifest.json')]==args.manifest_sha256,'Calibration manifest exact byte binding')
    require(meta['counters']['depths_decoded']==4 and [x['index'] for x in meta['reads'] if x.get('format')=='png']==CALIBRATION_INDICES,'Only first four depths used for calibration')
    require(meta['counters']['model_calls']==0 and meta['counters']['rgb_decodes']==0 and meta['counters']['trajectory_decodes']==0,'Calibration prohibited-input counters')
    eval_paths={s['depth_path'] for s in m['samples'][4:]}
    require(not eval_paths & {x['path'] for x in meta['identity_hashes']+meta['reads']},'Calibration must not even hash evaluation-depth bytes')
    require(timestamp(m['frozen_utc'])<timestamp(meta['started_utc'])<=timestamp(meta['completed_utc'])<timestamp(seal['sealed_utc'])<timestamp(rec.report['started_utc']),'Calibration freeze/run/seal/score order')
    for name,h in meta['output_sha256'].items():require(ids.get(str(directory/name))==h,'Calibration metadata output binding')
    rec.report.update(prediction_seal_verified_utc=utc(),prediction_seal_sha256=args.prediction_seal_sha256,
                      prediction_sealed_utc=seal['sealed_utc'],calibration_completed_utc=meta['completed_utc'])
    return directory


def calibrate(m, rec):
    import numpy as np
    verify_history(m,rec)
    eval_paths={s['depth_path'] for s in m['samples'][4:]}
    for p,h in m['identities'].items():
        if p not in eval_paths:rec.hash_check(p,h,'Calibration allowed input identity')
    rec.report['deferred_evaluation_depth_identity_paths']=sorted(eval_paths)
    rec.phase('decode_only_twenty_self_pointmaps_consume_z_channel')
    keys=[f'frame{i}_pts3d_in_self_view' for i in range(20)]
    values=rec.npz(m['history_predictions'],keys,'20 self pointmap arrays; consume Z only; no other heads')
    depth=[]
    for key in keys:
        a=values[key]
        require(a.shape==(1,224,224,3) and a.dtype==np.float32,'S15A self-pointmap shape/dtype')
        depth.append(a[0,:,:,2].astype(np.float64))
    raw_prediction=np.stack(depth);del values
    calibration_gt=[]
    for sample in m['samples'][:4]:
        rec.phase('decode_calibration_depth_'+str(sample['index']))
        calibration_gt.append(rec.depth(sample))
    gt=np.stack(calibration_gt)
    result=calibration_values(raw_prediction[:4],gt)
    with np.errstate(over='ignore',invalid='ignore',divide='ignore'):
        prediction_m=raw_prediction/result['s_model_per_meter']
    # Existing missing/nonpositive predictions are retained for coverage and missing-fail evaluation.
    require(not (np.isfinite(raw_prediction)&~np.isfinite(prediction_m)).any(),'Scale conversion arithmetic overflow')
    result.update(schema='s15c-pooled-calibration-v1',created_utc=utc(),
        calibration_indices=CALIBRATION_INDICES,evaluation_indices=EVALUATION_INDICES,
        source_prediction_sha256=sha(m['history_predictions']),manifest_sha256=rec.report['manifest_sha256'],
        prediction_key='model_depth_m',constant_key='constant_depth_m',
        scope='First four observed-view sensor depths; no evaluation target fit; no GT pose; no remap')
    write_json(rec.out/'calibration.json',result)
    np.savez_compressed(rec.out/'calibrated_predictions.npz',model_depth_m=prediction_m,
                        constant_depth_m=np.array(result['constant_depth_m'],dtype=np.float64))
    np.savez_compressed(rec.out/'calibration_gt.npz',calibration_gt_depth_m=gt)
    rec.report.update(calibration=result,output_array_shapes={'model_depth_m':[20,224,224],'constant_depth_m':[],
        'calibration_gt_depth_m':[4,224,224]},output_dtype='float64')
    require(rec.report['counters']['depths_decoded']==4 and rec.report['counters']['npz_arrays_decoded']==20,'Calibration exact data-read counts')


def score(args,m,rec):
    import numpy as np
    directory=verify_prediction_seal(args,m,rec)
    # History seal was already authenticated in the sealed calibration; authenticate again for changed-file detection.
    verify_history(m,rec)
    calib_paths={s['depth_path'] for s in m['samples'][:4]}
    for p,h in m['identities'].items():
        if p not in calib_paths:
            if p in {s['depth_path'] for s in m['samples'][4:]}:
                rec.report.setdefault('first_evaluation_depth_hash_utc',utc())
            rec.hash_check(p,h,'Scoring input identity after calibrated-prediction seal')
    rec.report['calibration_depths_not_reopened']=sorted(calib_paths)
    calibration=rec.json(directory/'calibration.json','Sealed pooled scale and constant')
    require(calibration['schema']=='s15c-pooled-calibration-v1' and calibration['manifest_sha256']==args.manifest_sha256,'Calibration source binding')
    require(calibration['calibration_indices']==CALIBRATION_INDICES and calibration['evaluation_indices']==EVALUATION_INDICES,'Calibration/evaluation split fixed')
    scalar=calibration['constant_depth_m'];scale=calibration['s_model_per_meter']
    require(isinstance(scalar,(int,float)) and isinstance(scale,(int,float)) and math.isfinite(scalar) and scalar>0 and math.isfinite(scale) and scale>0,'Sealed scale/constant finite positive')
    values=rec.npz(directory/'calibrated_predictions.npz',['model_depth_m','constant_depth_m'],'Sealed fixed predictions',True)
    prediction=values['model_depth_m'];constant=values['constant_depth_m']
    require(prediction.shape==(20,224,224) and prediction.dtype==np.float64,'Calibrated prediction schema')
    require(constant.shape==() and constant.dtype==np.float64 and float(constant)==scalar,'Constant JSON/NPZ exact binding')
    rows=[];all_arrays=[]
    (rec.out/'per_frame_arrays').mkdir()
    for sample in m['samples'][4:]:
        require('prediction_seal_verified_utc' in rec.report,'Prediction seal before evaluation depth')
        i=sample['index'];rec.phase('decode_and_score_evaluation_depth_'+str(i))
        gt=rec.depth(sample)
        current=np.stack([prediction[i],np.full((224,224),scalar,dtype=np.float64)])
        new_rows,arrays=compute_metrics(gt,current,i);rows.extend(new_rows);all_arrays.append(arrays)
        np.savez_compressed(rec.out/'per_frame_arrays'/f'frame{i}.npz',**arrays)
    require(len(rows)==32 and rec.report['counters']['depths_decoded']==16,'All sixteen frames and both methods required')
    summary=dict(schema='s15c-observed-depth-scores-v1',evidence_kind='REAL_SENSOR_DEPTH_SCORE_EXISTING_OBSERVED_RGB_PREDICTIONS',
        rows=rows,means=equal_frame_means(rows),calibration=calibration,
        labels=dict(real_model_run_this_stage=False,gt_pose_used=False,novel_view=False,new_method=False),
        any_empty_gt_frame=any(r['gt_valid_count']==0 for r in rows),
        any_nonfinite_error=any(r[k]=='NONFINITE_ARITHMETIC' for r in rows for k in ('own_error_status','common_error_status')))
    write_json(rec.out/'scores.json',summary)
    with (rec.out/'per_frame_metrics.csv').open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    np.savez_compressed(rec.out/'arrays.npz',**{k:np.stack([a[k] for a in all_arrays]) for k in all_arrays[0]})
    rec.report.update(frame_results=rows,means=summary['means'],any_empty_gt_frame=summary['any_empty_gt_frame'],
                      any_nonfinite_error=summary['any_nonfinite_error'])


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode',choices=['calibrate','score'])
    parser.add_argument('--manifest',type=Path,required=True)
    parser.add_argument('--manifest-sha256',required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--prediction-seal',type=Path)
    parser.add_argument('--prediction-seal-sha256')
    args=parser.parse_args()
    require(not args.output.exists(),'Preserve old results: output directory must be new')
    args.output.mkdir(parents=True);rec=Recorder(args.output,args.mode)
    started=time.monotonic();done=threading.Event()
    def timeout(signum,frame):raise TimeoutError('Fixed 600-second wall limit exceeded')
    def memory_limit(signum,frame):raise MemoryError('Fixed 8 GiB process RSS high-water gate exceeded')
    def peak():
        v=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        return int(v if sys.platform=='darwin' else v*1024)
    def monitor():
        while not done.wait(.1):
            if peak()>EXPECTED_CONTRACT['max_rss_bytes']:
                os.kill(os.getpid(),signal.SIGUSR1);return
    signal.signal(signal.SIGALRM,timeout);signal.signal(signal.SIGUSR1,memory_limit)
    signal.setitimer(signal.ITIMER_REAL,EXPECTED_CONTRACT['wall_seconds'])
    threading.Thread(target=monitor,daemon=True).start()
    try:
        rec.phase('verify_external_manifest_identity')
        rec.hash_check(args.manifest,args.manifest_sha256,'Externally root-frozen stage manifest')
        m=rec.json(args.manifest,'Frozen S15C contract and identity list')
        validate_manifest(m)
        require(os.path.realpath(m['python'])==os.path.realpath(sys.executable),'Python executable identity')
        require(timestamp(m['frozen_utc'])<timestamp(rec.report['started_utc']),'Manifest frozen before execution')
        require(args.mode=='score' or (args.prediction_seal is None and args.prediction_seal_sha256 is None),'Calibration cannot consume a later prediction seal')
        rec.hash_check(m['runner'],m['identities'][m['runner']],'Fixed scorer/calibrator source')
        rec.report.update(manifest_sha256=args.manifest_sha256,contract=m['contract'])
        shutil.copy2(args.manifest,args.output/'frozen_manifest.json')
        shutil.copy2(__file__,args.output/'source_snapshot.py')
        if args.mode=='score':shutil.copy2(args.prediction_seal,args.output/'input_prediction_seal.json')
        for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[key]='8'
        import numpy as np
        from PIL import Image
        rec.report.update(numpy_version=np.__version__,pillow_version=Image.__version__)
        if args.mode=='calibrate':calibrate(m,rec)
        else:score(args,m,rec)
        rec.phase('post_run_control_identity_check')
        for p in set(m['controls'])|{m['runner'],m['history_seal']}:
            rec.hash_check(p,m['identities'][p],'Post-run immutable controls')
        rec.hash_check(args.manifest,args.manifest_sha256,'Post-run manifest')
        require(peak()<=EXPECTED_CONTRACT['max_rss_bytes'],'Final 8 GiB process RSS gate')
        require(time.monotonic()-started<=EXPECTED_CONTRACT['wall_seconds'],'Final 600-second wall gate')
        rec.report['output_sha256']={str(p.relative_to(args.output)):sha(p) for p in sorted(args.output.rglob('*')) if p.is_file() and p.name!='run_metadata.json'}
        rec.report.update(status='SUCCESS',completed_utc=utc())
    except BaseException as error:
        rec.report.update(status='FAILED',completed_utc=utc(),error=repr(error),traceback=traceback.format_exc())
    finally:
        done.set();signal.setitimer(signal.ITIMER_REAL,0)
        rec.report.update(wall_seconds=time.monotonic()-started,process_peak_rss_bytes=peak())
        rec.flush()
    print(json.dumps(dict(status=rec.report['status'],output=str(args.output.resolve()),completed_utc=rec.report['completed_utc'])),flush=True)
    return 0 if rec.report['status']=='SUCCESS' else 1


if __name__=='__main__':
    raise SystemExit(main())
