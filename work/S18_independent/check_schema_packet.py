"""New file-schema integration only. Does not invoke real CLI identity gates."""
from pathlib import Path
from datetime import datetime,timezone
import importlib.util,hashlib,json,traceback
import numpy as np
import numerical_reference as ref
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent;RUN=HERE/'schema_packet'
OUT=HERE/'schema_check';OUT.mkdir(exist_ok=False)
spec=importlib.util.spec_from_file_location('s18_verifier',ROOT/'scripts/verify_s18_memory_bridge.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
report=dict(status='RUNNING',started_utc=datetime.now(timezone.utc).isoformat(),array_decodes=0,checks=[],real_archive_reads=0,model_calls=0,GT_reads=0,real_cli_identity_gate_tested=False,verifier_sha256=v.sha(ROOT/'scripts/verify_s18_memory_bridge.py'),helper_sha256=v.sha(HERE/'numerical_reference.py'),driver_sha256=v.sha(Path(__file__)))
def check(ok,label,**detail):
 report['checks'].append(dict(label=label,passed=bool(ok),**detail))
 if not ok:raise AssertionError(label)
try:
 m=dict(s17c_final=str(RUN/'invented_final.npz'),s17c_metadata=str(RUN/'invented_prior_metadata.json'))
 meta=v.read_json(RUN/'invented_metadata.json')
 # Only producer output domains, not the invented input archives, are run files.
 v.verify_math(m,RUN,meta,OUT,check,report,ref)
 v.check_counters(meta,report,check)
 report['status']='PASS_ARTIFICIAL_SCHEMA_ONLY'
except Exception as e:
 report['status']='FAIL';report['error']=repr(e);report['traceback']=traceback.format_exc()
finally:
 report['completed_utc']=datetime.now(timezone.utc).isoformat();v.write_json(OUT/'receipt.json',report)
 print(json.dumps({'status':report['status'],'checks':len(report['checks']),'error':report.get('error')}))
if report['status']=='FAIL':raise SystemExit(1)
