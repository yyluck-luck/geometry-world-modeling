#!/usr/bin/env python3
"""One request; project only five metadata fields. Never execute ZIP contents."""
from pathlib import Path, PurePosixPath
import argparse
import datetime as dt
import hashlib
import io
import json
import math
import os
import re
import stat
import subprocess
import zipfile

BASE = Path(__file__).resolve().parent
URL = 'https://storage.googleapis.com/dm-perception-test/zip_data/sample_annotations.zip'
MAX_BYTES = 4_999_999
FIELDS = {'split', 'video_id', 'frame_rate', 'num_frames', 'is_cup_game'}
STRING = re.compile(r'"(?:[^"\\\x00-\x1f]|\\["\\/bfnrt]|\\u[0-9a-fA-F]{4})*"')
NUMBER = re.compile(r'-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?')


def now():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def sha(data):
    return hashlib.sha256(data).hexdigest()


def save(name, data):
    with (BASE / name).open('x', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2, allow_nan=False)
        f.write('\n')


class Reject(Exception):
    """Only fixed machine codes; never include a source snippet."""


class Scanner:
    def __init__(self, raw):
        try:
            self.s = raw.decode('utf-8-sig')
        except UnicodeError:
            raise Reject('INVALID_UTF8') from None
        self.i = 0

    def ws(self):
        while self.i < len(self.s) and self.s[self.i] in ' \t\r\n':
            self.i += 1

    def peek(self):
        self.ws()
        if self.i == len(self.s):
            raise Reject('UNEXPECTED_END')
        return self.s[self.i]

    def eat(self, c):
        if self.peek() != c:
            raise Reject('JSON_STRUCTURE')
        self.i += 1

    def string(self, decode=False):
        self.ws()
        start = self.i
        m = STRING.match(self.s, self.i)
        if m is None:
            raise Reject('INVALID_STRING')
        self.i = m.end()
        # Decode keys and whitelisted scalars only. Skipped strings stay opaque.
        return json.loads(self.s[start:self.i]) if decode else None

    def value(self, keep=False, depth=0):
        if depth > 64:
            raise Reject('JSON_DEPTH_LIMIT')
        c = self.peek()
        if c in '{[':
            if keep:
                raise Reject('METADATA_NONSCALAR')
            closer = '}' if c == '{' else ']'
            self.i += 1
            seen = set()
            if self.peek() != closer:
                while True:
                    if c == '{':
                        key = self.string(True)
                        if key in seen:
                            raise Reject('DUPLICATE_NESTED_KEY')
                        seen.add(key)
                        self.eat(':')
                    self.value(False, depth + 1)
                    if self.peek() != ',':
                        break
                    self.i += 1
            self.eat(closer)
            return None
        if c == '"':
            return self.string(keep)
        start = self.i
        for literal in ('true', 'false', 'null'):
            if self.s.startswith(literal, self.i):
                self.i += len(literal)
                return json.loads(literal) if keep else None
        m = NUMBER.match(self.s, self.i)
        if m is None:
            raise Reject('INVALID_SCALAR')
        self.i = m.end()
        return json.loads(self.s[start:self.i]) if keep else None

    def metadata(self):
        self.eat('{')
        result = {}
        seen = set()
        if self.peek() != '}':
            while True:
                key = self.string(True)
                if key in seen:
                    raise Reject('DUPLICATE_METADATA_KEY')
                seen.add(key)
                self.eat(':')
                if key in FIELDS:
                    value = self.value(True, 2)
                    if key == 'split' and (type(value) is not str or value not in {'train', 'valid', 'test'}):
                        raise Reject('METADATA_SPLIT_SCHEMA')
                    if key == 'video_id' and (type(value) is not str or re.fullmatch(r'video_[0-9]+', value) is None):
                        raise Reject('METADATA_VIDEO_ID_SCHEMA')
                    if key == 'frame_rate' and (type(value) not in (int, float) or not math.isfinite(value) or value <= 0):
                        raise Reject('METADATA_FRAME_RATE_SCHEMA')
                    if key == 'num_frames' and (type(value) is not int or value <= 0):
                        raise Reject('METADATA_FRAME_COUNT_SCHEMA')
                    if key == 'is_cup_game' and not (type(value) is bool or (type(value) is int and value in (0, 1))):
                        raise Reject('METADATA_CUP_FLAG_SCHEMA')
                    result[key] = value
                else:
                    self.value(False, 2)
                if self.peek() != ',':
                    break
                self.i += 1
        self.eat('}')
        return result

    def record(self):
        if self.peek() != '{':
            self.value(False, 1)
            return None
        self.eat('{')
        result = None
        seen_metadata = False
        seen = set()
        if self.peek() != '}':
            while True:
                key = self.string(True)
                if key in seen:
                    raise Reject('DUPLICATE_RECORD_KEY')
                seen.add(key)
                self.eat(':')
                if key == 'metadata':
                    if seen_metadata:
                        raise Reject('DUPLICATE_METADATA')
                    seen_metadata = True
                    result = self.metadata()
                else:
                    self.value(False, 1)
                if self.peek() != ',':
                    break
                self.i += 1
        self.eat('}')
        return result

    def project(self):
        c = self.peek()
        top_type = {'{': 'object', '[': 'array', '"': 'string'}.get(c, 'scalar')
        rows, count = [], 0
        if c == '{':
            self.eat('{')
            seen = set()
            if self.peek() != '}':
                while True:
                    key = self.string(True)
                    if key in seen:
                        raise Reject('DUPLICATE_TOP_KEY')
                    seen.add(key)
                    self.eat(':')
                    row = self.record()
                    count += 1
                    if row is not None:
                        rows.append(row)
                    if self.peek() != ',':
                        break
                    self.i += 1
            self.eat('}')
        elif c == '[':
            self.eat('[')
            if self.peek() != ']':
                while True:
                    self.value(False, 1)
                    count += 1
                    if self.peek() != ',':
                        break
                    self.i += 1
            self.eat(']')
        else:
            self.value(False)
        self.ws()
        if self.i != len(self.s):
            raise Reject('TRAILING_CONTENT')
        types = {k: {} for k in sorted(FIELDS)}
        present = {k: 0 for k in sorted(FIELDS)}
        for row in rows:
            if set(row) - FIELDS:
                raise Reject('OUTPUT_ALLOWLIST')
            for key, value in row.items():
                typ = type(value).__name__
                types[key][typ] = types[key].get(typ, 0) + 1
                present[key] += 1
        return {'top_level_type': top_type, 'top_level_entry_count': count,
                'metadata_record_count': len(rows), 'field_presence': present,
                'field_types': types, 'metadata': rows}


def selftest():
    allowed = {'split': 'train', 'video_id': 'video_1', 'frame_rate': 30,
               'num_frames': 150, 'is_cup_game': True}
    fixture = {'video_1': {'metadata': {**allowed, 'forbidden': 'OPAQUE_MARKER'},
                         'mc_question': [{'question': 'OPAQUE_MARKER',
                                          'answers': ['OPAQUE_MARKER']}],
                         'future': {'boxes': [[9, 8, 7, 6]]}}}
    result = Scanner(json.dumps(fixture).encode()).project()
    assert result['metadata'] == [allowed]
    assert 'OPAQUE_MARKER' not in json.dumps(result)
    assert 'boxes' not in json.dumps(result)
    invalid_inputs = [b'{"v":{"metadata":{},"metadata":{}}}',
                    b'{"v":{"metadata":{"video_id":{}}}}', b'{"v":NaN}',
                    b'{"v":[]} trailing', b'{"v":{"metadata":{"split":"train","split":"test"}}}',
                    b'{"v":{"skip":{"x":1,"x":2}}}',
                    b'{"v":{},"\\u0076":{}}',
                    b'{"v":{"skip":"bad\\x20"}}',
                    b'{"v":{"metadata":{"frame_rate":1e999}}}',
                    b'{"v":{"metadata":{"video_id":"OPAQUE_MARKER"}}}',
                    b'{"v":{"metadata":{"num_frames":true}}}',
                    b'{"v":{"metadata":{"is_cup_game":"OPAQUE_MARKER"}}}',
                    b'{"v":{"metadata":{"split":"OPAQUE_MARKER"}}}',
                    b'{"v":' + b'[' * 70 + b'0' + b']' * 70 + b'}']
    for invalid in invalid_inputs:
        try:
            Scanner(invalid).project()
        except Reject as e:
            assert 'OPAQUE_MARKER' not in str(e)
            assert re.fullmatch(r'[A-Z_]+', str(e))
        else:
            raise AssertionError('Expected rejection')
    assert Scanner(b'[1,{"x":"hidden"}]').project()['metadata'] == []
    # Braces, escapes and Unicode in skipped strings cannot change the path.
    fixture['video_1']['mc_question'][0]['question'] = '"}]}\\\n\t中文😀'
    fixture['video_1']['skip_array'] = [True, None, -3.5e20, ['"', {'nested': '隐蔽'}]]
    escaped = json.dumps(fixture, ensure_ascii=True).encode()
    assert Scanner(escaped).project()['metadata'] == [allowed]
    escaped_key = escaped.replace(b'"metadata"', b'"\\u006detadata"')
    assert Scanner(escaped_key).project()['metadata'] == [allowed]
    assert Scanner(b'{"v":{"x":[{"metadata":{"video_id":"video_9"}}]}}').project()['metadata'] == []
    actual_flag = Scanner(b'{"v":{"metadata":{"is_cup_game":1}}}').project()['metadata'][0]['is_cup_game']
    assert type(actual_flag) is int  # Do not silently normalize a schema variation.
    return {'status': 'PASS', 'scope': 'synthetic projection checks only',
            'network_calls': 0, 'real_data_read': False,
            'rejection_cases': len(invalid_inputs),
            'coverage': ['allowlist', 'escaped strings', 'Unicode and escaped keys',
                         'nested arrays and skipped branches', 'duplicate keys',
                         'depth limits', 'invalid scalar and metadata types',
                         'fixed error codes without payload']}


def run():
    os.umask(0o077)
    script = Path(__file__).read_bytes()
    contract = (BASE / 'EXECUTION_CONTRACT.md').read_bytes()
    version = subprocess.run(['/usr/bin/curl', '--disable', '--version'], capture_output=True,
                             check=True, text=True).stdout.splitlines()[0]
    m = re.match(r'curl (\d+)\.(\d+)\.(\d+)', version)
    if not m or tuple(map(int, m.groups())) < (8, 4, 0):
        raise Reject('CURL_VERSION_TOO_OLD')
    save('RUN_STARTED.json', {'started_utc': now(), 'url': URL,
                             'contract_sha256': sha(contract),
                             'script_sha256': sha(script), 'curl_version': version,
                             'max_bytes': MAX_BYTES, 'attempt_limit': 1})
    body = BASE / 'sample_annotations.raw.part'
    args = ['/usr/bin/curl', '--disable', '--silent', '--show-error', '--fail', '--retry', '0',
            '--proto', '=https', '--connect-timeout', '10', '--max-time', '35',
            '--max-filesize', str(MAX_BYTES), '--dump-header', str(BASE / 'headers.txt'),
            '--output', str(body), '--write-out',
            'http_status=%{http_code}\nsize_download=%{size_download}\nhttp_version=%{http_version}\n', URL]
    receipt = {'request_started_utc': now(), 'argv': args,
               'status': 'FAILED', 'answer_values_exposed': False,
               'raw_download_may_contain_answer_bytes': True,
               'independent_blind_evaluation_preservation_established': False}
    try:
        p = subprocess.run(args, capture_output=True, timeout=45)
        (BASE / 'curl_stderr.txt').write_bytes(p.stderr)
        receipt['returncode'] = p.returncode
        metrics = p.stdout.decode('ascii', errors='replace')
        receipt['curl_metrics'] = metrics
        receipt['request_finished_utc'] = now()
        if body.exists():
            receipt['raw_bytes'] = body.stat().st_size
            receipt['raw_sha256'] = sha(body.read_bytes())
        if p.returncode != 0:
            raise Reject('CURL_FAILED')
        if 'http_status=200\n' not in metrics:
            raise Reject('HTTP_NOT_200')
        if not body.exists() or body.stat().st_size > MAX_BYTES:
            raise Reject('BODY_SIZE_LIMIT')
        archive = BASE / 'sample_annotations.zip'
        body.rename(archive)
        projections = []
        manifest = []
        with zipfile.ZipFile(archive) as z:
            members = z.infolist()
            if sum(x.file_size for x in members) > 100_000_000:
                raise Reject('ARCHIVE_TOTAL_SIZE')
            for info in members:
                path = PurePosixPath(info.filename)
                mode = info.external_attr >> 16
                if path.is_absolute() or '..' in path.parts or '\\' in info.filename:
                    raise Reject('ARCHIVE_PATH')
                if stat.S_ISLNK(mode) or info.flag_bits & 1:
                    raise Reject('ARCHIVE_SPECIAL_MEMBER')
                if info.file_size > 80_000_000:
                    raise Reject('ARCHIVE_MEMBER_SIZE')
                if info.is_dir():
                    continue
                if path.suffix.lower() != '.json':
                    raise Reject('ARCHIVE_NON_JSON')
                manifest.append({'name': info.filename, 'bytes': info.file_size,
                                 'compressed_bytes': info.compress_size})
            save('ARCHIVE_MANIFEST.json', manifest)
            for entry in manifest:
                raw = z.read(entry['name'])
                projection = Scanner(raw).project()
                projection['archive_member'] = entry['name']
                projections.append(projection)
        # Whole projection is validated before publication; raw contents never print.
        json.dumps(projections, allow_nan=False)
        save('METADATA_PROJECTION.json', projections)
        receipt['projected_files'] = len(projections)
        receipt['metadata_record_count'] = sum(x['metadata_record_count'] for x in projections)
        receipt['status'] = ('DOWNLOADED_AND_PROJECTED' if receipt['metadata_record_count']
                             else 'DOWNLOADED_NO_COMPATIBLE_METADATA')
        receipt['projection_sha256'] = sha((BASE / 'METADATA_PROJECTION.json').read_bytes())
    except subprocess.TimeoutExpired:
        receipt['error_code'] = 'OUTER_TIMEOUT'
    except Reject as e:
        receipt['error_code'] = str(e)
    except Exception as e:
        # Do not serialize exception text: parser/library messages may contain payload.
        receipt['error_code'] = 'UNEXPECTED_' + type(e).__name__
    finally:
        receipt.setdefault('request_finished_utc', now())
        receipt['completed_utc'] = now()
        if body.exists() and 'raw_sha256' not in receipt:
            receipt['raw_bytes'] = body.stat().st_size
            receipt['raw_sha256'] = sha(body.read_bytes())
        save('RUN_RECEIPT.json', receipt)
        print(json.dumps({'status': receipt['status'],
                          'error_code': receipt.get('error_code'),
                          'metadata_record_count': receipt.get('metadata_record_count', 0)}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--selftest', action='store_true')
    parser.add_argument('--execute', action='store_true')
    opt = parser.parse_args()
    if opt.selftest and not opt.execute:
        print(json.dumps(selftest()))
    elif opt.execute and not opt.selftest:
        run()
    else:
        raise SystemExit('Choose exactly one mode')
