"""Download hashed PyPI wheels and install only in a fresh local overlay."""
from pathlib import Path
import concurrent.futures,datetime,hashlib,json,os,subprocess,sys,time,traceback,zipfile
HERE=Path(__file__).resolve().parent;START=time.monotonic();utc=lambda:datetime.datetime.now(datetime.timezone.utc).isoformat()
plan=json.loads((HERE/'wheel_plan_v2.json').read_text());assert plan['status']=='PASS_CANDIDATE_WHEEL_PLAN'
TARGET=HERE/'site-packages'; WHEELS=HERE/'wheelhouse';assert not TARGET.exists() and not WHEELS.exists();WHEELS.mkdir()
report={'started_utc':utc(),'status':'DOWNLOADING','plan_sha256':hashlib.sha256((HERE/'wheel_plan_v2.json').read_bytes()).hexdigest(),'install_script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'wheels':[],'failures':[],'weight_loads':0,'image_reads':0,'model_runs':0}
def get(w):
 records=[]
 for attempt in range(1,4):
  part=WHEELS/(w['filename']+f'.attempt{attempt}.part'); before=utc()
  cp=subprocess.run(['curl','-q','--silent','--show-error','--max-time','45','--connect-timeout','12','--max-filesize',str(w['bytes']),'-o',str(part),'-w','%{http_code}',w['url']],capture_output=True,text=True)
  records.append(dict(started_utc=before,ended_utc=utc(),url=w['url'],http=cp.stdout,exit=cp.returncode,stderr=cp.stderr,bytes=part.stat().st_size if part.exists() else 0))
  (WHEELS/(w['filename']+'.requests.json')).write_text(json.dumps(records,indent=2))
  if cp.returncode==0 and cp.stdout=='200':
   digest=hashlib.sha256(part.read_bytes()).hexdigest();assert part.stat().st_size==w['bytes'] and digest==w['sha256']
   with zipfile.ZipFile(part) as z:assert z.testzip() is None
   dest=WHEELS/w['filename'];part.rename(dest);return {**w,'requests':records,'verified_utc':utc(),'local_path':str(dest)}
  if cp.returncode not in (18,28,35,52,55,56):break
 raise RuntimeError(w['filename']+' transport failed')
try:
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
  futs={pool.submit(get,w):w for w in plan['wheels']}
  for f in concurrent.futures.as_completed(futs):
   try:report['wheels'].append(f.result())
   except Exception as exc:report['failures'].append(str(exc))
   (HERE/'install_progress.json').write_text(json.dumps(report,indent=2))
 assert not report['failures'] and len(report['wheels'])==len(plan['wheels'])
 report['network_response_bytes']=sum(r['bytes'] for w in report['wheels'] for r in w['requests']);assert report['network_response_bytes']<=160000000
 cmd=[sys.executable,'-m','pip','install','--no-index','--no-deps','--no-compile','--require-hashes','--only-binary=:all:','--find-links',str(WHEELS),'--target',str(TARGET),'-r',str(HERE/'locked_wheels.txt')]
 env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',PIP_DISABLE_PIP_VERSION_CHECK='1',PIP_CONFIG_FILE='/dev/null')
 p=subprocess.run(cmd,env=env,capture_output=True,text=True,timeout=90)
 (HERE/'pip_install.stdout.txt').write_text(p.stdout);(HERE/'pip_install.stderr.txt').write_text(p.stderr);report['install_command']=cmd;report['install_exit']=p.returncode;assert p.returncode==0
 report['status']='PASS_INSTALLED_PENDING_IMPORT'
except Exception as exc:report['status']='FAILED';report['error']=traceback.format_exc()
report['ended_utc']=utc();report['elapsed_seconds']=time.monotonic()-START;(HERE/'install_receipt.json').write_text(json.dumps(report,indent=2));print(report['status'],len(report['wheels']),report.get('error',''))
