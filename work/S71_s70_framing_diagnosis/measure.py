"""Exploratory SIFT displacement on all already-seen S70 output pairs."""
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


def save(p, r):
    with p.open('x') as f:
        json.dump(r, f, indent=2, allow_nan=False)
        f.write('\n')


def main():
    cbytes = (D/'CONTRACT.json').read_bytes()
    assert len(sys.argv) == 2 and sha(cbytes) == sys.argv[1]
    c = json.loads(cbytes)
    out = D/'execution_01'
    out.mkdir(exist_ok=False)
    t0 = time.monotonic()
    r = dict(started_utc=utc(), status='RUNNING', contract_sha256=sha(cbytes),
             source_sha256=sha(Path(__file__).read_bytes()), reads=[], pairs=[],
             model_calls=0, weight_bytes=0, new_method_validated=False)
    try:
        import cv2
        import numpy as np
        from PIL import Image
        assert {k:version(k) for k in c['versions']} == c['versions']
        r['versions'] = c['versions']
        cv2.setNumThreads(c['budget']['opencv_threads'])
        cv2.setRNGSeed(71)
        sift = cv2.SIFT_create(**c['sift'])
        features = {}
        for name, expected in c['source_images'].items():
            p = Path(name)
            b = p.read_bytes()
            r['reads'].append(dict(path=name, bytes=len(b), sha256=sha(b)))
            assert sha(b) == expected
            with Image.open(io.BytesIO(b)) as im:
                assert im.mode == 'RGB' and im.size == (576,576)
                rgb = np.array(im)
            gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
            kp, des = sift.detectAndCompute(gray, None)
            features[p.stem] = (kp, des)
        r['keypoint_counts'] = {k:len(v[0]) for k,v in features.items()}
        bf = cv2.BFMatcher(cv2.NORM_L2, crossCheck=False)

        def ratio_matches(a,b):
            if a is None or b is None or len(b)<2:
                return {}
            return {m.queryIdx:m.trainIdx for row in bf.knnMatch(a,b,k=2)
                    if len(row)==2 for m,n in [row] if m.distance < 0.75*n.distance}

        def summary(src,dst,mask=None):
            if mask is not None:
                src,dst = src[mask],dst[mask]
            if len(src)==0:
                return None
            delta = dst-src
            dist = np.linalg.norm(delta,axis=1)
            return dict(count=len(src), displacement_quantiles_px=np.quantile(dist,[.25,.5,.75,.95]).tolist(),
                        median_dx_dy_px=np.median(delta,axis=0).tolist(),
                        source_span_xy=np.ptp(src,axis=0).tolist(), destination_span_xy=np.ptp(dst,axis=0).tolist(),
                        source_span_xy_fraction=(np.ptp(src,axis=0)/575).tolist(),
                        destination_span_xy_fraction=(np.ptp(dst,axis=0)/575).tolist())

        for target in c['targets']:
            for label in c['pairs']:
                arm1,arm2 = label.split('_')[:2]
                if label == 'A0_A1_repeat_control':
                    arm1,arm2='A0','A1'
                k1,d1=features[f'{arm1}_target_{target}']
                k2,d2=features[f'{arm2}_target_{target}']
                forward,reverse=ratio_matches(d1,d2),ratio_matches(d2,d1)
                ids=[(i,j) for i,j in sorted(forward.items()) if reverse.get(j)==i]
                src=np.array([k1[i].pt for i,j in ids],dtype=np.float64).reshape(-1,2)
                dst=np.array([k2[j].pt for i,j in ids],dtype=np.float64).reshape(-1,2)
                item=dict(target_id=target,pair=label,source_keypoints=len(k1),destination_keypoints=len(k2),
                          mutual_match_count=len(ids),all_matches=summary(src,dst),fit_status='INSUFFICIENT_MATCHES',
                          source_xy=src.tolist(),destination_xy=dst.tolist(),match_keypoint_ids=ids)
                if len(ids)>=c['homography']['min_matches']:
                    cv2.setRNGSeed(c['homography']['opencv_seed_per_fit'])
                    H,mask=cv2.findHomography(src,dst,cv2.RANSAC,c['homography']['reprojection_threshold_px'],
                                             maxIters=c['homography']['maxIters'],confidence=c['homography']['confidence'])
                    if H is not None and mask is not None and np.isfinite(H).all():
                        h=np.column_stack([src,np.ones(len(src))])@H.T
                        finite=np.isfinite(h).all(axis=1)&(np.abs(h[:,2])>1e-12)
                        inlier=mask.ravel().astype(bool)
                        item.update(H=H.tolist(),ransac_inlier_mask=inlier.tolist(),
                                    finite_projection_mask=finite.tolist(),inlier_count=int(inlier.sum()),
                                    inlier_summary=summary(src,dst,inlier))
                        if np.all(finite[inlier]):
                            pred=h[inlier,:2]/h[inlier,2,None]
                            residual=np.linalg.norm(pred-dst[inlier],axis=1)
                            item.update(fit_status='FITTED_DESCRIPTIVE_ONLY',
                                        inlier_reprojection_residual_px=residual.tolist(),
                                        inlier_residual_median_px=float(np.median(residual)))
                        else:
                            item['fit_status']='NONFINITE_INLIER_PROJECTION'
                    else:
                        item['fit_status']='NO_FINITE_HOMOGRAPHY'
                if label=='A0_A1_repeat_control':
                    item['zero_displacement_control_pass']=bool(len(ids)>0 and np.array_equal(src,dst))
                r['pairs'].append(item)
        r['all_repeat_controls_pass']=all(x.get('zero_displacement_control_pass',True) for x in r['pairs'])
        r['status']='COMPLETE_SAVED_IMAGE_EXPLORATION' if r['all_repeat_controls_pass'] else 'COMPLETED_WITH_CONTROL_FAILURE'
        r['interpretation_limits']=c['interpretation']
    except BaseException as exc:
        r.update(status='FAILED_PRESERVED',error=f'{type(exc).__name__}: {exc}',traceback=traceback.format_exc())
    r.update(completed_utc=utc(),elapsed_seconds=time.monotonic()-t0)
    save(out/'receipt.json',r)
    (out/'receipt.json').chmod(0o444)
    print(json.dumps({k:r[k] for k in ['status','completed_utc','elapsed_seconds']}))
    return 0 if r['status']=='COMPLETE_SAVED_IMAGE_EXPLORATION' else 1


if __name__=='__main__':
    raise SystemExit(main())
