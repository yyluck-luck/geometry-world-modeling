#!/usr/bin/env python3
"""C9 analysis. usage: analyze_c9.py <C9_SCORES.json> <C9_RECEIPT.json> <SEALED_S111_STATIC_SHA256.txt> <S113_SCORES.json> <out.json>

Gate: every 'native' output must be byte-identical to the sealed S111 static output of the same scene/window/seed,
and its PSNR must equal the sealed S113 static row. Only then is Delta = PSNR(gl) - PSNR(native) interpreted.
"""
import json, statistics as st, sys
from pathlib import Path
scores = json.loads(Path(sys.argv[1]).read_text())['arms']
runs = {r['tag']: r for r in json.loads(Path(sys.argv[2]).read_text())['runs']}
sealed = {}
for line in Path(sys.argv[3]).read_text().split('\n'):
    if line.strip():
        h, p = line.split(); sealed[Path(p).stem] = h          # stem like scene_13__w0050__static__s42
s113 = {r['tag']: r['psnr_db'] for r in json.loads(Path(sys.argv[4]).read_text())['rows'] if r['arm'] == 'static'}

gate_rows, gate_ok = [], True
for tag, v in scores.items():
    if v['convention'] != 'native': continue
    key = f"{v['scene']}__w{v['window_start']:04d}__static__s{v['seed']}"
    sha_ok = runs[tag]['output']['sha256'] == sealed.get(key)
    psnr_ok = key in s113 and abs(s113[key] - v['aggregate']['psnr_db']) < 1e-9
    gate_ok &= sha_ok and psnr_ok
    gate_rows.append({'tag': tag, 'sha_matches_sealed_s111': sha_ok, 'psnr_matches_s113': psnr_ok})

win = {}
for tag, v in scores.items():
    win.setdefault((v['scene'], v['window_start']), {}).setdefault(v['convention'], []).append(v['aggregate']['psnr_db'])
per_window = []
for (scene, start), d in sorted(win.items()):
    if 'native' in d and 'gl' in d:
        per_window.append({'scene': scene, 'window_start': start, 'native': st.mean(d['native']), 'gl': st.mean(d['gl']),
                           'delta': st.mean(d['gl']) - st.mean(d['native'])})
deltas = [w['delta'] for w in per_window]
mean_d = st.mean(deltas); n_pos = sum(d > 0 for d in deltas); n = len(deltas)
if not gate_ok:
    verdict = 'HARNESS_GATE_FAILED: native did not reproduce sealed S111 static; no delta interpreted'
elif mean_d >= 1.0 and n_pos >= 12:
    verdict = 'MISMATCH_CONFIRMED: converting to OpenGL improves generation'
elif mean_d <= -1.0 and (n - n_pos) >= 12:
    verdict = 'NATIVE_CORRECT: conversion degrades generation; mismatch hypothesis rejected'
elif abs(mean_d) < 0.3:
    verdict = 'NO_EFFECT: mismatch hypothesis refuted for generation'
else:
    verdict = 'INCONCLUSIVE'
res = {'schema': 'c9-analysis-v1', 'harness_gate_ok': gate_ok, 'gate': gate_rows, 'per_window': per_window,
       'mean_delta_db': mean_d, 'n_windows': n, 'n_positive': n_pos, 'verdict': verdict,
       'new_method_validated': False, 'novelty_authorization': 'NONE'}
Path(sys.argv[5]).write_text(json.dumps(res, indent=2) + '\n')
print(f"gate_ok={gate_ok}  ({sum(r['sha_matches_sealed_s111'] for r in gate_rows)}/{len(gate_rows)} sha, "
      f"{sum(r['psnr_matches_s113'] for r in gate_rows)}/{len(gate_rows)} psnr)")
for w in per_window: print(f"{w['scene']} w{w['window_start']:3d}  native {w['native']:.3f}  gl {w['gl']:.3f}  delta {w['delta']:+.3f}")
print(f"mean delta {mean_d:+.3f} dB, positive {n_pos}/{n}\nVERDICT: {verdict}")
