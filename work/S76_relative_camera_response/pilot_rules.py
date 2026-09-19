"""S76 source-only draft rules. No file reads, model calls or experiment runner."""
from __future__ import annotations
import hashlib
import json
import math
import random

YAW_DEGREES = 5.0
TARGET_IDS = [20, 21, 22, 23]
ORDERED_IDS = [19, 18, 13, 12, 20, 21, 22, 23]
QUANTILES = [.25, .5, .75, .95]
EPS = 1e-12
SIZE = 576


def require(ok, message):
    if not ok:
        raise RuntimeError(message)


def canonical_sha(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                    allow_nan=False).encode()).hexdigest()


def tuple_tree(value):
    return tuple(tuple_tree(x) for x in value) if isinstance(value, list) else value


def restore_common_rng(state, expected_canonical_sha, np, torch, capture_json):
    """Caller verifies file SHA first. Restore pre-do_sample state, not sampler-entry."""
    require(canonical_sha(state) == expected_canonical_sha, 'Saved common RNG state differs')
    require(set(state) == {'python','numpy','torch_cpu'}, 'Unexpected common RNG keys')
    n = state['numpy']
    require(n['engine'] == 'MT19937' and len(n['keys']) == 624, 'Unexpected NumPy engine')
    require(all(type(x) is int and 0 <= x <= 2**32-1 for x in n['keys']), 'Invalid NumPy keys')
    require(all(type(x) is int and 0 <= x <= 255 for x in state['torch_cpu']), 'Invalid Torch state')
    random.setstate(tuple_tree(state['python']))
    np.random.set_state((n['engine'], np.array(n['keys'],dtype=np.uint32),
                         n['position'],n['has_gauss'],n['cached_gaussian']))
    torch.set_rng_state(torch.tensor(state['torch_cpu'],dtype=torch.uint8,device='cpu'))
    require(canonical_sha(capture_json()) == expected_canonical_sha, 'Restored RNG differs')


def target_local_yaw(old_optical, ordered_ids, torch):
    """Right-handed +5 deg about each target's local optical +y (image down) axis."""
    require(ordered_ids == ORDERED_IDS, 'Unexpected source/target slot order')
    require(old_optical.shape == (8,4,4) and old_optical.dtype == torch.float32
            and old_optical.device.type == 'cpu' and bool(torch.isfinite(old_optical).all()),
            'Expected accepted optical FP32 cameras')
    a = math.radians(YAW_DEGREES); c,s = math.cos(a),math.sin(a)
    Q = torch.tensor([[c,0,s],[0,1,0],[-s,0,c]],dtype=torch.float32)
    new = old_optical.clone()
    new[4:,:3,:3] = old_optical[4:,:3,:3] @ Q
    require(torch.equal(new[:4],old_optical[:4]) and torch.equal(new[:,:3,3],old_optical[:,:3,3])
            and torch.equal(new[:,3,:],old_optical[:,3,:]), 'Unexpected history/center/homogeneous change')
    return new,Q


def project(points, H, np):
    """Old pixel coordinates -> new pixel coordinates; positive depth only."""
    points=np.asarray(points,dtype=np.float64).reshape(-1,2)
    homogeneous=np.column_stack([points,np.ones(len(points))]) @ H.T
    valid=np.isfinite(homogeneous).all(axis=1) & (homogeneous[:,2] > EPS)
    output=np.full((len(points),2),np.nan,dtype=np.float64)
    output[valid]=homogeneous[valid,:2]/homogeneous[valid,2,None]
    return output,valid


def in_frame(points,np):
    return np.isfinite(points).all(axis=1) & (points[:,0] >= 0) & (points[:,0] <= SIZE-1) \
           & (points[:,1] >= 0) & (points[:,1] <= SIZE-1)


def prescribed_homographies(old_optical,new_optical,K,np):
    """Use actual FP32 consumer rotations cast to FP64; no fitted correction."""
    old=np.asarray(old_optical,dtype=np.float64)
    new=np.asarray(new_optical,dtype=np.float64); K=np.asarray(K,dtype=np.float64)
    require(old.shape == new.shape == (8,4,4) and K.shape == (8,3,3), 'Camera/K shape differs')
    output=[]
    for slot in range(4,8):
        H=K[slot] @ new[slot,:3,:3].T @ old[slot,:3,:3] @ np.linalg.inv(K[slot])
        require(np.isfinite(H).all() and abs(np.linalg.det(H)) > EPS,'Invalid fixed homography')
        output.append(H)
    return output


def common_fov_masks(H,np):
    """Fixed geometric visibility on all pixel-center integer coordinates, before images."""
    yy,xx=np.mgrid[0:SIZE,0:SIZE]
    points=np.column_stack([xx.reshape(-1),yy.reshape(-1)]).astype(np.float64)
    mapped,valid=project(points,H,np)
    old_mask=(valid & in_frame(mapped,np)).reshape(SIZE,SIZE)
    inverse=np.linalg.inv(H)
    mapped_back,valid_back=project(points,inverse,np)
    new_mask=(valid_back & in_frame(mapped_back,np)).reshape(SIZE,SIZE)
    return old_mask,new_mask


def score_same_matches(source_xy,new_xy,H,np):
    """Every mutual descriptor match retained; common-FOV is a declared secondary restriction."""
    x=np.asarray(source_xy,dtype=np.float64).reshape(-1,2)
    y=np.asarray(new_xy,dtype=np.float64).reshape(-1,2)
    require(x.shape == y.shape,'Match length differs')
    mapped,valid=project(x,H,np)
    back,valid_back=project(y,np.linalg.inv(H),np)
    valid &= np.isfinite(x).all(axis=1) & np.isfinite(y).all(axis=1)
    common=valid & valid_back & in_frame(x,np) & in_frame(y,np) & in_frame(mapped,np) & in_frame(back,np)
    identity=np.full(len(x),np.nan); prescribed=np.full(len(x),np.nan)
    identity[valid]=np.linalg.norm(y[valid]-x[valid],axis=1)
    prescribed[valid]=np.linalg.norm(y[valid]-mapped[valid],axis=1)
    advantage=identity-prescribed

    def describe(mask):
        if not np.any(mask):
            return dict(count=0,identity_quantiles_px=None,H_quantiles_px=None,
                        paired_identity_minus_H_quantiles_px=None,identity_maximum_px=None,
                        H_maximum_px=None,paired_identity_minus_H_maximum_px=None,
                        positive_count=0,negative_count=0,zero_count=0)
        return dict(count=int(mask.sum()),identity_quantiles_px=np.quantile(identity[mask],QUANTILES).tolist(),
                    H_quantiles_px=np.quantile(prescribed[mask],QUANTILES).tolist(),
                    paired_identity_minus_H_quantiles_px=np.quantile(advantage[mask],QUANTILES).tolist(),
                    identity_maximum_px=float(identity[mask].max()),H_maximum_px=float(prescribed[mask].max()),
                    paired_identity_minus_H_maximum_px=float(advantage[mask].max()),
                    positive_count=int((advantage[mask]>0).sum()),negative_count=int((advantage[mask]<0).sum()),
                    zero_count=int((advantage[mask]==0).sum()))
    def finite_coordinates(a):
        return [float(v) if np.isfinite(v) else None for v in a]
    rows=[dict(index=i,source_xy=finite_coordinates(x[i]),new_xy=finite_coordinates(y[i]),valid=bool(valid[i]),
               common_fov=bool(common[i]),identity_error_px=float(identity[i]) if valid[i] else None,
               H_error_px=float(prescribed[i]) if valid[i] else None,
               paired_identity_minus_H_px=float(advantage[i]) if valid[i] else None) for i in range(len(x))]
    return dict(match_count=len(x),invalid_count=int((~valid).sum()),outside_common_fov_count=int((valid & ~common).sum()),
                all_valid_matches=describe(valid),common_fov_matches=describe(common),rows=rows)


if __name__ == '__main__':
    import sys
    if sys.argv[1:] != ['--compile-only']:
        raise SystemExit('Source-only rules: a reviewed bound single-arm runner and scorer are still required.')
    from pathlib import Path
    compile(Path(__file__).read_bytes(),__file__,'exec')
    print('COMPILE_ONLY_NO_PAYLOAD_OR_MODEL_RUN')
