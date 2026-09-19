from pathlib import Path
import importlib.util,sys,json,hashlib,datetime,contextlib,io,types,os
from unittest.mock import patch
r=Path('/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling');w=r/'work/S14D_pre_run_review/caller_artificial'
w.mkdir(exist_ok=False)
p=r/'scripts/run_s14d_controlled.py';spec=importlib.util.spec_from_file_location('audited_caller',p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
checks=[]
for case in ['success','bad_rss','spawn_failure','rss_limit']:
 d=w/case;d.mkdir();child=d/'child.py';child.write_text('import time\ntime.sleep(0.75)\n')
 manifest=d/'manifest.json';manifest.write_text(json.dumps({'identities':{str(p):h(p),str(child):h(child)},'python':sys.executable,'runner':str(child)}))
 args=['caller','--manifest',str(manifest),'--output',str(d/'output'),'--control',str(d/'control')]
 patcher=contextlib.nullcontext()
 if case=='bad_rss':patcher=patch.object(m.subprocess,'run',return_value=types.SimpleNamespace(stdout='not-a-number',returncode=0))
 elif case=='spawn_failure':patcher=patch.object(m.subprocess,'Popen',side_effect=OSError('artificial spawn failure'))
 elif case=='rss_limit':patcher=patch.object(m.subprocess,'run',return_value=types.SimpleNamespace(stdout=str(33*1024**2),returncode=0))
 stream=io.StringIO()
 with patch.object(sys,'argv',args),patcher,contextlib.redirect_stdout(stream):code=m.main()
 (d/'caller_stdout.txt').write_text(stream.getvalue())
 receipt=json.loads((d/'control/caller_receipt.json').read_text())
 expected='PASS' if case=='success' else 'FAILED'
 checks.append({'name':case+'_status','ok':receipt['status']==expected and code==(0 if case=='success' else 1)})
 checks.append({'name':case+'_terminal_receipt','ok':bool(receipt.get('completed_utc')) and receipt['status']!='RUNNING'})
 if receipt.get('pid'):
  try:os.kill(receipt['pid'],0);alive=True
  except ProcessLookupError:alive=False
  checks.append({'name':case+'_child_terminated','ok':not alive})
 if case=='rss_limit':checks.append({'name':'rss_exceeded_recorded','ok':receipt['rss_limit_exceeded']})
 if case in ['bad_rss','spawn_failure']:checks.append({'name':case+'_traceback','ok':bool(receipt.get('traceback'))})
assert all(x['ok'] for x in checks),checks
receipt={'status':'PASS','completed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'caller_sha256':h(p),'checks':checks,'check_count':len(checks),'cases':4,'scope':'only artificial child sleep processes; no model/weights/images/GT; no actual 600s timeout test','actual_model_runs':0}
(w/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps({k:receipt[k] for k in ['status','caller_sha256','cases','check_count','completed_utc']}))
