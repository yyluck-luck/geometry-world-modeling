"""Download precisely two preselected official ZIP members, then emit timing metadata."""
import datetime as dt
from fractions import Fraction
import hashlib
import json
import os
from pathlib import Path
import struct
import subprocess
import time
import traceback
import urllib.request
import zlib

BASE=Path(__file__).parent
D=BASE/'retry_01'
BUDGET=150*1024**2
START=time.monotonic()
R={'status':'RUNNING','started_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'archive_body_budget_bytes':BUDGET,'archive_body_bytes':0,'requests':[],'members':[],'connections_max':1,'RGB_frames_exported':0,'RGB_frames_viewed':0,'audio_decode_runs':0,'model_runs':0}
def utc(): return dt.datetime.now(dt.timezone.utc).isoformat()
def sha(b): return hashlib.sha256(b).hexdigest()
def write_json(path,data):
 with path.open('x') as f:json.dump(data,f,indent=2,allow_nan=False);f.write('\n')
def checkpoint(phase,**details):
 with (D/'progress.jsonl').open('a') as f:f.write(json.dumps({'utc':utc(),'phase':phase,'archive_body_bytes':R['archive_body_bytes'],**details})+'\n')
def check_time():
 if time.monotonic()-START>585:raise TimeoutError('585 s internal deadline before 600 s external deadline')
def file_identity(p):
 h=hashlib.sha256();n=0
 with p.open('rb') as f:
  while b:=f.read(1024**2):h.update(b);n+=len(b)
 return {'file':p.name,'bytes':n,'sha256':h.hexdigest()}
def fetch(offset,count,name):
 """At most two attempts; failed partials retained and charged to the shared cap."""
 for attempt in (1,2):
  check_time()
  if count>BUDGET-R['archive_body_bytes']:raise RuntimeError('Full requested range cannot fit remaining total body budget')
  r={'started_utc':utc(),'range':f'bytes={offset}-{offset+count-1}','expected_body_bytes':count,'observed_body_bytes':0,'attempt':attempt}
  R['requests'].append(r);path=D/f'{name}.attempt{attempt}';h=hashlib.sha256()
  try:
   request=urllib.request.Request(URL,headers={'Range':r['range'],'Accept-Encoding':'identity','User-Agent':'bounded-public-two-stream-metadata/1.0'})
   with urllib.request.urlopen(request,timeout=30) as response:
    r.update(status=response.status,content_range=response.headers.get('Content-Range'),content_length=response.headers.get('Content-Length'),content_encoding=response.headers.get('Content-Encoding'))
    assert response.status==206,'Ignored Range; body not read'
    assert r['content_range']==f'bytes {offset}-{offset+count-1}/{ARCHIVE_SIZE}'
    assert r['content_encoding'] in (None,'identity')
    assert int(r['content_length'])==count
    with path.open('xb') as f:
     while r['observed_body_bytes']<count:
      check_time();b=response.read(min(1024**2,count-r['observed_body_bytes']))
      if not b:raise EOFError('Truncated range body')
      R['archive_body_bytes']+=len(b);r['observed_body_bytes']+=len(b)
      assert R['archive_body_bytes']<=BUDGET
      f.write(b);h.update(b)
   assert r['observed_body_bytes']==count
   r['status_result']='EXACT_RANGE_COMPLETE';return path
  except Exception as exc:
   r['error']={'type':type(exc).__name__,'message':str(exc)}
   if attempt==2 or not isinstance(exc,(OSError,EOFError)):raise
  finally:
   r.update(completed_utc=utc(),sha256=h.hexdigest(),saved_file=path.name if path.exists() else None)
   with (D/'requests.jsonl').open('a') as f:f.write(json.dumps(r)+'\n')
   checkpoint('range_end',range=r['range'],attempt=attempt,observed_body_bytes=r['observed_body_bytes'],error=r.get('error'))
def member_download(member):
 camera=Path(member['name']).stem;checkpoint('member_start',camera=camera)
 m={'camera':camera,'catalog_member':member,'started_utc':utc()};R['members'].append(m)
 offset=member['local_header_offset'];fixed=fetch(offset,30,camera+'.local_fixed').read_bytes()
 sig,ver,flags,method,tm,date,crc,clen,ulen,nlen,xlen=struct.unpack('<4s5H3I2H',fixed)
 assert sig==b'PK\x03\x04' and flags==member['flags']==0 and method==member['method']==8
 assert crc==int(member['crc32'],16) and clen==member['compressed_bytes'] and ulen==member['uncompressed_bytes']
 assert nlen==len(member['name'].encode('utf-8'))
 rest=fetch(offset+30,nlen+xlen,camera+'.local_name_extra').read_bytes()
 assert rest[:nlen].decode('utf-8')==member['name']
 data_offset=offset+30+nlen+xlen
 assert data_offset+clen<=CAT['eocd']['central_directory_offset']
 m['local_header']={'offset':offset,'version_needed':ver,'flags':flags,'method':method,'filename_bytes':nlen,'extra_bytes':xlen,'data_offset':data_offset,'compressed_bytes':clen,'uncompressed_bytes':ulen,'crc32':f'{crc:08x}'}
 compressed=fetch(data_offset,clen,camera+'.deflate')
 m['compressed']=file_identity(compressed)
 output=D/f'{camera}.mp4';partial=D/f'{camera}.mp4.decompress_partial'
 decoder=zlib.decompressobj(-15);total=0;running_crc=0;h=hashlib.sha256()
 with compressed.open('rb') as f,partial.open('xb') as out:
  while block:=f.read(1024**2):
   check_time();pending=block
   while pending:
    b=decoder.decompress(pending,min(1024**2,ulen-total+1));pending=decoder.unconsumed_tail
    total+=len(b);assert total<=ulen,'Uncompressed length exceeds catalog'
    running_crc=zlib.crc32(b,running_crc);h.update(b);out.write(b)
    if not b and pending:raise ValueError('Inflater made no progress')
 assert decoder.eof and not decoder.unused_data and not decoder.unconsumed_tail
 assert total==ulen and running_crc==crc
 assert not output.exists();partial.rename(output)
 m['output']={'file':output.name,'bytes':total,'sha256':h.hexdigest(),'crc32':f'{running_crc:08x}','raw_deflate_eof':True}
 m['completed_utc']=utc();checkpoint('member_complete',camera=camera,bytes=total)
 return output

def probe(path):
 camera=path.stem;checkpoint('probe_start',camera=camera)
 commands=[('streams',['-show_format','-show_streams']),('frames',['-select_streams','v:0','-show_frames','-show_entries','frame=media_type,stream_index,key_frame,pts,pts_time,best_effort_timestamp,best_effort_timestamp_time,pkt_dts,pkt_dts_time,duration,duration_time,pkt_duration,pkt_duration_time'])]
 parsed={};runmeta=[]
 for label,args in commands:
  check_time();command=['/opt/homebrew/bin/ffprobe','-v','error','-threads','1',*args,'-of','json',str(path)]
  out=D/f'{camera}.{label}.json';err=D/f'{camera}.{label}.stderr.txt';t0=utc()
  with out.open('xb') as stdout,err.open('xb') as stderr:
   run=subprocess.run(command,stdout=stdout,stderr=stderr,timeout=min(180,max(1,580-(time.monotonic()-START))))
  item={'label':label,'argv':command,'started_utc':t0,'completed_utc':utc(),'returncode':run.returncode,'stdout':file_identity(out),'stderr':file_identity(err)}
  runmeta.append(item)
  assert run.returncode==0,'ffprobe failed'
  parsed[label]=json.loads(out.read_text())
 streams=parsed['streams']['streams'];video=[s for s in streams if s['codec_type']=='video'];audio=[s for s in streams if s['codec_type']=='audio']
 assert len(video)==1,'Exactly one video stream required'
 v=video[0];frames=parsed['frames']['frames'];assert frames
 assert all(f['media_type']=='video' and f['stream_index']==v['index'] and isinstance(f.get('pts'),int) for f in frames)
 pts=[f['pts'] for f in frames];timebase=Fraction(v['time_base']);times=[p*timebase for p in pts]
 summary={'camera':camera,'probe_runs':runmeta,'video_fields':{k:v.get(k) for k in ['codec_name','codec_long_name','profile','codec_type','width','height','coded_width','coded_height','pix_fmt','r_frame_rate','avg_frame_rate','time_base','start_pts','start_time','duration_ts','duration','nb_frames','bit_rate']},'audio_streams_identified_only':[{k:a.get(k) for k in ['index','codec_name','codec_type','sample_rate','channels','time_base','duration','nb_frames']} for a in audio],'frame_count':len(pts),'pts_all_present':True,'pts_strictly_increasing':all(a<b for a,b in zip(pts,pts[1:])),'pts_unique_count':len(set(pts)),'first_pts':pts[0],'last_pts':pts[-1],'first_pts_seconds_exact':str(times[0]),'last_pts_seconds_exact':str(times[-1]),'delta_pts_histogram':{str(delta):sum(b-a==delta for a,b in zip(pts,pts[1:])) for delta in sorted({b-a for a,b in zip(pts,pts[1:])})},'declared_frame_count_matches_observed':None if v.get('nb_frames') in (None,'N/A') else int(v['nb_frames'])==len(pts),'scope':'ffprobe video frame traversal may decode video internally; only timing metadata retained. No pixel export/view. Audio streams identified, not decoded.'}
 assert summary['pts_strictly_increasing'] and summary['pts_unique_count']==len(pts)
 if summary['declared_frame_count_matches_observed'] is not None:assert summary['declared_frame_count_matches_observed']
 write_json(D/f'{camera}.SUMMARY.json',summary);checkpoint('probe_complete',camera=camera,frame_count=len(pts))
 return summary,times

def main():
 global CAT,URL,ARCHIVE_SIZE
 try:
  catalog_path=BASE.parent/'zip_catalog_01/receipt.json';b=catalog_path.read_bytes()
  assert sha(b)=='e5ec5c9bb6a62ac26172823d5ab551b6412f4af4c2afb1cd6543d7ab3fa22d65'
  CAT=json.loads(b);URL=CAT['url'];ARCHIVE_SIZE=CAT['expected_archive_bytes'];R.update(url=URL,archive_bytes=ARCHIVE_SIZE,catalog_sha256=sha(b))
  pose_receipt=BASE.parent/'pose_metadata_01/retry_01/receipt.json';p=pose_receipt.read_bytes();assert sha(p)=='3456d3ef91ac366b93641ccc6c9cb54df192eaf9f0e1f85e18df6cf795e0075e'
  R['pose_receipt_sha256']=sha(p)
  selected=[next(m for m in CAT['members'] if m['name']==f'coffee_martini/{camera}.mp4') for camera in ['cam00','cam06']]
  outputs=[member_download(m) for m in selected]
  results=[probe(p) for p in outputs];a,b=[r[1] for r in results]
  timeline={'frame_counts':[len(a),len(b)],'frame_counts_equal':len(a)==len(b),'pts_time_sets_identical':set(a)==set(b),'ordered_pts_times_identical':a==b,'only_cam00_times_exact':[str(x) for x in sorted(set(a)-set(b))],'only_cam06_times_exact':[str(x) for x in sorted(set(b)-set(a))],'max_indexwise_time_difference_seconds':float(max((abs(x-y) for x,y in zip(a,b)),default=0)) if len(a)==len(b) else None,'interpretation':'Container presentation-time equality tests only the released aligned stream timeline. It does not independently certify physical exposure synchrony, rolling-shutter effects, object visibility, or future prediction validity. Official synchronization claim remains separate.'}
  write_json(D/'TIMELINE_COMPARISON.json',timeline)
  R.update(status='PASS_TWO_STREAM_CONTAINER_TIMING_ONLY',stream_summaries=[r[0] for r in results],timeline_comparison=timeline)
 except BaseException as e:R.update(status='FAIL_RETAINED',exception={'type':type(e).__name__,'message':str(e),'traceback':traceback.format_exc()})
 finally:
  R.update(completed_utc=utc(),elapsed_seconds=time.monotonic()-START,source_sha256=sha(Path(__file__).read_bytes()))
  write_json(D/'receipt.json',R);checkpoint('complete',status=R['status'])
 print(json.dumps({'status':R['status'],'archive_body_bytes':R['archive_body_bytes'],'elapsed_seconds':R['elapsed_seconds']}))
 return 0 if R['status']=='PASS_TWO_STREAM_CONTAINER_TIMING_ONLY' else 1
if __name__=='__main__':raise SystemExit(main())
