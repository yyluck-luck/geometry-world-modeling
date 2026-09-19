"""Frozen bounded curl probe. Credentials/redirect URLs remain in memory only."""
from pathlib import Path
from datetime import datetime, timezone
from urllib.parse import urlsplit
import hashlib, json, logging, os, re, selectors, subprocess, time
from huggingface_hub import hf_hub_url
from huggingface_hub.utils import build_hf_headers

ROOT=Path('/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling')
OUT=Path(__file__).resolve().parent
REV='ac5921080a57f5a634f4b9acbbc8f3db67c9d113'
EXPECTED_SHA='675dc486a02ea06ecf8b6ab0cf4ef88c92298751b2daacf9f65c59871fcb7fe4'
EXPECTED_SIZE=5056346672
PROXY='http://127.0.0.1:7897'
RANGE_SIZE=65536
CURL_ATTEMPTS=[]
MARK=b'\n__PROBE_METRICS__ '
logging.disable(logging.CRITICAL)

def now():
    return datetime.now(timezone.utc).isoformat()

def quoted(value):
    if '\r' in value or '\n' in value:
        raise ValueError('Invalid config value')
    return '"' + value.replace('\\','\\\\').replace('"','\\"') + '"'

def err_class(code, stderr, forced):
    if forced:
        return forced
    if code==0:
        return None
    low=stderr.lower()
    if b'certificate' in low:
        return 'TLS_CERTIFICATE_ERROR'
    if b'ssl' in low or b'tls' in low:
        return 'TLS_CONNECTION_ERROR'
    return {5:'PROXY_RESOLUTION_ERROR',6:'HOST_RESOLUTION_ERROR',7:'CONNECT_ERROR',
            28:'TIME_LIMIT',35:'TLS_CONNECTION_ERROR',52:'EMPTY_REPLY',
            56:'RECEIVE_ERROR',63:'FILE_SIZE_LIMIT'}.get(code,'CURL_ERROR')

def curl_once(url, auth_header=None, byte_range=None):
    host=urlsplit(url).hostname
    if urlsplit(url).scheme!='https':
        raise ValueError('HTTPS required')
    lines=['url = '+quoted(url),'proxy = '+quoted(PROXY)]
    if auth_header is not None:
        if host!='huggingface.co':
            raise ValueError('Bearer restricted to HF host')
        lines.append('header = '+quoted('Authorization: '+auth_header))
    config='\n'.join(lines)+'\n'
    args=['/usr/bin/curl','--disable','--silent','--show-error','--retry','0',
          '--connect-timeout','8','--max-time','15','--proto','=https',
          '--max-redirs','0','--write-out',
          '\n__PROBE_METRICS__ %{http_code} %{size_download} %{time_total} %{ssl_verify_result}\n',
          '--config','-']
    if byte_range is None:
        args += ['--head','--dump-header','-','--output','/dev/null']
    else:
        args += ['--range',byte_range,'--max-filesize',str(RANGE_SIZE),'--include','--output','-']
    started=now();t0=time.monotonic();stdout=bytearray();stderr=bytearray();forced=None
    CURL_ATTEMPTS.append({'host':host,'method':'HEAD' if byte_range is None else 'GET','started_utc':started})
    proc=subprocess.Popen(args,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    proc.stdin.write(config.encode());proc.stdin.close()
    config=None;lines=None;auth_header=None
    sel=selectors.DefaultSelector()
    sel.register(proc.stdout,selectors.EVENT_READ,'stdout')
    sel.register(proc.stderr,selectors.EVENT_READ,'stderr')
    try:
        while sel.get_map():
            if time.monotonic()-t0>20:
                forced='LOCAL_WALL_DEADLINE';proc.kill();break
            for key,_ in sel.select(timeout=0.2):
                chunk=os.read(key.fileobj.fileno(),65536)
                if not chunk:
                    sel.unregister(key.fileobj);continue
                buf=stdout if key.data=='stdout' else stderr
                limit=1048576 if key.data=='stdout' else 65536
                if len(buf)+len(chunk)>limit:
                    forced='LOCAL_CAPTURE_LIMIT';proc.kill();break
                buf.extend(chunk)
            if forced:
                break
        proc.wait(timeout=3)
    finally:
        if proc.poll() is None:
            proc.kill();proc.wait()
        sel.close();proc.stdout.close();proc.stderr.close()
    code=proc.returncode
    rec={'host':host,'method':'HEAD' if byte_range is None else 'GET',
         'requested_range':byte_range,'started_utc':started,'completed_utc':now(),
         'elapsed_seconds':time.monotonic()-t0,'curl_exit_code':code,
         'error_class':err_class(code,bytes(stderr),forced),'TLS_verification_disabled':False,
         'proxy_scope':'existing explicit per-process proxy','auth_header_sent':byte_range is None,
         'signed_query_retained':False,'raw_headers_or_stderr_retained':False}
    payload=bytes(stdout);metrics=None
    if MARK in payload:
        payload,tail=payload.rsplit(MARK,1)
        parts=tail.strip().split()
        if len(parts)==4:
            try:
                status=int(parts[0]);metrics={'http_status':status or None,
                  'curl_body_bytes':int(float(parts[1])),'curl_total_seconds':float(parts[2]),
                  'ssl_verify_result':int(parts[3])}
            except ValueError:
                pass
    if metrics:
        rec.update(metrics)
    else:
        rec['http_status']=None
    # Consume proxy CONNECT and final HTTP header blocks, all in memory.
    headers={};statuses=[]
    while payload.startswith(b'HTTP/'):
        sep=payload.find(b'\r\n\r\n')
        if sep<0:
            break
        block=payload[:sep];payload=payload[sep+4:]
        first,*rest=block.split(b'\r\n')
        try:
            statuses.append(int(first.split()[1]))
        except (ValueError,IndexError):
            pass
        headers={}
        for line in rest:
            if b':' in line:
                key,value=line.split(b':',1)
                headers[key.decode('ascii','ignore').lower()]=value.strip().decode('latin1')
    rec['header_status_sequence']=statuses
    if byte_range is None:
        rec['body_bytes_captured']=0
    else:
        rec['body_bytes_captured']=len(payload)
        rec['partial_body_sha256']=hashlib.sha256(payload).hexdigest()
        rec['content_range']=headers.get('content-range')
    stderr.clear();stdout.clear()
    return rec,headers

def main():
    receipt=OUT/'receipt.json'
    if receipt.exists():
        raise RuntimeError('Refuse to overwrite existing probe')
    protocol=json.loads((OUT/'protocol.json').read_text())
    source_sha=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    if source_sha!=protocol['source_sha256']:
        raise RuntimeError('Source identity mismatch')
    result={'started_utc':now(),'protocol_sha256':hashlib.sha256((OUT/'protocol.json').read_bytes()).hexdigest(),
       'source_sha256':source_sha,'legs':[],'range_probe_started':False,
       'range_size_limit':RANGE_SIZE,'model_runs':0,'browser_operations':0,
       'full_weight_downloaded':False,'full_weight_SHA_verified':False,
       'other_download_processes_touched':False,'raw_secret_values_retained':False}
    try:
        if os.environ.get('HF_HUB_OFFLINE')!='1':
            raise RuntimeError('Offline SDK header construction required')
        headers=build_hf_headers(token=True)
        bearer=headers.get('authorization')
        if not bearer:
            raise RuntimeError('Official saved auth unavailable')
        url=hf_hub_url('liguang0115/vmem','vmem_weights.pth',revision=REV)
        first,h=curl_once(url,auth_header=bearer)
        headers.clear();bearer=None
        result['legs'].append(first)
        matched=(h.get('x-repo-commit')==REV and h.get('x-linked-etag','').strip('"')==EXPECTED_SHA
                 and h.get('x-linked-size')==str(EXPECTED_SIZE))
        result['HF_published_identity_matches_expected']=matched
        result['HF_header_identity']={k:h.get(k) for k in ['x-repo-commit','x-linked-etag','x-linked-size']}
        signed=h.get('location');cdn=urlsplit(signed).hostname if signed else None
        allowed=bool(cdn and (cdn=='huggingface.co' or cdn.endswith('.huggingface.co') or cdn.endswith('.hf.co')))
        result['redirect_host']=cdn
        if first['curl_exit_code']==0 and first.get('http_status') in (301,302,303,307,308) and matched and allowed:
            result['range_probe_started']=True
            second,unused=curl_once(signed,byte_range='0-65535')
            signed=None;h.clear();unused.clear()
            result['legs'].append(second)
            result['range_validated']=(second['curl_exit_code']==0 and second.get('http_status')==206
                and second.get('content_range')==f'bytes 0-65535/{EXPECTED_SIZE}'
                and second.get('body_bytes_captured')==RANGE_SIZE
                and second.get('ssl_verify_result')==0)
            result['status']='RANGE_PASS' if result['range_validated'] else 'RANGE_NOT_VALIDATED'
        else:
            signed=None;h.clear()
            result['status']='STOPPED_AFTER_HF_METADATA_LEG'
            result['stop_reason']='HF transport/status/identity/redirect did not pass the predefined gate; CDN not blindly retried.'
    except BaseException as exc:
        result['status']='PROBE_ERROR'
        result['exception_type']=type(exc).__name__
    result['completed_utc']=now()
    result['explicit_curl_attempts']=len(CURL_ATTEMPTS)
    result['curl_attempt_log']=CURL_ATTEMPTS
    result['total_curl_body_bytes']=sum(x.get('curl_body_bytes',0) for x in result['legs'])
    result['total_body_bytes_captured']=sum(x.get('body_bytes_captured',0) for x in result['legs'])
    result['scope_note']='SDK used offline for normal saved-credential consumption and canonical URL building; actual network legs use curl. No saved credential file read directly.'
    receipt.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__=='__main__':
    main()
