"""S76 saved-output relative yaw diagnostic; no model, fit, alignment or new angle."""
from datetime import datetime,timezone
from pathlib import Path
import hashlib
import io
import json
import sys
import time
import traceback
import types

D=Path(__file__).resolve().parent

def sha(b):return hashlib.sha256(b).hexdigest()
def utc():return datetime.now(timezone.utc).isoformat()
def need(ok,msg):
    if not ok:raise RuntimeError(msg)
def save(p,x):
    with p.open('x') as f:json.dump(x,f,indent=2,ensure_ascii=False,allow_nan=False);f.write('\n')
    p.chmod(0o444)

def main():
    if sys.argv[1:]==['--compile-only']:
        compile(Path(__file__).read_bytes(),__file__,'exec');print('COMPILE_ONLY_NO_SCIENTIFIC_READ');return 0
    need(len(sys.argv)==4,'Expected contract, generation-receipt, external-receipt SHA arguments')
    cb=(D/'RUN_CONTRACT.json').read_bytes();need(sha(cb)==sys.argv[1],'Contract identity differs');c=json.loads(cb)
    out=D/'scoring_01';out.mkdir(exist_ok=False);start=time.monotonic()
    r=dict(schema='s76-fixed-yaw-relative-score-v1',status='RUNNING',started_utc=utc(),contract_sha256=sha(cb),
           source_sha256=sha(Path(__file__).read_bytes()),reads=[],targets=[],model_calls=0,new_method_validated=False)
    def read(item,kind):
        b=Path(item['path']).read_bytes();h=sha(b);r['reads'].append(dict(path=item['path'],kind=kind,bytes=len(b),sha256=h))
        need(h==item['sha256'],'Read identity differs: '+item['path']);return b
    def budget():need(time.monotonic()-start<c['score']['worker_seconds'],'Score time budget exceeded')
    success=False
    try:
        sys.path[:0]=c['score']['pythonpath']
        from importlib.metadata import version
        import cv2
        import numpy as np
        from PIL import Image
        need({k:version(k) for k in c['score']['versions']}==c['score']['versions'],'Score versions differ')
        cv2.setNumThreads(1);cv2.setRNGSeed(c['score']['seed'])
        rules=types.ModuleType('s76_score_rules');rules.__file__=c['rules_source']['path']
        exec(compile(read(c['rules_source'],'frozen_rule_source'),rules.__file__,'exec'),rules.__dict__)
        new=json.loads(read(dict(path=str(D/'execution_01/receipt.json'),sha256=sys.argv[2]),'new_generation_receipt'))
        external=json.loads(read(dict(path=str(D/'external_01/receipt.json'),sha256=sys.argv[3]),'actual_external_receipt'))
        need(external['returncode']==0 and external['stop_reason'] is None,'External generation failed/stopped')
        need(new['contract_sha256']==sha(cb) and new['status']=='COMPLETE_SINGLE_YAW_FIXED_STREAM'
             and new['stream_identity_pass'] and new['model_unchanged'] and new['all4_targets_preserved'],
             'New generation not comparable to accepted A0')
        old=json.loads(read(c['old_worker_receipt'],'S70_accepted_worker_metadata'))
        need(old['exact_replay_pass'] and old['shared_actual_random_stream_pass'],'Old replay failed')
        def array(item,kind):
            b=read(dict(path=item['path'],sha256=item['file_sha256']),kind)
            a=np.load(io.BytesIO(b),allow_pickle=False)
            need(list(a.shape)==item['shape'] and str(a.dtype)==item['dtype'] and a.nbytes==item['body_bytes']
                 and sha(np.ascontiguousarray(a).tobytes())==item['body_sha256'],'Saved array descriptor differs')
            return a
        baseline=array(old['arms']['A0']['arrays']['targets_uint8'],'old_A0_generated_uint8')
        yaw=array(new['arrays']['targets_uint8'],'new_yaw_generated_uint8')
        need(baseline.shape==yaw.shape==(4,576,576,3) and baseline.dtype==yaw.dtype==np.uint8,'Generated image shape/type differs')
        geometry=new['prescribed_geometry']; gb=read(geometry,'pre_generation_prescribed_geometry')
        with np.load(io.BytesIO(gb),allow_pickle=False) as archive:
            need(set(archive.files)==set(geometry['fields']),'Geometry field set differs')
            g={k:archive[k] for k in archive.files}
        for k,a in g.items():
            desc=geometry['fields'][k]
            need(list(a.shape)==desc['shape'] and str(a.dtype)==desc['dtype'] and a.nbytes==desc['body_bytes']
                 and sha(np.ascontiguousarray(a).tobytes())==desc['body_sha256'],'Geometry descriptor mismatch')
        predicted=rules.prescribed_homographies(g['old_optical'],g['new_optical'],g['K_pixels_576'],np)
        need(np.array_equal(np.stack(predicted),g['H_old_to_new']),'Saved prescribed H differs')
        r['geometry_source_sha256']=geometry['sha256'];r['generation_receipt_sha256']=sys.argv[2]
        r['external_receipt_sha256']=sys.argv[3]
        sift=cv2.SIFT_create(**c['score']['sift']);bf=cv2.BFMatcher(cv2.NORM_L2,crossCheck=False)
        def ratio(a,b):
            if a is None or b is None or len(b)<2:return {}
            return {m.queryIdx:m.trainIdx for row in bf.knnMatch(a,b,k=2) if len(row)==2
                    for m,n in [row] if m.distance<c['score']['ratio']*n.distance}
        def coverage(x):
            if not len(x):return dict(span_xy_fraction=None,occupied_4x4_cells=0)
            cell=np.clip(np.floor(x/144),0,3).astype(int)
            return dict(span_xy_fraction=(np.ptp(x,axis=0)/575).tolist(),occupied_4x4_cells=len(set(map(tuple,cell.tolist()))))
        for idx,target_id in enumerate(rules.TARGET_IDS):
            budget();H=predicted[idx];base,y=baseline[idx],yaw[idx]
            ma,mb=rules.common_fov_masks(H,np)
            need(np.array_equal(ma,g['old_common_fov_masks'][idx]) and np.array_equal(mb,g['new_common_fov_masks'][idx]),'Saved FOV mask differs')
            kp,dp=sift.detectAndCompute(cv2.cvtColor(base,cv2.COLOR_RGB2GRAY),None)
            kq,dq=sift.detectAndCompute(cv2.cvtColor(y,cv2.COLOR_RGB2GRAY),None)
            forward,reverse=ratio(dp,dq),ratio(dq,dp)
            matches=[(i,j) for i,j in sorted(forward.items()) if reverse.get(j)==i]
            x=np.array([kp[i].pt for i,j in matches],dtype=np.float64).reshape(-1,2)
            z=np.array([kq[j].pt for i,j in matches],dtype=np.float64).reshape(-1,2)
            scores=rules.score_same_matches(x,z,H,np)
            all_x=np.array([k.pt for k in kp],dtype=np.float64).reshape(-1,2)
            mapped,valid=rules.project(all_x,H,np);Nc=int((valid & rules.in_frame(mapped,np) & rules.in_frame(all_x,np)).sum())
            N=len(kp);M=len(matches);C=scores['common_fov_matches']['count']
            need(M<=N and C<=Nc,'Support denominator failure')
            row=dict(target_id=target_id,status='MATCHES_AVAILABLE' if M else 'NO_ACCEPTED_MATCHES',
                source_feature_count=N,new_feature_count=len(kq),match_count=M,unmatched_count=N-M,
                matched_fraction=M/N if N else None,unmatched_fraction=(N-M)/N if N else None,
                common_fov_source_feature_count=Nc,common_fov_matched_count=C,
                common_fov_matched_fraction_of_source=C/N if N else None,
                common_fov_matched_fraction_of_common_source=C/Nc if Nc else None,
                match_keypoint_ids=matches,source_coverage=coverage(x),new_coverage=coverage(z),
                H=H.tolist(),old_common_fov_pixels=int(ma.sum()),new_common_fov_pixels=int(mb.sum()),
                total_pixels=576*576,same_match_scores=scores)
            for family in ['all_valid_matches','common_fov_matches']:
                values=scores[family]['paired_identity_minus_H_quantiles_px']
                row[family+'_median_direction_positive']=None if values is None else bool(values[1]>0)
            row['images']={}
            for name,a in [('A0',base),('yaw_plus5',y)]:
                p=out/f'{name}_target_{target_id}.png'
                with p.open('xb') as f:Image.fromarray(a,mode='RGB').save(f,format='PNG')
                p.chmod(0o444);row['images'][name]=dict(path=str(p),sha256=sha(p.read_bytes()),pixel_sha256=sha(a.tobytes()))
            r['targets'].append(row)
            save(out/f'target_{target_id}.json',row)
        need([x['target_id'] for x in r['targets']]==rules.TARGET_IDS,'Missing target rows')
        r['descriptive_all4_positive_median_events']={}
        for family in ['all_valid_matches','common_fov_matches']:
            vals=[x[family+'_median_direction_positive'] for x in r['targets']]
            # Missing takes precedence. Never drop None before all().
            r['descriptive_all4_positive_median_events'][family]=None if any(x is None for x in vals) else all(vals)
        r.update(status='COMPLETE_SAVED_YAW_DIRECTION_DIAGNOSTIC',claim_boundary=c['score']['claim_boundary'])
        budget();success=True
    except Exception as e:
        r.update(status='FAILED',error_type=type(e).__name__,error=str(e),traceback=traceback.format_exc())
    finally:
        r.update(completed_utc=utc(),elapsed_seconds=time.monotonic()-start,
                 unrun_target_ids=[i for i in [20,21,22,23] if i not in [x['target_id'] for x in r['targets']]])
        save(out/'receipt.json',r)
    print(json.dumps(dict(status=r['status'],output=str(out),elapsed_seconds=r['elapsed_seconds'])))
    return 0 if success else 1

if __name__=='__main__':raise SystemExit(main())
