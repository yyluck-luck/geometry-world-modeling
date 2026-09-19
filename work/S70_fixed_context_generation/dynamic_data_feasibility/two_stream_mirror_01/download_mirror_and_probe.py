"""Fixed third-party transport of two original-camera files; metadata-only inspection."""
import ast
import datetime as dt
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import subprocess
import time
import traceback
import urllib.parse
import zlib

D=Path(__file__).parent
START=time.monotonic()
REV='cb729cfe56b76fa811ceff1716910a6002db8327'
CANDIDATE_SHA='c602ad6354faf22d9cfa6233c50bc3f2407b8eb575d1e022549554eb0b0a72cd'
PROBE_SOURCE_SHA='852355d0cf9d388237afceabceffedf154a441596e73ebf424da685ed16d8e65'
FILES=[('cam00',66440149,'8eadec32','09cc8b695b78ef13d7e02a3a8a1e7e4f5a9f915730c4515c7cc9bcd06c843ad9'),('cam06',64468940,'ca4382d1','3a5cb2acd5266d23c83d7dbd16c10b69da10eac73b689011e275b0da33695f0d')]
BUDGET=150*1024**2
R={'status':'RUNNING','started_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'media_body_budget_bytes':BUDGET,'media_body_bytes':0,'commands':[],'members':[],'max_connections':1,'automatic_retries':0,'RGB_exports_or_views':0,'audio_decode_runs':0,'model_runs':0,'S70_payload_reads':0,'original_license':'CC-BY-NC4.0; no mirror MIT relicensing assumed'}
def utc():return dt.datetime.now(dt.timezone.utc).isoformat()
def sha(b):return hashlib.sha256(b).hexdigest()
def check_time():
 if time.monotonic()-START>585:raise TimeoutError('585-second internal deadline')
def checkpoint(phase,**details):
 with (D/'progress.jsonl').open('a') as f:f.write(json.dumps({'utc':utc(),'phase':phase,'media_body_bytes':R['media_body_bytes'],**details})+'\n')
def json_file(p,j):
 with p.open('x') as f:json.dump(j,f,indent=2,allow_nan=False);f.write('\n')
def command(argv,label,timeout):
 check_time();row={'label':label,'argv':argv,'started_utc':utc()};R['commands'].append(row)
 stdout=D/(label+'.stdout.json');stderr=D/(label+'.stderr.txt')
 with stdout.open('xb') as out,stderr.open('xb') as err:
  p=subprocess.run(argv,stdout=out,stderr=err,timeout=min(timeout,max(1,580-(time.monotonic()-START))))
 row.update(completed_utc=utc(),returncode=p.returncode,stdout_file=stdout.name,stderr_file=stderr.name)
 meta=json.loads(stdout.read_text()) if stdout.stat().st_size else {}
 row['curl_metadata']=meta
 return p.returncode,meta

def download(camera,size,crc,expected_sha):
 checkpoint('member_start',camera=camera)
 url=f'https://huggingface.co/datasets/Spatial1ntelligence/Preprocessed_Neu3D/resolve/{REV}/coffee_martini/{camera}.mp4'
 item={'camera':camera,'revision_pinned_url':url,'expected_bytes':size,'original_zip_crc32':crc,'mirror_advertised_sha256':expected_sha,'started_utc':utc()};R['members'].append(item)
 head_path=D/(camera+'.HEAD.headers.txt')
 head=['/usr/bin/curl','-q','--head','--location','--silent','--show-error','--fail','--proto','=https','--proto-redir','=https','--connect-timeout','15','--max-time','45','--dump-header',str(head_path),'--output','/dev/null','--write-out','%{json}',url]
 code,meta=command(head,camera+'.HEAD',50)
 # HEAD is specified explicitly, so redirects carry no response body.
 assert meta.get('size_download',0)==0,'Unexpected HEAD body counter'
 assert code==0 and meta['http_code']==200,'HEAD failed'
 final_url=meta['url_effective'];assert urllib.parse.urlsplit(final_url).scheme=='https'
 headers=head_path.read_text();declared=[x.split(':',1)[1].strip() for x in headers.splitlines() if x.lower().startswith('content-length:')]
 assert declared and int(declared[-1])==size,'HEAD length differs'
 commits=[x.split(':',1)[1].strip() for x in headers.splitlines() if x.lower().startswith('x-repo-commit:')]
 assert commits and commits[0]==REV,'Pinned HF revision differs'
 assert size<=BUDGET-R['media_body_bytes']
 partial=D/(camera+'.mp4.download_partial');get_headers=D/(camera+'.GET.headers.txt')
 get=['/usr/bin/curl','-q','--silent','--show-error','--fail','--proto','=https','--connect-timeout','15','--max-time',str(max(1,int(575-(time.monotonic()-START)))),'--max-filesize',str(size),'--dump-header',str(get_headers),'--output',str(partial),'--write-out','%{json}',final_url]
 # No --location here: exactly one GET response, so every body byte is accounted by size_download.
 code,meta=command(get,camera+'.GET',max(1,580-(time.monotonic()-START)))
 downloaded=int(meta.get('size_download',0));R['media_body_bytes']+=downloaded
 item['actual_download_bytes']=downloaded
 assert R['media_body_bytes']<=BUDGET
 assert code==0 and meta['http_code']==200,'GET failed; partial retained'
 assert downloaded==size and partial.stat().st_size==size,'Actual MP4 length differs'
 h=hashlib.sha256();c=0;n=0
 with partial.open('rb') as f:
  while block:=f.read(1024**2):check_time();h.update(block);c=zlib.crc32(block,c);n+=len(block)
 item.update(actual_bytes=n,actual_sha256=h.hexdigest(),actual_crc32=f'{c:08x}')
 assert item['actual_sha256']==expected_sha,'Mirror declared SHA differs'
 assert item['actual_crc32']==crc,'Original ZIP CRC differs'
 output=D/(camera+'.mp4');assert not output.exists();partial.rename(output)
 item.update(file=output.name,completed_utc=utc(),status='FULL_IDENTITY_MATCH')
 output.chmod(0o444);checkpoint('member_complete',camera=camera,bytes=n)
 return output

def main():
 try:
  cand=D.parent/'MIRROR_TRANSPORT_CANDIDATE.md';assert sha(cand.read_bytes())==CANDIDATE_SHA
  catalog=D.parent/'zip_catalog_01/receipt.json';cat_bytes=catalog.read_bytes();assert sha(cat_bytes)=='e5ec5c9bb6a62ac26172823d5ab551b6412f4af4c2afb1cd6543d7ab3fa22d65'
  cat=json.loads(cat_bytes)
  for camera,size,crc,_ in FILES:
   m=next(m for m in cat['members'] if m['name']==f'coffee_martini/{camera}.mp4');assert m['uncompressed_bytes']==size and m['crc32']==crc
  R.update(candidate_sha256=CANDIDATE_SHA,original_catalog_sha256=sha(cat_bytes),revision=REV)
  outputs=[download(*item) for item in FILES]
  # Reuse the already frozen stdlib-only metadata helper, never the old downloader/main.
  source=D.parent/'two_stream_metadata_01/fetch_and_probe.py';data=source.read_bytes();assert sha(data)==PROBE_SOURCE_SHA
  nodes=[n for n in ast.parse(data,filename=str(source)).body if isinstance(n,ast.FunctionDef) and n.name in {'probe','file_identity','write_json'}]
  assert {n.name for n in nodes}=={'probe','file_identity','write_json'}
  env=dict(Path=Path,hashlib=hashlib,json=json,subprocess=subprocess,time=time,Fraction=Fraction,D=D,START=START,utc=utc,check_time=check_time,checkpoint=checkpoint)
  exec(compile(ast.Module(body=nodes,type_ignores=[]),str(source),'exec'),env)
  results=[env['probe'](p) for p in outputs];a,b=[r[1] for r in results]
  timeline={'frame_counts':[len(a),len(b)],'frame_counts_equal':len(a)==len(b),'pts_time_sets_identical':set(a)==set(b),'ordered_pts_times_identical':a==b,'only_cam00_times_exact':[str(x) for x in sorted(set(a)-set(b))],'only_cam06_times_exact':[str(x) for x in sorted(set(b)-set(a))],'max_indexwise_time_difference_seconds':float(max((abs(x-y) for x,y in zip(a,b)),default=0)) if len(a)==len(b) else None,'interpretation':'Released container presentation times only; agreement does not independently prove physical exposure synchronization, rolling-shutter timing, scene visibility, or a prediction result.'}
  json_file(D/'TIMELINE_COMPARISON.json',timeline)
  R.update(status='PASS_TWO_MIRROR_STREAMS_IDENTITY_AND_CONTAINER_TIMING_ONLY',probe_helper_source_sha256=PROBE_SOURCE_SHA,stream_summaries=[r[0] for r in results],timeline_comparison=timeline)
 except BaseException as exc:
  R.update(status='FAILED_PRESERVED',exception={'type':type(exc).__name__,'message':str(exc),'traceback':traceback.format_exc()})
 finally:
  # If a subprocess was interrupted before write-out, retained body sizes are a conservative
  # additional accounting witness (no redirects/retries on GET). Preserve this partial state.
  retained_sizes=sum(p.stat().st_size for p in D.iterdir() if p.name.endswith(('.mp4','.mp4.download_partial')))
  R['retained_media_bytes']=retained_sizes
  R['media_body_bytes_accounting_lower_bound']=max(R['media_body_bytes'],retained_sizes)
  R.update(completed_utc=utc(),elapsed_seconds=time.monotonic()-START,source_sha256=sha(Path(__file__).read_bytes()))
  json_file(D/'receipt.json',R);checkpoint('complete',status=R['status'])
 print(json.dumps({'status':R['status'],'media_body_bytes':R['media_body_bytes'],'elapsed_seconds':R['elapsed_seconds']}))
 return 0 if R['status'].startswith('PASS_') else 1
if __name__=='__main__':raise SystemExit(main())
