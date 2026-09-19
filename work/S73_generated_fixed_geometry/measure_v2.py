"""Existing generated-image diagnostic with explicit support denominators."""
from pathlib import Path
from datetime import datetime, timezone
from importlib.metadata import version
import hashlib
import io
import json
import sys
import time
import traceback

D = Path(__file__).resolve().parent


def sha(b):
    return hashlib.sha256(b).hexdigest()


def utc():
    return datetime.now(timezone.utc).isoformat()


def main():
    cb = (D / 'CONTRACT.json').read_bytes()
    assert len(sys.argv) == 2 and sha(cb) == sys.argv[1]
    c = json.loads(cb)
    out = D / 'execution_02'
    out.mkdir(exist_ok=False)
    start = time.monotonic()
    r = dict(started_utc=utc(), status='RUNNING', contract_sha256=sha(cb),
             source_sha256=sha(Path(__file__).read_bytes()), reads=[], pairs=[],
             shared_support=[], model_calls=0, weight_bytes=0, new_method_validated=False)

    def read(item, kind):
        b = Path(item['path']).read_bytes()
        r['reads'].append(dict(path=item['path'], kind=kind, bytes=len(b), sha256=sha(b)))
        assert sha(b) == item['sha256']
        return b

    try:
        import cv2
        import numpy as np
        from PIL import Image
        assert {k: version(k) for k in c['versions']} == c['versions']
        r['versions'] = c['versions']
        cv2.setNumThreads(1)
        cv2.setRNGSeed(72)
        accepted = json.loads(read(c['real_acceptance'], 'accepted_real_metadata'))
        assert accepted['status'] == 'ACCEPTED_S72_REAL_CONTROL_ARITHMETIC_ONLY'
        assert accepted['files_sha256']['execution_01/receipt.json'] == c['real_receipt']['sha256']
        old = json.loads(read(c['real_receipt'], 'real_saved_coordinates_and_F'))
        assert old['status'] == 'COMPLETE_REAL_CONTROL_DIAGNOSTIC'
        real = {row['target_id']: row for row in old['pairs']}
        assert sorted(real) == c['target_ids']
        sift = cv2.SIFT_create(**c['sift'])

        def features(item):
            with Image.open(io.BytesIO(read(item, 'RGB_PNG'))) as im:
                assert im.mode == 'RGB' and im.size == (576, 576)
                rgb = np.array(im)
            return sift.detectAndCompute(cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY), None)

        kp, desc = features(c['anchor'])
        N = len(kp)
        assert N == old['anchor_keypoints'] and N > 0 and desc is not None
        r.update(anchor_count=N, anchor_xy=[list(k.pt) for k in kp],
                 anchor_descriptors_sha256=sha(desc.tobytes()), anchor_descriptor_shape=list(desc.shape))
        for row in real.values():
            assert len(row['match_keypoint_ids']) == row['match_count']
            for (i, _), xy in zip(row['match_keypoint_ids'], row['source_xy']):
                assert list(kp[i].pt) == xy
        r['all_observed_real_anchor_ids_xy_exact'] = True
        bf = cv2.BFMatcher(cv2.NORM_L2, crossCheck=False)

        def ratio(a, b):
            if a is None or b is None or len(b) < 2:
                return {}
            return {m.queryIdx: m.trainIdx for row in bf.knnMatch(a, b, k=2)
                    if len(row) == 2 for m, n in [row] if m.distance < .75 * n.distance}

        def quantiles(x):
            return np.quantile(x, c['residual_quantiles']).tolist() if len(x) else None

        def coverage(x):
            if len(x) == 0:
                return dict(span_xy_fraction=None, occupied_4x4_cells=0)
            x = np.array(x, dtype=np.float64)
            cells = np.clip(np.floor(x / 144), 0, 3).astype(int)
            return dict(span_xy_fraction=(np.ptp(x, axis=0) / 575).tolist(),
                        occupied_4x4_cells=len(set(map(tuple, cells.tolist()))))

        def availability(row):
            m = row['match_count']
            assert len({i for i, _ in row['match_keypoint_ids']}) == m <= N
            valid = [v[2] for v in row['residuals'] if v is not None]
            row.update(anchor_population=N, matched_fraction=m/N, unmatched_count=N-m,
                       unmatched_fraction=(N-m)/N, valid_count=len(valid), invalid_count=m-len(valid),
                       threshold_counts={str(q): sum(v <= q for v in valid) for q in c['cutoffs_px']},
                       agreement_fraction_of_anchor={str(q): sum(v <= q for v in valid)/N for q in c['cutoffs_px']},
                       agreement_fraction_of_valid={str(q): sum(v <= q for v in valid)/len(valid) if valid else None for q in c['cutoffs_px']})

        for j in c['target_ids']:
            row = dict(real[j])
            row['arm'] = 'real'
            row['reused_from_S72'] = True
            availability(row)
            r['pairs'].append(row)
        for item in c['generated_images'].values():
            j, arm = item['target_id'], item['arm']
            F = np.array(real[j]['F_unit_frobenius'], dtype=np.float64)
            assert F.shape == (3, 3) and np.isfinite(F).all()
            kj, dj = features(item)
            forward, reverse = ratio(desc, dj), ratio(dj, desc)
            matches = [(i, k) for i, k in sorted(forward.items()) if reverse.get(k) == i]
            x = np.array([kp[i].pt for i, k in matches], dtype=np.float64).reshape(-1, 2)
            y = np.array([kj[k].pt for i, k in matches], dtype=np.float64).reshape(-1, 2)
            xh, yh = np.column_stack([x, np.ones(len(x))]), np.column_stack([y, np.ones(len(y))])
            lt, ls = xh @ F.T, yh @ F
            nt, ns = np.linalg.norm(lt[:, :2], axis=1), np.linalg.norm(ls[:, :2], axis=1)
            a = np.sum(yh * lt, axis=1)
            valid = np.isfinite(a) & np.isfinite(nt) & np.isfinite(ns)
            valid &= (nt > c['line_epsilon']) & (ns > c['line_epsilon'])
            dt, ds = np.abs(a[valid])/nt[valid], np.abs(a[valid])/ns[valid]
            mean = (dt+ds)/2
            residuals, vi = [], 0
            for good in valid:
                residuals.append([float(dt[vi]), float(ds[vi]), float(mean[vi])] if good else None)
                vi += int(good)
            row = dict(arm=arm, target_id=j, target_keypoints=len(kj), match_count=len(matches),
                       match_keypoint_ids=matches, source_xy=x.tolist(), target_xy=y.tolist(),
                       F_unit_frobenius=F.tolist(), valid_line_mask=valid.tolist(), residuals=residuals,
                       residual_quantiles_px=quantiles(mean), source_coverage=coverage(x), target_coverage=coverage(y),
                       status='COMPUTED_DESCRIPTIVE_ONLY' if valid.any() else 'NO_VALID_MATCHES',
                       reused_from_S72=False)
            availability(row)
            r['pairs'].append(row)
        by_pair = {(p['target_id'], p['arm']): p for p in r['pairs']}
        for j in c['target_ids']:
            maps = {arm: {a: row['residuals'][i] for i, (a, _) in enumerate(row['match_keypoint_ids'])}
                    for arm in ['real', 'A0', 'B'] for row in [by_pair[j, arm]]}
            intersection = sorted(set(maps['real']) & set(maps['A0']) & set(maps['B']))
            common_valid = [a for a in intersection if all(maps[arm][a] is not None for arm in maps)]
            row = dict(target_id=j, raw_intersection_ids=intersection, common_valid_ids=common_valid,
                       raw_intersection_count=len(intersection), common_valid_count=len(common_valid),
                       common_valid_anchor_fraction=len(common_valid)/N,
                       invalid_in_any_count=len(intersection)-len(common_valid),
                       raw_intersection_coverage=coverage([kp[a].pt for a in intersection]),
                       common_valid_coverage=coverage([kp[a].pt for a in common_valid]), arms={})
            for arm in c['arms']:
                delta = np.array([maps[arm][a][2]-maps['real'][a][2] for a in common_valid], dtype=np.float64)
                row['arms'][arm] = dict(delta_generated_minus_real_px=delta.tolist(), quantiles_px=quantiles(delta),
                    positive_count=int((delta > 0).sum()), negative_count=int((delta < 0).sum()), zero_count=int((delta == 0).sum()))
            r['shared_support'].append(row)
        r['predefined_exploratory_events'] = {}
        for arm in c['arms']:
            medians = [x['arms'][arm]['quantiles_px'][1] if x['arms'][arm]['quantiles_px'] else None for x in r['shared_support']]
            event = None if any(m is None for m in medians) else all(m > 0 for m in medians)
            r['predefined_exploratory_events'][arm] = dict(all4_positive_paired_median=event, target_medians_px=medians,
                scope='conditional on common surviving anchor matches; no significance, calibrated camera error or novelty')
        r['status'] = 'COMPLETE_EXISTING_GENERATED_GEOMETRY_DIAGNOSTIC'
        r['limits'] = c['limits']
    except BaseException as exc:
        r.update(status='FAILED_PRESERVED', error=f'{type(exc).__name__}: {exc}', traceback=traceback.format_exc())
    r.update(completed_utc=utc(), elapsed_seconds=time.monotonic()-start)
    p = out / 'receipt.json'
    with p.open('x') as f:
        json.dump(r, f, indent=2, allow_nan=False)
        f.write('\n')
    p.chmod(0o444)
    print(json.dumps({k: r[k] for k in ['status', 'completed_utc', 'elapsed_seconds']}))
    return 0 if r['status'] == 'COMPLETE_EXISTING_GENERATED_GEOMETRY_DIAGNOSTIC' else 1


if __name__ == '__main__':
    raise SystemExit(main())
