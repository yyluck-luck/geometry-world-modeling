#!/usr/bin/env python3
"""S146 operational-v1 self-audit: provenance checks plus an independent recomputation of every op-primary contrast
(own package lookup by context identity, not analyze_s146.pkg). usage: python self_audit_s146op.py  (run from this dir)
Expects the fetched namespace in results/operational_v1/. Writes results/operational_v1/SELF_AUDIT_CHECKS.json."""
import glob, hashlib, json, math, sys
from collections import defaultdict
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent; OP = HERE / 'results/operational_v1'
ROOMS = ('apt1_kitchen', 'apt2_luke', 'office2_5a'); EVAL = (42, 7, 1, 2)
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
J = lambda p: json.loads(Path(p).read_text())
checks, fails = {}, []


def check(name, ok, detail=None):
    checks[name] = {'ok': bool(ok), 'detail': detail}
    if not ok: fails.append(name)


# 1. code parity: every deployed *.py/*.sh/PROTOCOL.md hash recorded at chain start equals the committed local file
rec = {Path(l.split()[1]).name: l.split()[0] for l in (OP / 'CODE_SHA256.txt').read_text().splitlines() if l.strip()}
mism = {k: v for k, v in rec.items() if not (HERE / k).exists() or sha(HERE / k) != v}
check('code_parity_chain_start', not mism and 'analyze_s146.py' in rec and 'gen_s141.py' in rec, mism or len(rec))
check('kps_original_pinned', rec.get('kps.py', '').startswith('71528da4'), rec.get('kps.py'))
for p in (0, 1):
    r2 = {Path(l.split()[1]).name: l.split()[0] for l in (OP / f'gen_part{p}/CODE_SHA256.txt').read_text().splitlines() if l.strip()}
    check(f'gen_code_parity_part{p}', r2.get('gen_s141.py') == rec.get('gen_s141.py') and r2.get('s141_common.py') == rec.get('s141_common.py')
          and r2.get(f'plan_s146_part{p}.json') == sha(OP / f'plan_s146_part{p}.json'), r2)

# 2. gates recorded by the chain
check('observer_parity', J(OP / 'PARITY.json')['parity'] is True)
P = J(OP / 'POOL_OP.json')
check('availability_gate', P['n_windows'] == 24 and not P['unavailable'] and [sum(w['room'] == r for w in P['windows']) for r in ROOMS] == [8, 8, 8])
cnt = [[len(l['finite_at_best']) for l in w['stepA']['kps']] for w in P['windows']]
check('kps_construction_counts', all(c == [4, 19, 31] for c in cnt))
rp = [json.loads(l) for f in glob.glob(str(OP / 'replay/RUNS_*.jsonl')) for l in open(f) if l.strip()]
check('replay_hash', len(rp) == 1 and list(rp[0]['outputs'].values())[0].startswith('913394e0'), [list(r['outputs'].values()) for r in rp])

# 3. generation receipts, sealing order, scores
gpu_s, n_planned, runs = sum(r['seconds'] for r in rp), 0, []
for p in (0, 1):
    plan = J(OP / f'plan_s146_part{p}.json')['contexts']; n_planned += 4 * len(plan)
    R = [json.loads(l) for f in glob.glob(str(OP / f'gen_part{p}/RUNS_*.jsonl')) for l in open(f) if l.strip()]
    runs += R; gpu_s += sum(r['seconds'] for r in R)
    cells = {(r['ctx_key'], r['seed']) for r in R}
    check(f'receipts_part{p}', cells == {(c['ctx_key'], s) for c in plan for s in EVAL} and len(R) == len(cells)
          and all('3090' in r['gpu'] for r in R) and all(r.get('adapter') in (None, 'NONE') for r in R), {'runs': len(R), 'planned': 4 * len(plan)})
check('generation_cap_480', n_planned <= 480, n_planned)
seal = {l.split('  ', 1)[1]: l.split('  ', 1)[0] for l in (OP / 'SEAL_SHA256.txt').read_text().splitlines() if l.strip()}
npy_sealed = {k for k in seal if k.endswith('.npy') and k.startswith('gen_part')}
check('seal_covers_all_outputs', len(npy_sealed) == n_planned, len(npy_sealed))
rec_hash = {k: v for r in runs for k, v in r['outputs'].items()}
check('seal_matches_receipt_hashes', len(rec_hash) == n_planned and all(seal[k] == rec_hash.get(k.split('/', 1)[1]) for k in npy_sealed), len(rec_hash))
check('no_scores_inside_seal', not any(k.startswith('SCORES') or k.startswith('GEN_SCORES') or k.startswith('S146_OP') for k in seal))
G = J(OP / 'GEN_SCORES.json')['runs']
check('scores_complete_finite', len(G) == n_planned and all(math.isfinite(r['psnr_db']) and math.isfinite(r['ssim']) for r in G.values()), len(G))

# 4. independent recomputation
by = {}
for r in G.values():
    wid, sid = r['ctx_key'].split('__', 1); by[(wid, sid, r['seed'])] = r
def sid_of(w, refs, ordered=False):
    hits = [s['set_id'] for s in w['sets'] if (s['ctx_refs'] == list(refs) if ordered else sorted(s['ctx_refs']) == sorted(refs))]
    if ordered and not hits:  # native order equal to the bank-sorted package as a set
        hits = [s['set_id'] for s in w['sets'] if s.get('also_native_order') and sorted(s['ctx_refs']) == sorted(refs)]
    assert len(hits) == 1, (w['window_id'], refs, hits); return hits[0]
A = J(OP / 'S146_OP_PRIMARY.json'); recompute, max_err = {}, 0.0
pkgs = {'4': lambda w: sid_of(w, w['rules']['4']), '3': lambda w: sid_of(w, w['rules']['3']), '1': lambda w: sid_of(w, w['rules']['1']),
        '2': lambda w: sid_of(w, w['rules']['2']), 'nat': lambda w: sid_of(w, w['stepA']['raw_order'], ordered=True)}
contrasts = {'PRIMARY nearest4 - mem_vmem(sorted)': ('4', '3'), 'nearest4 - mem_vmem(native order)': ('4', 'nat'),
             'nearest4 - static': ('4', '1'), 'nearest4 - mem_pose': ('4', '2'), 'mem_vmem native - sorted': ('nat', '3')}
for metric in ('psnr_db', 'ssim'):
    out = {}
    for name, (a, b) in contrasts.items():
        cell = defaultdict(list)
        for w in P['windows']:
            for s in EVAL: cell[(w['room'], s)].append(by[(w['window_id'], pkgs[a](w), s)][metric] - by[(w['window_id'], pkgs[b](w), s)][metric])
        Dr = {r: float(np.mean([np.mean(cell[(r, s)]) for s in EVAL])) for r in ROOMS}
        Ds = {str(s): float(np.mean([np.mean(cell[(r, s)]) for r in ROOMS])) for s in EVAL}
        D = float(np.mean(list(Dr.values())))
        out[name] = {'D': D, 'D_room': Dr, 'D_seed': Ds, 'gate': bool(D >= 0.20 and all(v > 0 for v in Dr.values()) and sum(v > 0 for v in Ds.values()) >= 3)}
        f = A[metric][name]
        err = max([abs(D - f['D'])] + [abs(Dr[r] - f['D_room'][r]) for r in ROOMS] + [abs(Ds[k] - f['D_seed'][k]) for k in Ds])
        max_err = max(max_err, err)
        check(f'recompute_{metric}_{name}', err < 1e-9 and (metric == 'ssim' or out[name]['gate'] == f['gate']), round(err, 12))
    recompute[metric] = out
dec = A['DECISION']; ps, pn = recompute['psnr_db']['PRIMARY nearest4 - mem_vmem(sorted)']['gate'], recompute['psnr_db']['nearest4 - mem_vmem(native order)']['gate']
check('decision_consistent', dec['pass_sorted'] == ps and dec['pass_native'] == pn, dec)
out = {'schema': 's146op-self-audit-v1', 'n_checks': len(checks), 'failed': fails, 'max_abs_error_vs_frozen_analysis': max_err,
       'generation_gpu_hours_receipts': gpu_s / 3600, 'checks': checks, 'recompute': recompute}
(OP / 'SELF_AUDIT_CHECKS.json').write_text(json.dumps(out, indent=1) + '\n')
print(f'checks {len(checks) - len(fails)}/{len(checks)} pass; max |err| {max_err:.2e}; generation receipts {gpu_s / 3600:.2f} GPU-h')
for k, v in recompute['psnr_db'].items(): print(f"  {k:38s} D {v['D']:+.3f} rooms {({r: round(x, 3) for r, x in v['D_room'].items()})} gate {v['gate']} | SSIM D {recompute['ssim'][k]['D']:+.4f}")
if fails: print('FAILED:', fails); sys.exit(1)
