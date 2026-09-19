"""Bounded HTTP range inspection; no tar extraction, images or model imports."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib,json,subprocess,time,tarfile,re

HERE=Path(__file__).parent
URL='https://huggingface.co/datasets/TontonTremblay/RTMV/resolve/855627f73a6fdd4db7fa150097a576f6e890c569/abc.tar'
SIZE=12064450560
def utc():return datetime.now(timezone.utc).isoformat()
def sha(b):return hashlib.sha256(b).hexdigest()
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def scrub(s):
    return re.sub(r'(https?://[^\s?]+)\?[^\s]+',r'\1?[REDACTED_QUERY]',s)
def main():
    out=HERE/'rtmv_range_01';out.mkdir(exist_ok=False)
    start=time.monotonic()
    receipt=dict(started_utc=utc(),url=URL,expected_size=SIZE,code_sha256=sha(Path(__file__).read_bytes()),plan_sha256=sha((HERE/'RTMV_RANGE_PLAN.md').read_bytes()),requests=[],members=[],status='RUNNING',new_scientific_runs=0,full_archive_downloaded=False,full_archive_hash_verified=False,image_or_depth_payloads_requested=0)
    def request(offset,length,kind):
        assert time.monotonic()-start<240,'Overall wall budget exceeded'
        assert 0<=offset<SIZE and 0<length<=2097152 and offset+length<=SIZE
        body=out/f'{len(receipt["requests"]):02d}_{kind}.bin'
        began=utc();t=time.monotonic()
        run=subprocess.run(['/usr/bin/curl','--connect-timeout','10','--max-time',str(max(1,min(25,int(240-(time.monotonic()-start))))),'--max-filesize',str(length),'--retry','0','--max-redirs','5','-L','-sS','-H',f'Range: bytes={offset}-{offset+length-1}','-D','-','-o',str(body),'-w','\nS88_HTTP_CODE:%{http_code}\n',URL],capture_output=True,text=True)
        raw=body.read_bytes() if body.exists() else b''
        ranges=re.findall(r'(?im)^content-range:\s*bytes\s+(\d+)-(\d+)/(\d+)',run.stdout)
        statuses=re.findall(r'S88_HTTP_CODE:(\d+)',run.stdout)
        headers=[]
        for line in run.stdout.splitlines():
            if line.lower().startswith(('http/','content-range:','content-length:','etag:','last-modified:','content-type:','accept-ranges:','location:','s88_http_code:')):headers.append(scrub(line))
        entry=dict(started_utc=began,ended_utc=utc(),seconds=time.monotonic()-t,offset=offset,length=length,kind=kind,returncode=run.returncode,http=statuses[-1] if statuses else None,headers=headers,stderr=scrub(run.stderr),body=str(body.relative_to(out)),body_bytes=len(raw),sha256=sha(raw))
        receipt['requests'].append(entry);write(out/'RECEIPT.json',receipt)
        if kind=='json_quarantine':
            receipt['metadata_json_request_attempted']=True
            receipt['metadata_includes_possible_gt_bytes']=bool(raw)
            write(out/'RECEIPT.json',receipt)
        assert run.returncode==0,f'HTTP transport rc{run.returncode}'
        assert entry['http']=='206','Server did not return bounded206'
        assert ranges and list(map(int,ranges[-1]))==[offset,offset+length-1,SIZE],'Content-Range mismatch'
        assert len(raw)==length,'Body length mismatch'
        return raw,entry
    try:
        offset=0
        for index in range(24):
            raw,req=request(offset,512,'header')
            if raw==b'\0'*512:
                receipt['status']='TAR_END_WITHOUT_JSON';break
            item=tarfile.TarInfo.frombuf(raw,encoding='utf-8',errors='strict')
            info=dict(header_offset=offset,name=item.name,size=item.size,type=item.type.decode('ascii',errors='replace'),is_regular=item.isfile(),is_directory=item.isdir(),header_sha256=sha(raw))
            receipt['members'].append(info)
            assert item.size>=0,'Negative member size'
            assert item.type in (tarfile.REGTYPE,tarfile.AREGTYPE,tarfile.DIRTYPE),'Unsupported tar type; do not skip extension or sparse headers'
            assert not item.isdir() or item.size==0,'Nonempty directory payload unsupported'
            if item.isfile() and item.name.lower().endswith('.json'):
                assert 0<item.size<=2097152,'First JSON exceeds fixed cap'
                data,meta=request(offset+512,item.size,'json_quarantine')
                parsed=json.loads(data)
                assert isinstance(parsed,dict),'Top JSON is not an object'
                receipt['json_member']=info
                receipt['metadata_includes_possible_gt_bytes']=True
                receipt['top_level_keys']=list(parsed)
                camera={k:v for k,v in parsed.items() if 'camera' in k.lower() or k.lower() in ['intrinsics','extrinsics','world2cam','cam2world','w2c','c2w','width','height','focal_length']}
                write(out/'CAMERA_FIELDS.json',camera)
                receipt['status']='FIRST_JSON_CAMERA_FIELDS_OBTAINED';break
            # Only regular files and empty directories; unsupported extensions stop above.
            offset+=512+((item.size+511)//512)*512
            assert offset+512<=SIZE,'Next header outside object'
        else:receipt['status']='HEADER_BUDGET_STOP_NO_JSON'
    except Exception as exc:
        receipt.update(status='STOPPED',error_type=type(exc).__name__,error=scrub(str(exc)))
    receipt.update(completed_utc=utc(),elapsed_seconds=time.monotonic()-start)
    write(out/'RECEIPT.json',receipt)
    print(json.dumps({k:v for k,v in receipt.items() if k not in ['requests','members']},ensure_ascii=False))
if __name__=='__main__':main()
