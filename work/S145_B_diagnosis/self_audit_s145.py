#!/usr/bin/env python3
"""S145 self-audit: provenance checks plus an independent recomputation of every S145 contrast (separate minimal code; pair
labels derived from window ids, not POSE_ARMS.json; own bootstrap draw). usage: python self_audit_s145.py  (run from this dir)
Writes results/SELF_AUDIT_CHECKS.json and exits non-zero if any hard check fails."""
import glob, hashlib, json, math, re, sys
from collections import defaultdict
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent; RES = HERE / 'results'; W = HERE.parent
S141 = W / 'S141_finetune/results/tacc/eval'
ARMS = ('off', 'target_only', 'bias_only', 'permuted')
ADB_SHA = '0dd40c86ea928b74abfa992ba0738f61950bd97d5d26aaa3d0bc494487de1c56'
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
J = lambda p: json.loads(Path(p).read_text())
checks, fails = {}, []


def check(name, ok, detail=None):
    checks[name] = {'ok': bool(ok), 'detail': detail}
    if not ok: fails.append(name)


# 1. code parity: local files == the hashes recorded next to every arm's outputs on TACC
local = {'gen_s144.py': sha(W / 'S144_A_wgs/gen_s144.py'), 's141_common.py': sha(W / 'S141_finetune/s141_common.py'),
         'plan_s145.json': sha(HERE / 'plan_s145.json'), 'plan_replay.json': sha(HERE / 'plan_replay.json')}
for a in ARMS + ('replay',):
    rec = {Path(l.split()[1]).name: l.split()[0] for l in (RES / a / 'CODE_SHA256.txt').read_text().splitlines() if l.strip()}
    check(f'code_parity_{a}', all(local[k] == v for k, v in rec.items()) and len(rec) == 3, rec)
_chk = (S141 / 'ADAPTER_CHECK_B.txt').read_text()
check('adapter_B_expected', re.search(r'sha256 ([0-9a-f]{64}) -> OK', _chk).group(1) == ADB_SHA and
      (W / 'S141_finetune/results/audit_inputs/adapter_final_B.sha256').read_text().split()[0] == ADB_SHA)

# 2. replay gate
rp = (RES / 'REPLAY_SHA256.txt').read_text().split()
runs_rp = [json.loads(l) for f in glob.glob(str(RES / 'replay/RUNS_*.jsonl')) for l in open(f) if l.strip()]
check('replay_bytes_equal', rp[0] == rp[2] and list(runs_rp[0]['outputs'].values())[0] == rp[2] and runs_rp[0]['branch'] == 'orig', rp)

# 3. run receipts and scores per arm
plan = J(HERE / 'plan_s145.json'); plan_keys = {c['ctx_key'] for c in plan['contexts']}
gpu_s, moved = 0.0, []
for a in ARMS:
    R = [json.loads(l) for f in glob.glob(str(RES / a / 'RUNS_*.jsonl')) for l in open(f) if l.strip()]
    cells = {(r['ctx_key'], r['seed']) for r in R}
    outs = {k: v for r in R for k, v in r['outputs'].items()}
    gpu_s += sum(r['seconds'] for r in R)
    if a == 'permuted': moved += [x for r in R for x in r['perm_moved_fraction']]
    S = J(RES / f'SCORES_{a}.json')['runs']
    fin = all(math.isfinite(r[m]) for r in S.values() for m in ('psnr_db', 'ssim', 'psnr_covered', 'psnr_holes'))
    check(f'receipts_{a}', len(R) == 96 and len(cells) == 96 and {s for _, s in cells} == {3, 4, 5, 6} and
          {k for k, _ in cells} == plan_keys and len(outs) == 96 and all(r['branch'] == a for r in R) and
          all(r['adapter_sha256'] == ADB_SHA for r in R) and all('3090' in r['gpu'] for r in R), {'runs': len(R), 'outputs': len(outs)})
    check(f'scores_{a}', len(S) == 96 and fin and {r['ctx_key'] for r in S.values()} == plan_keys, len(S))
gpu_s += sum(r['seconds'] for r in runs_rp)
check('budget_generation_under_6h', gpu_s / 3600 < 6.0, round(gpu_s / 3600, 3))
check('permutation_not_identity', min(moved) > 0.5, {'mean': float(np.mean(moved)), 'min': float(min(moved)), 'n': len(moved)})

# 4. independent recomputation
def pair_of(wid):  # 'seq-02_from_seq-01_s0150' -> 'seq-01->seq-02'
    m = re.match(r'(seq-\d+)_from_(seq-\d+)_s\d+$', wid); return f'{m.group(2)}->{m.group(1)}'


def per_window(path, mode, metric):
    acc = defaultdict(list)
    for r in J(path)['runs'].values():
        if r['mode'] == mode and r['seed'] in (3, 4, 5, 6): acc[r['window_id']].append(r[metric])
    assert len(acc) == 24 and all(len(v) == 4 for v in acc.values())
    return {k: sum(v) / 4 for k, v in acc.items()}


A_out = J(RES / 'S145_ANALYSIS.json'); recompute, max_err = {}, 0.0
idx = np.random.default_rng(12345).integers(0, 24, size=(20000, 24))
for metric in ('psnr_db', 'ssim', 'psnr_covered', 'psnr_holes'):
    arm = {'B_original': per_window(S141 / 'SCORES_chess_B.json', 'B_mem', metric), 'A': per_window(S141 / 'SCORES_chess_A.json', 'A_mem', metric)}
    for a in ARMS: arm['B_' + a] = per_window(RES / f'SCORES_{a}.json', 'B_mem', metric)
    if metric in ('psnr_db', 'ssim'):
        arm['B2'] = {k: v['psnr' if metric == 'psnr_db' else 'ssim'] for k, v in J(S141 / 'SCORES_chess_B.json')['warps'].items()}
    out = {'means': {k: float(np.mean(list(v.values()))) for k, v in arm.items()}}
    for name, c in A_out[metric].items():
        if name == 'means': continue
        x, y = name.split(': ')[-1].split(' - ')
        ws = sorted(arm[x]); d = np.array([arm[x][w] - arm[y][w] for w in ws])
        pm = defaultdict(list)
        for w, v in zip(ws, d): pm[pair_of(w)].append(v)
        bt = d[idx].mean(1)
        out[name] = {'mean': float(d.mean()), 'wins': int((d > 0).sum()), 'pair_means': {p: float(np.mean(v)) for p, v in sorted(pm.items())},
                     'ci95_own_bootstrap': [float(np.percentile(bt, 2.5)), float(np.percentile(bt, 97.5))]}
        err = max([abs(out[name]['mean'] - c['mean'])] + [abs(out[name]['pair_means'][p] - c['pair_means'][p]) for p in c['pair_means']])
        max_err = max(max_err, err)
        check(f'recompute_{metric}_{name}', err < 1e-9 and out[name]['wins'] == c['wins'], round(err, 12))
        ci_own, ci = out[name]['ci95_own_bootstrap'], c['ci95']
        check(f'ci_agreement_{metric}_{name}', abs(ci_own[0] - ci[0]) < 0.05 * max(1, abs(d.mean())) and abs(ci_own[1] - ci[1]) < 0.05 * max(1, abs(d.mean())),
              {'frozen': ci, 'own': ci_own})
    for k, v in out['means'].items(): max_err = max(max_err, abs(v - A_out[metric]['means'][k]))
    recompute[metric] = out

# 5. teacher-forced probe (diagnostic only)
P = J(RES / 'PROBE.json'); rows = P['rows']
check('probe_rows', len(rows) == 32 * 6 * 5 * 3 and len({r['clip'] for r in rows}) == 32, len(rows))
check('probe_derived_identity', all(abs(r['clean_latent_mse'] - r['sigma'] ** 2 * r['eps_mse']) <= 1e-6 * max(1e-12, r['clean_latent_mse']) + 1e-12 for r in rows))
probe = {}
for br in ('c', 'guided'):
    for ix in sorted({r['sigma_index'] for r in rows}):
        base = np.mean([r['eps_mse'] for r in rows if r['branch'] == br and r['sigma_index'] == ix and r['condition'] == 'correct'])
        sig = next(r['sigma'] for r in rows if r['sigma_index'] == ix)
        probe[f'{br}|{ix}'] = {'sigma': sig, 'eps_mse_correct': float(base), **{cond: float(np.mean([r['eps_mse'] for r in rows if r['branch'] == br and
                               r['sigma_index'] == ix and r['condition'] == cond]) / base - 1) for cond in ('zero5', 'zero_latent', 'stratum_mean', 'permuted')}}
out = {'schema': 's145-self-audit-v1', 'n_checks': len(checks), 'failed': fails, 'max_abs_error_vs_frozen_analysis': max_err,
       'generation_gpu_hours': gpu_s / 3600, 'checks': checks, 'recompute': recompute,
       'probe_relative_eps_mse_change_vs_correct': probe}
(RES / 'SELF_AUDIT_CHECKS.json').write_text(json.dumps(out, indent=1) + '\n')
print(f'checks {len(checks) - len(fails)}/{len(checks)} pass; max |err| vs frozen analysis {max_err:.2e}; generation {gpu_s / 3600:.2f} GPU-h')
for k, v in probe.items(): print(' probe', k, {a: (round(b, 4) if isinstance(b, float) else b) for a, b in v.items()})
if fails: print('FAILED:', fails); sys.exit(1)
