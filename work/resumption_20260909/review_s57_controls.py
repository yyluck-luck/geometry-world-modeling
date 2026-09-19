from pathlib import Path
import datetime, hashlib, json, sys, time
import numpy as np

ROOT=Path(__file__).resolve().parents[2]
D=ROOT/'work/S57_camera_observer_calibration'
OUT=Path(__file__).parent/'S57_ROOT_SOURCE_CONTROL_REVIEW.json'
start=datetime.datetime.now(datetime.timezone.utc).isoformat(); timer=time.monotonic()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(D/'FROZEN_DELIVERY.json')=='a0897511c0269dc04faaa0485fe37c9f42e6b097b3fa880309d44b7a8b1bd93d'
assert sha(D/'AUTHOR_FINAL_RECEIPT.json')=='5ede09c971d747329ef9048768369bcf90065dca5bf37d8a78cb775ae5908ea9'
frozen=json.loads((D/'FROZEN_DELIVERY.json').read_text())
pins={**frozen['source_and_binding_sha256'],**frozen['evidence_files']}
for name,digest in pins.items():
    assert sha(D/name)==digest,name
    assert (D/name).stat().st_mode&0o777==0o444,name
cal=json.loads((D/'CALIBRATION.json').read_text())
known=json.loads((D/'controls/KNOWN_CORRECT_MAPPING_MEASUREMENTS.json').read_text())
cases=json.loads((D/'controls/ALL_16_CONTROL_CASES.json').read_text())
maximum_error=0.; measurements=0; point_residuals=0
for m in list(known.values())+[c['measurement'] for c in cases]:
    p=np.array(m['points1']);q=np.array(m['points2']); ones=np.ones((len(p),1))
    for key,H in [('requested',np.array(m['requested_H'])),('identity',np.eye(3)),('fitted',np.array(m['fitted_H']))]:
        forward=(H@np.concatenate((p,ones),axis=1).T).T
        backward=np.linalg.solve(H,np.concatenate((q,ones),axis=1).T).T
        values=(np.sqrt(np.sum((forward[:,:2]/forward[:,2,None]-q)**2,axis=1))+
                np.sqrt(np.sum((backward[:,:2]/backward[:,2,None]-p)**2,axis=1)))/2
        error=float(np.max(np.abs(values-np.array(m[key]['all_match_symmetric_px']))))
        maximum_error=max(maximum_error,error);point_residuals+=len(values)
        assert error<1e-9
        cells=np.floor(p[:,1]/144).astype(int)*4+np.floor(p[:,0]/144).astype(int)
        medians=[float(np.median(values[cells==i])) for i in range(16) if np.any(cells==i)]
        assert abs(float(np.median(medians))-m[key]['cell_balanced_median_px'])<1e-9
    measurements+=1
t=cal['thresholds']
expected=dict(residual_limit_px=3*max(m['requested']['cell_balanced_median_px'] for m in known.values()),
 separation_margin_px=min(known[f'yaw_{a:+g}']['identity']['cell_balanced_median_px']-known[f'yaw_{a:+g}']['requested']['cell_balanced_median_px'] for a in cal['control_angles'])/4,
 min_matches=max(4,min(m['match_count'] for m in known.values())//2),
 min_supported_source_cells=min(m['source_coverage']['supported'] for m in known.values()),
 min_supported_target_cells=min(m['target_coverage']['supported'] for m in known.values()),
 min_fitted_inlier_fraction=min(m['fitted_forward_inlier_fraction'] for m in known.values())/2)
assert expected==t
assert len(cases)==16 and len(known)==6
assert all((c['verdict']=='CONSISTENT_WITH_RECORDED_NOMINAL_REQUEST')==(c['kind']=='correct') for c in cases)
assert not (ROOT/'results/S57_B0_C1_camera_observer_exploration').exists()
receipt=dict(status='PASS_BOUNDED_SOURCE_CONTROL_REVIEW_FOR_FROZEN_ALL30_EXPLORATION',reviewer='/root',author='/root/c2_v9_recovery_author',
 started_utc=start,completed_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),elapsed_seconds=time.monotonic()-timer,
 frozen_delivery_sha256=sha(D/'FROZEN_DELIVERY.json'),verified_readonly_file_count=len(pins),source_review='Protocol, observer, calibration preparation and exact all-30 runner read in full; no source changes.',
 independent_saved_correspondence_residual_measurements=measurements,point_residuals_recomputed=point_residuals,
 maximum_numeric_difference_px=maximum_error,threshold_rules_recomputed=True,control_preview_visually_inspected=True,
 generated_pixel_body_reads=0,C2_pixel_body_reads=0,new_model_calls=0,
 permitted_next_action='One unchanged B0/C1 all-30-pair saved-output exploration',
 limitations=['Single-texture threshold calibration and same-control verification, no independent generalization.',
 'Nominal model camera and matched 2D support only; no physical camera calibration, full-scene geometry or long-horizon validity.',
 'S42 remains unchanged; this standard observer is not an innovative method.'],novelty_authorization='NONE',new_method_validated=False)
with OUT.open('x') as f:json.dump(receipt,f,ensure_ascii=False,indent=2);f.write('\n')
OUT.chmod(0o444)
sys.path.insert(0,str(ROOT/'scripts'))
from research_log import append_event
append_event('S57 标准观察器源码与控制结果独立复核',f'复核 {len(pins)} 个只读产物；独立用线性方程求解路径重算 {point_residuals} 个保存对应点残差，最大差 {maximum_error:.3g}px；6 项阈值一致。实际查看控制预览。批准一次原定全部30对的已生成像素探索，不代表物理相机/三维正确性或创新方法。',evidence=[str(OUT.relative_to(ROOT))],next_step='执行已冻结 B0/C1 全30对；保留全部 UNKNOWN。')
print(json.dumps(receipt,ensure_ascii=False))
