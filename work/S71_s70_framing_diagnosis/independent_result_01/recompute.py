"""One saved-coordinate arithmetic verification; no image/CV/model imports."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import math
import sys
import time
import traceback

D = Path(__file__).resolve().parent.parent
OUT = Path(__file__).resolve().parent
ATOL, RTOL = 1e-9, 1e-12  # arithmetic comparison only, never a scientific cutoff
PINS = {
    'execution_01/receipt.json': '33b6d6fa066aff7ba0e2857a8d21f954d2d410dca46aed43aac839c32277dff6',
    'external_01/receipt.json': 'b5f1f1b1080b361e8069e47bbe022fabf1f07d7192a67a007a0297277bc47fad',
    'ROOT_SOURCE_ACCEPTANCE.json': '845d785f47d4abf833acc07a4a8c005d60527546ebc8cdca74884e2e7bf0b663',
    'CONTRACT.json': '0a38f1bf3e3e56622f4937e6684b2bad3cc3138fcae5ee8896e5ba31ba366707',
    'measure.py': '47410568a1719066a7775a6c20701ca08e8f91b1c7fd8d5b284ef9462050c78f',
}


def utc():
    return datetime.now(timezone.utc).isoformat()


def quantile(values, q):
    ordered = sorted(values)
    position = (len(ordered) - 1) * q
    lo = math.floor(position)
    hi = math.ceil(position)
    fraction = position - lo
    return (1 - fraction) * ordered[lo] + fraction * ordered[hi]


def statistics(source, destination):
    deltas = [(b[0] - a[0], b[1] - a[1]) for a, b in zip(source, destination)]
    lengths = [math.hypot(x, y) for x, y in deltas]
    spans = [[max(p[k] for p in points) - min(p[k] for p in points)
              for k in (0, 1)] for points in (source, destination)]
    return {
        'count': len(source),
        'displacement_quantiles_px': [quantile(lengths, q) for q in (.25, .5, .75, .95)],
        'median_dx_dy_px': [quantile([v[k] for v in deltas], .5) for k in (0, 1)],
        'source_span_xy': spans[0], 'destination_span_xy': spans[1],
        'source_span_xy_fraction': [v / 575 for v in spans[0]],
        'destination_span_xy_fraction': [v / 575 for v in spans[1]],
    }


def flatten(value):
    if isinstance(value, list):
        return [z for v in value for z in flatten(v)]
    return [value]


def main(report):
    checks = report['checks']
    blobs = {}

    def check(name, passed, detail=None):
        checks.append({'name': name, 'pass': bool(passed), 'detail': detail})

    def read(rel, expected=None):
        p = D / rel
        data = p.read_bytes()
        digest = hashlib.sha256(data).hexdigest()
        report['reads'].append({'path': str(p), 'bytes': len(data), 'sha256': digest,
                                'mode': oct(p.stat().st_mode & 0o777)})
        if expected is not None:
            check('pin:' + rel, digest == expected)
            if digest != expected:
                raise ValueError('Pinned input changed: ' + rel)
        blobs[rel] = data
        return data

    def compare(name, actual, saved):
        av, sv = flatten(actual), flatten(saved)
        differences = [abs(a - s) for a, s in zip(av, sv)]
        bad = [i for i, (a, s) in enumerate(zip(av, sv))
               if not (math.isfinite(a) and math.isfinite(s)
                       and math.isclose(a, s, abs_tol=ATOL, rel_tol=RTOL))]
        check(name, len(av) == len(sv) and not bad,
              {'computed_count': len(av), 'saved_count': len(sv),
               'max_absolute_difference': max(differences, default=0),
               'mismatch_indices': bad})

    for rel, digest in PINS.items():
        read(rel, digest)
    worker = json.loads(blobs['execution_01/receipt.json'])
    external = json.loads(blobs['external_01/receipt.json'])
    contract = json.loads(blobs['CONTRACT.json'])
    accepted = json.loads(blobs['ROOT_SOURCE_ACCEPTANCE.json'])
    stdout = read('external_01/stdout.txt', external['stdout_sha256'])
    stderr = read('external_01/stderr.txt', external['stderr_sha256'])
    check('outer_success', external['returncode'] == 0 and external['timeout'] is False)
    check('outer_bindings', external['worker_receipt_sha256'] == PINS['execution_01/receipt.json']
          and external['root_acceptance_sha256'] == PINS['ROOT_SOURCE_ACCEPTANCE.json'])
    check('source_contract_bindings', worker['source_sha256'] == PINS['measure.py']
          and worker['contract_sha256'] == PINS['CONTRACT.json']
          and all(accepted['files_sha256'][k] == PINS[k] for k in ('measure.py', 'CONTRACT.json')))
    check('worker_success_and_scope', worker['status'] == 'COMPLETE_SAVED_IMAGE_EXPLORATION'
          and worker['model_calls'] == 0 and worker['weight_bytes'] == 0
          and worker['new_method_validated'] is False)
    check('terminal_logs', stderr == b'' and json.loads(stdout)['status'] == worker['status']
          and json.loads(stdout)['completed_utc'] == worker['completed_utc'])
    check('actual_time_order', accepted['accepted_utc'] <= external['started_utc']
          <= worker['started_utc'] <= worker['completed_utc'] <= external['completed_utc'])
    check('versions', worker['versions'] == contract['versions'])
    expected_order = [(t, label) for t in contract['targets'] for label in contract['pairs']]
    check('all_twelve_pairs_in_fixed_order', len(expected_order) == 12 and
          [(p['target_id'], p['pair']) for p in worker['pairs']] == expected_order)
    image_reads = worker['reads']
    check('recorded_image_readlist_only', len(image_reads) == 16
          and len({x['path'] for x in image_reads}) == 16
          and {x['path']: x['sha256'] for x in image_reads} == contract['source_images'])
    report['upstream_image_readlist_metadata_only'] = {
        'count': len(image_reads), 'bytes_claimed': sum(x['bytes'] for x in image_reads),
        'bodies_read_by_this_verifier': 0,
    }
    report['upstream_execution'] = {k: external[k] for k in
        ('started_utc', 'completed_utc', 'elapsed_seconds', 'returncode', 'timeout')}

    for p in worker['pairs']:
        target, label = p['target_id'], p['pair']
        tag = f'{target}/{label}/'
        a, b, ids = p['source_xy'], p['destination_xy'], p['match_keypoint_ids']
        n = len(a)
        check(tag + 'counts', n == len(b) == len(ids) == p['mutual_match_count'])
        check(tag + 'xy_shape_finite_native_domain', all(len(x) == 2 and
              all(math.isfinite(v) and 0 <= v < 576 for v in x) for x in a + b))
        src_name, dst_name = ('A0', 'A1') if label == 'A0_A1_repeat_control' else ('reference', label.split('_')[1])
        check(tag + 'keypoint_counts', p['source_keypoints'] == worker['keypoint_counts'][f'{src_name}_target_{target}']
              and p['destination_keypoints'] == worker['keypoint_counts'][f'{dst_name}_target_{target}'])
        check(tag + 'match_id_shape_domain_one_to_one', all(len(x) == 2 and
              all(type(v) is int for v in x) and 0 <= x[0] < p['source_keypoints']
              and 0 <= x[1] < p['destination_keypoints'] for x in ids)
              and len({x[0] for x in ids}) == n and len({x[1] for x in ids}) == n)
        computed = {'target_id': target, 'pair': label, 'all_matches': statistics(a, b)}
        for key, value in computed['all_matches'].items():
            compare(tag + 'all/' + key, value, p['all_matches'][key])
        if label == 'A0_A1_repeat_control':
            zero = n > 0 and all(x == y for x, y in zip(a, b))
            check(tag + 'exact_zero_displacement', zero and p['zero_displacement_control_pass'] is True)
            computed['exact_zero_displacement'] = zero
        if n < contract['homography']['min_matches']:
            check(tag + 'insufficient_match_retention', p['fit_status'] == 'INSUFFICIENT_MATCHES'
                  and not any(k in p for k in ('H', 'inlier_count', 'inlier_summary')))
            computed['fit_status'] = p['fit_status']
        else:
            H, mask = p['H'], p['ransac_inlier_mask']
            check(tag + 'H_shape_finite', len(H) == 3 and all(len(row) == 3 and
                  all(math.isfinite(v) for v in row) for row in H))
            check(tag + 'mask_shape_boolean', len(mask) == n and all(type(v) is bool for v in mask))
            projected = []
            finite = []
            for x, y in a:
                homogeneous = [math.fsum((row[0] * x, row[1] * y, row[2])) for row in H]
                ok = all(math.isfinite(v) for v in homogeneous) and abs(homogeneous[2]) > 1e-12
                finite.append(ok)
                projected.append([homogeneous[0] / homogeneous[2], homogeneous[1] / homogeneous[2]] if ok else None)
            check(tag + 'homogeneous_finite_mask', finite == p['finite_projection_mask'])
            retained = [i for i, included in enumerate(mask) if included]
            check(tag + 'inlier_count', len(retained) == p['inlier_count'])
            check(tag + 'inliers_have_finite_projection', all(finite[i] for i in retained))
            summary = statistics([a[i] for i in retained], [b[i] for i in retained])
            for key, value in summary.items():
                compare(tag + 'inlier/' + key, value, p['inlier_summary'][key])
            residual = [math.hypot(projected[i][0] - b[i][0], projected[i][1] - b[i][1]) for i in retained]
            compare(tag + 'each_inlier_reprojection_residual', residual, p['inlier_reprojection_residual_px'])
            compare(tag + 'inlier_residual_median', quantile(residual, .5), p['inlier_residual_median_px'])
            check(tag + 'fit_status', p['fit_status'] == 'FITTED_DESCRIPTIVE_ONLY')
            computed.update({'fit_status': p['fit_status'], 'inlier_summary': summary,
                             'finite_projection_count': sum(finite),
                             'independent_inlier_reprojection_residual_px': residual,
                             'independent_residual_median_px': quantile(residual, .5)})
        report['pairs'].append(computed)
    check('four_repeat_controls_worker_claim', worker['all_repeat_controls_pass'] is True
          and sum(p.get('exact_zero_displacement', False) for p in report['pairs']) == 4)


if __name__ == '__main__':
    started, timer = utc(), time.perf_counter()
    target = OUT / 'receipt.json'
    with target.open('x') as output:
        report = {'schema': 's71-independent-coordinate-arithmetic-review-v1',
                  'status': 'RUNNING', 'reviewer_role': '/root/c2_v9_source_primary',
                  'started_utc': started, 'python': sys.version,
                  'verifier_source_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                  'arithmetic_tolerance': {'absolute': ATOL, 'relative': RTOL},
                  'reads': [], 'checks': [], 'pairs': [], 'blockers': [],
                  'scope': 'Saved coordinates/H/masks and JSON/source/log identities only; no measure.py import, image body, feature extraction, H refit, model, weight or CV library.',
                  'limitation': 'Different-author arithmetic verification does not validate feature correspondence truth, global framing or a causal camera/memory mechanism.',
                  'new_method_validated': False}
        try:
            main(report)
            report['blockers'] = [c['name'] for c in report['checks'] if not c['pass']]
            report['status'] = 'PASS_S71_INDEPENDENT_COORDINATE_ARITHMETIC' if not report['blockers'] else 'DISCREPANCY_PRESERVED'
        except Exception:
            report['status'] = 'FAILED_INDEPENDENT_COORDINATE_ARITHMETIC'
            report['exception'] = traceback.format_exc()
            report['blockers'].append('exception')
        report['completed_utc'] = utc()
        report['elapsed_seconds'] = time.perf_counter() - timer
        report['input_file_count'] = len(report['reads'])
        report['input_bytes'] = sum(r['bytes'] for r in report['reads'])
        report['checks_passed'] = sum(c['pass'] for c in report['checks'])
        json.dump(report, output, indent=2, allow_nan=False)
        output.write('\n')
    target.chmod(0o444)
    print(json.dumps({k: report[k] for k in ('status', 'checks_passed', 'blockers', 'elapsed_seconds', 'input_file_count', 'input_bytes')}))
    raise SystemExit(0 if not report['blockers'] else 1)
