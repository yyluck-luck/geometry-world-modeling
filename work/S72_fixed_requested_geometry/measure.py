"""Fixed known-geometry diagnostic on four already-seen real image pairs."""
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
    out = D / 'execution_01'
    out.mkdir(exist_ok=False)
    start = time.monotonic()
    r = dict(started_utc=utc(), status='RUNNING', contract_sha256=sha(cb),
             source_sha256=sha(Path(__file__).read_bytes()), reads=[], pairs=[],
             model_calls=0, weight_bytes=0, new_method_validated=False)

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
        for path, h in c['source_metadata'].items():
            metadata = json.loads(read(dict(path=path, sha256=h), 'metadata'))
            assert all('rgbd_dataset_freiburg2_desk/rgb/' in v['rgb_path_metadata_only']
                       for v in metadata['records'])
        with np.load(io.BytesIO(read(c['camera_archive'], 'camera_archive')), allow_pickle=False) as z:
            ids, cameras = z['ids'].copy(), z['c2ws'].copy()
        assert ids.tolist() == [12, 13, 14, 18, 19, 20, 21, 22, 23]
        assert cameras.shape == (9, 4, 4) and cameras.dtype == np.float64
        assert np.isfinite(cameras).all()
        poses = dict(zip(ids.tolist(), cameras))
        with np.load(io.BytesIO(read(c['anchor_K_cache'], 'saved_cache_K_only')), allow_pickle=False) as z:
            K = z[c['anchor_K_cache']['field']].astype(np.float64)
        assert K.shape == (3, 3) and np.isfinite(K).all()
        Ki = np.linalg.inv(K)
        r['K_pixels_576'] = K.tolist()
        r['optical_c2ws_used'] = {str(i): poses[i].tolist() for i in [19, 20, 21, 22, 23]}
        sift = cv2.SIFT_create(**c['sift'])

        def features(item, anchor=False):
            with Image.open(io.BytesIO(read(item, 'RGB_PNG'))) as im:
                assert im.mode == 'RGB' and im.size == ((640, 480) if anchor else (576, 576))
                rgb = np.array(im)
            if anchor:
                rgb = cv2.resize(rgb, (768, 576), interpolation=cv2.INTER_AREA)[:, 96:672]
            kp, des = sift.detectAndCompute(cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY), None)
            return kp, des

        bf = cv2.BFMatcher(cv2.NORM_L2, crossCheck=False)

        def ratio(a, b):
            if a is None or b is None or len(b) < 2:
                return {}
            return {m.queryIdx: m.trainIdx for row in bf.knnMatch(a, b, k=2)
                    if len(row) == 2 for m, n in [row] if m.distance < .75 * n.distance}

        def coverage(x):
            if len(x) == 0:
                return dict(span_xy_fraction=None, occupied_4x4_cells=0)
            cells = np.clip(np.floor(x / 144), 0, 3).astype(int)
            return dict(span_xy_fraction=(np.ptp(x, axis=0) / 575).tolist(),
                        occupied_4x4_cells=len(set(map(tuple, cells.tolist()))))

        k0, d0 = features(c['anchor'], True)
        r['anchor_keypoints'] = len(k0)
        C0 = poses[19]
        for text_id, image in c['targets'].items():
            j = int(text_id)
            kj, dj = features(image)
            a, b = ratio(d0, dj), ratio(dj, d0)
            matches = [(i, k) for i, k in sorted(a.items()) if b.get(k) == i]
            x = np.array([k0[i].pt for i, k in matches], dtype=np.float64).reshape(-1, 2)
            y = np.array([kj[k].pt for i, k in matches], dtype=np.float64).reshape(-1, 2)
            Cj = poses[j]
            R = Cj[:3, :3].T @ C0[:3, :3]
            t = Cj[:3, :3].T @ (C0[:3, 3] - Cj[:3, 3])
            tx, ty, tz = t
            skew = np.array([[0., -tz, ty], [tz, 0., -tx], [-ty, tx, 0.]])
            Fraw = Ki.T @ skew @ R @ Ki
            scale = float(np.linalg.norm(Fraw))
            baseline = float(np.linalg.norm(t))
            row = dict(target_id=j, pair='real19_real_target', match_count=len(matches),
                       target_keypoints=len(kj), match_keypoint_ids=matches,
                       source_xy=x.tolist(), target_xy=y.tolist(),
                       source_coverage=coverage(x), target_coverage=coverage(y),
                       R_target_from_source=R.tolist(), t_target_from_source_m=t.tolist(),
                       baseline_m=baseline, Fraw=Fraw.tolist(), Fraw_norm=scale)
            if baseline <= c['baseline_insufficient_m'] or not np.isfinite(scale) or scale <= 0:
                row['status'] = 'INSUFFICIENT_BASELINE'
            elif len(matches) == 0:
                row['status'] = 'NO_MATCHES'
            else:
                F = Fraw / scale
                xh, yh = np.column_stack([x, np.ones(len(x))]), np.column_stack([y, np.ones(len(y))])
                target_lines, source_lines = xh @ F.T, yh @ F
                nt, ns = np.linalg.norm(target_lines[:, :2], axis=1), np.linalg.norm(source_lines[:, :2], axis=1)
                signed = np.sum(yh * target_lines, axis=1)
                valid = np.isfinite(nt) & np.isfinite(ns) & np.isfinite(signed)
                valid &= (nt > c['line_normal_epsilon']) & (ns > c['line_normal_epsilon'])
                dt, ds = np.abs(signed[valid]) / nt[valid], np.abs(signed[valid]) / ns[valid]
                symmetric = (dt + ds) / 2
                residuals, vi = [], 0
                for good in valid:
                    residuals.append([float(dt[vi]), float(ds[vi]), float(symmetric[vi])] if good else None)
                    vi += int(good)
                row.update(F_unit_frobenius=F.tolist(), valid_line_mask=valid.tolist(),
                           residual_columns=['to_target_px', 'to_source_px', 'symmetric_mean_px'],
                           residuals=residuals, valid_count=int(valid.sum()), invalid_count=int((~valid).sum()),
                           status='COMPUTED_DESCRIPTIVE_ONLY' if valid.any() else 'INSUFFICIENT_VALID_LINES',
                           residual_quantiles_px=np.quantile(symmetric, [.25, .5, .75, .95]).tolist() if len(symmetric) else None,
                           fractions_below_px={str(q): float(np.mean(symmetric <= q)) if len(symmetric) else None for q in [2, 5, 10]},
                           fraction_denominator='valid lines; invalid counts separately retained')
            r['pairs'].append(row)
        r['status'] = 'COMPLETE_REAL_CONTROL_DIAGNOSTIC'
        r['limits'] = c['limits']
    except BaseException as exc:
        r.update(status='FAILED_PRESERVED', error=f'{type(exc).__name__}: {exc}', traceback=traceback.format_exc())
    r.update(completed_utc=utc(), elapsed_seconds=time.monotonic() - start)
    p = out / 'receipt.json'
    with p.open('x') as f:
        json.dump(r, f, indent=2, allow_nan=False)
        f.write('\n')
    p.chmod(0o444)
    print(json.dumps({k: r[k] for k in ['status', 'completed_utc', 'elapsed_seconds']}))
    return 0 if r['status'] == 'COMPLETE_REAL_CONTROL_DIAGNOSTIC' else 1


if __name__ == '__main__':
    raise SystemExit(main())
