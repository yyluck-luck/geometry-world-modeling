"""Read saved metadata only; independent byte offsets and scalar camera math."""
import hashlib
import json
import math
import time
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATA = HERE.parent / 'rtmv_range_02'
OUT = HERE / 'RANGE_ACTUAL_REVIEW.json'
EXPECTED_RECEIPT = '4582349f3e2283f4c9cc893d4dbc0ad6138d05c72a1b1232306b2da18eda3867'
EXPECTED_JSON = 'e51fd4f99d0fc45d4eb34d8dc448545e3e412c4a4e8621a8b55ffe9bdc953e76'
TOTAL = 12064450560
CAMERA_TOL = 1e-6  # Numerical comparison of stored FP32-scale fields, not a science threshold.


def utc():
    return datetime.now(timezone.utc).isoformat()


def sha(b):
    return hashlib.sha256(b).hexdigest()


def transpose(a):
    return [list(x) for x in zip(*a)]


def dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def mm(a, b):
    return [[dot(row, col) for col in zip(*b)] for row in a]


def diff(a, b):
    return max(abs(x - y) for row, other in zip(a, b) for x, y in zip(row, other))


def cross(a, b):
    return [a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0]]


def unit(v):
    d = math.sqrt(dot(v, v))
    assert d > 0
    return [x / d for x in v]


def octal(b):
    assert not b[0] & 128, 'Base256 tar integer outside this small reader'
    s = b.rstrip(b'\0 ').lstrip(b' ')
    assert s and all(c in b'01234567' for c in s)
    return int(s, 8)


def main():
    assert not OUT.exists(), 'Create-only review; preserve any previous attempt'
    start = time.monotonic()
    report = dict(started_utc=utc(), status='RUNNING', source_sha256=sha(Path(__file__).read_bytes()),
                  scope='Different-author saved metadata recomputation; no root functions, tarfile, NumPy, Torch, network, RGB/EXR decoding or model.',
                  json_full_bytes_read_including_objects=True, objects_values_analyzed=False,
                  checks=[], files=[], header_details=[], numerical_tolerance=CAMERA_TOL)

    def check(label, condition):
        report['checks'].append(dict(label=label, passed=bool(condition)))
        assert condition, label

    def read(p):
        b = p.read_bytes()
        report['files'].append(dict(path=str(p), bytes=len(b), sha256=sha(b)))
        return b

    try:
        raw_receipt = read(DATA / 'RECEIPT.json')
        check('receipt identity', sha(raw_receipt) == EXPECTED_RECEIPT)
        rec = json.loads(raw_receipt)
        check('complete metadata receipt', rec['status'] == 'FIRST_JSON_CAMERA_FIELDS_OBTAINED')
        check('seven headers plus one JSON', len(rec['requests']) == 8 and len(rec['members']) == 7)
        check('expected total and possible GT exposure', rec['expected_size'] == TOTAL and rec['metadata_includes_possible_gt_bytes'] is True)
        next_offset, payloads = 0, []
        for i, req in enumerate(rec['requests']):
            p = (DATA / req['body']).resolve()
            check(f'{i}: local body path', p.parent == DATA.resolve())
            b = read(p)
            payloads.append(b)
            check(f'{i}: file identity/length', len(b) == req['body_bytes'] == req['length'] and sha(b) == req['sha256'])
            check(f'{i}: exact expected offset', req['offset'] == next_offset)
            # Reconstruct the final response block rather than taking a range from a redirect.
            block = []
            for line in req['headers']:
                if line.lower().startswith('http/'):
                    block = [line]
                else:
                    block.append(line)
            headers = {line.split(':', 1)[0].lower(): line.split(':', 1)[1].strip()
                       for line in block[1:] if ':' in line}
            expected_range = f'bytes {req["offset"]}-{req["offset"] + len(b) - 1}/{TOTAL}'
            check(f'{i}: final 206/range/length/rc', block[0].split()[1] == '206' and req['http'] == '206'
                  and req['returncode'] == 0 and headers['content-range'] == expected_range
                  and int(headers['content-length']) == len(b))
            check(f'{i}: offset range and cap', req['offset'] >= 0 and req['offset'] + len(b) <= TOTAL
                  and len(b) <= req['transport_body_cap'] == max(req['length'], 8192))
            check(f'{i}: persisted location query redacted', all('?[REDACTED_QUERY]' in x
                  for x in req['headers'] if x.lower().startswith('location:') and '?' in x))
            if i == 7:
                check('one first JSON body', req['kind'] == 'json_quarantine' and len(b) == 189899 and sha(b) == EXPECTED_JSON)
                continue
            check(f'{i}: 512 header only', req['kind'] == 'header' and len(b) == 512)
            stored_sum = octal(b[148:156])
            unsigned_sum = sum(b[:148]) + 8 * 32 + sum(b[156:])
            signed_sum = sum(x if x < 128 else x - 256 for x in b[:148]+b[156:]) + 8*32
            size = octal(b[124:136])
            typ = b[156:157]
            check(f'{i}: checksum and supported type', stored_sum in (unsigned_sum, signed_sum) and typ in (b'0', b'\0', b'5'))
            name = b[:100].split(b'\0', 1)[0].decode('utf-8')
            prefix = b[345:500].split(b'\0', 1)[0].decode('utf-8')
            check(f'{i}: standard ustar header', b[257:263] in (b'ustar\0', b'ustar '))
            if prefix:
                name = prefix + '/' + name
            if typ == b'5':
                name = name.rstrip('/')
                check(f'{i}: empty directory', size == 0)
            expected = dict(header_offset=next_offset, name=name, size=size,
                            type=typ.decode('ascii'), is_regular=typ in (b'0', b'\0'),
                            is_directory=typ == b'5', header_sha256=sha(b))
            check(f'{i}: independent full member fields', expected == rec['members'][i])
            report['header_details'].append(dict(**expected, checksum_recorded=stored_sum,
                                                 checksum_unsigned=unsigned_sum, checksum_signed=signed_sum))
            if i < 6:
                check(f'{i}: no earlier JSON', not name.lower().endswith('.json'))
                next_offset += 512 + ((size + 511) // 512) * 512
            else:
                check('first JSON identity', name == '00000/00108.json' and size == 189899)
                next_offset += 512
        check('saved total bytes', sum(map(len, payloads)) == 193483)
        parsed = json.loads(payloads[-1])
        check('top-level schema', list(parsed) == rec['top_level_keys'] == ['camera_data', 'objects'])
        exported = json.loads(read(DATA / 'CAMERA_FIELDS.json'))
        check('camera export equal original', exported == {'camera_data': parsed['camera_data']})
        c = parsed['camera_data']
        C, V = transpose(c['cam2world']), transpose(c['camera_view_matrix'])
        I4 = [[float(i == j) for j in range(4)] for i in range(4)]
        R = [row[:3] for row in C[:3]]
        I3 = [row[:3] for row in I4[:3]]
        t = [C[i][3] for i in range(3)]
        eye, at, up = [c['camera_look_at'][k] for k in ('eye', 'at', 'up')]
        forward = unit([at[i]-eye[i] for i in range(3)])
        right = unit(cross(forward, up))
        new_up = cross(right, forward)
        look_R = transpose([right, new_up, [-x for x in forward]])
        q = c['quaternion_world_xyzw']
        qnorm = math.sqrt(dot(q, q))
        x, y, z, w = [v/qnorm for v in q]
        Q = [[1-2*(y*y+z*z), 2*(x*y-z*w), 2*(x*z+y*w)],
             [2*(x*y+z*w), 1-2*(x*x+z*z), 2*(y*z-x*w)],
             [2*(x*z-y*w), 2*(y*z+x*w), 1-2*(x*x+y*y)]]
        inverse = [R[0][:], R[1][:], R[2][:]]
        inverse = transpose(inverse)
        inverse = [row + [-dot(row, t)] for row in inverse] + [[0., 0., 0., 1.]]
        det = dot(R[0], cross(R[1], R[2]))
        numeric = dict(C_times_V_identity_max=diff(mm(C,V), I4), V_times_C_identity_max=diff(mm(V,C), I4),
                       rigid_inverse_vs_view_max=diff(inverse, V), R_transpose_R_identity_max=diff(mm(transpose(R),R),I3),
                       determinant_error=abs(det-1), C_last_row_max=diff([C[3]], [I4[3]]), V_last_row_max=diff([V[3]],[I4[3]]),
                       eye_vs_C_translation_max=max(abs(a-b) for a,b in zip(eye,t)),
                       location_world_vs_C_translation_max=max(abs(a-b) for a,b in zip(c['location_world'],t)),
                       look_at_rotation_max=diff(look_R,R), xyzw_normalized_rotation_max=diff(Q,R),
                       quaternion_norm_error=abs(qnorm-1))
        report['camera_numeric_residuals'] = numeric
        for label, value in numeric.items():
            check(label, math.isfinite(value) and value <= CAMERA_TOL)
        eye_cam = [dot(row, eye+[1.]) for row in V]
        at_cam = [dot(row, at+[1.]) for row in V]
        report['camera_diagnostics'] = dict(R_determinant=det, quaternion_original_norm=qnorm,
                                           eye_in_camera=eye_cam, at_in_camera=at_cam,
                                           observed_forward_convention='at-eye matches negative third column of transposed cam2world')
        check('eye camera origin', max(abs(v) for v in eye_cam[:3]) <= CAMERA_TOL)
        check('look-at central negative-Z ray', max(abs(v) for v in at_cam[:2]) <= CAMERA_TOL and at_cam[2] < 0)
        report.update(status='PASS_SAVED_RANGE_AND_CAMERA_METADATA_ARITHMETIC_ONLY',
                      scientific_limit='One JSON only. Transposition, inverse, xyzw and look-at are mutually consistent within stated rounding tolerance. This does not establish physical calibration, metric unit, renderer depth type, distortion/pixel-center semantics, same-scene other-view identity, synchronized/static-state qualification, generated object identity, or method accuracy.',
                      byte_scope='Seven 512B tar headers and full189899B JSON read; objects bytes present and parsed but object values not analyzed. No RGB/EXR/depth body read or network call by this reviewer.',
                      counts=dict(header_files=7,json_body_files=1,saved_transfer_bytes=193483,models=0,scores=0,image_decodes=0,new_network_requests=0))
    except Exception as exc:
        report.update(status='FAILED_PRESERVED', error_type=type(exc).__name__, error=str(exc))
    report.update(completed_utc=utc(), elapsed_seconds=time.monotonic()-start)
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ('checks','files','header_details')}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
