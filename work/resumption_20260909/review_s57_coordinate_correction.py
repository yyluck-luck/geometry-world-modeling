from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,sys
import numpy as np
R=Path(__file__).resolve().parents[2];D=R/'work/S57_coordinate_convention_audit'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(D/'FINAL_DELIVERY.json')=='02e5b39d7020233df60629d68336c9174dac47d41cb6c9cfd08a8be6cd0ec9ef'
receipt=json.loads((D/'FINAL_DELIVERY.json').read_text())
for f in receipt['files']:
 p=Path(f['path']);assert sha(p)==f['sha256'];assert p.stat().st_mode&0o777==0o444
new=json.loads((D/'ALL_30_SOURCE_D_CORRECTION.json').read_text())
old=json.loads((R/'results/S57_B0_C1_camera_observer_exploration/ALL_30_PAIRS.json').read_text())
meta=json.loads((R/'work/S57_camera_observer_calibration/CAMERA_METADATA_BINDING.json').read_text())
maxerr=0.;count=0
for row,pairs in new['rows'].items():
 assert len(pairs)==15
 for after,before in zip(pairs,old['rows'][row]['pairs']):
  assert after['pair']==before['pair'];i,j=after['pair'];m=before['measurement']
  frames=meta['rows'][row]['frames'];Ri=np.array(frames[i]['c2w'])[:3,:3].copy();Rj=np.array(frames[j]['c2w'])[:3,:3].copy()
  Ri[:,1:]*=-1;Rj[:,1:]*=-1
  Ki=np.array(frames[i]['K_opencv_index']);Kj=np.array(frames[j]['K_opencv_index'])
  p=np.array(m['points1']);q=np.array(m['points2']);one=np.ones((len(p),1))
  world_i=Ri@np.linalg.solve(Ki,np.concatenate((p,one),axis=1).T)
  projected_j=Kj@np.linalg.solve(Rj,world_i);forward=projected_j[:2].T/projected_j[2,:,None]
  world_j=Rj@np.linalg.solve(Kj,np.concatenate((q,one),axis=1).T)
  projected_i=Ki@np.linalg.solve(Ri,world_j);backward=projected_i[:2].T/projected_i[2,:,None]
  values=(np.linalg.norm(forward-q,axis=1)+np.linalg.norm(backward-p,axis=1))/2
  error=float(np.max(np.abs(values-np.array(after['corrected_requested_residual']['all_match_symmetric_px']))));maxerr=max(maxerr,error)
  assert error<1e-9;count+=len(p)
  if before['verdict']=='UNKNOWN_COVERAGE_OR_MATCH_COHERENCE':assert after['corrected_verdict']==before['verdict']
  assert after['match_count']==len(p)
out=Path(__file__).parent/'S57_COORDINATE_CORRECTION_ROOT_REVIEW.json'
result=dict(completed_utc=datetime.now(timezone.utc).isoformat(),status='PASS_SOURCE_DERIVED_OBSERVER_ERRATUM_ONLY',reviewer='/root',correction_author='/root/negative_result_question_triage',
 final_delivery_sha256=sha(D/'FINAL_DELIVERY.json'),source_review='Root directly read pipeline1124-1145 and1242-1304, util72-167, navigation195-280; both context and target enter column flip before Plucker; archived targets retain preflip.',
 independent_direct_ray_correspondences=count,all30_pairs_checked=True,maximum_difference_px=maxerr,generated_pixel_reads=0,new_model_calls=0,
 scope='Post-exposure saved-data observer correction, no generator update, no independent calibration, no physical camera or novelty validation',counts=new['counts'],
 withdrawn_interpretation='Original S57 inconsistency labels cannot support baseline camera failure; missing D was an observer defect.',new_method_validated=False)
with out.open('x') as f:json.dump(result,f,ensure_ascii=False,indent=2);f.write('\n')
out.chmod(0o444)
sys.path.insert(0,str(R/'scripts'));from research_log import append_event
append_event('S57 相机观察器正式勘误：漏掉y/z基轴转换',f'独立agent源码审计后，root核实际射线消费链并通过直接空间射线路径复算全部30对、{count}个对应点，最大差{maxerr:.3g}px。原观察器的15个不一致标签撤回为模型缺陷证据；原结果保留。修正后B0为13一致/1不确定/1端点，C1为14不确定/1端点。13个原覆盖UNKNOWN全部保留，主MSE不变；这是工具修复，不是新方法或模型收益。',[str(out.relative_to(R)),str((D/'SOURCE_AND_RESULT_AUDIT.md').relative_to(R))],'制作全30对勘误图并更新交接；C2真实生成继续，不触碰其像素。')
print(json.dumps(result,ensure_ascii=False))
