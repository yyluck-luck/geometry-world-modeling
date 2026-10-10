#!/usr/bin/env python3
"""S141 automated self-audit (no codex). usage: self_audit_s141.py <results_dir> <out.json>
results_dir holds: clips_s141.json (repo copy), FIDELITY_SHA256.txt, train_log_A/B.jsonl, RUNS_chess_A/B.jsonl (merged),
SCORES_chess_A/B.json, SCORES_base_regions.json, S139_ALL_SSIM_tacc.json, adapter_final_A/B.sha256, S141_ANALYSIS.json,
BASE_VERIFY.json (verify_base_s141.py). Exits 1 if any check fails (R254 F5)."""
import json, sys
from pathlib import Path
import numpy as np
D, OUT = Path(sys.argv[1]), Path(sys.argv[2]); HERE = Path(__file__).resolve().parent
chk = {}
# 1 leakage: training clips use only the six training scenes; monitor sequences never appear in training clips
cl = json.loads((HERE / 'clips_s141.json').read_text())['clips']
scenes = {'fire', 'heads', 'office', 'pumpkin', 'redkitchen', 'stairs'}
mon = {'office/seq-10', 'redkitchen/seq-14'}
tr = [c for c in cl if c['split'] == 'train']
chk['clips_only_training_scenes'] = all(c['scene'] in scenes and all(r.split('/')[0] in scenes for r in c['ctx'] + c['tgt']) for c in cl)
chk['no_chess_or_rgbd_in_clips'] = not any(('chess' in r or 'scene_1' in r) for c in cl for r in c['ctx'] + c['tgt'])
chk['monitor_seqs_absent_from_train'] = not any('/'.join(r.split('/')[:2]) in mon for c in tr for r in c['ctx'] + c['tgt'])
chk['n_train_clips'] = len(tr)
# 2 fidelity gate: zero-init adapters reproduce the base S139 output (A and B)
f = [l.split()[0] for l in (D / 'FIDELITY_SHA256.txt').read_text().strip().splitlines()]
chk['fidelity_A_byte_identical'] = f[0] == f[1]; chk['fidelity_B_byte_identical'] = f[0] == f[2]
# 3 training completed 10000 steps, finite losses
for v in 'AB':
    L = [json.loads(l) for l in (D / f'train_log_{v}.jsonl').read_text().splitlines()]
    st = [r for r in L if 'loss' in r]; va = [r for r in L if 'val' in r]
    chk[f'train_{v}_reached_10000'] = st[-1]['step'] == 10000 and va[-1]['step'] == 10000
    chk[f'train_{v}_losses_finite'] = bool(np.isfinite([r['loss'] for r in st]).all())
    chk[f'train_{v}_val_first_last'] = [va[0]['val'], va[-1]['val']]
# 4 evaluation used the final adapters, all plan cells present
for v, n in (('A', 48 * 4), ('B', 24 * 4)):
    R = [json.loads(l) for l in (D / f'RUNS_chess_{v}.jsonl').read_text().splitlines()]
    sha = (D / f'adapter_final_{v}.sha256').read_text().split()[0]
    chk[f'eval_{v}_cells_complete'] = len({(r['ctx_key'], r['seed']) for r in R}) == n == len(R)
    chk[f'eval_{v}_all_final_adapter'] = all(r['adapter_sha256'] == sha for r in R)
    chk[f'eval_{v}_all_rtx3090'] = all('3090' in r['gpu'] for r in R)
# 5 independent recomputation of both primaries (simple loops, no shared code with analyze_s141.py)
A = json.loads((D / 'SCORES_chess_A.json').read_text())['runs']; B = json.loads((D / 'SCORES_chess_B.json').read_text())
base = json.loads((D / 'S139_ALL_SSIM_tacc.json').read_text())['runs']
def mean_by_window(rows):
    acc = {}
    for w, x in rows: acc.setdefault(w, []).append(x)
    return {w: sum(v) / len(v) for w, v in acc.items()}
am = mean_by_window([(r['window_id'], r['psnr_db']) for r in A.values() if r['mode'] == 'A_mem'])
bm = mean_by_window([(r['window_id'], r['psnr_db']) for r in base.values() if 'mem_vmem' in r['arms'] and r['seed'] in (3, 4, 5, 6)])
Bm = mean_by_window([(r['window_id'], r['psnr_db']) for r in B['runs'].values() if r['mode'] == 'B_mem'])
chk['recomputed_primary_A_db'] = sum(am[w] - bm[w] for w in am) / len(am)
chk['recomputed_primary_B_db'] = sum(Bm[w] - B['warps'][w]['psnr'] for w in Bm) / len(Bm)
an = json.loads((D / 'S141_ANALYSIS.json').read_text())['contrasts']['psnr_db']
chk['primary_A_matches_analysis'] = abs(chk['recomputed_primary_A_db'] - an['PRIMARY_A: A_mem - base_mem']['mean']) < 1e-9
chk['primary_B_matches_analysis'] = abs(chk['recomputed_primary_B_db'] - an['PRIMARY_B: B_mem - B2_warp']['mean']) < 1e-9
bv = json.loads((D / 'BASE_VERIFY.json').read_text()); chk['base_outputs_match_receipts'] = bv['n_bad'] == 0 and bv['n'] == (48 + 16) * 4
OUT.write_text(json.dumps(chk, indent=1) + '\n')
bad = [k for k, v in chk.items() if v is False]
print(json.dumps(chk, indent=1)); print('FAILED:', bad if bad else 'none'); sys.exit(1 if bad else 0)
