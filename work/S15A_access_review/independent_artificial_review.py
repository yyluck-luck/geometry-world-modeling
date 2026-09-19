"""Independent artificial ZIP/HTTP review. Never opens network or real members."""
from pathlib import Path
import contextlib,copy,datetime,hashlib,importlib.util,io,json,struct,zipfile,zlib
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[2]
OUT=Path(__file__).resolve().parent
SRC=ROOT/'scripts/fetch_s15_zip_members.py'
spec=importlib.util.spec_from_file_location('fetcher_under_review',SRC);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
start=datetime.datetime.now(datetime.timezone.utc).isoformat()
checks=[]
def record(name,ok,**extra):
 checks.append(dict(name=name,passed=bool(ok),**extra))
 if not ok:raise AssertionError(name)

def archive(name='root/a.txt',data=b'synthetic metadata only\n',compression=zipfile.ZIP_DEFLATED):
 b=io.BytesIO()
 with zipfile.ZipFile(b,'w',compression=compression) as z:z.writestr(name,data)
 raw=b.getvalue()
 with zipfile.ZipFile(io.BytesIO(raw)) as z:
  e=z.infolist()[0];cd=z.start_dir
 return raw,dict(name=e.filename,compressed_bytes=e.compress_size,uncompressed_bytes=e.file_size,compression_method=e.compress_type,crc32=e.CRC,local_header_offset=e.header_offset),cd

def run(name,*,data=None,entry=None,cd=None,custom=None,response_mode=None,budget=None,expected_error=None,expected_data=None):
 case=OUT/'cases'/name;case.mkdir(parents=True,exist_ok=False)
 if data is None:data,entry,cd=archive()
 inventory=case/'inventory.json';inventory.write_text(json.dumps({'entries':[entry]}))
 c=dict(schema='s15-range-member-contract-v1',url='https://example.invalid/artificial.zip',archive_total_bytes=len(data),central_directory_offset=cd,etag='"artificial"',last_modified='Wed, 01 Jan 2025 00:00:00 GMT',inventory_path=str(inventory),inventory_sha256=m.sha(inventory.read_bytes()),fetcher_sha256=m.sha(SRC.read_bytes()),members=[entry['name']],max_requests=2,max_response_bytes=100000,max_member_uncompressed_bytes=1000)
 if budget is not None:c['max_response_bytes']=budget
 if custom:c.update(custom)
 cp=case/'contract.json';cp.write_text(json.dumps(c));expected=m.sha(cp.read_bytes())
 reads=[];requests=[]
 class Response:
  def __init__(self,req):
   rang=req.get_header('Range');requests.append(rang);lo,hi=map(int,rang.removeprefix('bytes=').split('-'));self.payload=data[lo:hi+1];self.status=206;self.url=c['url'];self.headers={'Content-Range':f'bytes {lo}-{hi}/{len(data)}','Content-Length':str(hi-lo+1),'ETag':c['etag'],'Last-Modified':c['last_modified']}
   if response_mode=='200':self.status=200
   if response_mode=='range':self.headers['Content-Range']=f'bytes {lo}-{hi+1}/{len(data)}'
   if response_mode=='etag':self.headers['ETag']='"changed"'
   if response_mode=='last_modified':self.headers['Last-Modified']='changed'
   if response_mode=='url':self.url='https://other.invalid/artificial.zip'
   if response_mode=='encoding':self.headers['Content-Encoding']='gzip'
   if response_mode=='content_length':self.headers['Content-Length']=str(hi-lo+2)
   if response_mode=='short':self.payload=self.payload[:-1]
   if response_mode=='overlong':self.payload+=b'X';self.headers.pop('Content-Length')
  def __enter__(self):return self
  def __exit__(self,*a):return False
  def read(self,n):reads.append(n);return self.payload[:n]
 with patch.object(m.urllib.request,'urlopen',side_effect=lambda req,timeout:Response(req)):
  with contextlib.redirect_stdout(io.StringIO()):code=m.execute(cp,expected,case/'output')
 r=json.loads((case/'output'/'receipt.json').read_text())
 if expected_error:
  record(name,code==1 and expected_error in r.get('error',''),error=r.get('error'),http_requests=len(requests),body_read_calls=len(reads),body_bytes=r['body_bytes'])
 else:
  actual=Path(r['members'][0]['path']).read_bytes() if r['members'] else None
  record(name,code==0 and r['status']=='PASS' and actual==expected_data,http_requests=len(requests),body_read_calls=len(reads),body_bytes=r['body_bytes'])
 return r,reads

for meth,label in [(zipfile.ZIP_STORED,'stored'),(zipfile.ZIP_DEFLATED,'deflate')]:
 b,e,cd=archive(compression=meth);run(label,data=b,entry=e,cd=cd,expected_data=b'synthetic metadata only\n')
for mode,err in [('200','range unsupported'),('range','Content-Range mismatch'),('etag','archive identity changed'),('last_modified','archive identity changed'),('url','range unsupported'),('encoding','encoded range'),('content_length','Content-Length mismatch')]:
 r,reads=run('http_'+mode,response_mode=mode,expected_error=err);record('http_'+mode+'_body_not_read',len(reads)==0)
run('short_body',response_mode='short',expected_error='range response length mismatch')
run('overlong_body',response_mode='overlong',expected_error='range response length mismatch')
run('request_budget',custom={'max_requests':3},expected_error='two requests per member budget')
run('byte_budget_before_first_read',budget=29,expected_error='network byte budget')
run('declared_uncompressed_budget',custom={'max_member_uncompressed_bytes':1},expected_error='declared uncompressed budget')
b,e,cd=archive();bad=bytearray(b);bad[0]=0
run('signature',data=bytes(bad),entry=e,cd=cd,expected_error='local signature')
bad=bytearray(b);struct.pack_into('<H',bad,6,1)
run('encrypted_header',data=bytes(bad),entry=e,cd=cd,expected_error='encrypted or masked')
bad=bytearray(b);struct.pack_into('<I',bad,14,e['crc32']^1)
run('local_central_crc',data=bytes(bad),entry=e,cd=cd,expected_error='local/central metadata mismatch')
bad=bytearray(b);bad[30]=ord('z')
run('member_name_mismatch',data=bytes(bad),entry=e,cd=cd,expected_error='member name mismatch')
for pname in ('../evil.txt','/absolute.txt','root/../../evil.txt','root\\evil.txt'):
 b2,e2,c2=archive(name=pname);run('unsafe_path_'+str(len(checks)),data=b2,entry=e2,cd=c2,expected_error='unsafe member path')
b2,e2,c2=archive(compression=zipfile.ZIP_STORED);bad=bytearray(b2);bad[30+len(e2['name'])]^=1
run('payload_crc',data=bytes(bad),entry=e2,cd=c2,expected_error='CRC32 mismatch')
b2,e2,c2=archive(data=b'X'*10000);e2['uncompressed_bytes']=10;bad=bytearray(b2);struct.pack_into('<I',bad,22,10)
run('deflate_bomb',data=bytes(bad),entry=e2,cd=c2,expected_error='deflate termination/budget')
b2,e2,c2=archive();bad=bytearray(b2);struct.pack_into('<H',bad,6,8);struct.pack_into('<III',bad,14,0,0,0)
run('descriptor_header',data=bytes(bad),entry=e2,cd=c2,expected_data=b'synthetic metadata only\n')
b2,e2,c2=archive();run('central_directory_guard',data=b2,entry=e2,cd=29,expected_error='not a local member range')
r,reads=run('hard_byte_budget_probe',budget=30,response_mode='overlong',expected_error='range response length mismatch')
record('hard_budget_overread_observation',r['body_bytes']==31,max_budget=30,actual_body_bytes=r['body_bytes'],interpretation='Actual code reads length+1; one-byte overread possible on malformed reply at exact budget. Root notified before real access.')
result={'schema':'s15a-access-independent-artificial-review-v1','started_utc':start,'ended_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'reviewer':'s15_bonn_calibration','fetcher_sha256':m.sha(SRC.read_bytes()),'metadata_contract_sha256':m.sha((ROOT/'work/S15A_access/metadata_contract.json').read_bytes()),'review_source_sha256':m.sha(Path(__file__).read_bytes()),'checks':checks,'real_network_requests':0,'real_member_decodes':0,'model_calls':0,'status':'PASS_BOUNDARY_CHECKS_WITH_ONE_BYTE_HARD_BUDGET_FINDING'}
(OUT/'checks.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='checks'}));print('checks',len(checks))
