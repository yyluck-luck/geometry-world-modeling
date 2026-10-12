"""Frozen P1 CPU cross-pair residual policy. All outputs are new artifacts."""
import argparse
import hashlib
import itertools
import json
import math
import os
from pathlib import Path
import platform
import time

import numpy as np
from PIL import Image
import scipy
from scipy.ndimage import gaussian_filter, median_filter
import torch

CONTROLS = ['W', 'G', 'constant', 'region', 'bands', 'covered_G',
            'lowW_highG', 'lowG_highW', 'smoothW', 'medianW', 'smoothG']
METHODS = CONTROLS + ['candidate']
ROOT = Path('/mnt/gluster_dcpu/yiyangliu/gwm_s134')
GEN = ROOT / 'out/s140_confirm_tacc/gen'
WARP = ROOT / 'data/S140_warps_chess'
DS = ROOT / 'data/s139_datasets'


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda: f.read(1048576), b''):
            h.update(chunk)
    return h.hexdigest()


def save(path, obj):
    path = Path(path)
    assert not path.exists(), f'Refusing overwrite: {path}'
    path.write_text(json.dumps(obj, indent=2, allow_nan=False) + '\n')


def box_solve(q, b):
    """Global solution of a small convex quadratic over [0,1]^d."""
    d = len(b)
    best = None
    for state in itertools.product((-1, 0, 1), repeat=d):
        free = np.flatnonzero(np.array(state) == -1)
        fixed = np.flatnonzero(np.array(state) != -1)
        a = np.array([max(0, x) for x in state], dtype=np.float64)
        if len(free):
            rhs = b[free] - q[np.ix_(free, fixed)] @ a[fixed]
            sol = np.linalg.lstsq(q[np.ix_(free, free)], rhs, rcond=1e-12)[0]
            if np.max(np.abs(q[np.ix_(free, free)] @ sol - rhs)) > 1e-9:
                continue
            if np.any(sol < -1e-10) or np.any(sol > 1 + 1e-10):
                continue
            a[free] = np.clip(sol, 0, 1)
        value = float(a @ q @ a - 2 * a @ b)
        if best is None or value < best[0] - 1e-15:
            best = (value, a)
    assert best is not None
    a = best[1]
    grad = q @ a - b
    kkt = max(float(np.max(np.abs(grad[(a > 1e-8) & (a < 1 - 1e-8)]), initial=0)),
              float(np.max(-grad[a <= 1e-8], initial=0)),
              float(np.max(grad[a >= 1 - 1e-8], initial=0)))
    assert kkt < 1e-8, ('KKT failure', kkt)
    return a


def mapping(name):
    if name == 'constant':
        return np.ones((6, 1))
    if name == 'region':
        return np.repeat(np.eye(2), 3, axis=0)
    if name == 'bands':
        return np.vstack([np.eye(3), np.eye(3)])
    assert name == 'candidate'
    return np.eye(6)


def ref_grid(path):
    rgb = np.asarray(Image.open(path).convert('RGB'), dtype=np.uint8)
    t = torch.from_numpy(rgb.transpose(2, 0, 1).copy()).float()[None] / 255.0
    t = torch.nn.functional.interpolate(t, size=(576, 768), mode='area',
                                        antialias=False)[:, :, :, 96:672]
    return np.clip(t[0].permute(1, 2, 0).numpy() * 255.0, 0, 255).astype(np.uint8)


def target(c):
    frames = []
    for ref in c['target_refs']:
        sq, fr = ref.split('/')
        frames.append(ref_grid(DS / c['scene_dir'] / sq / f'frame-{fr}.color.png'))
    return np.stack(frames)


def inputs(c, seed):
    arr = np.load(GEN / f"{c['ctx_key']}__s{seed}.npy", allow_pickle=False)
    assert arr.shape == (4, 3, 576, 576) and np.isfinite(arr).all()
    gs = []
    for fr in arr:
        im = fr.transpose(1, 2, 0)
        if float(im.min()) < -0.1:
            im = (im + 1.0) / 2.0
        gs.append(np.clip(im * 255.0, 0, 255).astype(np.uint8))
    ws, ms = [], []
    for name in c['warp_files']:
        with np.load(WARP / name, allow_pickle=False) as z:
            ws.append(z['filled'])
            assert z['valid'].dtype == np.bool_
            ms.append(z['valid'])
    w, g, m = np.stack(ws), np.stack(gs), np.stack(ms)
    assert w.shape == g.shape == (4, 576, 576, 3)
    return w, g, m


def low(x, sigma):
    return gaussian_filter(x, sigma=(0, sigma, sigma, 0), mode='reflect', truncate=4)


def features(w, g):
    r = g - w
    l2, l8 = low(r, 2), low(r, 8)
    return np.stack([l8, l2 - l8, r - l2])


def accumulate(phi, m, y):
    q = np.zeros((6, 6)); b = np.zeros(6)
    for region, mask in enumerate((m, ~m)):
        x = phi[:, mask, :].reshape(3, -1)
        z = y[mask, :].reshape(-1)
        sl = slice(region * 3, region * 3 + 3)
        q[sl, sl] = x @ x.T / y.size
        b[sl] = x @ z / y.size
    return q, b


def predict(c, seed, coefficients):
    w8, g8, m = inputs(c, seed)
    w, g = w8.astype(np.float64) / 255, g8.astype(np.float64) / 255
    phi = features(w, g)
    result = {'W': w8, 'G': g8}
    for name in ('constant', 'region', 'bands', 'candidate'):
        a = np.array(coefficients[name]['expanded'])
        rc = np.einsum('b,bthwc->thwc', a[:3], phi)
        rh = np.einsum('b,bthwc->thwc', a[3:], phi)
        result[name] = w + np.where(m[..., None], rc, rh)
    lw, lg = low(w, 8), low(g, 8)
    result.update(covered_G=np.where(m[..., None], g, w),
                  lowW_highG=lw + g - lg, lowG_highW=lg + w - lw,
                  smoothW=low(w, 1), medianW=median_filter(w, size=(1, 3, 3, 1), mode='reflect'),
                  smoothG=low(g, 1))
    return np.stack([result[n] if result[n].dtype == np.uint8 else
                     np.clip(result[n] * 255.0, 0, 255).astype(np.uint8) for n in METHODS])


def score_many(pred, gt):
    """Original S140 metric, batching predictions; never pool seeds."""
    d = pred.astype(np.float64) - gt[None].astype(np.float64)
    mse = np.mean(d * d, axis=(1, 2, 3, 4))
    psnr = -10 * np.log10(mse / 255**2)
    v = torch.exp(-((torch.arange(11) - 5.0) ** 2) / (2 * 1.5**2)); v = v / v.sum()
    k = (v[:, None] * v[None, :])[None, None]
    filt = lambda z: torch.nn.functional.conv2d(z, k, padding=5)
    lum = np.array([0.299, 0.587, 0.114])
    ss = np.zeros(len(pred))
    with torch.no_grad():
        for i in range(4):
            x = torch.from_numpy(pred[:, i].astype(np.float64) @ lum).float()[:, None]
            y = torch.from_numpy(gt[i].astype(np.float64) @ lum).float()[None, None]
            mx, my = filt(x), filt(y)
            vx, vy, cv = filt(x*x)-mx*mx, filt(y*y)-my*my, filt(x*y)-mx*my
            c1, c2 = (0.01*255)**2, (0.03*255)**2
            z = ((2*mx*my+c1)*(2*cv+c2))/((mx*mx+my*my+c1)*(vx+vy+c2))
            ss += z[..., 5:-5, 5:-5].mean(dim=(1, 2, 3)).numpy() / 4
    return {n: {'psnr': float(psnr[i]), 'ssim': float(ss[i])} for i, n in enumerate(METHODS)}


def analyze(rows):
    windows = sorted({r['window'] for r in rows})
    pair_of = {r['window']: r['pair'] for r in rows}
    a = {n: {m: np.array([np.mean([r['scores'][n][m] for r in rows if r['window'] == w])
                          for w in windows]) for m in ('psnr', 'ssim')} for n in METHODS}
    means = {n: {m: float(x.mean()) for m, x in v.items()} for n, v in a.items()}
    best = max(CONTROLS, key=lambda n: means[n]['psnr'])
    contrasts = {}
    for n in CONTROLS:
        d = a['candidate']['psnr'] - a[n]['psnr']
        boot = np.random.default_rng(0).choice(d, (10000, len(d))).mean(axis=1)
        contrasts[n] = {'mean': float(d.mean()), 'ci95': np.quantile(boot, [.025, .975]).tolist(),
                        'positive_windows': int((d > 0).sum()),
                        'per_pair': {p: float(np.mean([d[i] for i, w in enumerate(windows) if pair_of[w] == p]))
                                     for p in sorted(set(pair_of.values()))}}
    diff = a['candidate']['psnr'] - a[best]['psnr']
    remaining = float(np.sort(diff)[:-2].mean())
    pairs = contrasts[best]['per_pair']
    gates = {'beats_every_control_by_0.2dB': all(c['mean'] >= .2 for c in contrasts.values()),
             'ssim_not_below_W': means['candidate']['ssim'] >= means['W']['ssim'],
             'ssim_not_below_strongest_control': means['candidate']['ssim'] >= means[best]['ssim'],
             'positive_at_least_two_pairs': sum(x > 0 for x in pairs.values()) >= 2,
             'no_pair_below_minus_0.2dB': min(pairs.values()) >= -.2,
             'top_two_removed_gain_at_least_0.1dB': remaining >= .1}
    return {'means': means, 'strongest_control': best, 'contrasts': contrasts,
            'window_order': windows, 'candidate_minus_best': diff.tolist(),
            'top_two_removed_mean': remaining,
            'top_two_positive_gain_share': float(np.maximum(np.sort(diff)[-2:], 0).sum() / max(np.maximum(diff, 0).sum(), 1e-30)),
            'gates': gates, 'verdict': 'CONTINUE_TO_SOURCE_HELDOUT_QUESTION' if all(gates.values()) else 'STOP_TESTED_POLICY',
            'new_method_validated': False, 'novelty_authorization': 'NONE'}


def run(stage):
    t0 = time.time()
    torch.set_num_threads(2); torch.set_num_interop_threads(1)
    assert os.environ.get('CUDA_VISIBLE_DEVICES') == ''
    out = stage / 'results'; out.mkdir(exist_ok=False)
    preds = out / 'predictions'; preds.mkdir()
    manifest = json.loads((stage / 'INPUT_MANIFEST.json').read_text())
    for path, info in manifest['files'].items():
        assert sha(path) == info['sha256'], f'Input changed: {path}'
    plan = manifest['plan']; contexts = sorted(plan['contexts'], key=lambda c: c['window_id'])
    pairmap = {r['window_id']: r['pair'] for r in json.loads((stage/'POSE_ARMS.json').read_text())['rows']}
    assert len(contexts) == 24 and len({c['window_id'] for c in contexts}) == 24
    pairs = sorted({pairmap[c['window_id']] for c in contexts})
    assert len(pairs) == 3 and all(c['mode'] == 'W2' and c['strength'] == .5 for c in contexts)
    targets = {p: {r for c in contexts if pairmap[c['window_id']] == p for r in c['target_refs']} for p in pairs}
    refs = {p: {r for c in contexts if pairmap[c['window_id']] == p for r in c['ctx_refs']} for p in pairs}
    assert all(not targets[p] & (targets[q] | refs[q]) for p in pairs for q in pairs if p != q)
    save(out/'ENVIRONMENT.json', {'python': platform.python_version(), 'numpy': np.__version__, 'scipy': scipy.__version__,
                                 'torch': torch.__version__, 'cpu_threads': 2, 'gpu_hours': 0,
                                 'protocol_sha256': sha(stage/'PROTOCOL.md'), 'code_sha256': sha(__file__),
                                 'input_manifest_sha256': sha(stage/'INPUT_MANIFEST.json'), 'started_epoch': t0})
    print('Input hashes and cross-pair reference disjointness passed.', flush=True)
    stats = {p: {'q': np.zeros((6, 6)), 'b': np.zeros(6), 'cells': []} for p in pairs}
    for c in contexts:
        p = pairmap[c['window_id']]
        y = target(c).astype(np.float64) / 255
        for seed in (3, 4):
            w8, g8, m = inputs(c, seed)
            w, g = w8.astype(np.float64)/255, g8.astype(np.float64)/255
            q, b = accumulate(features(w, g), m, y-w)
            stats[p]['q'] += q; stats[p]['b'] += b
            stats[p]['cells'].append([c['window_id'], seed])
        print('Training sufficient statistics:', c['window_id'], flush=True)
    serial = {p: {**s, 'q': s['q'].tolist(), 'b': s['b'].tolist()} for p, s in stats.items()}
    save(out/'TRAINING_STATS.json', serial)
    coefficients = {}
    for heldout in pairs:
        train = [p for p in pairs if p != heldout]
        cells = sum([stats[p]['cells'] for p in train], [])
        assert all(pairmap[w] != heldout and seed in (3, 4) for w, seed in cells)
        q = sum(stats[p]['q'] for p in train) / len(cells)
        b = sum(stats[p]['b'] for p in train) / len(cells)
        coef = {}
        for n in ('constant', 'region', 'bands', 'candidate'):
            transform = mapping(n)
            a = box_solve(transform.T @ q @ transform, transform.T @ b)
            coef[n] = {'coefficients': a.tolist(), 'expanded': (transform @ a).tolist()}
        coefficients[heldout] = {'train_pairs': train, 'train_cells': cells, 'models': coef}
    save(out/'COEFFICIENTS.json', coefficients)
    sealed = []
    for c in contexts:
        pair = pairmap[c['window_id']]
        for seed in (5, 6):
            arr = predict(c, seed, coefficients[pair]['models'])
            path = preds / f"{c['window_id']}__s{seed}.npy"
            np.save(path, arr, allow_pickle=False)
            sealed.append({'file': str(path), 'sha256': sha(path), 'bytes': path.stat().st_size,
                           'window': c['window_id'], 'pair': pair, 'seed': seed})
        print('Predictions sealed:', c['window_id'], flush=True)
    assert sum(x['bytes'] for x in sealed) < 4 * 1024**3
    save(out/'PREDICTION_SEAL.json', {'coefficients_sha256': sha(out/'COEFFICIENTS.json'),
         'methods': METHODS, 'predictions': sealed, 'sealed_epoch': time.time(), 'target_scoring_not_started': True})
    # Held-out targets first enter scorer only after ALL predictions are sealed.
    baseline = json.loads((GEN/'S140_SCORES.json').read_text())
    ctx = {c['window_id']: c for c in contexts}; rows = []; max_psnr = 0.; max_ssim = 0.
    for item in sealed:
        c = ctx[item['window']]; path = Path(item['file'])
        assert sha(path) == item['sha256']
        scores = score_many(np.load(path, allow_pickle=False), target(c))
        old = baseline['runs'][f"{c['ctx_key']}__s{item['seed']}"]
        for n, oldpsnr, oldssim in [('G', old['psnr_db'], old['ssim']),
                                   ('W', baseline['warps'][item['window']]['psnr'], baseline['warps'][item['window']]['ssim'])]:
            max_psnr = max(max_psnr, abs(scores[n]['psnr'] - oldpsnr))
            max_ssim = max(max_ssim, abs(scores[n]['ssim'] - oldssim))
        rows.append({**item, 'scores': scores})
        print('Scored sealed cell:', item['window'], item['seed'], flush=True)
    assert max_psnr < 1e-8 and max_ssim < 2e-6, ('baseline discrepancy', max_psnr, max_ssim)
    save(out/'SCORES.json', {'rows': rows, 'baseline_agreement_max_abs': {'psnr': max_psnr, 'ssim': max_ssim}})
    result = analyze(rows)
    result.update(wall_seconds=time.time()-t0, gpu_hours=0, input_manifest_sha256=sha(stage/'INPUT_MANIFEST.json'),
                  score_sha256=sha(out/'SCORES.json'), coefficient_sha256=sha(out/'COEFFICIENTS.json'))
    save(out/'RESULT.json', result)
    print('FINISHED', result['verdict'], flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('stage', type=Path)
    args = parser.parse_args(); run(args.stage.resolve())
