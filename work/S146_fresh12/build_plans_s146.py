#!/usr/bin/env python3
"""S146 generation/scoring plans from POOL.json. usage: build_plans_s146.py <POOL.json> <out_dir>
One context per (window, ordered package): ctx_key = ctx_group = <window>__<set_id>, scene_dir = room, convention = room
winner (gen_s141 convert: gl -> P.F, native -> P), warp_files keyed by the ordered tuple. part0 = first 12 windows, part1 =
last 12 (complete windows per GPU)."""
import json, sys
from pathlib import Path
P, OUT = json.loads(Path(sys.argv[1]).read_text()), Path(sys.argv[2])
ctxs = []
for w in P['windows']:
    for s in w['sets']:
        k = f"{w['window_id']}__{s['set_id']}"; tag = '-'.join(r.replace('/', '_') for r in s['ctx_refs'])
        ctxs.append({'ctx_key': k, 'ctx_group': k, 'window_id': w['window_id'], 'room': w['room'], 'scene_dir': w['room'],
                     'convention': w['convention'], 'ctx_refs': s['ctx_refs'], 'target_refs': w['targets'], 'rules': s['rules'],
                     'native_order_of_rule': s.get('native_order_of_rule'), 'also_native_order': s.get('also_native_order', False),
                     'mode': s['set_id'], 'strength': None,
                     'warp_files': [f"{w['window_id']}__{tag}__{t.replace('/', '_')}.npz" for t in w['targets']]})
assert len({c['ctx_key'] for c in ctxs}) == len(ctxs)
wins = [w['window_id'] for w in P['windows']]; half = set(wins[:12])
for i, part in enumerate(([c for c in ctxs if c['window_id'] in half], [c for c in ctxs if c['window_id'] not in half])):
    (OUT / f'plan_s146_part{i}.json').write_text(json.dumps({'schema': 's146-plan-v1', 'contexts': part}, indent=1) + '\n'); print('part', i, len(part))
(OUT / 'plan_s146_all.json').write_text(json.dumps({'schema': 's146-plan-v1', 'contexts': ctxs}, indent=1) + '\n')
