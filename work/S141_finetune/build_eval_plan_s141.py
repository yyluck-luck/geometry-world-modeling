#!/usr/bin/env python3
"""S141 evaluation plans from the S139 plan (static_recent / mem_vmem contexts) and the S140 confirm plan (mem_vmem warp
files; every context carries them so the S140 scorer can split covered/hole regions).
usage: build_eval_plan_s141.py <S139 plan.json> <S140 plan_confirm.json> <out_dir>
Writes plan_eval_A.json (A_static, A_mem), plan_eval_B.json (B_mem), plan_fid_A/B.json (fidelity: 1 context), plan_base_regions.json."""
import json, sys
from pathlib import Path
P139, P140, OUT = json.loads(Path(sys.argv[1]).read_text()), json.loads(Path(sys.argv[2]).read_text()), Path(sys.argv[3])
warps = {c['window_id']: c['warp_files'] for c in P140['contexts']}
base = {}
for c in P139['contexts']:
    for arm in c['arms']:
        if arm in ('static_recent', 'mem_vmem'): base[(c['window_id'], arm)] = c
wins = sorted({w for w, _ in base})
assert len(wins) == 24 and all((w, a) in base for w in wins for a in ('static_recent', 'mem_vmem'))
def ctx(w, arm, tag):
    b = base[(w, arm)]
    for c in P140['contexts']:
        if c['window_id'] == w and arm == 'mem_vmem': assert c['ctx_refs'] == b['ctx_refs'], w
    return {'ctx_key': f"{b['ctx_key']}__{tag}", 'ctx_group': f"{b['ctx_key']}__{tag}", 'base_ctx_key': b['ctx_key'],
            'window_id': w, 'scene_dir': 'chess', 'convention': 'gl', 'ctx_refs': b['ctx_refs'], 'target_refs': b['target_refs'],
            'warp_files': warps[w], 'mode': tag, 'strength': None, 'arm': arm}
A = [ctx(w, 'static_recent', 'A_static') for w in wins] + [ctx(w, 'mem_vmem', 'A_mem') for w in wins]
B = [ctx(w, 'mem_vmem', 'B_mem') for w in wins]
fid = [dict(A[24], ctx_key=A[24]['base_ctx_key'], ctx_group='fidA'), ]
fidB = [dict(B[0], ctx_key=B[0]['base_ctx_key'], ctx_group='fidB')]
BR = [dict(b, ctx_key=b['base_ctx_key'], ctx_group=b['base_ctx_key'], mode='base_mem') for b in B]   # base outputs, region split
# Amendment 1 (exploratory): B with static_recent contexts and the warps of those contexts (S141_warps_chess_static)
BS = [dict(ctx(w, 'static_recent', 'B_static'), warp_files=[f"{w}__static_recent__{t.replace('/', '_')}.npz" for t in base[(w, 'static_recent')]['target_refs']]) for w in wins]
BSR = [dict(b, ctx_key=b['base_ctx_key'], ctx_group=b['base_ctx_key'], mode='base_static') for b in BS]   # base static, region split
M = json.loads((Path(sys.argv[1]).parent / 'WINDOW_MANIFEST.json').read_text())
assert all(base[(w['window_id'], 'static_recent')]['ctx_refs'] == w['static_recent'] for w in M['windows'])
for name, cs in (('plan_eval_A.json', A), ('plan_eval_B.json', B), ('plan_fid_A.json', fid), ('plan_fid_B.json', fidB), ('plan_base_regions.json', BR), ('plan_eval_Bstatic.json', BS), ('plan_base_static_regions.json', BSR)):
    (OUT / name).write_text(json.dumps({'schema': 's141-eval-plan-v1', 'scene_dir': 'chess', 'contexts': cs}, indent=1) + '\n')
    print(name, len(cs))
