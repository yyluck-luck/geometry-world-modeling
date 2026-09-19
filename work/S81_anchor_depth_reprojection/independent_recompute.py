#!/usr/bin/env python3
"""Independent scalar recomputation of frozen S81; no import of experiment code.

NumPy is used only for safe NPZ container loading and array identity descriptors.
All sampling, projection, residual and summary arithmetic uses Python/math.
A run opens the original frozen depth PNG: do not run before authorization.
"""
import argparse
import csv
import hashlib
import io
import json
import math
from pathlib import Path
import resource
import signal
import sys
from importlib.metadata import version
import time
import traceback
from datetime import datetime, timezone

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
PIXEL_ATOL = 1e-7
METRE_ATOL = 1e-12
QUANTILES = (.25, .5, .75, .95)


def utc():
    return datetime.now(timezone.utc).isoformat()


def digest(data):
    return hashlib.sha256(data).hexdigest()


def linear_quantiles(values):
    data = sorted(float(v) for v in values if math.isfinite(float(v)))
    if not data:
        return None
    out = []
    for q in QUANTILES:
        at = (len(data) - 1) * q
        low = math.floor(at)
        high = math.ceil(at)
        out.append(data[low] + (data[high] - data[low]) * (at - low))
    return out


def dot3(a, b):
    return math.fsum(a[i] * b[i] for i in range(3))


def scalar_sample(xy, depth):
    u, v = (float(xy[0]) + 96.0) / 1.2, float(xy[1]) / 1.2
    finite = math.isfinite(u) and math.isfinite(v)
    ix, iy = (math.floor(u + .5), math.floor(v + .5)) if finite else (-1, -1)
    domain = finite and 0 <= u <= 639 and 0 <= v <= 479
    domain = domain and 0 <= ix < 640 and 0 <= iy < 480
    raw = int(depth.getpixel((ix, iy))) if domain else -1
    valid = domain and raw > 0
    return dict(native_xy=[u, v], sample_xy=[ix, iy], raw_depth=raw,
                z_m=raw / 5000.0 if valid else math.nan, depth_valid=valid,
                reason='VALID' if valid else 'ZERO_DEPTH' if domain else 'SOURCE_OUTSIDE')


def scalar_projection(xy, z, K, source, target, epsilon):
    # Frozen K has zero skew and bottom row [0,0,1]. Use explicit pinhole
    # equations, then two separate world transforms, not relative R/t.
    ray = [(float(xy[0]) - K[0][2]) / K[0][0],
           (float(xy[1]) - K[1][2]) / K[1][1], 1.0]
    point = [a * z for a in ray]
    world = [dot3(source[i][:3], point) + source[i][3] for i in range(3)]
    translated = [world[i] - target[i][3] for i in range(3)]
    camera = [math.fsum(target[j][i] * translated[j] for j in range(3)) for i in range(3)]
    valid = all(math.isfinite(a) for a in camera) and camera[2] > epsilon
    expected = [math.nan, math.nan]
    if valid:
        expected = [K[0][0] * camera[0] / camera[2] + K[0][2],
                    K[1][1] * camera[1] / camera[2] + K[1][2]]
        valid = all(math.isfinite(a) for a in expected)
    fov = valid and 0 <= expected[0] <= 575 and 0 <= expected[1] <= 575
    return dict(expected_xy=expected, target_z_m=camera[2], valid=valid, in_fov=fov)


def scalar_line(F, source_xy):
    point = [float(source_xy[0]), float(source_xy[1]), 1.0]
    return [dot3(row, point) for row in F]


def scalar_record(sample, projection, source_xy, target_xy, F, line_epsilon):
    line = scalar_line(F, source_xy)
    norm = math.hypot(line[0], line[1])
    line_valid = math.isfinite(norm) and norm > line_epsilon
    target_distance = abs(dot3(line, [*target_xy, 1.0])) / norm if line_valid else math.nan
    valid = projection['valid']
    error = along = plane = math.nan
    if valid:
        dx = target_xy[0] - projection['expected_xy'][0]
        dy = target_xy[1] - projection['expected_xy'][1]
        error = math.hypot(dx, dy)
        if line_valid:
            along = math.fsum([-line[1] * dx, line[0] * dy]) / norm
            plane = abs(dot3(line, [*projection['expected_xy'], 1.0])) / norm
    reason = sample['reason']
    if sample['depth_valid'] and not valid:
        reason = 'INVALID_PROJECTION'
    if valid and not projection['in_fov']:
        reason = 'VALID_OUT_OF_VIEW'
    return dict(error_px=error, along_line_signed_px=along, expected_line_px=plane,
                target_line_px=target_distance, reason=reason, line_valid=line_valid)


class Review:
    def __init__(self):
        self.checks = 0
        self.reads = []
        self.max_pixel_difference = 0.0
        self.max_metre_difference = 0.0

    def exact(self, actual, expected, label):
        self.checks += 1
        if actual != expected:
            raise AssertionError(f'{label}: {actual!r} != {expected!r}')

    def truth(self, condition, label):
        self.exact(bool(condition), True, label)

    def close(self, actual, expected, label, kind='pixel'):
        self.checks += 1
        if actual is None or expected is None:
            if actual is not None or expected is not None:
                raise AssertionError(f'{label}: None mismatch')
            return
        a, e = float(actual), float(expected)
        if math.isnan(a) or math.isnan(e):
            if not (math.isnan(a) and math.isnan(e)):
                raise AssertionError(f'{label}: NaN mask mismatch')
            return
        if not (math.isfinite(a) and math.isfinite(e)):
            raise AssertionError(f'{label}: unexpected nonfinite {a}, {e}')
        error = abs(a - e)
        tolerance = METRE_ATOL if kind == 'metre' else PIXEL_ATOL
        if kind == 'metre':
            self.max_metre_difference = max(self.max_metre_difference, error)
        else:
            self.max_pixel_difference = max(self.max_pixel_difference, error)
        if error > tolerance:
            raise AssertionError(f'{label}: actual={a}, expected={e}, absdiff={error}, atol={tolerance}')

    def vector(self, actual, expected, label, kind='pixel'):
        self.exact(len(actual), len(expected), label + ':length')
        for i, (a, e) in enumerate(zip(actual, expected)):
            self.close(a, e, f'{label}[{i}]', kind)

    def read(self, path, expected_sha=None, expected_bytes=None):
        p = Path(path)
        b = p.read_bytes()
        h = digest(b)
        self.reads.append(dict(path=str(p), bytes=len(b), sha256=h))
        if expected_sha is not None:
            self.exact(h, expected_sha, str(p) + ':sha256')
        if expected_bytes is not None:
            self.exact(len(b), expected_bytes, str(p) + ':bytes')
        return b

    def spec_bytes(self, spec):
        return self.read(spec['path'], spec['sha256'], spec.get('bytes'))

    def spec_json(self, spec):
        return json.loads(self.spec_bytes(spec))

    def npz(self, spec, fields):
        with np.load(io.BytesIO(self.spec_bytes(spec)), allow_pickle=False) as packet:
            result = {}
            for field in fields:
                a = packet[field]
                descriptors = spec.get('arrays', spec.get('fields', {}))
                if field in descriptors:
                    d = descriptors[field]
                    self.exact(list(a.shape), d['shape'], field + ':shape')
                    self.exact(str(a.dtype), d['dtype'], field + ':dtype')
                    expected_hash = d.get('sha256', d.get('body_sha256'))
                    if expected_hash:
                        self.exact(digest(a.tobytes(order='C')), expected_hash, field + ':array_hash')
                result[field] = a.tolist()
            return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--contract-sha', required=True)
    parser.add_argument('--checker-sha', required=True)
    parser.add_argument('--output-manifest-sha', required=True)
    parser.add_argument('--execution-dir', type=Path, default=HERE/'execution_01')
    parser.add_argument('--output-dir', type=Path, default=HERE/'independent_recompute_01')
    args = parser.parse_args()
    review = Review()
    args.output_dir.mkdir(exist_ok=False)
    begin = time.monotonic()
    receipt = dict(schema='S81_INDEPENDENT_SCALAR_RECOMPUTATION_V1', started_utc=utc(),
                   status='RUNNING', pixel_absolute_tolerance=PIXEL_ATOL,
                   metre_absolute_tolerance=METRE_ATOL, relative_tolerance=0,
                   depth_decodes=0, model_calls=0, new_matching_calls=0,
                   rgb_decodes=0, new_method_validated=False,
                   independence='Separate Python/math pixel sampling, pinhole ray, world then target transform and hand-sorted quantiles. NumPy is NPZ I/O only; no import of experiment program.',
                   versions={'Python':sys.version, 'numpy':np.__version__, 'Pillow':version('Pillow')},
                   scope_limits=['No independent physical correspondence truth, target visibility, temporal registration or camera calibration established.',
                                 'No new neural inference or feature matching; assertion count is not sample size.',
                                 'This reviewer authored earlier S80 observer code, not the S81 experiment projection code.'])
    row_results = []
    try:
        receipt['checker_sha256'] = digest(review.read(__file__, args.checker_sha))
        contract_bytes = review.read(HERE/'CONTRACT.json', args.contract_sha)
        contract = json.loads(contract_bytes)
        receipt['contract_sha256'] = digest(contract_bytes)
        review.exact({key:version(key) for key in contract['versions']}, contract['versions'], 'runtime versions')
        review.exact(contract['identity_atol_px'], PIXEL_ATOL, 'frozen pixel tolerance')
        review.exact(contract['thresholds_px'], [2, 5, 10], 'frozen descriptive cutoffs')
        def timed_out(signum, frame):
            raise TimeoutError('Independent scalar recomputation exceeded 60 seconds')
        signal.signal(signal.SIGALRM, timed_out)
        signal.alarm(60)
        # Bind existing output files to the separately supplied manifest identity.
        manifest = json.loads(review.read(args.execution_dir/'OUTPUT_MANIFEST.json', args.output_manifest_sha))
        output_specs = {}
        for item in manifest:
            path = Path(item['path'])
            review.truth(path.is_relative_to(args.execution_dir), 'manifest output containment')
            name = str(path.relative_to(args.execution_dir))
            review.truth(name not in output_specs, 'unique output manifest path')
            output_specs[name] = item
        def output_json(name):
            return review.spec_json(output_specs[name])
        def output_npz(name, fields):
            return review.npz(output_specs[name], fields)
        run_receipt = output_json('RECEIPT.json')
        review.exact(run_receipt['status'], 'COMPLETED_DESCRIPTIVE_ONLY', 'experiment completion')
        review.exact(run_receipt['contract_sha256'], args.contract_sha, 'executed contract')
        review.read(HERE/'run_reprojection.py', run_receipt['source_sha256'])
        rows = review.spec_json(contract['rows'])
        review.exact([r['row_id'] for r in rows], contract['row_order'], 'row identity/order')
        review.exact(len(rows), 24, 'all24')
        review.exact(sum(r['M'] for r in rows), 7757, 'all7757')
        geometry = review.spec_json(contract['geometry_receipt'])
        K = geometry['K_pixels_576']
        review.exact([K[0][1], K[1][0], *K[2]], [0.0, 0.0, 0.0, 0.0, 1.0], 'pinhole K shape')
        cameras = review.npz(contract['cameras'], ['ids', 'c2ws'])
        camera = dict(zip(cameras['ids'], cameras['c2ws']))
        for ident in [19, 20, 21, 22, 23]:
            review.exact(camera[ident], geometry['optical_c2ws_used'][str(ident)], f'optical_camera_{ident}')
        features = review.npz(contract['source_features'], ['keypoints', 'image_size'])
        source_xy = features['keypoints']
        review.exact(len(source_xy), 1313, 'source features N')
        review.exact(features['image_size'], [576.0, 576.0], 'native image size')
        for point in source_xy:
            review.truth(len(point) == 2 and all(math.isfinite(v) for v in point), 'finite source coordinate')
        original_depth = review.spec_bytes(contract['depth'])
        review.exact(original_depth[:8], b'\x89PNG\r\n\x1a\n', 'depth PNG')
        review.exact(list(original_depth[24:26]), [16, 0], 'depth16bit grayscale')
        with Image.open(io.BytesIO(original_depth)) as depth:
            review.exact(depth.size, (640, 480), 'depth image dimensions')
            depth.load()
            receipt['depth_decodes'] += 1
            samples = [scalar_sample(point, depth) for point in source_xy]
        stored = output_npz('SOURCE_SAMPLES.npz', ['source_xy', 'native_xy', 'sample_xy', 'raw_depth', 'z_m', 'depth_valid', 'reason'])
        review.exact(stored['source_xy'], source_xy, 'source coordinate identities')
        for i, sample in enumerate(samples):
            review.vector(stored['native_xy'][i], sample['native_xy'], f'sample{i}:native')
            for key in ['sample_xy', 'raw_depth', 'depth_valid', 'reason']:
                review.exact(stored[key][i], sample[key], f'sample{i}:{key}')
            review.close(stored['z_m'][i], sample['z_m'], f'sample{i}:Z', 'metre')
        projections = {}
        projection_counts = []
        for target in [20, 21, 22, 23]:
            calculated = [scalar_projection(p, s['z_m'], K, camera[19], camera[target], contract['z_epsilon_m']) for p, s in zip(source_xy, samples)]
            saved = output_npz(f'ALL_SOURCE_TO_{target}.npz', ['expected_xy', 'target_z_m', 'valid', 'in_fov'])
            for i, (got, want) in enumerate(zip(saved['expected_xy'], calculated)):
                review.vector(got, want['expected_xy'], f'projection{target}:{i}:xy')
                review.close(saved['target_z_m'][i], want['target_z_m'], f'projection{target}:{i}:Z', 'metre')
                review.exact(saved['valid'][i], want['valid'], f'projection{target}:{i}:valid')
                review.exact(saved['in_fov'][i], want['in_fov'], f'projection{target}:{i}:fov')
            review.exact(len(saved['expected_xy']), 1313, f'projection{target}:N')
            projections[target] = calculated
            projection_counts.append(dict(target_id=target, N=1313, depth_valid=sum(s['depth_valid'] for s in samples), projected=sum(p['valid'] for p in calculated), in_fov=sum(p['in_fov'] for p in calculated)))
        review.exact(output_json('SOURCE_PROJECTION_COUNTS.json'), projection_counts, 'all-source projection counts')
        summaries = output_json('ROWS.json')
        review.exact([r['row_id'] for r in summaries], contract['row_order'], 'output24 row order')
        cache = {}
        csv_records = []
        for row, summary in zip(rows, summaries):
            rid = row['row_id']
            frozen = review.npz(row['saved'], ['accepted_indices', 'source_xy', 'target_xy', 'correct_F', 'correct_residuals'])
            ids = frozen['accepted_indices']
            review.exact(len(ids), row['M'], rid + ':M')
            review.exact(len({p[0] for p in ids}), len(ids), rid + ':unique source indices')
            review.exact(len({p[1] for p in ids}), len(ids), rid + ':unique target indices')
            saved = output_npz('pairs/' + rid + '.npz', ['accepted_indices', 'expected_xy', 'target_xy', 'target_z_m', 'valid', 'in_fov', 'error_px', 'along_line_signed_px', 'depth_valid', 'target_line_px', 'expected_line_px', 'reason'])
            review.exact(saved['accepted_indices'], ids, rid + ':copied accepted indices')
            review.exact(saved['target_xy'], frozen['target_xy'], rid + ':copied target coordinates')
            computed = []
            values = {}
            for k, (source_id, target_id) in enumerate(ids):
                review.truth(0 <= source_id < 1313 and 0 <= target_id < row['N_target'], rid + ':index domain')
                review.exact(frozen['source_xy'][k], source_xy[source_id], rid + ':source identity')
                sample = samples[source_id]
                projection = projections[row['target_id']][source_id]
                target_xy = frozen['target_xy'][k]
                review.truth(all(math.isfinite(v) for v in target_xy), rid + ':finite target')
                result = scalar_record(sample, projection, source_xy[source_id], target_xy, frozen['correct_F'], contract['line_epsilon'])
                review.vector(saved['expected_xy'][k], projection['expected_xy'], f'{rid}:{k}:expected')
                review.close(saved['target_z_m'][k], projection['target_z_m'], f'{rid}:{k}:targetZ', 'metre')
                for key in ['valid', 'in_fov']:
                    review.exact(saved[key][k], projection[key], f'{rid}:{k}:{key}')
                review.exact(saved['depth_valid'][k], sample['depth_valid'], f'{rid}:{k}:depth valid')
                review.exact(saved['reason'][k], result['reason'], f'{rid}:{k}:reason')
                for key in ['error_px', 'along_line_signed_px', 'target_line_px', 'expected_line_px']:
                    review.close(saved[key][k], result[key], f'{rid}:{k}:{key}')
                review.close(frozen['correct_residuals'][k][0], result['target_line_px'], f'{rid}:{k}:original target-line distance')
                if projection['valid'] and result['line_valid']:
                    review.truth(result['expected_line_px'] <= PIXEL_ATOL, rid + ':expected lies on target line')
                    review.truth(result['error_px'] + PIXEL_ATOL >= result['target_line_px'], rid + ':target-line bound')
                combined = dict(sample, **projection, **result)
                computed.append(combined)
                values[source_id] = (target_id, result['error_px'])
                def csv_number(value):
                    return float(value) if math.isfinite(float(value)) else ''
                csv_records.append(dict(row_id=rid, match_row=k, source_id=source_id, target_id=target_id,
                    raw_depth=sample['raw_depth'], sample_x=sample['sample_xy'][0], sample_y=sample['sample_xy'][1],
                    expected_x=csv_number(projection['expected_xy'][0]), expected_y=csv_number(projection['expected_xy'][1]),
                    matched_x=target_xy[0], matched_y=target_xy[1], target_z_m=csv_number(projection['target_z_m']),
                    valid=projection['valid'], in_fov=projection['in_fov'], error_px=csv_number(result['error_px']),
                    along_line_px=csv_number(result['along_line_signed_px']), status=result['reason'], visibility='UNKNOWN'))
            cache[rid] = values
            M, V = len(computed), sum(v['valid'] for v in computed)
            reasons = {}
            for item in computed:
                if not item['valid']:
                    reasons[item['reason']] = reasons.get(item['reason'], 0) + 1
            exact_summary = dict(row_id=rid, target_id=row['target_id'], arm=row['arm'], matcher=row['matcher'],
                N=1313, M=M, unmatched_N=1313-M, depth_valid=sum(v['depth_valid'] for v in computed),
                V=V, in_fov=sum(v['in_fov'] for v in computed), out_of_view=sum(v['valid'] and not v['in_fov'] for v in computed),
                V_over_M=V/M, V_over_N=V/1313, invalid_reasons=reasons, visibility_status='UNKNOWN')
            for key, value in exact_summary.items():
                review.exact(summary[key], value, rid + ':summary:' + key)
            qsets = {'error_q25_q50_q75_q95_px': [v['error_px'] for v in computed],
                     'in_fov_error_quantiles_px': [v['error_px'] for v in computed if v['in_fov']],
                     'abs_along_line_quantiles_px': [abs(v['along_line_signed_px']) for v in computed]}
            for key, data in qsets.items():
                q = linear_quantiles(data)
                if q is None:
                    review.exact(summary[key], None, rid + ':' + key)
                else:
                    review.vector(summary[key], q, rid + ':' + key)
            for threshold in contract['thresholds_px']:
                key = str(threshold)
                good = sum(v['valid'] and v['error_px'] <= threshold for v in computed)
                review.exact(summary['counts_le_px'][key], good, rid + ':threshold count ' + key)
                for name, denominator in [('fractions_le_valid', V), ('fractions_le_M', M), ('fractions_le_N', 1313)]:
                    review.exact(summary[name][key], good/denominator if denominator else None, rid + ':' + name + ':' + key)
            finite_planes = [v['expected_line_px'] for v in computed if math.isfinite(v['expected_line_px'])]
            review.close(summary['max_expected_to_epiline_px'], max(finite_planes) if finite_planes else None, rid + ':max expected line')
            row_results.append(dict(row_id=rid, M=M, V=V, invalid_reasons=reasons,
                                    median_px=linear_quantiles([v['error_px'] for v in computed])[1] if V else None))
        # Four targets x (four generated-real + three LG-BF comparisons) =28.
        paired = output_json('PAIRED.json')
        comparisons = []
        for target in [20,21,22,23]:
            comparisons += [(f't{target}_real_{m}',f't{target}_{a}_{m}') for m in ['BF','LG'] for a in ['A0','B']]
            comparisons += [(f't{target}_{a}_BF',f't{target}_{a}_LG') for a in ['real','A0','B']]
        review.exact(len(paired), 28, 'all28 paired comparisons')
        total_paired_records = 0
        for stored_pair, (left, right) in zip(paired, comparisons):
            review.exact([stored_pair['left'],stored_pair['right']], [left,right], 'paired order/identity')
            a, b = cache[left], cache[right]
            shared = sorted(set(a) & set(b))
            review.exact(stored_pair['shared_sources'],len(shared),'paired source denominator')
            review.exact([v['source_id'] for v in stored_pair['records']],shared,'all shared source records')
            deltas=[]
            for record, source_id in zip(stored_pair['records'],shared):
                at,ae = a[source_id];bt,be=b[source_id]
                review.exact(record['left_target_feature_id'],at,'paired left target index')
                review.exact(record['right_target_feature_id'],bt,'paired right target index')
                delta = be-ae if math.isfinite(ae) and math.isfinite(be) else None
                review.close(record['difference_right_minus_left_px'],delta,'paired right-minus-left error')
                if delta is not None:
                    deltas.append(delta)
                if left.endswith('_BF') and right.endswith('_LG') and at==bt:
                    review.truth((math.isnan(ae) and math.isnan(be)) or ae==be,'same image and feature edge equal error')
            review.exact(stored_pair['valid_pairs'],len(deltas),'paired valid denominator')
            q=linear_quantiles(deltas)
            if q is None:
                review.exact(stored_pair['differences_quantiles_px'],None,'paired empty quantiles')
            else:
                review.vector(stored_pair['differences_quantiles_px'],q,'paired quantiles')
            total_paired_records += len(shared)
        saved_csv=list(csv.DictReader(io.StringIO(review.spec_bytes(output_specs['ALL_RECORDS.csv']).decode())))
        review.exact(len(saved_csv),7757,'all7757 CSV rows')
        review.exact(len(csv_records),7757,'all7757 independently assembled records')
        numeric_csv={'expected_x','expected_y','matched_x','matched_y','target_z_m','error_px','along_line_px'}
        for i,(actual,expected) in enumerate(zip(saved_csv,csv_records)):
            review.exact(set(actual),set(expected),'CSV column identities')
            for key,value in expected.items():
                if key in numeric_csv and value!='':
                    review.close(float(actual[key]),value,f'CSV{i}:{key}','metre' if key=='target_z_m' else 'pixel')
                else:
                    review.exact(actual[key],str(value),f'CSV{i}:{key}')
        for key,value in {'row_count':24,'accepted_records':7757,'all_source_count':1313,
                          'source_depth_valid':sum(s['depth_valid'] for s in samples),'paired_count':28}.items():
            review.exact(run_receipt[key],value,'run receipt:'+key)
        receipt.update(status='PASS_INDEPENDENT_SCALAR_SAVED_DATA_RECOMPUTATION_ONLY',source_samples=1313,
                       target_projection_records=4*1313,accepted_records=7757,row_count=24,
                       paired_comparisons=28,paired_source_records=total_paired_records)
    except BaseException as error:
        receipt.update(status='FAILED',exception=repr(error),traceback=traceback.format_exc())
        raise
    finally:
        signal.alarm(0)
        receipt.update(completed_utc=utc(),wall_seconds=time.monotonic()-begin,checks=review.checks,
                       max_absolute_pixel_difference=review.max_pixel_difference,
                       max_absolute_metre_difference=review.max_metre_difference,
                       reads=review.reads,rows=row_results,
                       ru_maxrss_bytes_macos=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
        with (args.output_dir/'RECEIPT.json').open('x') as f:
            json.dump(receipt,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
        text = '# S81 independent scalar recomputation\n\n'
        text += f"Status: {receipt['status']}\n\nStarted UTC: {receipt['started_utc']}\nCompleted UTC: {receipt['completed_utc']}\n\n"
        text += f"Actual assertions: {review.checks}; these are not independent experiments.\n\n"
        text += 'Scope: all frozen source sampling, four target projections, 24 saved match rows, scalar target-line/forward/along-line arithmetic, all 28 paired comparisons and full CSV, up to the actual reached check on failure. See RECEIPT.json for counts, hashes and any traceback.\n\n'
        text += 'No model, matching or physical-truth validation. Pixel absolute tolerance1e-7; target-Z arithmetic tolerance1e-12 metres; states, indices, counts and denominators exact.\n'
        (args.output_dir/'REVIEW.md').write_text(text)


if __name__ == '__main__':
    main()
