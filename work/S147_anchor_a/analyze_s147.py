#!/usr/bin/env python3
"""S147 development analysis (frozen with the protocol; R273 §7 E). usage: analyze_s147.py <SCORES_dev.json> <S144 SCORES_dev.json> <out DEV_GATE.json>
Cell = pooled four-target PSNR / frame-mean SSIM; clip = mean over seeds 3,4; sequence = mean over its clips; panel = equal
mean of the two sequence means. Descriptive 10k bootstrap (rng 0), clips resampled within sequence.
PRIMARY_SCREEN: F_geo - F_null >= +0.20 dB, > 0 in both sequences, SSIM >= -0.01.
USEFUL_CONTENT_SCREEN: PRIMARY and, for X in {A_none, F_geo_proto}: F_geo - X >= +0.20 dB, > 0 in both sequences, SSIM >= -0.01;
  and F_geo - F_geo_perm > 0 in both sequences.
PRACTICAL: for X in {A_none, A_cont, COPY, B2, V, BL_A0, BL_AC}: F_geo - X >= +0.20 dB, no negative sequence mean, SSIM >= -0.01.
GO iff USEFUL_CONTENT_SCREEN and PRACTICAL (engineering/completeness gates are checked by the chain and here)."""
import json, math, sys
from pathlib import Path
import numpy as np
S, S4, OUT = json.loads(Path(sys.argv[1]).read_text()), json.loads(Path(sys.argv[2]).read_text()), Path(sys.argv[3])
THR, TOL = 0.20, -0.01
ARMS = ['F_geo', 'F_null', 'J_geo', 'A_cont', 'F_geo_proto', 'F_geo_perm', 'A_none', 'COPY', 'B2', 'V', 'BL_A0', 'BL_AC']
PRACTICAL = ['A_none', 'A_cont', 'COPY', 'B2', 'V', 'BL_A0', 'BL_AC']
runs = S['runs']; assert len(runs) == 64
expected = {c['ctx_key']: c for c in json.loads(Path(__file__).with_name('plan_dev_s147.json').read_text())['contexts']}   # frozen plan (R274 #10)
assert len(expected) == 32 and set(runs) == {f'{w}__s{s}' for w in expected for s in (3, 4)}
clips = sorted(expected)
for w, c in expected.items():
    rr = [runs[f'{w}__s{s}'] for s in (3, 4)]; assert rr[0]['geometry_valid'] == rr[1]['geometry_valid'], w
    for s, r in zip((3, 4), rr):
        assert (r['window_id'], r['seed'], r['seq'], r['kind']) == (c['window_id'], s, c['seq'], c['kind']), (w, s)
        for a in ARMS:
            for m in ('psnr_db', 'ssim'): assert isinstance(r[a][m], (int, float)) and math.isfinite(r[a][m]), (w, s, a, m)
seq = {r['window_id']: r['seq'] for r in runs.values()}; SEQS = sorted(set(seq.values())); assert len(SEQS) == 2
valid = {r['window_id']: r['geometry_valid'] for r in runs.values()}
# comparators on valid packages must equal the archived S144 scores (same cells, same functions)
maxd = 0.0
for k, r in runs.items():
    if not r['geometry_valid']: continue
    for arm in ('A_none', 'B2', 'V', 'BL_AC'):
        for m in ('psnr_db', 'ssim', 'psnr_covered', 'psnr_holes'):
            x, y = r[arm][m], S4['runs'][k][arm][m]
            if x is None and y is None: continue
            maxd = max(maxd, abs(x - y))
assert maxd < 1e-9, f'comparator recomputation differs from S144 by {maxd}'


def clip_means(arm, m):
    out = {}
    for w in clips:
        v = [runs[f'{w}__s{s}'][arm][m] for s in (3, 4)]
        out[w] = None if any(x is None for x in v) else float(np.mean(v))
        if m in ('psnr_db', 'ssim'): assert out[w] is not None and math.isfinite(out[w]), (arm, m, w)
    return out


def panel(d):   # equal mean of sequence means over clips with defined values; None if a sequence has none (regions only)
    if any(not any(seq[w] == q and d[w] is not None for w in clips) for q in SEQS):
        return None, {q: None for q in SEQS}
    sm = {q: float(np.mean([d[w] for w in clips if seq[w] == q and d[w] is not None])) for q in SEQS}
    return float(np.mean(list(sm.values()))), sm


def contrast(a, b):
    d = {w: (a[w] - b[w]) if a[w] is not None and b[w] is not None else None for w in clips}
    m, sm = panel(d); rng = np.random.default_rng(0); groups = {q: [d[w] for w in clips if seq[w] == q and d[w] is not None] for q in SEQS}
    if m is None: return {'mean': None, 'seq_means': sm, 'ci95': None, 'wins': None, 'n': 0}
    bt = [np.mean([np.mean(rng.choice(groups[q], len(groups[q]))) for q in SEQS]) for _ in range(10000)]
    return {'mean': m, 'seq_means': sm, 'ci95': [float(x) for x in np.percentile(bt, [2.5, 97.5])],
            'wins': int(sum(v > 0 for v in d.values() if v is not None)), 'n': int(sum(v is not None for v in d.values()))}


res = {'comparator_max_abs_diff_vs_S144_valid_packages': maxd, 'n_invalid_packages': sum(not v for v in valid.values())}
pairs = [('F_geo', 'F_null'), ('F_geo', 'F_geo_proto'), ('F_geo', 'F_geo_perm')] + [('F_geo', x) for x in PRACTICAL if x != 'A_none'] + \
        [('F_geo', 'A_none'), ('F_geo', 'J_geo'), ('J_geo', 'A_cont'), ('F_null', 'A_cont'), ('J_geo', 'F_null'), ('A_cont', 'A_none'), ('J_geo', 'B2')]
for m in ('psnr_db', 'ssim', 'psnr_covered', 'psnr_holes'):
    U = {a: clip_means(a, m) for a in ARMS}
    blk = {'means': {a: panel(U[a])[0] for a in ARMS}, 'seq_means': {a: panel(U[a])[1] for a in ARMS}}
    for a, b in pairs: blk[f'{a} - {b}'] = contrast(U[a], U[b])
    # per-seed panel values (sequence-equal) for the primary
    blk['seed_panels_F_geo_minus_F_null'] = {str(s): float(np.mean([np.mean([runs[f'{w}__s{s}']['F_geo'][m] - runs[f'{w}__s{s}']['F_null'][m]
                                              for w in clips if seq[w] == q and runs[f'{w}__s{s}']['F_geo'][m] is not None
                                              and runs[f'{w}__s{s}']['F_null'][m] is not None]) for q in SEQS])) for s in (3, 4)}
    res[m] = blk
P, Q = res['psnr_db'], res['ssim']


def descriptive(ws, seeds=(3, 4), src=None, arms=None):   # descriptive only; cannot change any gate (R274 #10)
    src = src or runs; arms = arms or ARMS; out = {'n_clips': len(ws), 'sequences': {}}
    for q in SEQS:
        ww = [w for w in ws if seq[w] == q]
        out['sequences'][q] = {'n_clips': len(ww), 'means': {m: {a: (float(np.mean([np.mean([src[f'{w}__s{s}'][a][m] for s in seeds]) for w in ww])) if ww else None)
                                                                for a in arms} for m in ('psnr_db', 'ssim')}}
    ok = all(out['sequences'][q]['n_clips'] for q in SEQS)
    out['means'] = {m: {a: (float(np.mean([out['sequences'][q]['means'][m][a] for q in SEQS])) if ok else None) for a in arms} for m in ('psnr_db', 'ssim')}
    if src is runs:
        out['contrasts'] = {m: {f'{a} - {b}': (out['means'][m][a] - out['means'][m][b]) if ok else None for a, b in pairs} for m in ('psnr_db', 'ssim')}
    return out


res['fallback_fraction'] = sum(not v for v in valid.values()) / len(clips)
res['valid_only_descriptive'] = descriptive([w for w in clips if valid[w]])
res['individual_seed_panels_descriptive'] = {str(s): descriptive(clips, (s,)) for s in (3, 4)}
res['categories_descriptive'] = {kd: descriptive([w for w in clips if expected[w]['kind'] == kd]) for kd in ('memory', 'static')}
res['archived_BL_FC_original_geometry_descriptive_only'] = descriptive(clips, src=S4['runs'], arms=['BL_FC'])
res['region_pixel_denominators'] = {k: r['region_pixels'] for k, r in runs.items()}
ge = lambda a, b: P[f'{a} - {b}']['mean'] >= THR and Q[f'{a} - {b}']['mean'] >= TOL
pos2 = lambda a, b: all(v > 0 for v in P[f'{a} - {b}']['seq_means'].values())
nonneg2 = lambda a, b: all(v >= 0 for v in P[f'{a} - {b}']['seq_means'].values())
primary = bool(ge('F_geo', 'F_null') and pos2('F_geo', 'F_null'))
useful = bool(primary and all(ge('F_geo', x) and pos2('F_geo', x) for x in ('A_none', 'F_geo_proto')) and pos2('F_geo', 'F_geo_perm'))
practical = {x: bool(ge('F_geo', x) and nonneg2('F_geo', x)) for x in PRACTICAL}
res['GATE'] = {'PRIMARY_SCREEN_PASS': primary, 'USEFUL_CONTENT_SCREEN_PASS': useful, 'PRACTICAL': practical,
               'PRACTICAL_PASS': all(practical.values()), 'GO': bool(useful and all(practical.values())),
               'thresholds': {'psnr_db': THR, 'ssim_tolerance': TOL}}
OUT.write_text(json.dumps(res, indent=1) + '\n')
print('means', {a: round(v, 3) for a, v in P['means'].items()})
for k, c in P.items():
    if ' - ' in k and isinstance(c, dict) and 'mean' in c:
        print(f"  {k:22s} {c['mean']:+.3f} [{c['ci95'][0]:+.3f},{c['ci95'][1]:+.3f}] wins {c['wins']}/{c['n']} seq {({g: round(v, 3) for g, v in c['seq_means'].items()})} | SSIM {Q[k]['mean']:+.4f}")
print('GATE', res['GATE'])
