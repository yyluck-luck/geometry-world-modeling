#!/usr/bin/env python3
"""Acquire author-published 512 DPT checkpoint with exact LFS identity and bounded transfer."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,subprocess,time,traceback
R=Path(__file__).resolve().parents[1]
def utc():return datetime.now(timezone.utc).isoformat()
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
    out=R/'work/S17A_checkpoint_acquisition';assert not out.exists();out.mkdir(parents=True)
    name='cut3r_512_dpt_4_64.pth';target=R/'data/cut3r'/name;partial=target.with_suffix('.pth.s17a.partial');assert not target.exists() and not partial.exists()
    url='https://huggingface.co/liguang0115/cut3r/resolve/b14faf986da0df405cff1b41e60e2975c4da2745/'+name
    expected='45f7e98a0a64dbeb54901ae2b878cd8cd125f20a4497316483f0bd6f109f8103';size=3173761006
    contract=dict(frozen_utc=utc(),url=url,source='VMem-author linked public CUT3R 512 DPT; pinned HF revision',expected_bytes=size,expected_sha256=expected,max_wall_seconds=1200,max_retries=2,partial_file=str(partial),final_file=str(target),source_metadata=str(R/'work/S17_vmem_feasibility/cut3r_cdn_range_head_receipt.json'),source_metadata_sha256=sha(R/'work/S17_vmem_feasibility/cut3r_cdn_range_head_receipt.json'),fetcher_sha256=sha(__file__),credentials_used=False,checkpoint_deserializations=0)
    (out/'contract.json').write_text(json.dumps(contract,indent=2)+'\n');start=time.monotonic();receipt=dict(started_utc=utc(),status='RUNNING',contract_sha256=sha(out/'contract.json'),progress=[],weight_deserializations=0,model_calls=0)
    def save():
        receipt.update(updated_utc=utc(),elapsed_seconds=time.monotonic()-start,partial_bytes=partial.stat().st_size if partial.exists() else 0);(out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    cmd=['/usr/bin/curl','--disable','--silent','--show-error','--fail','--location','--proto','=https','--proto-redir','=https','--max-redirs','5','--connect-timeout','20','--max-time','1200','--retry','2','--retry-delay','2','--retry-max-time','1200','--continue-at','-','--max-filesize',str(size),'--output',str(partial),'--write-out','HTTP_STATUS:%{http_code}\nTRANSFER_BYTES:%{size_download}\n',url]
    process=None
    try:
        with (out/'curl_stdout.txt').open('w') as stdout,(out/'curl_stderr.txt').open('w') as stderr:
            process=subprocess.Popen(cmd,stdout=stdout,stderr=stderr);last=0;save()
            while process.poll() is None:
                elapsed=time.monotonic()-start
                if elapsed-last>=30:
                    last=elapsed;item=dict(utc=utc(),bytes=partial.stat().st_size if partial.exists() else 0);receipt['progress'].append(item);save();print(json.dumps(item),flush=True)
                if elapsed>1200:raise TimeoutError('1200 second whole acquisition budget')
                if partial.exists() and partial.stat().st_size>size:raise ValueError('Unexpected oversized checkpoint')
                time.sleep(.5)
            receipt['returncode']=process.returncode
        if receipt['returncode']!=0:raise RuntimeError('curl transfer failed; partial and error retained')
        if partial.stat().st_size!=size:raise ValueError('Exact author file size mismatch')
        actual=sha(partial);receipt['actual_sha256']=actual
        if actual!=expected:raise ValueError('Exact author LFS SHA256 mismatch')
        partial.rename(target);receipt.update(status='PASS',path=str(target),bytes=size,sha256=actual)
    except BaseException as e:receipt.update(status='FAIL',error=repr(e),traceback=traceback.format_exc())
    finally:
        if process is not None and process.poll() is None:
            process.terminate()
            try:process.wait(timeout=5)
            except subprocess.TimeoutExpired:process.kill();process.wait()
        receipt['completed_utc']=utc();save();print(json.dumps(receipt,indent=2),flush=True)
    return int(receipt['status']!='PASS')
if __name__=='__main__':raise SystemExit(main())
