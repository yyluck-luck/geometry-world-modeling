#!/usr/bin/env python3
"""Read a bounded remote ZIP central directory, never image/GT member payloads."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import struct
import traceback
import urllib.request

BASE = Path(__file__).resolve().parent
URL = 'https://www.ipb.uni-bonn.de/html/projects/rgbd_dynamic2019/rgbd_bonn_static_close_far.zip'
MAX_BYTES = 2 * 1024 * 1024

def now():
    return datetime.now(timezone.utc).isoformat()

def save(path, obj):
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n')

def main():
    out = BASE / 'directory_receipt.json'
    assert not out.exists(), 'Preserve an earlier receipt'
    source = Path(__file__).read_bytes()
    contract = dict(frozen_utc=now(), url=URL, max_response_bytes=MAX_BYTES,
                    max_requests=2, allowed='ZIP tail and central directory metadata only',
                    forbidden='Member contents, images, RGB/depth/GT arrays, model or scoring',
                    source_sha256=hashlib.sha256(source).hexdigest())
    assert not (BASE / 'access_contract.json').exists()
    save(BASE / 'access_contract.json', contract)
    receipt = dict(started_utc=now(), status='RUNNING', requests=[], body_bytes=0,
                   member_payloads_read=0, complete_archive_downloaded=False)
    save(out, receipt)
    try:
        def fetch(range_value, limit):
            assert len(receipt['requests']) < 2 and receipt['body_bytes'] + limit <= MAX_BYTES
            request = urllib.request.Request(URL, headers={'Range':range_value, 'Accept-Encoding':'identity',
                'User-Agent':'ResearchMetadataAudit/1.0'})
            item = dict(started_utc=now(), requested_range=range_value)
            receipt['requests'].append(item)
            with urllib.request.urlopen(request, timeout=25) as response:
                item.update(status=response.status, final_url=response.url,
                            headers={k:response.headers.get(k) for k in ['Content-Range','Content-Length','ETag','Last-Modified']})
                if response.status != 206:
                    raise ValueError('Server did not honor range; body not read')
                assert response.url == URL, 'Unexpected redirection'
                match = re.fullmatch(r'bytes (\d+)-(\d+)/(\d+)', response.headers.get('Content-Range',''))
                assert match, 'Missing precise Content-Range'
                start, end, total = map(int, match.groups())
                assert 0 <= start <= end < total and end-start+1 <= limit
                data = response.read(limit+1)
                receipt['body_bytes'] += len(data)
                assert len(data) == end-start+1 <= limit, 'Unexpected response size'
                item.update(ended_utc=now(), bytes=len(data), sha256=hashlib.sha256(data).hexdigest())
                return data, start, total
        tail, tail_start, total = fetch('bytes=-65557',65557)
        (BASE / 'archive_tail_metadata.bin').write_bytes(tail)
        at = tail.rfind(b'PK\x05\x06')
        assert at >= 0, 'No ordinary EOCD; no expanded acquisition'
        sig, disk, cd_disk, disk_entries, count, size, offset, comment = struct.unpack_from('<4s4H2IH',tail,at)
        assert disk == cd_disk == 0 and disk_entries == count and count < 65535
        assert at+22+comment == len(tail), 'EOCD boundary mismatch'
        assert size < MAX_BYTES-65557 and offset+size == tail_start+at
        if offset >= tail_start:
            central = tail[offset-tail_start:offset-tail_start+size]
        else:
            central, start2, total2 = fetch(f'bytes={offset}-{offset+size-1}',size)
            assert start2 == offset and total2 == total
            assert receipt['requests'][0]['headers']['ETag'] == receipt['requests'][1]['headers']['ETag']
            assert receipt['requests'][0]['headers']['Last-Modified'] == receipt['requests'][1]['headers']['Last-Modified']
        entries=[];pos=0
        while pos < len(central):
            assert central[pos:pos+4] == b'PK\x01\x02'
            v=struct.unpack_from('<4s6H3I5H2I',central,pos)
            flags, method, crc, compressed, uncompressed = v[3],v[4],v[7],v[8],v[9]
            nlen, xlen, clen = v[10:13]
            name=central[pos+46:pos+46+nlen].decode('utf-8' if flags & 0x800 else 'cp437')
            entries.append(dict(name=name,compressed_bytes=compressed,uncompressed_bytes=uncompressed,
                                compression_method=method,crc32=crc,local_header_offset=v[16]))
            pos += 46+nlen+xlen+clen
        assert pos == len(central) and len(entries) == count
        (BASE / 'central_directory_metadata.bin').write_bytes(central)
        save(BASE / 'member_inventory.json',dict(entries=entries))
        candidates=[e for e in entries if re.search(r'(?i)(readme|license|copying|calib|intrinsic)',e['name'])]
        receipt.update(status='PASS',archive_total_bytes=total,central_directory_offset=offset,
                       central_directory_bytes=size,member_count=count,metadata_name_candidates=candidates,
                       limitations='Range bytes have hashes and matching server identity; full archive SHA and member data not verified. A directory may lack a standalone license; no license is inferred.')
    except Exception as exc:
        receipt.update(status='FAIL',exception=repr(exc),traceback=traceback.format_exc())
    finally:
        receipt.update(ended_utc=now(),source_unchanged=Path(__file__).read_bytes()==source)
        save(out,receipt)
    print(json.dumps({k:v for k,v in receipt.items() if k not in ['requests','traceback']},ensure_ascii=False))

if __name__ == '__main__':
    main()
