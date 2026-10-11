#!/usr/bin/env python3
"""S147 development scorer (R273 §7 D-E). The S144 metric functions (score_s144_functions.py, verbatim) on every arm and
comparator, one conversion path. usage:
  score_s147.py <data_root> <plan_dev_s147_gen.json> <warp_dir> <prep_dir> <fallback V dir> <S144 dev_F> <S144 dev_A>
                <S144 ALPHA.json> <out.json> ARM=DIR [...]
prep_dir holds DEV_GEOMETRY_VALIDITY.json (validity + COPY map), fallback_warps/ and BL_A0_ALPHA.json (prep_dev_s147.py).
Per (clip, seed in 3,4): valid package -> B2 = warp, mask = warp valid, V = S144 VAE round trip, BL_AC = 0.6 A_C + 0.4 B2;
invalid package -> B2 = COPY, mask = zeros, V = VAE round trip of COPY, BL_AC = 0.6 A_none + 0.4 COPY (operational fallback
extension of the S144 estimator). COPY (all packages) = nearest-pose context per target on the reference grid.
BL_A0 = alpha0 A_none + (1 - alpha0) B2. PSNR pooled over the four targets; SSIM frame mean; regions on the mask (null if empty)."""
import json, sys, types
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parent
M = types.ModuleType('s144f'); exec(compile((HERE / 'score_s144_functions.py').read_text(), 'score_s144_functions.py', 'exec'), M.__dict__)
DS, PL, WD, PD, FV, FD, AD = [Path(a) for a in sys.argv[1:8]]
A_AC = json.loads(Path(sys.argv[8]).read_text())['alpha']['AC']; OUT = Path(sys.argv[9])
ARMS = dict(a.split('=', 1) for a in sys.argv[10:]); SEEDS = (3, 4)
VAL = json.loads((PD / 'DEV_GEOMETRY_VALIDITY.json').read_text()); A0 = json.loads((PD / 'BL_A0_ALPHA.json').read_text())['alpha']
plan = json.loads(PL.read_text())['contexts']; assert len(plan) == 32 and len({c['ctx_key'] for c in plan}) == 32
runs = {}
for c in plan:
    k = c['ctx_key']; root = DS / c['scene_dir']; ok = VAL['packages'][k]['valid']; assert c['geometry_valid'] == ok
    refs = [M.ref_grid(root / r.split('/')[0] / f"frame-{r.split('/')[1]}.color.png") for r in c['target_refs']]
    COPY = [M.ref_grid(root / r.split('/')[0] / f"frame-{r.split('/')[1]}.color.png") for r in VAL['copy'][k]['context_ref_per_target']]
    if ok:
        zs = [np.load(WD / f) for f in c['warp_files']]; B2 = [z['filled'] for z in zs]; Mk = [z['valid'].astype(bool) for z in zs]
        V = [M.pred_u8(f) for f in np.load(FD / f"{k}__V__s0.npy")]
    else:
        zs = [np.load(PD / 'fallback_warps' / f"{k}__fallback__t{j}.npz") for j in range(4)]; B2 = [z['filled'] for z in zs]
        assert all(np.array_equal(b, cp) for b, cp in zip(B2, COPY)); Mk = [np.zeros((576, 576), bool) for _ in range(4)]
        V = [M.pred_u8(f) for f in np.load(FV / f"{k}__fallback__V__s0.npy")]
    for s in SEEDS:
        A_none = [M.pred_u8(f) for f in np.load(AD / f"{k}__s{s}.npy")]
        src = [M.pred_u8(f) for f in np.load(AD / f"{k}__C__s{s}.npy")] if ok else A_none
        arm = {'B2': B2, 'V': V, 'COPY': COPY, 'A_none': A_none, 'BL_AC': M.blend(src, B2, A_AC), 'BL_A0': M.blend(A_none, B2, A0)}
        for name, d in ARMS.items():
            arr = np.load(Path(d) / f"{k}__s{s}.npy"); assert arr.shape == (4, 3, 576, 576) and np.isfinite(arr).all(), (name, k, s)
            arm[name] = [M.pred_u8(f) for f in arr]
        assert all(len(v) == 4 and all(x.shape == (576, 576, 3) and x.dtype == np.uint8 for x in v) for v in arm.values())
        rec = {'window_id': c['window_id'], 'seed': s, 'seq': c.get('seq'), 'kind': c.get('kind'), 'geometry_valid': ok}
        for name, ims in arm.items(): rec[name] = M.metrics(ims, refs, Mk)
        key = f"{k}__s{s}"; assert key not in runs; runs[key] = rec
    print(k, ok, {n: round(v['psnr_db'], 2) for n, v in rec.items() if isinstance(v, dict) and 'psnr_db' in v}, flush=True)
assert len(runs) == 64
OUT.write_text(json.dumps({'schema': 's147-dev-scores-v1', 'seeds': list(SEEDS), 'arms': ARMS, 'alpha_AC': A_AC, 'alpha_A0': A0, 'runs': runs}, indent=1) + '\n')
print('scored', len(runs))
