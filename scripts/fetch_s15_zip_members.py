#!/usr/bin/env python3
"""Fetch only frozen public ZIP members, with precise range and ZIP identity checks.

This unpacks ZIP compression but does not decode any image format.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path, PurePosixPath
import struct
import traceback
import urllib.request
import zlib


def now():
    return datetime.now(timezone.utc).isoformat()


def sha(data):
    return hashlib.sha256(data).hexdigest()


def save(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def require(value, message):
    if not value:
        raise ValueError(message)


def parse_header(data, entry):
    require(len(data) == 30, 'local header size')
    sig, version, flags, method, mt, md, crc, compressed, uncompressed, nlen, xlen = struct.unpack('<4s5H3I2H', data)
    require(sig == b'PK\x03\x04', 'local signature')
    require(not flags & (1 | 64 | 8192), 'encrypted or masked ZIP unsupported')
    require(method in (0, 8) and method == entry['compression_method'], 'compression method')
    require(0 < nlen <= 1024 and xlen <= 65535, 'name/extra bounds')
    if not flags & 8:
        require((crc, compressed, uncompressed) == (entry['crc32'], entry['compressed_bytes'], entry['uncompressed_bytes']), 'local/central metadata mismatch')
    else:
        require(crc in (0, entry['crc32']) and compressed in (0, entry['compressed_bytes']) and uncompressed in (0, entry['uncompressed_bytes']), 'descriptor local metadata mismatch')
    return flags, nlen, xlen


def unpack_member(header, rest, entry, max_uncompressed):
    flags, nlen, xlen = parse_header(header, entry)
    require(len(rest) == nlen + xlen + entry['compressed_bytes'], 'member range size')
    name = rest[:nlen].decode('utf-8' if flags & 0x800 else 'cp437')
    require(name == entry['name'], 'member name mismatch')
    path = PurePosixPath(name)
    require(not path.is_absolute() and '..' not in path.parts and '\\' not in name and not name.endswith('/'), 'unsafe member path')
    require(0 <= entry['uncompressed_bytes'] <= max_uncompressed, 'uncompressed budget')
    compressed = rest[nlen+xlen:]
    if entry['compression_method'] == 8:
        decoder = zlib.decompressobj(-15)
        data = decoder.decompress(compressed, entry['uncompressed_bytes'] + 1)
        require(decoder.eof and not decoder.unused_data and not decoder.unconsumed_tail, 'deflate termination/budget')
    else:
        data = compressed
    require(len(data) == entry['uncompressed_bytes'], 'uncompressed size')
    require(zlib.crc32(data) & 0xffffffff == entry['crc32'], 'CRC32 mismatch')
    return data


def execute(contract_path, expected_sha, output):
    output = Path(output)
    require(not output.exists(), 'fresh output required; preserve earlier attempts')
    output.mkdir(parents=True)
    receipt = dict(schema='s15-range-member-receipt-v1', started_utc=now(), status='RUNNING', requests=[], members=[], body_bytes=0, image_array_decodes=0, model_calls=0)
    try:
        raw = Path(contract_path).read_bytes()
        require(sha(raw) == expected_sha, 'contract SHA mismatch')
        c = json.loads(raw)
        require(c['schema'] == 's15-range-member-contract-v1', 'contract schema')
        require(sha(Path(__file__).read_bytes()) == c['fetcher_sha256'], 'fetcher SHA mismatch')
        inv_raw = Path(c['inventory_path']).read_bytes()
        require(sha(inv_raw) == c['inventory_sha256'], 'inventory SHA mismatch')
        inventory = {e['name']:e for e in json.loads(inv_raw)['entries']}
        require(len(c['members']) == len(set(c['members'])) > 0, 'empty or duplicate members')
        require(all(n in inventory for n in c['members']), 'unknown member')
        require(c['max_requests'] == 2 * len(c['members']), 'two requests per member budget')
        receipt.update(contract_sha256=expected_sha, contract_path=str(Path(contract_path).resolve()), url=c['url'], archive_total_bytes=c['archive_total_bytes'])
        save(output/'receipt.json', receipt)

        def fetch(start, length):
            require(len(receipt['requests']) < c['max_requests'], 'request budget')
            require(length > 0 and receipt['body_bytes'] + length + 1 <= c['max_response_bytes'], 'network byte budget including overlength sentinel')
            end = start + length - 1
            require(0 <= start <= end < c['central_directory_offset'], 'not a local member range')
            item = dict(started_utc=now(), requested_range=f'bytes={start}-{end}')
            receipt['requests'].append(item)
            req = urllib.request.Request(c['url'], headers={'Range':item['requested_range'], 'Accept-Encoding':'identity', 'If-Match':c['etag'], 'If-Range':c['etag'], 'User-Agent':'ResearchBoundedMemberAccess/1.0'})
            with urllib.request.urlopen(req, timeout=25) as response:
                item.update(status=response.status, final_url=response.url, headers={k:response.headers.get(k) for k in ('Content-Range','Content-Length','Content-Encoding','ETag','Last-Modified')})
                require(response.status == 206 and response.url == c['url'], 'range unsupported or redirect; body not read')
                require(response.headers.get('Content-Range') == f"bytes {start}-{end}/{c['archive_total_bytes']}", 'Content-Range mismatch')
                require(response.headers.get('ETag') == c['etag'] and response.headers.get('Last-Modified') == c['last_modified'], 'archive identity changed')
                require(response.headers.get('Content-Encoding') in (None,'identity'), 'encoded range')
                require(response.headers.get('Content-Length') in (None,str(length)), 'Content-Length mismatch')
                data = response.read(length + 1)
                receipt['body_bytes'] += len(data)
                item.update(ended_utc=now(), bytes=len(data), sha256=sha(data))
                require(len(data) == length, 'range response length mismatch')
            save(output/'receipt.json', receipt)
            return data

        for name in c['members']:
            entry = inventory[name]
            require(entry['uncompressed_bytes'] <= c['max_member_uncompressed_bytes'], 'declared uncompressed budget')
            header = fetch(entry['local_header_offset'],30)
            flags, nlen, xlen = parse_header(header,entry)
            rest = fetch(entry['local_header_offset']+30,nlen+xlen+entry['compressed_bytes'])
            data = unpack_member(header,rest,entry,c['max_member_uncompressed_bytes'])
            path = output/'members'/name
            path.parent.mkdir(parents=True,exist_ok=True)
            require(not path.exists(),'refuse overwrite')
            path.write_bytes(data)
            receipt['members'].append(dict(**entry,path=str(path.resolve()),bytes=len(data),sha256=sha(data),zip_crc32_verified=True))
            save(output/'receipt.json',receipt)
        receipt['status'] = 'PASS'
    except Exception as error:
        receipt.update(status='FAIL',error=repr(error),traceback=traceback.format_exc())
    finally:
        receipt['ended_utc'] = now()
        save(output/'receipt.json',receipt)
    print(json.dumps(dict(status=receipt['status'],members=len(receipt['members']),body_bytes=receipt['body_bytes'],receipt=str(output/'receipt.json'))))
    return 0 if receipt['status'] == 'PASS' else 1


if __name__ == '__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--contract',required=True);p.add_argument('--contract-sha256',required=True);p.add_argument('--output',required=True)
    a=p.parse_args()
    raise SystemExit(execute(a.contract,a.contract_sha256,a.output))
