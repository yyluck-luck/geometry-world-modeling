#!/usr/bin/env python3
"""S136 step-B plan (CPU, receipts only).

usage: build_plan_s136.py <s134_native_orig.json> <s134_gl_orig.json> <s136_repaired.json | NONE> <plan_out.json> [arm:conv:receipt ...]
Extra arm:conv:receipt triples add memory arms, e.g. mem_fix_gl:gl:<S134 gl/fix receipt> (S134 Amendment 1: its gl gate passed).
Arms: static_native, static_gl (16 windows w0-w350, offsets 0,15,30,45); mem_orig_native, mem_orig_gl (S134 H800
contexts, 14 windows); mem_rep_gl (S136 canonical contexts, 14 windows, omitted if NONE). VMem default clean NMS-on.
Identical (window, convention, ordered ids) tuples are generated once.
"""
import json, sys
from pathlib import Path

NAT, GL, REP, OUT = sys.argv[1:5]
EXTRA = [a.split(':', 2) for a in sys.argv[5:]]
SCENES = ('scene_13', 'scene_14'); STATIC_WINDOWS = (0, 50, 100, 150, 200, 250, 300, 350)


def ctx(p):
    return {(r['scene'], int(r['window_start'])): [int(x) for x in r['consumer_contexts']['memory_nms_on_clean']]
            for r in json.loads(Path(p).read_text())['records'] if r.get('status') == 'OK'}


arms = {'mem_orig_native': ('native', ctx(NAT)), 'mem_orig_gl': ('gl', ctx(GL))}
if REP != 'NONE':
    arms['mem_rep_gl'] = ('gl', ctx(REP))
for arm, conv, path in EXTRA:
    arms[arm] = (conv, ctx(path))
contexts = {}


def add(arm, conv, scene, start, ids):
    k = f"{scene}__w{start:04d}__{conv}__" + '-'.join(str(i) for i in ids)
    c = contexts.setdefault(k, {'ctx_key': k, 'scene': scene, 'window_start': start, 'convention': conv,
                                'ctx_ids': ids, 'arms': []})
    c['arms'].append(arm)


for s in SCENES:
    for w in STATIC_WINDOWS:
        for conv in ('native', 'gl'):
            add(f'static_{conv}', conv, s, w, [w + o for o in (0, 15, 30, 45)])
for arm, (conv, table) in arms.items():
    for (s, w), ids in table.items():
        add(arm, conv, s, w, ids)
summary = {'unique_contexts': len(contexts), 'arms': {a: sum(a in c['arms'] for c in contexts.values())
                                                     for a in ['static_native', 'static_gl', *arms]}}
Path(OUT).write_text(json.dumps({'schema': 's136-plan-v1', 'summary': summary,
                                 'contexts': sorted(contexts.values(), key=lambda c: c['ctx_key'])}, indent=1) + '\n')
print(json.dumps(summary))
