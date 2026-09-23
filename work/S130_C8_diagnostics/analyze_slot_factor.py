#!/usr/bin/env python3
"""Analyze C8 Experiment 1 (slot-0 factor separation). CPU only.

usage: analyze_slot_factor.py <C8_ARM_SCORES.json> <S107_ARM_SCORES.json> <out.json>

Step 1 is a harness gate: convention N, seed 42 must reproduce S107 orderings o0 (order A)
and o3 (order B) exactly (per-frame absolute and squared integer sums identical). If the
gate fails, no delta is interpreted. Step 2 computes the preregistered estimand
delta(m, q, s) = PSNR(order B) - PSNR(order A) and applies the preregistered decision table.
"""
import json, sys
from pathlib import Path

THRESH_DB = 0.15   # preregistered, DESIGN_AND_PREREGISTRATION.md
MULTISETS = ['M1_55x2_40x2', 'M2_50x2_45x2']
CONVENTIONS = ['N', 'R', 'S', 'RS']
SEEDS = [42, 7]

c8 = json.loads(Path(sys.argv[1]).read_text())['arms']
s107 = json.loads(Path(sys.argv[2]).read_text())['arms']
out = {'schema': 'c8-slot-factor-analysis-v1', 'threshold_db': THRESH_DB,
       'new_method_validated': False, 'novelty_authorization': 'NONE'}

def ints(arm):
    return [(f['frame_id'], f['absolute_integer_sum'], f['squared_integer_sum']) for f in arm['frames']]

# ---- Step 1: harness gate -------------------------------------------------------------
gate = {}
for m in MULTISETS:
    for lab, oi in (('A', 0), ('B', 3)):
        mine = c8.get(f'{m}__{lab}__N__s42'); ref = s107.get(f'{m}__o{oi}')
        ok = mine is not None and ref is not None and ints(mine) == ints(ref)
        gate[f'{m}__{lab}'] = {'reproduces_s107_o%d' % oi: ok,
                               'c8_psnr': mine and mine['aggregate']['psnr_db'],
                               's107_psnr': ref and ref['aggregate']['psnr_db']}
gate_pass = all(v[k] for v in gate.values() for k in v if k.startswith('reproduces'))
out['harness_gate'] = {'pass': gate_pass, 'detail': gate}

# ---- Step 2: estimand ---------------------------------------------------------------
deltas = {}
for m in MULTISETS:
    for q in CONVENTIONS:
        for s in SEEDS:
            a, b = c8.get(f'{m}__A__{q}__s{s}'), c8.get(f'{m}__B__{q}__s{s}')
            if a is None or b is None:
                deltas[f'{m}|{q}|s{s}'] = None; continue
            deltas[f'{m}|{q}|s{s}'] = {
                'delta_psnr_db': b['aggregate']['psnr_db'] - a['aggregate']['psnr_db'],
                'delta_mae': b['aggregate']['mae_0_1'] - a['aggregate']['mae_0_1'],
                'psnr_A': a['aggregate']['psnr_db'], 'psnr_B': b['aggregate']['psnr_db']}
out['deltas'] = deltas

# ---- Step 3: preregistered decision (primary seed 42 only) ----------------------------
def below(q):
    vals = [deltas.get(f'{m}|{q}|s42') for m in MULTISETS]
    if any(v is None for v in vals): return None
    return all(abs(v['delta_psnr_db']) < THRESH_DB for v in vals)
R, S, RS, N = below('R'), below('S'), below('RS'), below('N')
if not gate_pass:
    verdict = 'HARNESS_GATE_FAILED: convention N did not reproduce S107; no delta is interpreted'
elif RS is None:
    verdict = 'INCOMPLETE'
elif N:
    verdict = 'NATIVE_EFFECT_ABSENT: N itself is below threshold; the S107 slot-0 effect did not recur'
elif RS and R and not S:
    verdict = 'RAY_REFERENCE_DOMINATES'
elif RS and S and not R:
    verdict = 'TRANSLATION_SCALE_DOMINATES'
elif RS and not R and not S:
    verdict = 'REFERENCE_SCALE_INTERACTION'
elif RS:
    verdict = 'COORDINATE_OR_SCALE_EXPLAINS (R and S each below threshold too)'
else:
    verdict = 'RESIDUAL_ORDER_EFFECT: RS not below threshold; tensor-order/temporal-position effect plausible'
out['primary'] = {'N_below': N, 'R_below': R, 'S_below': S, 'RS_below': RS, 'verdict': verdict}
out['secondary_seed7_note'] = 'seed 7 deltas are reported for robustness only and do not change the verdict'
Path(sys.argv[3]).write_text(json.dumps(out, indent=2, sort_keys=True) + '\n')
print(json.dumps(out['harness_gate'], indent=2)); print(json.dumps(out['primary'], indent=2))
for k, v in deltas.items():
    print(f"{k:24s} " + ('MISSING' if v is None else f"delta={v['delta_psnr_db']:+.4f} dB  (A {v['psnr_A']:.3f}, B {v['psnr_B']:.3f})"))
