"""Independent saved-header audit of the completed S89 index_01 attempt."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import time

HERE = Path(__file__).resolve().parent
CURRENT = HERE.parent
PREVIOUS = CURRENT.parent / 'S88_independent_geometry_data'
OUT = HERE / 'INDEX_ACTUAL_REVIEW.json'
SOURCE_SHA = 'fd568ca4aced01e663bad129d71e16ae4eee7d9249bd5ec99faaa281871e8997'
PLAN_SHA = 'd71131607884af528db294a94d82cd4d0c5255f33f11a3496a2a2b5d030f5917'
PRIOR_SHA = '4582349f3e2283f4c9cc893d4dbc0ad6138d05c72a1b1232306b2da18eda3867'


def sha(b):
    return hashlib.sha256(b).hexdigest()


def utc():
    return datetime.now(timezone.utc).isoformat()


def octal(b):
    assert not b[0] & 128, 'No base256 integers in this bounded independent reader'
    return int(b.rstrip(b'\0 ').lstrip(b' '), 8)


def decode(b, offset):
    assert len(b) == 512
    stored = octal(b[148:156])
    unsigned = sum(b[:148]) + 256 + sum(b[156:])
    signed = sum(v if v < 128 else v-256 for v in b[:148]+b[156:]) + 256
    assert stored in (unsigned, signed), 'Tar checksum mismatch'
    assert b[257:263] in (b'ustar\0', b'ustar ')
    typ, size = b[156:157], octal(b[124:136])
    assert typ in (b'0', b'\0', b'5') and size >= 0
    name = b[:100].split(b'\0', 1)[0].decode('utf-8')
    prefix = b[345:500].split(b'\0', 1)[0].decode('utf-8')
    if prefix:
        name = prefix + '/' + name
    if typ == b'5':
        assert size == 0
        name = name.rstrip('/')
    parts = name.split('/')
    assert name and not name.startswith('/') and '..' not in parts
    normal = '/'.join(p for p in parts if p not in ('', '.'))
    return dict(header_offset=offset, content_offset=offset+512, name=name,
                normalized_name=normal, size=size, type=typ.decode('ascii'),
                is_regular=typ in (b'0', b'\0'), is_directory=typ == b'5', header_sha256=sha(b)), stored


def main():
    assert not OUT.exists(), 'Create only; retain any failed review'
    result = dict(started_utc=utc(), status='RUNNING', source_sha256=sha(Path(__file__).read_bytes()),
                  scope='Different-author actual metadata/failure record audit; no tarfile or root implementation imported.',
                  checks=[], files=[], hand_decoded_headers=[])
    start = time.monotonic()

    def check(label, condition):
        result['checks'].append(dict(label=label, passed=bool(condition)))
        assert condition, label

    def read(p):
        b = p.read_bytes()
        result['files'].append(dict(path=str(p), bytes=len(b), sha256=sha(b)))
        return b

    try:
        receipt_bytes = read(CURRENT/'index_01/RECEIPT.json')
        rec = json.loads(receipt_bytes)
        check('final receipt gate', rec['status'] != 'RUNNING' and 'completed_utc' in rec)
        plan_bytes = read(CURRENT/'INDEX_PLAN.json')
        check('frozen plan identity', sha(plan_bytes) == PLAN_SHA == rec['plan_sha256'])
        plan = json.loads(plan_bytes)
        check('frozen actual source identity', sha(read(CURRENT/'index_rtmv.py')) == SOURCE_SHA == rec['code_sha256'])
        frozen = json.loads(read(CURRENT/'ROOT_INDEX_FREEZE.json'))
        check('root freeze source/plan', frozen['code_sha256'] == SOURCE_SHA and frozen['plan_sha256'] == PLAN_SHA)
        prior_bytes = read(PREVIOUS/'rtmv_range_02/RECEIPT.json')
        check('accepted prior identity', sha(prior_bytes) == PRIOR_SHA)
        prior = json.loads(prior_bytes)
        for bind in plan['source_bindings']:
            check('bound prior '+bind['relative_path'], sha(read(PREVIOUS/bind['relative_path'])) == bind['sha256'])
        old, offset = [], 0
        for index, item in enumerate(prior['members']):
            request = next(r for r in prior['requests'] if r['offset'] == item['header_offset'] and r['kind'] == 'header')
            b = read(PREVIOUS/'rtmv_range_02'/request['body'])
            check(f'old{index}: body identity', sha(b) == request['sha256'] == item['header_sha256'])
            check(f'old{index}: contiguous padded offset', item['header_offset'] == offset)
            parsed, checksum = decode(b, offset)
            check(f'old{index}: saved fields equal manual parse', all(parsed[k] == v for k,v in item.items()))
            old.append(parsed)
            result['hand_decoded_headers'].append(dict(**parsed, checksum=checksum))
            offset += 512 + ((parsed['size']+511)//512)*512
        check('all old7 preserved', len(old) == 7 and old == rec['previous_members'])
        check('resume offset', offset == plan['start_offset'] == rec['start_offset'] == 11460608)
        check('one failed request and no new header', rec['status'] == 'STOPPED' and len(rec['requests']) == 1 and rec['new_members'] == [])
        req = rec['requests'][0]
        check('exact failed header request', req['offset'] == offset and req['length'] == 512)
        check('failure is actual TLS transport', req['returncode'] == 35 and req['http'] == '302'
              and 'SSL_ERROR_SYSCALL' in req['stderr'] and 'SSL_connect' in req['stderr']
              and rec['error'] == 'Transport rc35')
        body = CURRENT/'index_01'/req['body']
        check('failed response filename confined', body.resolve().parent == (CURRENT/'index_01').resolve())
        b = read(body) if body.exists() else b''
        result['failed_response_body_exists'] = body.exists()
        check('actual no saved response body', len(b) == req['body_bytes'] == rec['downloaded_body_bytes'] == 0 and sha(b) == req['sha256'])
        check('only redirect response recorded', sum(x.lower().startswith('http/') for x in req['headers']) == 1
              and req['headers'][0].split()[1] == '302' and not any(x.lower().startswith('content-range:') for x in req['headers']))
        check('signed query redacted in saved header', all('?[REDACTED_QUERY]' in x for x in req['headers'] if x.lower().startswith('location:') and '?' in x))
        views = {}
        for item in old:  # Actual attempt had no new accepted header; do not invent one.
            parts = item['normalized_name'].split('/')
            if not item['is_regular'] or len(parts) != 2 or parts[0] != plan['scene']:
                continue
            leaf = parts[1]
            if len(leaf) <= 6 or not leaf[:5].isascii() or not leaf[:5].isdigit():
                continue
            suffix = leaf[5:]
            roles = {'.json':'json', '.exr':'exr', '.depth.exr':'depth.exr', '.seg.exr':'seg.exr'}
            if suffix in roles:
                views.setdefault(leaf[:5], {}).setdefault(roles[suffix], []).append(item)
        complete = sorted(k for k,v in views.items() if all(len(v.get(r, [])) == 1 for r in ('json','exr','depth.exr')))
        matched_bytes = read(CURRENT/'index_01/MATCHED_VIEWS.json')
        check('matched manifest identity', sha(matched_bytes) == rec['matched_manifest_sha256'])
        matched = json.loads(matched_bytes)
        expected = dict(scene=plan['scene'], scope='verified scanned archive prefix, not whole scene',
                        selection_rule='smallest complete five-digit ID in scanned prefix for format development only',
                        complete_view_ids=complete, selected_development_view=complete[0] if complete else None,
                        all_views=views, body_contents_verified=False, static_multiview_verified=False)
        check('full independently paired manifest exact', matched == expected)
        check('six partial views and no selected candidate', len(views) == 6 and complete == [] and rec['complete_view_ids'] == [] and rec['selected_development_view'] is None)
        check('budgets', len(rec['requests']) <= plan['max_new_headers'] == 256 and rec['downloaded_body_bytes'] <= plan['max_transport_body_bytes'] == 2097152 and rec['elapsed_seconds'] < plan['wall_seconds'] == 600)
        check('no scientific body requests or false completeness', rec['image_or_depth_payloads_requested'] == rec['json_payloads_requested'] == rec['new_model_runs'] == 0
              and rec['all_scene_members_enumerated'] is False and rec['full_archive_downloaded'] is False and rec['full_archive_hash_verified'] is False)
        check('no scene/budget stop mislabel', 'boundary_member' not in rec and 'rejected_member' not in rec and 'next_header_offset' not in rec)
        result.update(status='PASS_FAILED_ATTEMPT_RECORD_ONLY', attempt_status=rec['status'],
                      actual_summary=dict(logical_new_requests=1, accepted_new_headers=0, received_new_body_bytes=0,
                                          old_verified_members=7, partial_view_ids=sorted(views), complete_view_ids=[], selected_development_view=None,
                                          attempted_resume_offset=offset, attempt_elapsed_seconds=rec['elapsed_seconds'],
                                          timestamp_elapsed_seconds=(datetime.fromisoformat(rec['completed_utc'])-datetime.fromisoformat(rec['started_utc'])).total_seconds()),
                      conclusion='The saved TLS failure, original prefix reconstruction and empty complete-triplet selection are consistent. No new member or scene boundary was reached. This does not establish absence of matching views in RTMV. No new image/depth/JSON body was obtained.',
                      limitations='Runtime success, scene boundary and full256-header paths remain unexercised here; no independent network repeat. This is failure/provenance arithmetic, not a scientific effect or data qualification result.',
                      own_actions=dict(network_requests=0,model_runs=0,image_depth_decodes=0,new_json_body_reads=0,tarfile_imports=0,indexer_imports=0))
    except Exception as exc:
        result.update(status='FAILED_REVIEW_PRESERVED', error_type=type(exc).__name__, error=str(exc))
    result.update(completed_utc=utc(), elapsed_seconds=time.monotonic()-start)
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('checks','files','hand_decoded_headers')}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
