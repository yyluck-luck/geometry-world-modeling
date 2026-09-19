"""Bounded metadata-only ZIP catalog; never downloads or extracts archive members."""
import datetime
import hashlib
import json
from pathlib import Path
import re
import struct
import time
import traceback
import urllib.request

D=Path(__file__).resolve().parent
URL='https://github.com/facebookresearch/Neural_3D_Video/releases/download/v1.0/coffee_martini.zip'
EXPECTED_SIZE=1186324684
CAP=2*1024*1024
START=time.monotonic()
report=dict(status='RUNNING',started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
 url=URL,expected_archive_bytes=EXPECTED_SIZE,total_body_budget=CAP,total_body_bytes=0,
 requests=[],metadata_only=True,extracted_members=0,media_decode_runs=0)

def ensure(value,message):
 if not value:raise RuntimeError(message)
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def sha(x):return hashlib.sha256(x).hexdigest()
def fetch(start,end,name):
 ensure(0<=start<=end<EXPECTED_SIZE,'Invalid planned range')
 size=end-start+1
 ensure(report['total_body_bytes']+size<=CAP,'Request would exceed total body budget')
 remain=120-(time.monotonic()-START)
 ensure(remain>0,'120s total budget reached')
 row=dict(started_utc=now(),range=f'bytes={start}-{end}',expected_body_bytes=size,
          observed_body_bytes=0,range_honored=False)
 report['requests'].append(row)
 raw=bytearray()
 try:
  request=urllib.request.Request(URL,headers={'User-Agent':'bounded-research-zip-metadata','Range':row['range'],'Accept-Encoding':'identity'})
  with urllib.request.urlopen(request,timeout=min(25,remain)) as response:
   row.update(status=response.status,content_range=response.headers.get('Content-Range'),
              content_length=response.headers.get('Content-Length'),
              content_encoding=response.headers.get('Content-Encoding'))
   ensure(response.status==206,'Server ignored byte Range; stop before reading body')
   ensure(row['content_range']==f'bytes {start}-{end}/{EXPECTED_SIZE}','Unexpected Content-Range')
   ensure(row['content_encoding'] in (None,'identity'),'Unexpected encoded HTTP body')
   ensure(row['content_length'] is None or int(row['content_length'])==size,'Wrong Content-Length')
   row['range_honored']=True
   # Read at most the exact allowed metadata interval; never an unbounded read.
   while len(raw)<size:
    ensure(time.monotonic()-START<120,'120s total budget reached')
    block=response.read(min(65536,size-len(raw),CAP-report['total_body_bytes']))
    ensure(block,'Truncated metadata interval')
    raw.extend(block);report['total_body_bytes']+=len(block);row['observed_body_bytes']+=len(block)
   ensure(len(raw)==size,'Unexpected metadata interval length')
  row['sha256']=sha(raw)
  with (D/name).open('xb') as stream:stream.write(raw)
  row['saved_file']=name
  return bytes(raw)
 except Exception as error:
  row['error']=f'{type(error).__name__}: {error}'
  if raw:
   partial=name+'.partial'
   with (D/partial).open('xb') as stream:stream.write(raw)
   row.update(saved_file=partial,sha256=sha(raw))
  raise
 finally:
  row['completed_utc']=now()
  with (D/'requests.jsonl').open('a') as stream:stream.write(json.dumps(row)+'\n')

try:
 # A zero-comment EOCD requires only the final22 metadata bytes. If not present,
 # stop rather than probing backwards through unknown compressed member data.
 footer=fetch(EXPECTED_SIZE-22,EXPECTED_SIZE-1,'eocd.bin')
 signature,disk,cd_disk,n_disk,n_total,cd_size,cd_offset,comment=struct.unpack('<4s4H2IH',footer)
 ensure(signature==b'PK\x05\x06' and comment==0,'No zero-comment EOCD at final22bytes; bounded metadata route insufficient')
 ensure(disk==cd_disk==0 and n_disk==n_total,'Multi-disk ZIP not supported in this bounded catalog')
 ensure(n_total!=65535 and cd_size!=0xffffffff and cd_offset!=0xffffffff,'ZIP64 needs a separately scoped metadata reader')
 ensure(cd_offset+cd_size==EXPECTED_SIZE-22,'Central directory is not exactly before EOCD')
 ensure(cd_size>0 and cd_size+22<=CAP,'Central directory exceeds body budget')
 report['eocd']=dict(member_count=n_total,central_directory_bytes=cd_size,central_directory_offset=cd_offset,
                     comment_bytes=comment,disk=disk)
 data=fetch(cd_offset,cd_offset+cd_size-1,'central_directory.bin')
 cursor=0;members=[]
 while cursor<len(data):
  ensure(cursor+46<=len(data),'Truncated central directory header')
  v=struct.unpack_from('<4s6H3I5H2I',data,cursor)
  ensure(v[0]==b'PK\x01\x02','Invalid central directory signature')
  _,made,needed,flags,method,mtime,mdate,crc,compressed,uncompressed,nlen,xlen,clen,start_disk,iattr,eattr,offset=v
  end=cursor+46+nlen+xlen+clen
  ensure(end<=len(data),'Truncated central directory entry')
  name_raw=data[cursor+46:cursor+46+nlen]
  name=name_raw.decode('utf-8' if flags&0x800 else 'cp437')
  ensure('\x00' not in name and not name.startswith('/') and '..' not in name.split('/'),'Unsafe archive name; no extraction performed')
  ensure(start_disk==0 and compressed!=0xffffffff and uncompressed!=0xffffffff and offset!=0xffffffff,'ZIP64/split member outside scope')
  ensure(offset<cd_offset,'Member offset not before central directory')
  members.append(dict(name=name,compressed_bytes=compressed,uncompressed_bytes=uncompressed,
    method=method,method_name={0:'stored',8:'deflate'}.get(method,'other'),flags=flags,
    encrypted=bool(flags&1),crc32=f'{crc:08x}',local_header_offset=offset,
    central_filename_bytes=nlen,central_extra_bytes=xlen,central_comment_bytes=clen,
    is_directory=name.endswith('/')))
  cursor=end
 ensure(len(members)==n_total and cursor==len(data),'Member count/central bounds differ')
 ensure(len({m['name'] for m in members})==len(members),'Duplicate member names')
 videos=[m for m in members if re.fullmatch(r'cam\d+\.mp4',Path(m['name']).name)]
 tests=[m for m in videos if Path(m['name']).name=='cam00.mp4']
 training=sorted([m for m in videos if Path(m['name']).name!='cam00.mp4'],key=lambda m:m['name'])
 calibration=[m for m in members if Path(m['name']).name=='poses_bounds.npy']
 metadata=[m for m in members if not m['is_directory'] and not m['name'].lower().endswith('.mp4')]
 ensure(len(tests)==1 and len(training)>0 and len(calibration)==1,'Missing/ambiguous test,training or camera metadata')
 eligible=[m for m in training if not m['encrypted'] and m['method'] in (0,8)]
 ensure(eligible and not tests[0]['encrypted'] and not calibration[0]['encrypted'],'Unusable encrypted data member')
 cheapest=min(eligible,key=lambda m:(m['compressed_bytes'],m['name']))
 report.update(status='PASS_METADATA_CATALOG_ONLY',members=members,video_count=len(videos),
  heldout_test=tests[0],training_cameras_sorted=[m['name'] for m in training],metadata_members=metadata,
  minimum_byte_candidate_training=cheapest,
  minimum_pair_plus_pose_compressed_bytes=sum(m['compressed_bytes'] for m in [tests[0],cheapest,calibration[0]]),
  minimum_pair_scope='Byte-minimum training stream by central metadata only; scientific viewpoint/visibility not certified',
  future_read_requirements=['Local member headers still needed to locate compressed data starts; central extra-length is not a local-header length',
  'Future selected member bytes require CRC/contenthash validation, bounded decompression and actual MP4/NPY format checks',
  'Actual per-frame PTS,fps,camera conventions,visible continuous-motion interval remain unchecked'])
except Exception as error:
 report.update(status='FAILED_OR_INSUFFICIENT_PRESERVED',error_type=type(error).__name__,error=str(error),traceback=traceback.format_exc())
report.update(completed_utc=now(),elapsed_seconds=time.monotonic()-START,source_sha256=sha(Path(__file__).read_bytes()))
with (D/'receipt.json').open('x') as stream:json.dump(report,stream,indent=2);stream.write('\n')
for path in D.iterdir():
 if path.is_file():path.chmod(0o444)
print(json.dumps({k:report.get(k) for k in ['status','total_body_bytes','elapsed_seconds','eocd','video_count','minimum_pair_plus_pose_compressed_bytes','error']},indent=2))
if report.get('minimum_byte_candidate_training'):print(json.dumps(report['minimum_byte_candidate_training']))
raise SystemExit(0 if report['status']=='PASS_METADATA_CATALOG_ONLY' else 1)
