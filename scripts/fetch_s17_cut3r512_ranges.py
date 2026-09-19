#!/usr/bin/env python3
"""Bounded, byte-exact public checkpoint continuation; never deserialize weights."""
from pathlib import Path
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib, json, re, subprocess, threading, time, traceback

R = Path(__file__).resolve().parents[1]
O = R / 'work/S17A_checkpoint_resume_ranges'
SIZE = 3173761006
EXPECTED = '45f7e98a0a64dbeb54901ae2b878cd8cd125f20a4497316483f0bd6f109f8103'
URL = 'https://huggingface.co/liguang0115/cut3r/resolve/b14faf986da0df405cff1b41e60e2975c4da2745/cut3r_512_dpt_4_64.pth'
PREFIX = R / 'data/cut3r/cut3r_512_dpt_4_64.pth.s17a.partial'
FINAL = R / 'data/cut3r/cut3r_512_dpt_4_64.pth'
def now(): return datetime.now(timezone.utc).isoformat()
def sha(p):
    with Path(p).open('rb') as f: return hashlib.file_digest(f, 'sha256').hexdigest()
def dump(p, x): Path(p).write_text(json.dumps(x, indent=2) + '\n')

def main():
    assert not O.exists() and not FINAL.exists()
    prior = R / 'work/S17A_checkpoint_acquisition/receipt.json'
    previous = json.loads(prior.read_text())
    assert previous['status'] == 'FAIL' and previous['returncode'] == 18
    offset = PREFIX.stat().st_size
    assert offset == previous['partial_bytes'] == 533225219
    block = 64 * 1024 * 1024
    ranges = [(i, a, min(SIZE-1, a+block-1)) for i, a in enumerate(range(offset, SIZE, block))]
    assert ranges[0][1] == offset and ranges[-1][2] == SIZE-1
    assert all(ranges[i][2]+1 == ranges[i+1][1] for i in range(len(ranges)-1))
    assert sum(b-a+1 for _, a, b in ranges) + offset == SIZE
    O.mkdir(parents=True)
    contract = dict(frozen_utc=now(), url=URL, expected_bytes=SIZE, expected_sha256=EXPECTED,
                    prefix_path=str(PREFIX), prefix_bytes=offset, prefix_sha256=sha(PREFIX),
                    previous_receipt_sha256=sha(prior), script_sha256=sha(__file__),
                    ranges=ranges, workers=4, attempts_per_range=3, max_wall_seconds=1200,
                    max_attempt_seconds=180, max_response_body_bytes=3*(SIZE-offset),
                    policy='Preserve previous prefix and failed receipts; exact Content-Range and length per block; whole author SHA before rename.',
                    credentials_used=False, weight_deserializations=0, model_calls=0)
    dump(O/'contract.json', contract)
    start = time.monotonic(); lock = threading.Lock()
    receipt = dict(started_utc=now(), status='RUNNING', contract_sha256=sha(O/'contract.json'),
                   attempts=[], completed_ranges=[], bytes_received=0, weight_deserializations=0, model_calls=0)
    def save():
        receipt['updated_utc'] = now(); receipt['elapsed_seconds'] = time.monotonic()-start
        dump(O/'receipt.json', receipt)
    def worker(item):
        i, a, b = item; n = b-a+1
        for attempt in range(1, 4):
            remaining = 1200-(time.monotonic()-start)
            if remaining <= 0: raise TimeoutError('Frozen whole transfer deadline reached')
            p = O/f'range_{i:02d}_attempt_{attempt}.bin'
            begin=now(); t=time.monotonic()
            cmd=['/usr/bin/curl','--disable','--silent','--show-error','--fail','--location',
                 '--proto','=https','--proto-redir','=https','--max-redirs','5','--connect-timeout','20',
                 '--max-time',str(max(1, int(min(180, remaining)))), '--max-filesize',str(n),
                 '--range',f'{a}-{b}','--dump-header','-', '--output',str(p), URL]
            proc=subprocess.run(cmd, capture_output=True)
            # Never persist redirected signed URLs or cookies: retain only final byte headers.
            headers=proc.stdout.decode('latin1')
            cr=re.findall(r'(?im)^content-range:\s*([^\r\n]+)',headers)
            http=re.findall(r'(?im)^HTTP/\S+\s+(\d+)',headers)
            amount=p.stat().st_size if p.exists() else 0
            ok=proc.returncode==0 and http and http[-1]=='206' and cr and cr[-1]==f'bytes {a}-{b}/{SIZE}' and amount==n
            record=dict(index=i, start=a, end=b, attempt=attempt, started_utc=begin,
                        completed_utc=now(), elapsed_seconds=time.monotonic()-t,
                        returncode=proc.returncode, http_status=http[-1] if http else None,
                        content_range=cr[-1] if cr else None, body_bytes=amount, status='PASS' if ok else 'FAIL',
                        error=proc.stderr.decode('utf8',errors='replace')[:800], path=str(p))
            if ok: record['sha256']=sha(p)
            with lock:
                receipt['attempts'].append(record); receipt['bytes_received']+=amount
                if ok: receipt['completed_ranges'].append(i)
                save(); print(json.dumps({k:record[k] for k in ['index','attempt','status','body_bytes','completed_utc']}),flush=True)
            if ok: return i,p
        raise RuntimeError(f'Range {i} failed all frozen attempts')
    save(); good={}
    try:
        with ThreadPoolExecutor(max_workers=4) as pool:
            futures=[pool.submit(worker,item) for item in ranges]
            for f in as_completed(futures):
                i,p=f.result(); good[i]=p
        assert len(good)==len(ranges) and sha(PREFIX)==contract['prefix_sha256']
        assembled=FINAL.with_suffix('.pth.s17a.assembled')
        assert not assembled.exists()
        with assembled.open('xb') as out:
            for p in [PREFIX]+[good[i] for i,_,_ in ranges]:
                with p.open('rb') as f:
                    while data:=f.read(8*1024*1024): out.write(data)
        assert assembled.stat().st_size==SIZE
        actual=sha(assembled); receipt['actual_sha256']=actual
        if actual!=EXPECTED: raise ValueError('Whole author LFS SHA mismatch')
        assembled.rename(FINAL)
        receipt.update(status='PASS',path=str(FINAL),bytes=SIZE,sha256=actual)
    except BaseException as e:
        receipt.update(status='FAIL',error=repr(e),traceback=traceback.format_exc())
    finally:
        receipt['completed_utc']=now(); save()
        print(json.dumps({k:v for k,v in receipt.items() if k not in ['attempts','completed_ranges']},indent=2),flush=True)
    return int(receipt['status']!='PASS')
if __name__=='__main__': raise SystemExit(main())
