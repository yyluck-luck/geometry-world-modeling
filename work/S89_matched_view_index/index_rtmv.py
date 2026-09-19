"""Continue a verified tar prefix with bounded header requests only."""
from pathlib import Path, PurePosixPath
from datetime import datetime, timezone
import hashlib
import json
import re
import subprocess
import tarfile
import time

HERE = Path(__file__).resolve().parent
PREV = HERE.parent / 'S88_independent_geometry_data'


def sha(b):
    return hashlib.sha256(b).hexdigest()


def utc():
    return datetime.now(timezone.utc).isoformat()


def write(p, obj):
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n')


def scrub(s):
    return re.sub(r'(https?://[^\s?]+)\?[^\s]+', r'\1?[REDACTED_QUERY]', s)


def info(raw, offset):
    item = tarfile.TarInfo.frombuf(raw, encoding='utf-8', errors='strict')
    assert item.size >= 0
    assert item.type in (tarfile.REGTYPE, tarfile.AREGTYPE, tarfile.DIRTYPE), 'Unsupported tar extension/type'
    assert not item.isdir() or item.size == 0, 'Nonempty directory unsupported'
    path = PurePosixPath(item.name)
    assert not path.is_absolute() and '..' not in path.parts and path.parts, 'Unsafe or empty member name'
    return dict(header_offset=offset, content_offset=offset + 512, name=item.name,
                normalized_name=str(path), size=item.size, type=item.type.decode('ascii'),
                is_regular=item.isfile(), is_directory=item.isdir(), header_sha256=sha(raw))


def main():
    plan = json.loads((HERE / 'INDEX_PLAN.json').read_text())
    out = HERE / 'index_01'
    out.mkdir(exist_ok=False)
    start = time.monotonic()
    receipt = dict(started_utc=utc(), code_sha256=sha(Path(__file__).read_bytes()),
                   plan_sha256=sha((HERE / 'INDEX_PLAN.json').read_bytes()),
                   status='RUNNING', requests=[], new_members=[], previous_members=[],
                   image_or_depth_payloads_requested=0, json_payloads_requested=0,
                   full_archive_downloaded=False, full_archive_hash_verified=False,
                   new_model_runs=0, all_scene_members_enumerated=False)
    size = plan['archive_bytes']

    def request(offset):
        remaining = plan['wall_seconds'] - (time.monotonic() - start)
        assert remaining > 0, 'Cooperative wall budget exceeded'
        assert len(receipt['requests']) < plan['max_new_headers'], 'Request budget exceeded'
        assert offset % 512 == 0 and 0 <= offset <= size - 512
        body = out / f"{len(receipt['requests']):03d}_header.bin"
        began, t = utc(), time.monotonic()
        result = subprocess.run([
            '/usr/bin/curl', '--connect-timeout', '10', '--max-time', str(max(0.01, min(25, remaining))),
            '--max-filesize', str(plan['transport_body_cap']), '--retry', '0', '--max-redirs', '5',
            '-L', '-sS', '-H', f'Range: bytes={offset}-{offset+511}', '-D', '-',
            '-o', str(body), '-w', '\nS89_HTTP_CODE:%{http_code}\n', plan['url']
        ], capture_output=True, text=True)
        raw = body.read_bytes() if body.exists() else b''
        ranges = re.findall(r'(?im)^content-range:\s*bytes\s+(\d+)-(\d+)/(\d+)', result.stdout)
        statuses = re.findall(r'S89_HTTP_CODE:(\d+)', result.stdout)
        headers = [scrub(line) for line in result.stdout.splitlines() if line.lower().startswith(
            ('http/', 'content-range:', 'content-length:', 'etag:', 'last-modified:',
             'content-type:', 'accept-ranges:', 'location:', 's89_http_code:'))]
        entry = dict(started_utc=began, ended_utc=utc(), seconds=time.monotonic()-t,
                     offset=offset, length=512, returncode=result.returncode,
                     http=statuses[-1] if statuses else None, headers=headers,
                     stderr=scrub(result.stderr), body=body.name, body_bytes=len(raw), sha256=sha(raw))
        receipt['requests'].append(entry)
        write(out / 'RECEIPT.json', receipt)
        assert result.returncode == 0, f'Transport rc{result.returncode}'
        assert entry['http'] == '206', 'Expected exact 206 response'
        assert ranges and list(map(int, ranges[-1])) == [offset, offset+511, size], 'Range mismatch'
        assert len(raw) == 512, 'Wrong header length'
        return raw

    try:
        for binding in plan['source_bindings']:
            assert sha((PREV / binding['relative_path']).read_bytes()) == binding['sha256'], 'Previous evidence changed'
        prior = json.loads((PREV / 'rtmv_range_02/RECEIPT.json').read_text())
        assert prior['status'] == 'FIRST_JSON_CAMERA_FIELDS_OBTAINED'
        assert prior['url'] == plan['url'] and prior['expected_size'] == size
        for old in prior['members']:
            request_record = next(x for x in prior['requests'] if x['offset'] == old['header_offset'] and x['kind'] == 'header')
            raw = (PREV / 'rtmv_range_02' / request_record['body']).read_bytes()
            assert len(raw) == 512 and sha(raw) == old['header_sha256'] == request_record['sha256']
            decoded = info(raw, old['header_offset'])
            assert all(decoded[k] == old[k] for k in old), 'Previous header decoded differently'
            receipt['previous_members'].append(decoded)
        last = receipt['previous_members'][-1]
        assert last['name'] == '00000/00108.json' and last['size'] == 189899
        offset = last['header_offset'] + 512 + ((last['size']+511)//512)*512
        assert offset == plan['start_offset'] == 11460608
        receipt['start_offset'] = offset
        names = {x['normalized_name'] for x in receipt['previous_members']}
        for _ in range(plan['max_new_headers']):
            raw = request(offset)
            if raw == b'\0'*512:
                receipt.update(status='FIRST_ZERO_TAR_BLOCK', next_header_offset=offset)
                break
            item = info(raw, offset)
            next_offset = offset + 512 + ((item['size']+511)//512)*512
            if next_offset > size:
                receipt['rejected_member'] = item
            assert next_offset <= size, 'Member extends outside archive'
            receipt['new_members'].append(item)
            receipt['next_header_offset'] = next_offset
            if PurePosixPath(item['normalized_name']).parts[0] != plan['scene']:
                receipt.update(status='SCENE_BOUNDARY', boundary_member=item)
                break
            assert item['normalized_name'] not in names, 'Duplicate member name conflict retained; stop'
            names.add(item['normalized_name'])
            offset = next_offset
            if offset == size:
                receipt['status'] = 'OBJECT_END_NO_TERMINATOR'
                break
        else:
            receipt['status'] = 'HEADER_BUDGET_STOP'
    except Exception as exc:
        receipt.update(status='STOPPED', error_type=type(exc).__name__, error=scrub(str(exc)))
    # Preserve all repeated entries in lists; ambiguities do not count as complete.
    views = {}
    for item in receipt['previous_members'] + receipt['new_members']:
        match = re.fullmatch(re.escape(plan['scene']) + r'/(\d{5})\.(json|depth\.exr|seg\.exr|exr)', item['normalized_name'])
        if match and item['is_regular']:
            view, suffix = match.groups()
            views.setdefault(view, {}).setdefault(suffix, []).append(item)
    complete = sorted(view for view, types in views.items()
                      if all(len(types.get(suffix, [])) == 1 for suffix in ('json', 'exr', 'depth.exr')))
    matched = dict(scene=plan['scene'], scope='verified scanned archive prefix, not whole scene',
                   selection_rule='smallest complete five-digit ID in scanned prefix for format development only',
                   complete_view_ids=complete, selected_development_view=complete[0] if complete else None,
                   all_views=views, body_contents_verified=False, static_multiview_verified=False)
    write(out / 'MATCHED_VIEWS.json', matched)
    receipt.update(completed_utc=utc(), elapsed_seconds=time.monotonic()-start,
                   downloaded_body_bytes=sum(x['body_bytes'] for x in receipt['requests']),
                   matched_manifest_sha256=sha((out / 'MATCHED_VIEWS.json').read_bytes()),
                   complete_view_ids=complete, selected_development_view=matched['selected_development_view'])
    write(out / 'RECEIPT.json', receipt)
    print(json.dumps({k:v for k,v in receipt.items() if k not in ('requests','previous_members','new_members')}, ensure_ascii=False))


if __name__ == '__main__':
    main()
