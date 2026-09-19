"""Compare independent NumPy2 formulas against an invented original-code packet."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib,json,traceback
import numpy as np
import numerical_reference as ref

HERE=Path(__file__).resolve().parent;PACKET=HERE/'artificial_packet'
report=dict(started_utc=datetime.now(timezone.utc).isoformat(),numpy=np.__version__,checks=[],
 real_archive_reads=0,gt_reads=0,model_calls=0,source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),helper_sha256=hashlib.sha256((HERE/'numerical_reference.py').read_bytes()).hexdigest())
def check(name,ok,**detail):
 report['checks'].append(dict(name=name,passed=bool(ok),**detail))
 if not ok: raise AssertionError(name)
def load(name):
 with np.load(PACKET/name,allow_pickle=False) as z:return {k:z[k] for k in z.files}
try:
 check('NumPy2 independent environment',np.__version__.startswith('2.3.'))
 inp,red=load('inputs.npz'),load('reduced.npz')
 for key in ['pointcloud','depths','confs']:
  a,_=ref.resize_point05(inp[key]);err=float(np.max(abs(a-red[key])))
  check('bilinear '+key,np.allclose(a,red[key],atol=1e-5,rtol=1e-5),max_error=err)
 for i in range(2):
  actual=load(f'geometry{i}.npz')
  expected=ref.candidates(red['pointcloud'][i],red['depths'][i],red['confs'][i],inp['scaled_focal'][i],inp['c2ws'][i])
  for k,a in actual.items():
   exact=k in {'valid_mask','candidate_flat_ids'}
   check(f'frame{i} '+k,np.array_equal(a,expected[k]) if exact else np.allclose(a,expected[k],atol=1e-5,rtol=1e-5),max_error=float(np.max(abs(a.astype(float)-expected[k].astype(float)))))
 small=load('small.npz')
 check('odd size given scale',np.array_equal(ref.resize_point05(small['odd'])[0],small['odd_reduced']))
 check('FP32 quantile fractional rank',ref.quantile999(small['quantile_input'])==small['quantile'])
 tree=load('tree.npz');original=json.loads((PACKET/'receipt.json').read_text())
 independent=ref.LegacyTree(tree['old'])
 check('default split traversal exact', [independent.query(q,.21)[0] for q in tree['queries']]==original['tree_neighbors'])
 a,b=load('render_inputs.npz'),load('render.npz')
 expected,diag=ref.render_reference(a['positions'],a['normals'],a['radii'],a['c2w'],a['focal'],a['pp'],40,30)
 for key in b:check('render '+key,np.array_equal(b[key],expected[key]) if key=='surfel_index_map' else np.allclose(b[key],expected[key],atol=1e-5,rtol=1e-5),max_error=float(np.max(abs(b[key].astype(float)-expected[key].astype(float)))))
 votes=ref.vote_reference(b,original['votes']['sources'])
 check('legacy first vote and double accumulation',np.allclose(votes['weights'],original['votes']['weights'],atol=1e-12,rtol=1e-12) and votes['counts']==original['votes']['counts'])
 # Tiny source-tie failure must be observable rather than accepted by numeric tolerance.
 corrupt=b['surfel_index_map'].copy();occupied=np.flatnonzero(corrupt.reshape(-1)>=0)
 corrupt.flat[int(occupied[0])]=99
 check('intentional one-pixel provenance corruption rejected',not np.array_equal(corrupt,expected['surfel_index_map']))
 check('legacy float32 dot promotes against double threshold',np.float64(np.float32(.6))>np.float64(.6))
 report['status']='PASS_ARTIFICIAL_INDEPENDENT_ONLY'
except Exception as e:
 report['status']='FAIL';report['error']=repr(e);report['traceback']=traceback.format_exc()
finally:
 report['completed_utc']=datetime.now(timezone.utc).isoformat()
 out=HERE/'artificial_check_receipt.json';out.write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps({'status':report['status'],'checks':len(report['checks']),'error':report.get('error')}))
if report['status']=='FAIL':raise SystemExit(1)
