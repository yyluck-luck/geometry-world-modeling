#!/usr/bin/env python3
"""S144 plans. usage: build_plans_s144.py <clips_s141.json> <S140 plan_confirm.json> <S140 plan_dev.json> <out_dir>
Generation plans (per panel): W2CR entries (strength 0.5) + 'vae' entries (frozen run only) + 'none' entries (monitor, A run only).
Scoring plans: one entry per output key (<ctx>__C, <ctx>__R, <ctx>__V, <ctx>) for score_s140.py."""
import json, sys
from pathlib import Path
CL, PC, PD, OUT = [json.loads(Path(p).read_text()) for p in sys.argv[1:4]] + [Path(sys.argv[4])]
mon = [c for c in CL['clips'] if c['split'] == 'val']; assert len(mon) == 32
base = []
for c in mon:
    strip = lambda r: '/'.join(r.split('/')[1:])
    base.append({'ctx_key': c['id'], 'ctx_group': c['id'], 'window_id': c['id'], 'scene_dir': c['scene'], 'convention': 'gl',
                 'ctx_refs': [strip(r) for r in c['ctx']], 'target_refs': [strip(r) for r in c['tgt']], 'strength': 0.5,
                 'warp_files': [f"{c['id']}__t{j}.npz" for j in range(4)], 'kind': c['kind'], 'seq': c['C']})
chess = [{k: v for k, v in c.items() if k not in ('mode',)} | {'ctx_key': c['window_id'], 'ctx_group': c['window_id']} for c in PC['contexts']]
assert len(chess) == 24 and all(c['strength'] == 0.5 for c in chess)
rgbd = [{k: v for k, v in c.items() if k not in ('mode',)} | {'ctx_key': c['window_id'], 'ctx_group': c['window_id']}
        for c in PD['contexts'] if c['mode'] == 'W2' and c['strength'] == 0.5]
assert len(rgbd) == 16
def gen(ctxs, F):
    out = [dict(c, mode='W2CR') for c in ctxs]
    out += [dict(c, mode='vae') for c in ctxs] if F else []
    return out
for name, ctxs in (('dev', base), ('chess', chess), ('rgbd', rgbd)):
    (OUT / f'plan_{name}_F.json').write_text(json.dumps({'contexts': gen(ctxs, True)}, indent=1) + '\n')
    a = gen(ctxs, False) + ([dict(c, mode='none') for c in ctxs] if name == 'dev' else [])
    (OUT / f'plan_{name}_A.json').write_text(json.dumps({'contexts': a}, indent=1) + '\n')
    sc = []
    for c in ctxs:
        for suf, lab in (('__C', 'C'), ('__R', 'R'), ('__V', 'V'), ('', 'none')):
            sc.append(dict(c, ctx_key=c['ctx_key'] + suf, mode=lab, strength=c['strength']))
    (OUT / f'plan_{name}_score.json').write_text(json.dumps({'contexts': sc}, indent=1) + '\n')
    print(name, len(ctxs))
