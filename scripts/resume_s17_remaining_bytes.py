#!/usr/bin/env python3
"""After a terminal failed range attempt, freeze and obtain only still-missing bytes."""
from pathlib import Path
from datetime import datetime,timezone
from concurrent.futures import ThreadPoolExecutor,as_completed
import hashlib,json,re,subprocess,threading,time,traceback
R=Path(__file__).resolve().parents[1]
OLD=R/'work/S17A_checkpoint_resume_ranges'
OUT=R/'work/S17A_checkpoint_remaining_v2'
SIZE=3173761006
SHA='45f7e98a0a64dbeb54901ae2b878cd8cd125f20a4497316483f0bd6f109f8103'
def utc():return datetime.now(timezone.utc).isoformat()
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def dump(p,x):Path(p).write_text(json.dumps(x,indent=2)+'\n')
def main():
    previous=json.loads((OLD/'receipt.json').read_text());original=json.loads((OLD/'contract.json').read_text())
    assert previous['status']=='FAIL','Run only after the previous contract is terminal; never alter its bound.'
    assert not OUT.exists();target=R/'data/cut3r/cut3r_512_dpt_4_64.pth';assert not target.exists()
    assert original['expected_sha256']==SHA and original['expected_bytes']==SIZE
    prefix=Path(original['prefix_path']);assert sha(prefix)==original['prefix_sha256']
    parts=[dict(start=0,end=original['prefix_bytes']-1,path=str(prefix),bytes=original['prefix_bytes'],sha256=original['prefix_sha256'])]
    missing=[]
    for index,a,b in original['ranges']:
        candidates=[x for x in previous['attempts'] if x['index']==index and x['http_status']=='206'
                    and x['content_range']==f'bytes {a}-{b}/{SIZE}' and 0<x['body_bytes']<=b-a+1]
        selected=max(candidates,key=lambda x:x['body_bytes']) if candidates else None
        size=0
        if selected:
            p=Path(selected['path']);size=selected['body_bytes'];assert p.stat().st_size==size
            parts.append(dict(start=a,end=a+size-1,path=str(p),bytes=size,sha256=sha(p),earlier_status=selected['status']))
        if a+size<=b:missing.append(dict(index=index,start=a+size,end=b,bytes=b-a-size+1))
    assert sum(p['bytes'] for p in parts)+sum(x['bytes'] for x in missing)==SIZE
    interval=sorted([(p['start'],p['end']) for p in parts]+[(x['start'],x['end']) for x in missing])
    assert interval[0][0]==0 and interval[-1][1]==SIZE-1 and all(x[1]+1==y[0] for x,y in zip(interval,interval[1:]))
    OUT.mkdir();start=time.monotonic();lock=threading.Lock()
    contract=dict(frozen_utc=utc(),source_receipt=str(OLD/'receipt.json'),source_receipt_sha256=sha(OLD/'receipt.json'),
                   source_contract_sha256=sha(OLD/'contract.json'),script_sha256=sha(__file__),url=original['url'],
                   expected_bytes=SIZE,expected_sha256=SHA,preserved_parts=parts,missing=missing,
                   workers=4,attempts_per_range=3,retry_backoff_seconds=2,max_wall_seconds=1800,max_attempt_seconds=300,
                   transport='HTTPS HTTP/1.1; public URL, no credentials; exact206/Content-Range/size then whole LFS SHA',
                   rationale='Prior terminal transfer incomplete. Preserve every authenticated contiguous response prefix; re-fetch only missing tails. HTTP/1.1 avoids observed HTTP/2 stream errors.',
                   preserved_bytes=sum(x['bytes'] for x in parts),missing_bytes=sum(x['bytes'] for x in missing),
                   max_response_body_bytes=3*sum(x['bytes'] for x in missing),checkpoint_deserializations=0)
    dump(OUT/'contract.json',contract)
    receipt=dict(status='RUNNING',started_utc=utc(),contract_sha256=sha(OUT/'contract.json'),attempts=[],completed_ranges=[],bytes_received=0,model_calls=0,weight_deserializations=0)
    def save():receipt.update(updated_utc=utc(),elapsed_seconds=time.monotonic()-start);dump(OUT/'receipt.json',receipt)
    def obtain(item):
        i,a,b,n=item['index'],item['start'],item['end'],item['bytes']
        for attempt in range(1,4):
            if attempt>1:time.sleep(2)
            remaining=1800-(time.monotonic()-start)
            if remaining<=0:raise TimeoutError('Frozen remaining-byte total deadline')
            path=OUT/f'range_{i:02d}_attempt_{attempt}.bin';begin=utc()
            command=['/usr/bin/curl','--disable','--http1.1','--silent','--show-error','--fail','--location',
                     '--proto','=https','--proto-redir','=https','--max-redirs','5','--connect-timeout','20',
                     '--max-time',str(max(1,int(min(300,remaining)))),'--max-filesize',str(n),'--range',f'{a}-{b}',
                     '--dump-header','-','--output',str(path),original['url']]
            proc=subprocess.run(command,capture_output=True);headers=proc.stdout.decode('latin1')
            cr=re.findall(r'(?im)^content-range:\s*([^\r\n]+)',headers);status=re.findall(r'(?im)^HTTP/\S+\s+(\d+)',headers)
            received=path.stat().st_size if path.exists() else 0
            ok=proc.returncode==0 and status and status[-1]=='206' and cr and cr[-1]==f'bytes {a}-{b}/{SIZE}' and received==n
            row=dict(index=i,start=a,end=b,attempt=attempt,path=str(path),started_utc=begin,completed_utc=utc(),
                     returncode=proc.returncode,http_status=status[-1] if status else None,content_range=cr[-1] if cr else None,
                     body_bytes=received,error=proc.stderr.decode('utf8',errors='replace')[:800],status='PASS' if ok else 'FAIL')
            if ok:row['sha256']=sha(path)
            with lock:
                receipt['attempts'].append(row);receipt['bytes_received']+=received
                if ok:receipt['completed_ranges'].append(i)
                save();print(json.dumps({k:row[k] for k in ['index','attempt','status','body_bytes','completed_utc']}),flush=True)
            if ok:return dict(start=a,end=b,path=str(path),bytes=n,sha256=row['sha256'])
        raise RuntimeError(f'Missing range {i} failed all bounded attempts')
    save()
    try:
        with ThreadPoolExecutor(max_workers=4) as pool:
            for f in as_completed([pool.submit(obtain,x) for x in missing]):parts.append(f.result())
        parts.sort(key=lambda x:x['start'])
        assert parts[0]['start']==0 and parts[-1]['end']==SIZE-1 and all(x['end']+1==y['start'] for x,y in zip(parts,parts[1:]))
        assert all(Path(x['path']).stat().st_size==x['bytes'] and sha(x['path'])==x['sha256'] for x in parts)
        assembled=target.with_suffix('.pth.s17a.v2.assembled');assert not assembled.exists()
        with assembled.open('xb') as out:
            for x in parts:
                with Path(x['path']).open('rb') as source:
                    while data:=source.read(8*1024*1024):out.write(data)
        actual=sha(assembled);receipt['actual_sha256']=actual
        assert assembled.stat().st_size==SIZE and actual==SHA
        assembled.rename(target);receipt.update(status='PASS',path=str(target),bytes=SIZE,sha256=actual)
    except BaseException as error:receipt.update(status='FAIL',error=repr(error),traceback=traceback.format_exc())
    finally:receipt['completed_utc']=utc();save();print(json.dumps({k:v for k,v in receipt.items() if k not in ['attempts','completed_ranges']},indent=2),flush=True)
    return int(receipt['status']!='PASS')
if __name__=='__main__':raise SystemExit(main())
