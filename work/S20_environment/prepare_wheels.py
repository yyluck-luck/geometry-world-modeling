"""Resolve explicit additional wheels against retained packages using PyPI JSON metadata.
No installation here; bounded public metadata GETs only, failures retained.
"""
from pathlib import Path
import concurrent.futures, datetime, hashlib, importlib.metadata as md,json,os,subprocess,sys,time
from packaging.requirements import Requirement
from packaging.tags import sys_tags
from packaging.utils import parse_wheel_filename,canonicalize_name
HERE=Path(__file__).resolve().parent
ROOT=HERE.parent.parent
sys.path.insert(0,str(ROOT/'work/S17C_environment/site-packages'))
START=time.monotonic(); utc=lambda:datetime.datetime.now(datetime.timezone.utc).isoformat()
PINS=dict(x.strip().split('==') for x in (HERE/'requested.txt').read_text().splitlines() if x.strip())
TAGS=list(sys_tags()); RANK={t:i for i,t in enumerate(TAGS)}
def metadata(item):
 name,ver=item; url=f'https://pypi.org/pypi/{name}/{ver}/json'; records=[]
 for attempt in range(1,4):
  dest=HERE/f'{name}-{ver}.metadata.attempt{attempt}.json'
  before=utc(); cp=subprocess.run(['curl','-q','--silent','--show-error','--max-time','18','--connect-timeout','10','--max-filesize','2000000','-o',str(dest),'-w','%{http_code}',url],capture_output=True,text=True)
  records.append(dict(started_utc=before,ended_utc=utc(),url=url,attempt=attempt,http=cp.stdout,exit=cp.returncode,stderr=cp.stderr))
  if cp.returncode==0 and cp.stdout=='200': break
 else: raise RuntimeError(json.dumps(records))
 obj=json.loads(dest.read_text()); candidates=[]
 for f in obj['urls']:
  if not f['filename'].endswith('.whl') or f.get('yanked'): continue
  _,_,_,tags=parse_wheel_filename(f['filename']); ranks=[RANK[t] for t in tags if t in RANK]
  if ranks:candidates.append((min(ranks),f))
 if not candidates:raise RuntimeError('No compatible wheel: '+name)
 f=min(candidates,key=lambda x:(x[0],x[1]['filename']))[1]
 return dict(name=name,version=ver,url=f['url'],filename=f['filename'],bytes=f['size'],sha256=f['digests']['sha256'],requires=obj['info']['requires_dist'] or [],metadata_path=str(dest),metadata_sha256=hashlib.sha256(dest.read_bytes()).hexdigest(),requests=records)
report=dict(started_utc=utc(),status='RESOLVING',wheels=[],failures=[])
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
 futures={pool.submit(metadata,p):p for p in PINS.items()}
 for f in concurrent.futures.as_completed(futures):
  try:report['wheels'].append(f.result())
  except Exception as e:report['failures'].append(str(e))
  (HERE/'metadata_progress.json').write_text(json.dumps(report,indent=2))
existing={canonicalize_name(d.metadata['Name']):d.version for d in md.distributions()}
versions={**existing,**{canonicalize_name(n):v for n,v in PINS.items()}}
checks=[]
for w in report['wheels']:
 for raw in w['requires']:
  r=Requirement(raw)
  if r.marker and not r.marker.evaluate({'extra':''}):continue
  n=canonicalize_name(r.name); actual=versions.get(n); ok=actual is not None and r.specifier.contains(actual)
  checks.append(dict(package=w['name'],requirement=raw,actual=actual,pass_=ok))
report['requirements_checks']=checks; report['total_wheel_bytes']=sum(w['bytes'] for w in report['wheels']);report['ended_utc']=utc();report['elapsed_seconds']=time.monotonic()-START
report['status']='PASS_CANDIDATE_WHEEL_PLAN' if not report['failures'] and all(x['pass_'] for x in checks) and report['total_wheel_bytes']<150000000 else 'FAILED_CANDIDATE_WHEEL_PLAN'
(HERE/'wheel_plan.json').write_text(json.dumps(report,indent=2))
print(json.dumps({k:v for k,v in report.items() if k not in ['wheels','requirements_checks']},indent=2));print('unsatisfied', [x for x in checks if not x['pass_']])
