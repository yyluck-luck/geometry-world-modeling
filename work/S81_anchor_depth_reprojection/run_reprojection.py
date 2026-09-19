#!/usr/bin/env python3
"""Frozen, one-shot source sensor Z diagnostic; no model or RGB reads."""
import argparse
import csv
import hashlib
import io
import json
from pathlib import Path
import resource
import signal
import time
import traceback
from datetime import datetime, timezone
from importlib.metadata import version

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent


def utc():
    return datetime.now(timezone.utc).isoformat()


def sha(b):
    return hashlib.sha256(b).hexdigest()


def dump(path, obj):
    with path.open('x') as f:
        json.dump(obj, f, ensure_ascii=False, indent=2, allow_nan=False)
        f.write('\n')


def quant(a):
    a = np.asarray(a, dtype=np.float64)
    a = a[np.isfinite(a)]
    return np.quantile(a, [.25, .5, .75, .95], method='linear').tolist() if len(a) else None


def sample(x, depth):
    """Nominal old-K inverse map; no clipping, interpolation, or fallback."""
    native = (x + np.array([96., 0.])) / 1.2
    finite = np.isfinite(native).all(1)
    index = np.full(x.shape, -1, dtype=np.int64)
    index[finite] = np.floor(native[finite] + .5).astype(np.int64)
    domain = finite & (native[:, 0] >= 0) & (native[:, 0] <= 639)
    domain &= (native[:, 1] >= 0) & (native[:, 1] <= 479)
    domain &= (index[:, 0] >= 0) & (index[:, 0] < 640)
    domain &= (index[:, 1] >= 0) & (index[:, 1] < 480)
    raw = np.full(len(x), -1, dtype=np.int64)
    raw[domain] = depth[index[domain, 1], index[domain, 0]]
    valid = domain & (raw > 0)
    z = np.full(len(x), np.nan)
    z[valid] = raw[valid] / 5000.
    reason = np.where(domain, np.where(raw > 0, 'VALID', 'ZERO_DEPTH'), 'SOURCE_OUTSIDE')
    return native, index, raw, z, valid, reason


def project(x, z, K, Cs, Ct, epsilon):
    rays = np.column_stack([x, np.ones(len(x))]) @ np.linalg.inv(K).T
    source = rays * z[:, None]
    R = Ct[:3, :3].T @ Cs[:3, :3]
    t = Ct[:3, :3].T @ (Cs[:3, 3] - Ct[:3, 3])
    target = source @ R.T + t
    valid = np.isfinite(target).all(1) & (target[:, 2] > epsilon)
    expected = np.full(x.shape, np.nan)
    p = target[valid] @ K.T
    expected[valid] = p[:, :2] / p[:, 2:]
    valid &= np.isfinite(expected).all(1)
    fov = valid & (expected[:, 0] >= 0) & (expected[:, 0] <= 575)
    fov &= (expected[:, 1] >= 0) & (expected[:, 1] <= 575)
    return expected, target[:, 2], valid, fov


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--contract-sha', required=True)
    p.add_argument('--source-sha', required=True)
    args = p.parse_args()
    cb = (HERE/'CONTRACT.json').read_bytes()
    assert sha(cb) == args.contract_sha
    assert sha(Path(__file__).read_bytes()) == args.source_sha
    c = json.loads(cb)
    out = HERE/'execution_01'
    out.mkdir(exist_ok=False)
    (out/'pairs').mkdir()
    started = time.monotonic()
    receipt = dict(started_utc=utc(), status='RUNNING', contract_sha256=sha(cb),
                   source_sha256=args.source_sha, reads=[], depth_decodes=0,
                   model_calls=0, rgb_decodes=0, new_method_validated=False)

    def read(spec):
        b = Path(spec['path']).read_bytes()
        h = sha(b)
        receipt['reads'].append(dict(path=spec['path'], bytes=len(b), sha256=h))
        assert h == spec['sha256'] and len(b) == spec['bytes'], spec['path']
        return b

    def load(spec, fields):
        with np.load(io.BytesIO(read(spec)), allow_pickle=False) as a:
            return {k:a[k].copy() for k in fields}

    def stop(signum, frame):
        raise TimeoutError('Frozen 60 second compute wall budget reached')

    signal.signal(signal.SIGALRM, stop)
    signal.alarm(c['wall_seconds'])
    try:
        receipt['versions'] = {k:version(k) for k in c['versions']}
        assert receipt['versions'] == c['versions']
        rows = json.loads(read(c['rows']))
        assert [r['row_id'] for r in rows] == c['row_order']
        assert len(rows) == 24 and sum(r['M'] for r in rows) == 7757
        geom = json.loads(read(c['geometry_receipt']))
        K = np.array(geom['K_pixels_576'], dtype=np.float64)
        cams = load(c['cameras'], ['ids', 'c2ws'])
        C = dict(zip(cams['ids'].tolist(), cams['c2ws']))
        for k in [19, 20, 21, 22, 23]:
            assert np.array_equal(C[k], np.array(geom['optical_c2ws_used'][str(k)]))
        f = load(c['source_features'], ['keypoints', 'image_size'])
        x = f['keypoints'].astype(np.float64)
        assert x.shape == (1313, 2) and np.isfinite(x).all()
        assert f['image_size'].tolist() == [576, 576]
        b = read(c['depth'])
        assert b[:8] == b'\x89PNG\r\n\x1a\n' and b[24:26] == bytes([16, 0])
        with Image.open(io.BytesIO(b)) as im:
            assert im.size == (640, 480)
            depth = np.array(im)
        receipt['depth_decodes'] += 1
        assert depth.dtype.kind in 'ui' and depth.shape == (480, 640)
        assert depth.min() >= 0 and depth.max() <= 65535
        native, index, raw, z, dv, reason = sample(x, depth)
        np.savez(out/'SOURCE_SAMPLES.npz', source_xy=x, native_xy=native,
                 sample_xy=index, raw_depth=raw, z_m=z, depth_valid=dv, reason=reason)
        expected = {}
        source_projection = []
        for j in [20,21,22,23]:
            e, tz, valid, fov = project(x,z,K,C[19],C[j],c['z_epsilon_m'])
            assert np.all(~valid | dv)
            expected[j] = (e,tz,valid,fov)
            np.savez(out/f'ALL_SOURCE_TO_{j}.npz', expected_xy=e,target_z_m=tz,
                     valid=valid,in_fov=fov)
            source_projection.append(dict(target_id=j,N=1313,depth_valid=int(dv.sum()),
                                          projected=int(valid.sum()),in_fov=int(fov.sum())))
        summaries, cache, records = [], {}, []
        for row in rows:
            a=load(row['saved'], ['accepted_indices','source_xy','target_xy','correct_F','correct_residuals'])
            ids=a['accepted_indices']; s=ids[:,0]; y=a['target_xy']
            assert ids.shape==(row['M'],2) and len(set(s.tolist()))==len(s)
            assert np.array_equal(x[s],a['source_xy'])
            all_e,all_tz,all_v,all_fov=expected[row['target_id']]
            e,tz,v,fov=all_e[s],all_tz[s],all_v[s],all_fov[s]
            assert np.isfinite(y).all()
            error=np.full(len(s),np.nan)
            error[v]=np.linalg.norm(y[v]-e[v],axis=1)
            lines=np.column_stack([x[s],np.ones(len(s))])@a['correct_F'].T
            norm=np.linalg.norm(lines[:,:2],axis=1)
            lv=np.isfinite(norm)&(norm>c['line_epsilon'])
            checks=v&lv
            plane=np.full(len(s),np.nan)
            plane[checks]=np.abs((np.column_stack([e[checks],np.ones(checks.sum())])*lines[checks]).sum(1))/norm[checks]
            dt=a['correct_residuals'][:,0]
            assert np.all(plane[checks]<=c['identity_atol_px'])
            assert np.all(error[checks]+c['identity_atol_px']>=dt[checks])
            direction=np.column_stack([-lines[:,1],lines[:,0]])
            along=np.full(len(s),np.nan)
            along[checks]=np.sum((y[checks]-e[checks])*direction[checks],axis=1)/norm[checks]
            reasons=reason[s].astype('<U32')
            reasons[dv[s]&~v]='INVALID_PROJECTION'
            reasons[v&~fov]='VALID_OUT_OF_VIEW'
            np.savez(out/'pairs'/f"{row['row_id']}.npz", accepted_indices=ids,
                     expected_xy=e,target_xy=y,target_z_m=tz,valid=v,in_fov=fov,
                     error_px=error,along_line_signed_px=along,depth_valid=dv[s],
                     target_line_px=dt,expected_line_px=plane,reason=reasons)
            n=len(s);nv=int(v.sum())
            counts={str(t):int(np.count_nonzero(error[v]<=t)) for t in c['thresholds_px']}
            summary=dict(row_id=row['row_id'],target_id=row['target_id'],arm=row['arm'],
                         matcher=row['matcher'],N=1313,M=n,unmatched_N=1313-n,
                         depth_valid=int(dv[s].sum()),V=nv,in_fov=int(fov.sum()),
                         out_of_view=int((v&~fov).sum()),V_over_M=nv/n,V_over_N=nv/1313,
                         invalid_reasons={str(q):int(((reasons==q)&~v).sum()) for q in np.unique(reasons[~v])},
                         error_q25_q50_q75_q95_px=quant(error), in_fov_error_quantiles_px=quant(error[fov]),
                         abs_along_line_quantiles_px=quant(abs(along)),counts_le_px=counts,
                         fractions_le_valid={t:k/nv if nv else None for t,k in counts.items()},
                         fractions_le_M={t:k/n for t,k in counts.items()},
                         fractions_le_N={t:k/1313 for t,k in counts.items()},
                         max_expected_to_epiline_px=float(np.max(plane[checks])) if checks.any() else None,
                         visibility_status='UNKNOWN')
            summaries.append(summary)
            cache[row['row_id']]={int(si):(int(ti),float(er)) for (si,ti),er in zip(ids,error)}
            for k,(si,ti) in enumerate(ids):
                def number(value):
                    return float(value) if np.isfinite(value) else ''
                records.append(dict(row_id=row['row_id'],match_row=k,source_id=int(si),target_id=int(ti),
                    raw_depth=int(raw[si]),sample_x=int(index[si,0]),sample_y=int(index[si,1]),
                    expected_x=number(e[k,0]),expected_y=number(e[k,1]),matched_x=float(y[k,0]),matched_y=float(y[k,1]),
                    target_z_m=number(tz[k]),valid=bool(v[k]),in_fov=bool(fov[k]),error_px=number(error[k]),
                    along_line_px=number(along[k]),status=str(reasons[k]),visibility='UNKNOWN'))
        assert len(records)==7757
        paired=[]
        for j in [20,21,22,23]:
            comparisons=[(f't{j}_real_{m}',f't{j}_{a}_{m}') for m in ['BF','LG'] for a in ['A0','B']]
            comparisons += [(f't{j}_{a}_BF',f't{j}_{a}_LG') for a in ['real','A0','B']]
            for left,right in comparisons:
                ca,cb=cache[left],cache[right];shared=sorted(ca.keys()&cb.keys())
                vals=[dict(source_id=s,left_target_feature_id=ca[s][0],right_target_feature_id=cb[s][0],
                      difference_right_minus_left_px=cb[s][1]-ca[s][1] if np.isfinite([ca[s][1],cb[s][1]]).all() else None) for s in shared]
                if left.endswith('BF') and right.endswith('LG'):
                    for s in shared:
                        if ca[s][0]==cb[s][0]:
                            assert (np.isnan(ca[s][1]) and np.isnan(cb[s][1])) or ca[s][1]==cb[s][1]
                good=[v['difference_right_minus_left_px'] for v in vals if v['difference_right_minus_left_px'] is not None]
                paired.append(dict(left=left,right=right,shared_sources=len(shared),valid_pairs=len(good),
                                   differences_quantiles_px=quant(good),records=vals))
        dump(out/'ROWS.json',summaries);dump(out/'PAIRED.json',paired)
        dump(out/'SOURCE_PROJECTION_COUNTS.json',source_projection)
        with (out/'ALL_RECORDS.csv').open('x') as f:
            w=csv.DictWriter(f,fieldnames=list(records[0]));w.writeheader();w.writerows(records)
        receipt.update(status='COMPLETED_DESCRIPTIVE_ONLY',row_count=24,accepted_records=7757,
                       all_source_count=1313,source_depth_valid=int(dv.sum()),paired_count=len(paired))
    except BaseException as e:
        receipt.update(status='FAILED',exception=repr(e),traceback=traceback.format_exc())
        raise
    finally:
        signal.alarm(0)
        receipt.update(completed_utc=utc(),wall_seconds=time.monotonic()-started,
                       ru_maxrss_bytes_macos=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
        dump(out/'RECEIPT.json',receipt)
        manifest=[dict(path=str(f),bytes=f.stat().st_size,sha256=sha(f.read_bytes())) for f in sorted(out.rglob('*')) if f.is_file()]
        dump(out/'OUTPUT_MANIFEST.json',manifest)


if __name__=='__main__':
    main()
