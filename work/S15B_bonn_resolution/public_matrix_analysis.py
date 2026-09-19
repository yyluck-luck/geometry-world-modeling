from pathlib import Path
from datetime import datetime, timezone
import numpy as np, json, hashlib, ast
out=Path(__file__).parent
start=datetime.now(timezone.utc).isoformat()
M=np.array([[1.0157,.1828,-.2389,.0113],[.0009,-.8431,-.6413,-.0098],[-.3009,.6147,-.8085,.0111],[0,0,0,1.]])
U,s,Vh=np.linalg.svd(M[:3,:3]); R=U@Vh
assert np.linalg.det(R)>0
mu=float(s.mean()); S=M.copy();S[:3,:3]=mu*R
# An artificial rigid relative body motion. Never a Bonn trajectory.
z=.3;c=np.cos(z);sn=np.sin(z)
A=np.array([[c,-sn,0,.12],[sn,c,0,-.07],[0,0,1,.05],[0,0,0,1.]])
B=np.linalg.inv(S)@A@S
Br=np.linalg.inv(M)@A@M
checks=[{'name':'AX=XB for declared artificial similarity X','pass':bool(np.allclose(A@S,S@B,atol=1e-12,rtol=0)),'error':float(np.max(np.abs(A@S-S@B)))},
{'name':'uniform scale cancels in conjugated rotation','pass':bool(np.allclose(B[:3,:3].T@B[:3,:3],np.eye(3),atol=1e-12,rtol=0)),'error':float(np.max(np.abs(B[:3,:3].T@B[:3,:3]-np.eye(3))))},
{'name':'raw rounded published M is not silently accepted as rigid','pass':bool(np.max(np.abs(Br[:3,:3].T@Br[:3,:3]-np.eye(3)))>1e-8),'error':float(np.max(np.abs(Br[:3,:3].T@Br[:3,:3]-np.eye(3))))}]
assert all(x['pass'] for x in checks)
launch=(out/'cut3r_video_launch.py').read_text();tree=ast.parse(launch)
callnames=[]
for n in ast.walk(tree):
 if isinstance(n,ast.Call):
  try:callnames.append(ast.unparse(n.func))
  except Exception:pass
report={'schema':'s15b-public-algebra-v1','started_utc':start,'ended_utc':datetime.now(timezone.utc).isoformat(),'evidence_kind':'PUBLIC_CONSTANTS_AND_ARTIFICIAL_MOTION_ONLY','new_real_rgb_reads':0,'depth_reads':0,'trajectory_reads':0,'model_calls':0,'published_singular_values':s.tolist(),'nearest_similarity_scale':mu,'published_minus_nearest_similarity_max_abs':float(np.max(np.abs(M-S))),'nearest_R_det':float(np.linalg.det(R)),'checks':checks,'source_static_audit':{'launch_gt_traj_func_occurrences':launch.count('gt_traj_func'),'launch_undistort_occurrences':launch.count('undistort'),'launch_gt_loadtxt_call':any('loadtxt' in c for c in callnames),'warning':'No executed dataset adapter; AST and source text only'},'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
(out/'public_matrix_analysis.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
