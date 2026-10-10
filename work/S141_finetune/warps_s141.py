#!/usr/bin/env python3
"""S141 variant-B inputs: the S139/S140 B2 warp (CUT3R + KPS depth of the context frames, gl/OpenCV poses, corrected
pixel-centre depth map, 1-pixel z-buffer splat, nearest fill) at each target pose, then its VMem VAE latent and the
72x72 coverage (avg-pooled valid mask), exactly as gen_s140 encodes S140 warps. CUT3R runs on the GPU here (S139/S140
ran it on CPU), so warps can differ slightly from a CPU run.
usage: warps_s141.py <data_root (scene/seq-XX/frame-*)> <clips.json> <out_dir> [SHARD=i/N env]
Writes <out_dir>/<clip_id>.npz (filled uint8 [4,576,576,3], valid bool [4,576,576]) and <clip_id>.pt (zw, cov)."""
import json, os, sys, time
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import s141_common as C
import torch
from PIL import Image
from scipy import ndimage
import modeling.pipeline as PM
from cloud_opt.dust3r_opt import init_im_poses as IIP
from utils import tensor_to_pil
import kps

D, CL, OUT = Path(sys.argv[1]), json.loads(Path(sys.argv[2]).read_text())['clips'], Path(sys.argv[3])
SI, SN = map(int, os.environ.get('SHARD', '0/1').split('/'))
OUT.mkdir(parents=True, exist_ok=True)
LOG = []; kps.install(IIP, log=LOG)
ck = str(C.WEIGHTS / 'cut3r_512_dpt_4_64.pth'); PM.add_path_to_dust3r(ck)
cut3r = PM.ARCroco3DStereo.from_pretrained(ck).to('cuda').eval()
ae = C.AutoEncoder(chunk_size=1).to('cuda', torch.float32).eval()
K = C.K7.astype(np.float64)


def to_model_grid(rgb_u8):  # geometry_baselines.to_model_grid
    t = torch.from_numpy(rgb_u8.transpose(2, 0, 1).copy()).float().unsqueeze(0) / 255.0
    t = torch.nn.functional.interpolate(t, size=(576, 768), mode='area', antialias=False)[:, :, :, 96:672]
    return np.clip(t[0].permute(1, 2, 0).numpy() * 255.0, 0, 255).astype(np.uint8)


def depth640(d):  # baselines_s139.depth640 (S137 Amendment 2 mapping)
    v0, u0 = np.mgrid[0:480, 0:640]
    x = np.round(((u0 + 0.5) * 1.2 - 96) * 512 / 576 - 0.5).astype(int); y = np.round((v0 + 0.5) * 1.2 * 512 / 576 - 64 - 0.5).astype(int)
    ok = (x >= 0) & (x < 512) & (y >= 0) & (y < 384); out = np.zeros((480, 640)); out[ok] = d[y[ok], x[ok]]; return out


def warp_both(ctx, Tt, H=480, W=640):
    """geometry_baselines.warp with SPLAT=1, also returning the pre-fill coverage (== warp_raw's mask)."""
    zbuf = np.full((H, W), np.inf); img = np.zeros((H, W, 3), np.uint8)
    v, u = np.mgrid[0:H, 0:W]; Kinv = np.linalg.inv(K)
    for rgb, depth, Tc in ctx:
        m = depth > 0
        pix = np.stack([u[m], v[m], np.ones(m.sum())], 0)
        Xw = Tc[:3, :3] @ ((Kinv @ pix) * depth[m]) + Tc[:3, 3:4]
        Xt = Tt[:3, :3].T @ (Xw - Tt[:3, 3:4])
        z = Xt[2]; ok = z > 1e-3
        uu = np.round(K[0, 0] * Xt[0, ok] / z[ok] + K[0, 2]).astype(int)
        vv = np.round(K[1, 1] * Xt[1, ok] / z[ok] + K[1, 2]).astype(int)
        col = rgb[m][ok]; zz = z[ok]
        inb = (uu >= 0) & (uu < W) & (vv >= 0) & (vv < H)
        uu, vv, col, zz = uu[inb], vv[inb], col[inb], zz[inb]
        order = np.argsort(-zz); uu, vv, col, zz = uu[order], vv[order], col[order], zz[order]
        closer = zz < zbuf[vv, uu]
        zbuf[vv[closer], uu[closer]] = zz[closer]; img[vv[closer], uu[closer]] = col[closer]
    valid = np.isfinite(zbuf)
    if valid.any() and not valid.all():
        _, (iy, ix) = ndimage.distance_transform_edt(~valid, return_indices=True)
        img = img[iy, ix]
    return img, valid


def path(ref, kind):
    sc, q, f = ref.split('/'); return D / sc / q / f'frame-{f}.{kind}'


todo = [c for k, c in enumerate(CL) if k % SN == SI]
t0 = time.time(); logf = OUT / f'WARP_LOG_{SI}of{SN}.jsonl'
for c in todo:
    fo = OUT / f"{c['id']}.pt"
    if fo.exists(): continue
    ts = time.time(); LOG.clear()
    seen = []; [seen.append(r) for r in c['ctx'] if r not in seen]
    poses = np.array([C.load_pose_path(path(r, 'pose.txt')) for r in seen], dtype=np.float32)
    pils = [tensor_to_pil(C.load_rgb_path(path(r, 'color.png'))) for r in seen]
    with torch.no_grad():
        out = PM.run_inference_from_pil(pils, cut3r, poses=poses, depths=None, lr=0.01, niter=0, device='cuda')
    ctx = [(np.asarray(Image.open(path(r, 'color.png')).convert('RGB')), depth640(d[0].detach().float().cpu().numpy()), p.astype(np.float64))
           for r, d, p in zip(seen, out['depths'], poses)]
    filled, valid = [], []
    for t in c['tgt']:
        img, val = warp_both(ctx, C.load_pose_path(path(t, 'pose.txt')).astype(np.float64))
        filled.append(to_model_grid(img))
        valid.append(to_model_grid(np.repeat(val[..., None].astype(np.uint8) * 255, 3, 2))[..., 0] > 127)
    filled = np.stack(filled); valid = np.stack(valid)
    np.savez_compressed(OUT / f"{c['id']}.npz", filled=filled, valid=valid)
    wimg = torch.from_numpy(filled.astype(np.float32) / 255. * 2 - 1).permute(0, 3, 1, 2).cuda()
    with torch.inference_mode():
        zw = ae.encode(wimg, 1).float().cpu()
    cov = torch.nn.functional.avg_pool2d(torch.from_numpy(valid.astype(np.float32))[:, None], 8)[:, 0]
    torch.save({'zw': zw, 'cov': cov}, fo.with_suffix('.tmp')); fo.with_suffix('.tmp').rename(fo)
    rec = {'id': c['id'], 'n_ctx_unique': len(seen), 'coverage': float(valid.mean()), 'kps': [dict(l) for l in LOG],
           'seconds': round(time.time() - ts, 2)}
    with logf.open('a') as fh: fh.write(json.dumps(rec, default=float) + '\n')
    print(f"[warp] {c['id']} cov {rec['coverage']:.3f} kps {[l.get('kps') for l in LOG]} {rec['seconds']}s", flush=True)
print('[warp] done', len(todo), round(time.time() - t0, 1))
