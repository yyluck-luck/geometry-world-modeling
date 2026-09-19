"""Small direct rotation formula check on the saved four-camera alignment."""
from pathlib import Path
import hashlib,json,math,sys
from datetime import datetime,timezone
import numpy as np
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
SOURCE=ROOT/'results/S27M_mst_gradient_diagnostic/alignment_0.npz'
DEST=HERE/'rotation_formula_check.json'
assert not DEST.exists()
started=datetime.now(timezone.utc).isoformat()
before=hashlib.sha256(SOURCE.read_bytes()).hexdigest()
assert before=='7e343530ce47c46290bf4c2675edcc4f5fcb6729fd80a2c225dee65637fa379a'
with np.load(SOURCE,allow_pickle=False) as z:
    pred=z['predicted_c2w'].astype(np.float64);given=z['given_c2w'].astype(np.float64);rot=z['rotation'].astype(np.float64)
rows=[]
for i in range(4):
    mapped=rot@pred[i,:3,:3]
    relative=given[i,:3,:3].T@mapped
    cosine=(np.trace(relative)-1)/2
    vee=np.array([relative[2,1]-relative[1,2],relative[0,2]-relative[2,0],relative[1,0]-relative[0,1]])/2
    theta_atan2=math.degrees(math.atan2(float(np.linalg.norm(vee)),float(cosine)))
    theta_acos=math.degrees(math.acos(float(np.clip(cosine,-1,1))))
    row={'index':i,'trace_acos_deg':theta_acos,'skew_trace_atan2_deg':theta_atan2,'angle_formula_delta_deg':abs(theta_acos-theta_atan2),
         'predicted_rotation_orthogonality_max_abs':float(np.abs(pred[i,:3,:3].T@pred[i,:3,:3]-np.eye(3)).max()),
         'given_rotation_orthogonality_max_abs':float(np.abs(given[i,:3,:3].T@given[i,:3,:3]-np.eye(3)).max()),
         'mapped_rotation_orthogonality_max_abs':float(np.abs(mapped.T@mapped-np.eye(3)).max()),
         'relative_rotation_det':float(np.linalg.det(relative))}
    assert row['angle_formula_delta_deg']<1e-4
    rows.append(row)
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==before
result={'status':'PASS_DIRECT_FORMULA_CONSISTENCY_ONLY','started_utc':started,'completed_utc':datetime.now(timezone.utc).isoformat(),
        'command':[sys.executable,str(Path(__file__).resolve())],'source_sha256':before,'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'why_this_small_followup':'Large orientation discrepancy warranted checking a second direct angle formula; all four cameras retained. No SVD/SO3 projection or fit.',
        'rows':rows,'limitation':'Saved FP32 matrices are approximate rotations; formulas agree to stated small arithmetic discrepancy, not exact analytic SO3 equality.',
        'new_MST':0,'new_PnP':0,'new_forward':0,'new_backward':0,'new_optimizer_steps':0,'sensor_GT_reads':0}
DEST.write_text(json.dumps(result,indent=2,ensure_ascii=False,allow_nan=False)+'\n')
print(json.dumps({'status':result['status'],'max_formula_delta_deg':max(x['angle_formula_delta_deg'] for x in rows),'rows':rows},indent=2))
