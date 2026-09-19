#!/usr/bin/env python3
"""Frozen twenty-depth ZIP extraction over bounded persistent HTTPS ranges; no image decode."""
import argparse
import http.client
import json
from pathlib import Path
import socket
import ssl
import time
import traceback
from urllib.parse import urlsplit
from fetch_s15_zip_members import now, sha, save, require, parse_header, unpack_member

URL = 'https://www.ipb.uni-bonn.de/html/projects/rgbd_dynamic2019/rgbd_bonn_static_close_far.zip'
TRANSPORT_ERRORS = (ssl.SSLError, ConnectionError, TimeoutError, socket.gaierror,
                    http.client.RemoteDisconnected, http.client.IncompleteRead)


class RangeFetcher:
    def __init__(self, contract, output, receipt, connection_factory=http.client.HTTPSConnection,
                 clock=time.monotonic):
        self.c = contract; self.out = Path(output); self.r = receipt
        self.factory = connection_factory; self.clock = clock; self.started = clock()
        self.connection = None; self.connection_id = 0
        self.url = urlsplit(contract['url'])

    def remaining(self):
        return self.c['wall_seconds'] - (self.clock() - self.started)

    def close(self):
        if self.connection is not None:
            self.connection.close(); self.connection = None

    def snapshot(self):
        self.r['elapsed_seconds'] = self.clock() - self.started
        self.r['connection_objects_created'] = self.connection_id
        save(self.out/'receipt.json', self.r)

    def fetch(self, start, length, member, role):
        c = self.c; r = self.r
        end = start + length - 1
        require(length > 0 and 0 <= start <= end < c['central_directory_offset'], 'local member range bounds')
        for attempt in range(1, c['max_attempts_per_range'] + 1):
            require(self.remaining() > 0, 'total wall budget exhausted')
            require(len(r['requests']) < c['max_request_attempts'], 'request attempt budget exhausted')
            require(r['body_bytes'] + length + 1 <= c['max_response_bytes'], 'response byte budget including sentinel')
            item = dict(started_utc=now(), member=member, role=role, range_attempt=attempt,
                requested_range=f'bytes={start}-{end}', request_attempt=len(r['requests'])+1,
                status='REQUEST_ATTEMPT', bytes=0)
            r['requests'].append(item); self.snapshot()
            response = None; body = bytearray()
            response_path = self.out/'responses'/f"request_{item['request_attempt']:03d}.bin"
            try:
                timeout = min(25., self.remaining())
                require(timeout > 0, 'total wall budget exhausted')
                if self.connection is None:
                    self.connection_id += 1
                    self.connection = self.factory(self.url.hostname, port=self.url.port or 443, timeout=timeout)
                self.connection.timeout = timeout
                if getattr(self.connection, 'sock', None) is not None:
                    self.connection.sock.settimeout(timeout)
                item['connection_object'] = self.connection_id
                self.connection.request('GET', self.url.path, headers={
                    'Range': item['requested_range'], 'Accept-Encoding': 'identity',
                    'If-Match': c['etag'], 'If-Range': c['etag'], 'Connection': 'keep-alive',
                    'User-Agent': 'BoundedResearchDepthMemberAccess/1.0'})
                response = self.connection.getresponse()
                item.update(http_status=response.status, final_url=c['url'], headers={
                    k: response.getheader(k) for k in ('Content-Range', 'Content-Length', 'Content-Encoding', 'ETag', 'Last-Modified')})
                require(response.status == 206, 'HTTP status must be 206; no redirect or full-body read')
                require(response.getheader('Content-Range') == f"bytes {start}-{end}/{c['archive_total_bytes']}", 'Content-Range mismatch')
                require(response.getheader('ETag') == c['etag'] and response.getheader('Last-Modified') == c['last_modified'], 'archive identity mismatch')
                require(response.getheader('Content-Encoding') in (None, 'identity'), 'encoded range rejected')
                require(response.getheader('Content-Length') in (None, str(length)), 'Content-Length mismatch')
                while len(body) < length + 1:
                    timeout = min(25., self.remaining())
                    require(timeout > 0, 'total wall budget exhausted during body')
                    if getattr(self.connection, 'sock', None) is not None:
                        self.connection.sock.settimeout(timeout)
                    try:
                        chunk = response.read(min(65536, length + 1 - len(body)))
                    except http.client.IncompleteRead as error:
                        body.extend(error.partial)
                        r['body_bytes'] += len(error.partial)
                        raise
                    body.extend(chunk); r['body_bytes'] += len(chunk)
                    require(r['body_bytes'] <= c['max_response_bytes'], 'response byte budget exceeded')
                    if not chunk:
                        break
                item.update(bytes=len(body), sha256=sha(body), ended_utc=now())
                response_path.parent.mkdir(parents=True, exist_ok=True)
                response_path.write_bytes(body)
                item['response_path'] = str(response_path.resolve())
                require(len(body) == length, 'response body length mismatch')
                require(self.remaining() > 0, 'total wall budget exhausted after body')
                item['status'] = 'PASS'; self.snapshot()
                return bytes(body)
            except TRANSPORT_ERRORS as error:
                item.update(status='TRANSPORT_FAILURE', ended_utc=now(), error=repr(error),
                    bytes=len(body), sha256=sha(body), retry_allowed=attempt < c['max_attempts_per_range'])
                response_path.parent.mkdir(parents=True, exist_ok=True)
                response_path.write_bytes(body); item['response_path'] = str(response_path.resolve())
                self.close(); self.snapshot()
                if attempt == c['max_attempts_per_range']:
                    raise
            except Exception as error:
                item.update(status='PROTOCOL_OR_BUDGET_FAILURE', ended_utc=now(), error=repr(error),
                    bytes=len(body), sha256=sha(body), retry_allowed=False)
                response_path.parent.mkdir(parents=True, exist_ok=True)
                response_path.write_bytes(body); item['response_path'] = str(response_path.resolve())
                self.close(); self.snapshot()
                raise
            finally:
                if response is not None:
                    response.close()
        raise RuntimeError('Unreachable retry exhaustion')


def validate_contract(c):
    require(c['schema'] == 's15c-depth-range-contract-v1' and c['url'] == URL, 'fixed contract schema/source')
    for key, value in [('max_request_attempts', 60), ('max_attempts_per_range', 3),
                       ('max_response_bytes', 10*1024**2), ('wall_seconds', 600),
                       ('max_member_uncompressed_bytes', 2*1024**2), ('image_array_decodes', 0)]:
        require(c[key] == value, 'contract budget: ' + key)
    require(len(c['members']) == len(set(c['members'])) == 20, 'exact twenty distinct members')
    require(all(n.startswith('rgbd_bonn_static_close_far/depth/') and n.endswith('.png') for n in c['members']), 'depth member domain')
    expected = dict(c['identities'])
    require(expected.get(str(Path(__file__).resolve())) == c['fetcher_sha256'], 'fetcher role binding')
    require(expected.get(str(Path(__file__).with_name('fetch_s15_zip_members.py').resolve())) == c['zip_parser_sha256'], 'parser role binding')
    for key in ['inventory', 'samples', 'protocol']:
        require(expected.get(c[key+'_path']) == c[key+'_sha256'], key + ' role binding')
    require(len(expected) == 5, 'only five frozen preparation inputs')
    for path, digest in expected.items():
        require(Path(path).is_absolute() and str(Path(path).resolve()) == path, 'canonical frozen input')
        require(sha(Path(path).read_bytes()) == digest, 'frozen input SHA: ' + path)
    samples = json.loads(Path(c['samples_path']).read_text())['samples'][:20]
    require([x['index'] for x in samples] == list(range(20)) and all(x['role'] == 'history' for x in samples), 'original twenty sample roles')
    require(c['members'] == [x['depth_member'] for x in samples], 'exact preselected matched depths')
    inventory = {e['name']: e for e in json.loads(Path(c['inventory_path']).read_text())['entries']}
    require(c['member_entries'] == [inventory[n] for n in c['members']], 'exact frozen central entries')
    for e in c['member_entries']:
        require(0 < e['uncompressed_bytes'] <= c['max_member_uncompressed_bytes'], 'declared member budget')
        require(e['compression_method'] in (0, 8), 'declared supported compression')
    return inventory


def execute(contract_path, expected_sha, output):
    output = Path(output); require(not output.exists(), 'fresh output required; preserve earlier attempts')
    output.mkdir(parents=True)
    r = dict(schema='s15c-depth-range-receipt-v1', started_utc=now(), status='RUNNING',
        requests=[], members=[], body_bytes=0, image_array_decodes=0, model_calls=0,
        transport='persistent HTTPSConnection objects; reconnect on transport failure only',
        completed_members_refetched=0)
    fetcher = None; started = time.monotonic()
    try:
        raw = Path(contract_path).read_bytes(); require(sha(raw) == expected_sha, 'contract SHA')
        c = json.loads(raw); inventory = validate_contract(c)
        r.update(contract_path=str(Path(contract_path).resolve()), contract_sha256=expected_sha,
            url=c['url'], archive_total_bytes=c['archive_total_bytes'], input_identities=c['identities'])
        (output/'frozen_contract.json').write_bytes(raw)
        save(output/'receipt.json', r)
        fetcher = RangeFetcher(c, output, r)
        fetcher.started = started
        for index, name in enumerate(c['members']):
            entry = inventory[name]
            header = fetcher.fetch(entry['local_header_offset'], 30, name, 'local_header')
            _, name_length, extra_length = parse_header(header, entry)
            rest = fetcher.fetch(entry['local_header_offset']+30,
                name_length+extra_length+entry['compressed_bytes'], name, 'name_extra_compressed_payload')
            data = unpack_member(header, rest, entry, c['max_member_uncompressed_bytes'])
            require(fetcher.remaining() > 0, 'total wall budget exhausted during ZIP unpacking')
            path = output/'members'/name; path.parent.mkdir(parents=True, exist_ok=True)
            require(not path.exists(), 'completed member must never be overwritten')
            path.write_bytes(data)
            r['members'].append(dict(**entry, index=index, path=str(path.resolve()), bytes=len(data),
                sha256=sha(data), zip_crc32_verified=True, completed_utc=now()))
            fetcher.snapshot()
        require(sha(Path(contract_path).read_bytes()) == expected_sha, 'post-download contract changed')
        for path, digest in c['identities'].items():
            require(sha(Path(path).read_bytes()) == digest, 'post-download frozen input changed: ' + path)
        require(fetcher.remaining() > 0, 'total wall budget exhausted during final identity gate')
        r.update(status='PASS', before_after_identity_pass=True)
    except Exception as error:
        r.update(status='FAIL', error=repr(error), traceback=traceback.format_exc())
    finally:
        if fetcher is not None:
            fetcher.close(); fetcher.snapshot()
        r.update(ended_utc=now(), elapsed_seconds=time.monotonic()-started)
        save(output/'receipt.json', r)
    print(json.dumps(dict(status=r['status'], members=len(r['members']), requests=len(r['requests']), body_bytes=r['body_bytes'], elapsed_seconds=r['elapsed_seconds'])))
    return int(r['status'] != 'PASS')


if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('--contract', required=True)
    p.add_argument('--contract-sha256', required=True); p.add_argument('--output', required=True)
    a = p.parse_args(); raise SystemExit(execute(a.contract, a.contract_sha256, a.output))
