from pathlib import Path
import sys,io,zipfile,json,hashlib,struct,importlib.util,datetime,contextlib
from types import SimpleNamespace
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).resolve().parent;sys.path.insert(0,str(ROOT/'scripts'))
p=ROOT/'scripts/fetch_s15_last_two_curl.py';spec=importlib.util.spec_from_file_location('under_review',p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
start=datetime.datetime.now(datetime.timezone.utc).isoformat();check=[]
b=io.BytesIO()
with zipfile.ZipFile(b,'w') as z:z.writestr('fake/a.png',b'artificial A',compress_type=zipfile.ZIP_STORED);z.writestr('fake/b.png',b'artificial B',compress_type=zipfile.ZIP_DEFLATED)
blob=b.getvalue()
with zipfile.ZipFile(io.BytesIO(blob)) as z:
 cd=z.start_dir;entries=[dict(name=e.filename,compressed_bytes=e.compress_size,uncompressed_bytes=e.file_size,compression_method=e.compress_type,crc32=e.CRC,local_header_offset=e.header_offset) for e in z.infolist()]
for mode in ('success','200','etag','range','curl_limit','redirect','oversize'):
 case=OUT/mode;case.mkdir(exist_ok=False);inv=case/'inv.json';inv.write_text(json.dumps({'entries':entries}));url='https://example.invalid/fake.zip'
 c=dict(schema='s15-range-member-contract-v1',url=url,archive_total_bytes=len(blob),central_directory_offset=cd,etag='"same"',last_modified='Wed, 01 Jan 2025 00:00:00 GMT',inventory_path=str(inv),inventory_sha256=m.sha(inv.read_bytes()),fetcher_sha256=m.sha(p.read_bytes()),zip_parser_sha256=m.sha((ROOT/'scripts/fetch_s15_zip_members.py').read_bytes()),members=[e['name'] for e in entries],max_requests=4,max_response_bytes=10000,max_member_uncompressed_bytes=1000);cp=case/'contract.json';cp.write_text(json.dumps(c));calls=[]
 def stub(cmd,capture_output,text,timeout):
  assert cmd[0:2]==['/usr/bin/curl','--disable'];assert cmd[cmd.index('--retry')+1]=='0' and cmd[cmd.index('--max-redirs')+1]=='0';assert '--location' not in cmd and '-L' not in cmd;assert cmd[cmd.index('--proto')+1]=='=https';assert cmd[cmd.index('--max-time')+1]=='25' and timeout==30
  lo,hi=map(int,cmd[cmd.index('--range')+1].split('-'));assert int(cmd[cmd.index('--max-filesize')+1])==hi-lo+2
  calls.append(cmd);head=Path(cmd[cmd.index('--dump-header')+1]);body=Path(cmd[cmd.index('--output')+1]);raw=blob[lo:hi+1];status=200 if mode=='200' else 302 if mode=='redirect' else 206;etag='"changed"' if mode=='etag' else c['etag'];cr=f'bytes {lo}-{hi+(mode=="range")}/{len(blob)}'
  if mode=='oversize':raw+=b'X'
  head.write_bytes(('HTTP/1.1 200 Connection established\r\n\r\n'+f'HTTP/2 {status}\r\nContent-Range: {cr}\r\nETag: {etag}\r\nLast-Modified: '+c['last_modified']+'\r\n\r\n').encode());body.write_bytes(raw)
  return SimpleNamespace(returncode=63 if mode=='curl_limit' else 0,stdout=f'{status} {url}',stderr='artificial limit' if mode=='curl_limit' else '')
 with patch.object(sys,'argv',['x','--contract',str(cp),'--contract-sha256',m.sha(cp.read_bytes()),'--output',str(case/'out')]),patch.object(m.subprocess,'check_output',return_value='curl 8.7.1 (artificial version stub)'),patch.object(m.subprocess,'run',side_effect=stub),contextlib.redirect_stdout(io.StringIO()):rc=m.main()
 r=json.loads((case/'out/receipt.json').read_text());ok=(rc==0 and len(r['members'])==2 and len(calls)==4) if mode=='success' else (rc==1 and len(r['members'])==0 and len(calls)==1)
 if mode=='success':ok=ok and [Path(e['path']).read_bytes() for e in r['members']]==[b'artificial A',b'artificial B']
 check.append(dict(name=mode,passed=ok,returncode=rc,curl_calls=len(calls),body_bytes=r['body_bytes'],error=r.get('error')));assert ok,check[-1]
result=dict(schema='s15a-curl-transport-difference-checks-v1',started_utc=start,completed_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),status='PASS',checks=check,real_network_requests=0,real_PNG_reads=0,model_calls=0,source_sha256=m.sha(p.read_bytes()),contract_v2_sha256=m.sha((ROOT/'work/S15A_access/history_curl_contract_v2.json').read_bytes()))
(OUT/'checks.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
