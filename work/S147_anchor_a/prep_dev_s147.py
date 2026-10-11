#!/usr/bin/env python3
"""S147 development preparation (CPU; before any S147 training). R273 §7 D-E.
usage: prep_dev_s147.py <plan_dev_s147.json> <data_root (S144 stage7)> <CPU warp dir> <S144 dev_A dir> <out_dir>
1. DEV_GEOMETRY_VALIDITY.json: per package, from its own CPU construction receipt (WARP_LOG_monitor_cpu.jsonl) and arrays:
   every KPS record has finite median reprojection, finite positive sigma and finite focals; filled is uint8 (576,576,3);
   valid is a (576,576) boolean mask. No target pixels are read.
2. COPY (every package): per target, the context frame nearest to the target camera under the S141 geo distance
   (0.1 x camera-centre distance + relative rotation angle, trace clamp; ties -> first in context order), on the reference grid.
   For invalid packages a fallback warp file (filled = COPY, valid = zeros) is written to <out>/fallback_warps/ together
   with plan_dev_fallback_vae.json (mode vae) for the V round trip.
3. BL_A0_ALPHA.json: alpha in {0, 0.05, ..., 1} maximising the seed-then-clip, sequence-equal mean PSNR of
   alpha*A_none + (1-alpha)*B2' on the archived S144 development cells (B2' = COPY for invalid packages); ties -> smaller."""
import hashlib, io, json, math, sys, types
from pathlib import Path
import numpy as np, torch
from PIL import Image
HERE = Path(__file__).resolve().parent
M = types.ModuleType('s144f'); exec(compile((HERE / 'score_s144_functions.py').read_text(), 'score_s144_functions.py', 'exec'), M.__dict__)
PL, DS, WD, AD, OUT = [Path(a) for a in sys.argv[1:6]]
OUT.mkdir(parents=True, exist_ok=True); (OUT / 'fallback_warps').mkdir(exist_ok=True)
plan = json.loads(PL.read_text())['contexts']; assert len(plan) == 32
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
fin = lambda x: isinstance(x, (int, float)) and math.isfinite(x)
logs = {}
for l in open(WD / 'WARP_LOG_monitor_cpu.jsonl'):
    if l.strip(): r = json.loads(l); logs[r['id']] = r


def pose(root, ref):
    sq, f = ref.split('/'); return np.loadtxt(io.StringIO((root / sq / f'frame-{f}.pose.txt').read_text()), dtype=np.float32).reshape(4, 4)


def geo(a, b):  # build_clips_s141.geo (W_T = 0.1)
    a = torch.from_numpy(np.asarray(a, np.float32)); b = torch.from_numpy(np.asarray(b, np.float32))
    tr = torch.clamp(torch.trace(a[:3, :3].T @ b[:3, :3]), -1.0, 3.0)
    return float(torch.norm(a[:3, 3] - b[:3, 3]) * 0.1 + torch.acos((tr - 1) / 2))


validity, copies, fb_plan = {}, {}, []
for c in plan:
    k = c['ctx_key']; root = DS / c['scene_dir']; r = logs.get(k); why = []
    if r is None: why.append('no receipt')
    else:
        for q in r['kps']:
            if not (fin(q.get('median_reproj_px')) and fin(q.get('sigma')) and q['sigma'] > 0 and all(fin(f) for f in q.get('focals', []))):
                why.append('non-finite KPS record')
    for f in c['warp_files']:
        z = np.load(WD / f)
        if z['filled'].dtype != np.uint8 or z['filled'].shape != (576, 576, 3) or z['valid'].shape != (576, 576) or z['valid'].dtype != bool:
            why.append(f'array check {f}')
    validity[k] = {'valid': not why, 'reasons': sorted(set(why)), 'warp_sha256': [sha(WD / f) for f in c['warp_files']]}
    cp = [min(range(len(c['ctx_refs'])), key=lambda i: (geo(pose(root, t), pose(root, c['ctx_refs'][i])), i)) for t in c['target_refs']]
    copies[k] = {'context_index_per_target': cp, 'context_ref_per_target': [c['ctx_refs'][i] for i in cp]}
    if why:
        names = []
        for j, i in enumerate(cp):
            sq, f = c['ctx_refs'][i].split('/')
            im = M.ref_grid(root / sq / f'frame-{f}.color.png')
            n = f"{k}__fallback__t{j}.npz"; np.savez_compressed(OUT / 'fallback_warps' / n, filled=im, valid=np.zeros((576, 576), bool)); names.append(n)
        fb_plan.append(dict(c, ctx_key=k + '__fallback', ctx_group=k + '__fallback', warp_files=names, mode='vae'))
(OUT / 'DEV_GEOMETRY_VALIDITY.json').write_text(json.dumps({'rule': __doc__.split('1. ')[1].split('2. ')[0].strip(), 'packages': validity,
    'n_invalid': sum(not v['valid'] for v in validity.values()), 'copy': copies}, indent=1) + '\n')
(OUT / 'plan_dev_fallback_vae.json').write_text(json.dumps({'contexts': fb_plan}, indent=1) + '\n')
(OUT / 'plan_dev_s147_gen.json').write_text(json.dumps({'contexts': [dict(c, geometry_valid=validity[c['ctx_key']]['valid']) for c in plan]}, indent=1) + '\n')
print('invalid packages', [k for k, v in validity.items() if not v['valid']])

# 3. BL_A0 alpha (archived S144 A_none outputs; development-fitted baseline)
GRID = [round(0.05 * i, 2) for i in range(21)]; per = {}
for c in plan:
    k = c['ctx_key']; root = DS / c['scene_dir']
    refs = [M.ref_grid(root / r.split('/')[0] / f"frame-{r.split('/')[1]}.color.png") for r in c['target_refs']]
    if validity[k]['valid']:
        zs = [np.load(WD / f) for f in c['warp_files']]; B2 = [z['filled'] for z in zs]; Mk = [z['valid'] for z in zs]
    else:
        zs = [np.load(OUT / 'fallback_warps' / f"{k}__fallback__t{j}.npz") for j in range(4)]; B2 = [z['filled'] for z in zs]; Mk = [z['valid'] for z in zs]
    for s in (3, 4):
        A = [M.pred_u8(f) for f in np.load(AD / f"{k}__s{s}.npy")]
        per[(k, s)] = {a: M.metrics(M.blend(A, B2, a), refs, Mk, with_ssim=False)['psnr_db'] for a in GRID}
seq = {c['ctx_key']: c['seq'] for c in plan}
def score(a):
    cm = {k: np.mean([per[(k, s)][a] for s in (3, 4)]) for k in seq}
    return float(np.mean([np.mean([v for kk, v in cm.items() if seq[kk] == q]) for q in sorted(set(seq.values()))]))
sc = {a: score(a) for a in GRID}; best = max(sc.values()); alpha = min(a for a in GRID if sc[a] == best)
(OUT / 'BL_A0_ALPHA.json').write_text(json.dumps({'alpha': alpha, 'psnr_by_alpha': sc, 'rule': 'max seed-then-clip, sequence-equal mean PSNR; ties smaller',
    'inputs': {'plan_sha256': sha(PL), 'A_none_dir': str(AD), 'validity_sha256': sha(OUT / 'DEV_GEOMETRY_VALIDITY.json')}}, indent=1) + '\n')
print('BL_A0 alpha', alpha, round(best, 4))
