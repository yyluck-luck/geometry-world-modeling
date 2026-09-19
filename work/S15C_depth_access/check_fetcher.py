"""Artificial transport/parser checks; never creates a real network connection."""
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import ssl
import struct
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'scripts'))
import fetch_s15c_depth_members as f
OUT = Path(__file__).resolve().parent/'artificial'
OUT.mkdir(exist_ok=False)
started = f.now(); checks = []
name = 'rgbd_bonn_static_close_far/depth/artificial.png'
buf = io.BytesIO()
with zipfile.ZipFile(buf, 'w', compression=zipfile.ZIP_DEFLATED) as z:
    z.writestr(name, b'Artificial bytes only. This is not a real PNG. '*4)
archive = buf.getvalue()
with zipfile.ZipFile(io.BytesIO(archive)) as z:
    q = z.getinfo(name)
    entry = dict(name=name, compressed_bytes=q.compress_size, uncompressed_bytes=q.file_size,
        compression_method=q.compress_type, crc32=q.CRC, local_header_offset=q.header_offset)
base = dict(url=f.URL, max_request_attempts=60, max_attempts_per_range=3,
    max_response_bytes=10*1024**2, wall_seconds=600, central_directory_offset=len(archive),
    archive_total_bytes=len(archive), etag='"synthetic"', last_modified='synthetic')


class Response:
    def __init__(self, body, start, end, status=206, override=None):
        self.status = status; self.buffer = io.BytesIO(body); self.read_count = 0
        self.headers = {'Content-Range': f'bytes {start}-{end}/{len(archive)}',
            'Content-Length': str(end-start+1), 'Content-Encoding': None,
            'ETag': base['etag'], 'Last-Modified': base['last_modified']}
        self.headers.update(override or {})
    def getheader(self, name): return self.headers.get(name)
    def read(self, n): self.read_count += 1; return self.buffer.read(n)
    def close(self): pass


class Factory:
    def __init__(self, modes): self.modes = iter(modes); self.calls = []; self.responses=[]; self.objects=0
    def __call__(self, hostname, port, timeout):
        assert hostname == 'www.ipb.uni-bonn.de' and port == 443 and 0 < timeout <= 25
        self.objects += 1; parent = self
        class Connection:
            sock = None
            def request(self, method, path, headers):
                assert method == 'GET' and headers['If-Match'] == base['etag'] and headers['If-Range'] == base['etag']
                assert headers['Accept-Encoding'] == 'identity'
                start, end = map(int, headers['Range'][6:].split('-'))
                parent.calls.append((start,end)); mode = next(parent.modes)
                if mode == 'ssl': raise ssl.SSLError('artificial TLS failure')
                if mode == 'reset': raise ConnectionResetError('artificial connection reset')
                status = 200 if mode == '200' else 206
                override = {'ETag':'"changed"'} if mode == 'etag' else None
                body = archive[start:end+1]
                if mode == 'short': body=body[:-1]
                self.response=Response(body,start,end,status,override); parent.responses.append(self.response)
            def getresponse(self): return self.response
            def close(self): pass
        return Connection()


def trial(label, modes, mutation=None):
    c = dict(base); r=dict(requests=[],members=[],body_bytes=0)
    if mutation: mutation(c,r)
    out = OUT/label; out.mkdir()
    factory=Factory(modes); fetcher=f.RangeFetcher(c,out,r,factory)
    return fetcher,r,factory,out


def check(label, condition):
    assert condition, label
    checks.append(dict(name=label,status='PASS'))


def rejects(label, fetcher, expected):
    try: fetcher.fetch(0,30,name,'local_header')
    except Exception as e:
        assert expected in str(e), (label,repr(e)); checks.append(dict(name=label,status='PASS',expected_error=repr(e)))
    else: raise AssertionError('did not reject '+label)


fetcher,r,factory,out=trial('success',['ok','ok'])
header=fetcher.fetch(0,30,name,'local_header'); _,nl,xl=f.parse_header(header,entry)
rest=fetcher.fetch(30,nl+xl+entry['compressed_bytes'],name,'payload')
data=f.unpack_member(header,rest,entry,2*1024**2)
check('persistent object reused for both ranges',factory.objects==1 and len(factory.calls)==2)
check('exact payload decompressed and CRC verified',data==b'Artificial bytes only. This is not a real PNG. '*4)
check('actual body byte accounting',r['body_bytes']==30+len(rest))
check('response evidence retained',len(list((out/'responses').glob('*.bin')))==2)
fetcher,r,factory,out=trial('retry_success',['ssl','reset','ok'])
check('two transport failures then success',fetcher.fetch(0,30,name,'local_header')==header)
check('exact three attempts and reconnect objects',len(r['requests'])==3 and factory.objects==3)
check('TLS failure zero response bytes recorded',r['requests'][0]['bytes']==0 and r['body_bytes']==30)
fetcher,r,factory,out=trial('retry_exhausted',['ssl','ssl','ssl','ok'])
rejects('third transport failure stops',fetcher,'artificial TLS')
check('no fourth retry attempted',len(factory.calls)==3)
fetcher,r,factory,out=trial('http200',['200','ok'])
rejects('HTTP 200 rejected without body read or retry',fetcher,'206')
check('HTTP 200 body unopened',factory.responses[0].read_count==0 and len(factory.calls)==1)
fetcher,r,factory,out=trial('etag',['etag','ok'])
rejects('changed ETag rejected without retry',fetcher,'identity mismatch')
check('changed identity body unopened',factory.responses[0].read_count==0 and len(factory.calls)==1)
fetcher,r,factory,out=trial('short',['short','ok'])
rejects('short body protocol failure is not retried',fetcher,'body length mismatch')
check('short body preserved and exactly counted',r['body_bytes']==29 and len(factory.calls)==1 and (out/'responses/request_001.bin').stat().st_size==29)
fetcher,r,factory,out=trial('attempt_budget',[],lambda c,r:r['requests'].extend([{}]*60))
rejects('attempt budget before network',fetcher,'request attempt budget')
check('attempt budget opened zero connections',factory.objects==0)
fetcher,r,factory,out=trial('byte_budget',[],lambda c,r:r.update(body_bytes=10*1024**2-30))
rejects('sentinel byte budget before network',fetcher,'response byte budget')
fetcher,r,factory,out=trial('time_budget',[]);fetcher.started-=601
rejects('total time budget before network',fetcher,'wall budget')
bad=dict(entry,crc32=entry['crc32']^1)
try: f.unpack_member(header,rest,bad,2*1024**2)
except ValueError as e: check('local/central CRC mismatch fails', 'metadata mismatch' in str(e))
else: raise AssertionError('bad CRC accepted')
unsafe=dict(entry,name='../bad.png')
try: f.unpack_member(header,rest,unsafe,2*1024**2)
except ValueError as e: check('unexpected member path fails', 'name mismatch' in str(e))
else: raise AssertionError('unsafe name accepted')
receipt=dict(schema='s15c-depth-fetcher-artificial-checks-v1',started_utc=started,ended_utc=f.now(),
    status='PASS',check_count=len(checks),checks=checks,real_network_requests=0,real_image_decodes=0,
    real_zip_member_payloads_read=0,fetcher_sha256=f.sha(Path(f.__file__).read_bytes()),
    parser_sha256=f.sha((ROOT/'scripts/fetch_s15_zip_members.py').read_bytes()))
f.save(OUT/'receipt.json',receipt)
print(json.dumps(dict(status=receipt['status'],check_count=len(checks),fetcher_sha256=receipt['fetcher_sha256'])))
