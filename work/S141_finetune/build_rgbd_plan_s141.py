#!/usr/bin/env python3
"""S141 secondary panel (exposed RGB-D Scenes 13/14, 16 windows, VMem static contexts 0/15/30/45, gl). Plans for A and B
(B uses the S140 dev warps of those contexts) and a base plan for the S136 RTX 3090 static_gl outputs (seeds 3-6).
usage: build_rgbd_plan_s141.py <S140 plan_dev.json> <out_dir>"""
import json, sys
from pathlib import Path
P, OUT = json.loads(Path(sys.argv[1]).read_text()), Path(sys.argv[2])
win = {}
for c in P['contexts']:
    if c['mode'] in ('ref', 'none'): continue
    win.setdefault(c['window_id'], c)
assert len(win) == 16
def ctx(c, tag):
    sc, w = c['window_id'].split('__w'); w = int(w)
    basekey = f"{sc}__w{w:04d}__gl__" + '-'.join(str(w + o) for o in (0, 15, 30, 45))
    assert [int(r.split('/')[1]) for r in c['ctx_refs']] == [w, w + 15, w + 30, w + 45]
    key = basekey if tag == 'base_static' else f'{basekey}__{tag}'
    return {'ctx_key': key, 'ctx_group': key, 'base_ctx_key': basekey, 'window_id': c['window_id'], 'scene_dir': c['scene_dir'],
            'convention': 'gl', 'ctx_refs': c['ctx_refs'], 'target_refs': c['target_refs'], 'warp_files': c['warp_files'],
            'mode': tag, 'strength': None, 'arm': 'static_gl'}
for name, tag in (('plan_rgbd_A.json', 'A_static'), ('plan_rgbd_B.json', 'B_static'), ('plan_rgbd_base.json', 'base_static')):
    cs = [ctx(c, tag) for _, c in sorted(win.items())]
    (OUT / name).write_text(json.dumps({'schema': 's141-rgbd-plan-v1', 'contexts': cs}, indent=1) + '\n'); print(name, len(cs))
