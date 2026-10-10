#!/usr/bin/env python3
"""S140 plans. usage: build_plans_s140.py dev <out.json>
                       build_plans_s140.py confirm <mode> <strength> <S139 plan_v2.json> <out.json>
dev: 16 RGB-D Scenes windows x {W1 0.3/0.5/0.7, W2 0.5/1.0, W3} + fidelity pair (ref vs none) on scene_13 w0.
confirm: 24 chess windows, S139 mem_vmem contexts, selected variant only."""
import json, sys
REL = {'scene_13': 'heldout_3dmatch_scene13/extracted/rgbd-scenes-v2-scene_13',
       'scene_14': 'heldout_3dmatch_scene14/extracted/rgbd-scenes-v2-scene_14'}
VARIANTS = [('W1', 0.3), ('W1', 0.5), ('W1', 0.7), ('W2', 0.5), ('W2', 1.0), ('W3', 1.0)]
ctx = []
if sys.argv[1] == 'dev':
    for sc in ('scene_13', 'scene_14'):
        for w in range(0, 400, 50):
            wid = f'{sc}__w{w:04d}'; refs = [f'seq-01/{w + o:06d}' for o in (0, 15, 30, 45)]
            tg = [f'seq-01/{w + o:06d}' for o in (60, 75, 90, 105)]
            wf = [f'{sc}__w{w:04d}__t{w + o:06d}.npz' for o in (60, 75, 90, 105)]
            vs = VARIANTS + ([('ref', 1.0), ('none', 1.0)] if (sc, w) == ('scene_13', 0) else [])
            for m, s in vs:
                ctx.append({'ctx_key': f'{wid}__gl__{m}_{s:.1f}', 'ctx_group': wid, 'window_id': wid, 'scene_dir': REL[sc],
                            'convention': 'gl', 'ctx_refs': refs, 'target_refs': tg, 'warp_files': wf, 'mode': m, 'strength': s})
    out = sys.argv[2]
else:
    mode, s, plan = sys.argv[2], float(sys.argv[3]), json.load(open(sys.argv[4])); out = sys.argv[5]
    for c in plan['contexts']:
        if 'mem_vmem' not in c['arms']: continue
        wid = c['window_id']
        wf = [f"{wid}__mem_vmem__{t.replace('/', '_')}.npz" for t in c['target_refs']]
        ctx.append({'ctx_key': f'{wid}__gl__{mode}_{s:.1f}', 'ctx_group': wid, 'window_id': wid, 'scene_dir': 'chess',
                    'convention': 'gl', 'ctx_refs': c['ctx_refs'], 'target_refs': c['target_refs'], 'warp_files': wf,
                    'mode': mode, 'strength': s})
json.dump({'schema': 's140-plan-v1', 'contexts': ctx}, open(out, 'w'), indent=1)
print(len(ctx), 'contexts')
