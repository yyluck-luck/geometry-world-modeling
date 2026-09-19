#!/usr/bin/env python3
"""Re-read all S6 raw predictions and S5 history references without model imports.

This checks output files independently of the run-time comparison function.
State tensors are not archived: their finite/equality evidence can only be
checked against run metadata and the authenticated runner, not recomputed here.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
RUNNER_SHA='cc3ae6fd6243ce3531e540dc8c70ef61af0e868c919c7232a16616cf750ba292'
BASE_SHA='efb3c8b72ada668818d4211e6d5bb4aa357a3404778cf29d849f8551160bf923'
MANIFEST_SHA='7ffa1467f5640bee2013a1ed1d30313be14da339ab28f7c364cfc2790f16f126'
PROTOCOL_SHA='03af5253e22e7f82064edce5acd3c18f7ca1ebe294eab790e7fdc85eacf02392'
ADAPTER_SHA='6939dcead1b87e920eafce9aae47c1cc9a46b7a651ef816b3f521c779582152e'
SHAPES={'pts3d_in_self_view':(1,224,224,3),'pts3d_in_other_view':(1,224,224,3),
        'rgb':(1,224,224,3),'conf_self':(1,224,224),'conf':(1,224,224),
        'camera_pose':(1,7),'camera_c2w':(1,4,4)}

def now():return datetime.now(timezone.utc).isoformat()

def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(2**20),b''):h.update(block)
    return h.hexdigest()

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run',type=Path,default=ROOT/'results/S6_cut3r_cpu')
    parser.add_argument('--reference',type=Path,default=ROOT/'results/CUT3R_S5_cpu')
    args=parser.parse_args()
    target=args.run/'raw_outputs_verification.json'
    if target.exists():parser.error('Verification output exists; preserve it')
    checks=[]
    report={'started_utc':now(),'verifier_sha256':sha(__file__),'model_inference_performed':False,
            'evidence_level':'independent file re-read and raw-array comparison; same author, separate implementation',
            'state_evidence_limit':'Runtime state tensors are not archived; this re-read checks their recorded hashes/equality and authenticated runner, not a fresh state-tensor comparison',
            'blocks':[],'checks':checks,'ok':False}
    def check(label,condition):
        checks.append({'name':label,'passed':bool(condition)})
        if not condition:raise AssertionError(label)
    try:
        seq=json.loads((args.run/'sequence_metadata.json').read_text())
        check('sequence_complete',seq.get('ok') is True and seq.get('phase')=='complete')
        check('three_ordered_blocks',[b['block'] for b in seq['blocks']]==[0,1,2])
        check('separate_processes',len({b['pid'] for b in seq['blocks']})==3)
        check('frozen_model_runner',seq['runner_sha256']==RUNNER_SHA)
        check('sequence_snapshot_sha',sha(args.run/'sequence_runner_snapshot.py')==seq['sequence_runner_sha256'])
        check('input_manifest_sha',sha(args.run/'frozen_inputs.json')==MANIFEST_SHA==seq['manifest_sha256'])
        check('S6_protocol_sha',sha(args.run/'frozen_protocol.md')==PROTOCOL_SHA==seq['protocol_sha256'])
        manifest=json.loads((args.run/'frozen_inputs.json').read_text())
        expected_flags=[{'frame':i,'img_mask':[True],'ray_mask':[False],
                         'update':[i<20],'reset':[False]} for i in range(24)]
        for block in range(3):
            folder=args.run/f'block{block}';prior=args.reference/f'block{block}'
            meta=json.loads((folder/'run_metadata.json').read_text())
            old=json.loads((prior/'run_metadata.json').read_text())
            result={'block':block,'new_predictions_sha256':sha(folder/'predictions.npz'),
                    'S5_predictions_sha256':sha(prior/'predictions.npz'),
                    'arrays_checked':0,'historical_arrays_checked':0,'historical_max_abs_difference':0.0,
                    'historical_arrays_exactly_equal':True,'query_changes_descriptive_only':{}}
            check(f'B{block}:run_success',meta.get('ok') is True and meta.get('history_only_memory_ok') is True)
            check(f'B{block}:S5_success',old.get('ok') is True)
            check(f'B{block}:runtime_identity',meta['device']=='cpu' and meta['dtype']=='float32' and meta['cpu_threads']==8 and meta['seed']==0)
            check(f'B{block}:view_counts',meta['views']==24 and meta['history_count']==20 and meta['query_count']==4)
            check(f'B{block}:runner_snapshot_sha',sha(folder/'runner_snapshot.py')==RUNNER_SHA==meta['runner_sha256'])
            check(f'B{block}:S5_runner_snapshot_sha',sha(prior/'runner_snapshot.py')==BASE_SHA==old['runner_sha256']==meta['base_runner_sha256'])
            check(f'B{block}:new_prediction_hash',result['new_predictions_sha256']==meta['predictions_sha256']==seq['blocks'][block]['predictions_sha256'])
            check(f'B{block}:S5_prediction_hash',result['S5_predictions_sha256']==old['predictions_sha256'])
            check(f'B{block}:resource_budget',meta['peak_process_rss_bytes']<=16*1024**3 and seq['blocks'][block]['returncode']==0)
            check(f'B{block}:adapter_identity',meta['runtime_compatibility']['adapter_sha256']==ADAPTER_SHA)
            check(f'B{block}:input_staging',len(meta['input_device_staging']['checks'])==168 and all(c['values_preserved'] for c in meta['input_device_staging']['checks']))
            for field in ('requested_view_flags','prepared_view_flags','view_flags_before_inference','view_flags_after_inference'):
                check(f'B{block}:{field}',meta[field]==expected_flags)
            check(f'B{block}:same_images_as_S5',meta['images']==old['images'])
            check(f'B{block}:images_match_frozen_hashes',[f['sha256'] for f in meta['images']]==[f['rgb_sha256'] for f in manifest['blocks'][block]['frames']])
            state=meta['query_state_write_audit']
            check(f'B{block}:state_schema',state['ok'] is True and state['actual_snapshots']==25 and state['anchor_snapshot_index']==20 and len(state['checks'])==8)
            check(f'B{block}:state_check_coverage',{(c['field'],c['snapshot_index']) for c in state['checks']}=={(f,s) for f in ('state_feat','pose_memory') for s in (21,22,23,24)})
            for c in state['checks']:
                check(f'B{block}:state_record:{c["field"]}:{c["snapshot_index"]}',
                      c['finite'] and c['anchor_finite'] and c['same_shape_and_dtype'] and c['exactly_unchanged']
                      and c['max_absolute_difference']==0 and c['tensor_sha256']==c['anchor_tensor_sha256'])
            with np.load(folder/'predictions.npz',allow_pickle=False) as arrays, np.load(prior/'predictions.npz',allow_pickle=False) as references:
                expected={f'frame{i}_{key}' for i in range(24) for key in SHAPES}
                check(f'B{block}:all_prediction_keys',set(arrays.files)==set(references.files)==expected)
                for frame in range(24):
                    for key,shape in SHAPES.items():
                        name=f'frame{frame}_{key}';new=arrays[name];ref=references[name]
                        check(f'B{block}:{name}:raw_shape_dtype_finite',new.shape==shape and new.dtype==np.dtype('float32') and np.isfinite(new).all())
                        result['arrays_checked']+=1
                        check(f'B{block}:{name}:metadata_matches',meta['outputs'][name]['shape']==list(shape) and meta['outputs'][name]['dtype']==str(new.dtype) and meta['outputs'][name]['all_finite'] is True)
                        if frame<20:
                            check(f'B{block}:{name}:S5_shape_dtype_finite',ref.shape==new.shape and ref.dtype==new.dtype and np.isfinite(ref).all())
                            difference=float(np.abs(new.astype(np.float64)-ref.astype(np.float64)).max())
                            check(f'B{block}:{name}:S5_frozen_tolerance',np.allclose(new,ref,atol=1e-3,rtol=1e-3))
                            result['historical_arrays_checked']+=1
                            result['historical_max_abs_difference']=max(result['historical_max_abs_difference'],difference)
                            result['historical_arrays_exactly_equal'] &= bool(np.array_equal(new,ref))
                        else:
                            result['query_changes_descriptive_only'][name]={'max_abs_difference_from_S5':float(np.abs(new.astype(np.float64)-ref.astype(np.float64)).max()),'exactly_equal_to_S5':bool(np.array_equal(new,ref))}
                comparison=json.loads((folder/'s5_history_comparison.json').read_text())
                check(f'B{block}:runtime_history_comparison_complete',comparison['ok'] is True and comparison['atol']==1e-3 and comparison['rtol']==1e-3 and len(comparison['per_array'])==140)
                check(f'B{block}:history_comparison_sha',sha(folder/'s5_history_comparison.json')==seq['blocks'][block]['history_comparison_sha256'])
            result['ok']=True;report['blocks'].append(result)
        report['ok']=True
    except Exception as error:
        report['error']=repr(error)
    report['completed_utc']=now();report['check_count']=len(checks)
    shutil.copy2(__file__,args.run/'raw_verifier_snapshot.py')
    target.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:report[k] for k in ('ok','check_count','completed_utc')}))
    return 0 if report['ok'] else 1

if __name__=='__main__':raise SystemExit(main())
