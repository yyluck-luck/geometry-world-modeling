#!/usr/bin/env python3
"""S141 exploratory output diagnostics (after all verdicts; changes none). For chess mem_vmem contexts, per window & seed
(3-6), for base_mem / A_mem / B_mem and the B2 warp: mean signed RGB error vs target (brightness/colour bias), full PSNR,
low-pass PSNR (Gaussian sigma 4 px on both images), high-pass energy ratio (output vs target), PSNR to the warp.
usage: diag_outputs_s141.py <s139_gen_dir> <chess_A_dir> <chess_B_dir> <data_root> <plan_eval_B.json> <warp_dir> <out.json>"""
import io, json, math, sys
from pathlib import Path
import numpy as np, torch
from PIL import Image
G139, GA, GB, DS, PB, WD, OUT = [Path(a) for a in sys.argv[1:8]]
plan = json.loads(PB.read_text())['contexts']
def ref_grid(p):
    rgb = np.asarray(Image.open(io.BytesIO(p.read_bytes())).convert('RGB'), dtype=np.uint8)
    t = torch.from_numpy(rgb.transpose(2, 0, 1).copy()).float().unsqueeze(0) / 255.0
    t = torch.nn.functional.interpolate(t, size=(576, 768), mode='area', antialias=False)[:, :, :, 96:672]
    return np.clip(t[0].permute(1, 2, 0).numpy() * 255.0, 0, 255).astype(np.uint8)
def pred_u8(fr):
    im = fr.transpose(1, 2, 0); im = (im + 1.0) / 2.0 if float(im.min()) < -0.1 else im
    return np.clip(im * 255.0, 0, 255).astype(np.uint8)
g = torch.exp(-((torch.arange(25) - 12.0) ** 2) / (2 * 4.0 ** 2)); g = (g / g.sum())
def blur(x):  # (H,W,3) uint8 -> float
    t = torch.from_numpy(x.astype(np.float32)).permute(2, 0, 1)[:, None]
    t = torch.nn.functional.conv2d(torch.nn.functional.pad(t, (12, 12, 0, 0), mode='reflect'), g.view(1, 1, 1, 25))
    t = torch.nn.functional.conv2d(torch.nn.functional.pad(t, (0, 0, 12, 12), mode='reflect'), g.view(1, 1, 25, 1))
    return t[:, 0].permute(1, 2, 0).numpy()
def psnr(a, b): m = ((a.astype(np.float64) - b.astype(np.float64)) ** 2).mean(); return 10 * math.log10(255 ** 2 / m)
rows = {k: [] for k in ('base_mem', 'A_mem', 'B_mem', 'warp')}
for c in plan:
    refs = [ref_grid(DS / 'chess' / r.split('/')[0] / f"frame-{r.split('/')[1]}.color.png") for r in c['target_refs']]
    warps = [np.load(WD / f)['filled'] for f in c['warp_files']]
    base_key = c['base_ctx_key']
    for s in (3, 4, 5, 6):
        outs = {'base_mem': np.load(G139 / f'{base_key}__s{s}.npy'), 'A_mem': np.load(GA / f'{base_key}__A_mem__s{s}.npy'),
                'B_mem': np.load(GB / f'{base_key}__B_mem__s{s}.npy')}
        for name in ('base_mem', 'A_mem', 'B_mem', 'warp'):
            ims = warps if name == 'warp' else [pred_u8(f) for f in outs[name]]
            bias = float(np.mean([(p.astype(np.float64) - r).mean() for p, r in zip(ims, refs)]))
            full = float(np.mean([psnr(p, r) for p, r in zip(ims, refs)]))
            low = float(np.mean([psnr(blur(p), blur(r)) for p, r in zip(ims, refs)]))
            hp = float(np.mean([np.abs(p.astype(np.float32) - blur(p)).mean() / max(np.abs(r.astype(np.float32) - blur(r)).mean(), 1e-6) for p, r in zip(ims, refs)]))
            tow = float(np.mean([psnr(p, w) for p, w in zip(ims, warps)]))
            rows[name].append({'window_id': c['window_id'], 'seed': s, 'bias': bias, 'psnr_full': full, 'psnr_lowpass': low, 'highpass_ratio': hp, 'psnr_to_warp': tow})
        if name == 'warp' and s > 3: rows['warp'] = rows['warp'][:-1]   # warp is deterministic: keep one row per window
    print(c['window_id'], {k: round(np.mean([r['psnr_full'] for r in v]), 2) for k, v in rows.items()}, flush=True)
summ = {k: {m: float(np.mean([r[m] for r in v])) for m in ('bias', 'psnr_full', 'psnr_lowpass', 'highpass_ratio', 'psnr_to_warp')} for k, v in rows.items()}
OUT.write_text(json.dumps({'schema': 's141-output-diagnostics-v1', 'note': 'exploratory, after verdicts', 'summary': summ, 'rows': rows}, indent=1) + '\n')
print(json.dumps(summ, indent=1))
