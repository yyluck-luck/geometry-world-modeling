#!/usr/bin/env python3
"""S143 generation plans from POOL.json. usage: build_plan_s143.py <POOL.json> <out_dir>
plan_s143_part0/1.json: complete windows per part (part0 = first 12 windows, part1 = last 12), one context per unique ordered
set (ctx_key = ctx_group = <window>__<set_id>, warp_files = that set's own warps). plan_s143_replay.json: the S139 mem_vmem
context of the first window in its ORIGINAL order (must reproduce the archived S139 seed-3 output)."""
import json, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent; P, OUT = json.loads(Path(sys.argv[1]).read_text()), Path(sys.argv[2])
S139 = json.loads((HERE.parent / 'S139_crossseq_revisit/plan.json').read_text())
ctxs = []
for w in P['windows']:
    for s in w['sets']:
        k = f"{w['window_id']}__{s['set_id']}"
        ctxs.append({'ctx_key': k, 'ctx_group': k, 'window_id': w['window_id'], 'scene_dir': 'chess', 'convention': 'gl',
                     'ctx_refs': s['ctx_refs'], 'target_refs': w['targets'], 'rules': s['rules'], 'mode': s['set_id'], 'strength': None,
                     'warp_files': [f"{k}__{t.replace('/', '_')}.npz" for t in w['targets']]})
wins = [w['window_id'] for w in P['windows']]; half = set(wins[:12])
for i, part in enumerate(([c for c in ctxs if c['window_id'] in half], [c for c in ctxs if c['window_id'] not in half])):
    (OUT / f'plan_s143_part{i}.json').write_text(json.dumps({'schema': 's143-plan-v1', 'contexts': part}, indent=1) + '\n'); print('part', i, len(part))
rep = next(c for c in S139['contexts'] if c['window_id'] == wins[0] and 'mem_vmem' in c['arms'])
(OUT / 'plan_s143_replay.json').write_text(json.dumps({'schema': 's143-plan-v1', 'contexts': [dict(rep, ctx_group='replay', scene_dir='chess', mode='replay', strength=None)]}, indent=1) + '\n')
assert len({c['ctx_key'] for c in ctxs}) == len(ctxs); print('contexts', len(ctxs), 'replay', rep['ctx_key'])
