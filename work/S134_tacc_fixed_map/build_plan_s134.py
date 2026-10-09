#!/usr/bin/env python3
"""S134: build the step-B generation plan from step-A retrieval receipts (CPU, no data access).

usage: build_plan_s134.py <orig_native.json> <fix_native.json> <sealed_c8_receipt.json> <plan_out.json> [<orig_gl.json> <fix_gl.json>]
Optional gl receipts add static_gl, mem_on_orig_gl, mem_on_fix_gl (Amendment 1; only if the gl gate passed).
Arms per window: static (offsets 0,15,30,45), mem_on_{orig,fix} (VMem default clean NMS-on),
mem_off_{orig,fix}. Identical (window, ordered context) tuples are generated once (ctx_key).
Also reports whether the gpu13 'orig' contexts reproduce the sealed H800 C8 contexts.
"""
import json, sys
from pathlib import Path

ORIG, FIX, SEALED, OUT = map(Path, sys.argv[1:5])
GL = tuple(map(Path, sys.argv[5:7])) if len(sys.argv) >= 7 else None
ARMS = {'mem_on': 'memory_nms_on_clean', 'mem_off': 'memory_nms_off'}


def by_window(p):
    recs = json.loads(p.read_text())['records']
    return {(r['scene'], int(r['window_start'])): r for r in recs}


orig, fix, sealed = by_window(ORIG), by_window(FIX), by_window(SEALED)
gl_orig, gl_fix = (by_window(GL[0]), by_window(GL[1])) if GL else ({}, {})
contexts, report = {}, []
for key in sorted(orig):
    scene, start = key
    ro, rf = orig[key], fix[key]
    if ro.get('status') != 'OK' or rf.get('status') != 'OK':
        report.append({'scene': scene, 'window_start': start, 'status': 'BLOCKED',
                       'orig': ro.get('error'), 'fix': rf.get('error')})
        continue
    arm_ctx = {'static': [start + o for o in (0, 15, 30, 45)]}
    for short, name in ARMS.items():
        arm_ctx[f'{short}_orig'] = [int(x) for x in ro['consumer_contexts'][name]]
        arm_ctx[f'{short}_fix'] = [int(x) for x in rf['consumer_contexts'][name]]
    conv_of = {a: 'native' for a in arm_ctx}
    if GL:
        go, gf = gl_orig.get(key, {}), gl_fix.get(key, {})
        arm_ctx['static_gl'] = list(arm_ctx['static']); conv_of['static_gl'] = 'gl'
        if go.get('status') == 'OK': arm_ctx['mem_on_orig_gl'] = [int(x) for x in go['consumer_contexts']['memory_nms_on_clean']]; conv_of['mem_on_orig_gl'] = 'gl'
        if gf.get('status') == 'OK': arm_ctx['mem_on_fix_gl'] = [int(x) for x in gf['consumer_contexts']['memory_nms_on_clean']]; conv_of['mem_on_fix_gl'] = 'gl'
    for arm, ids in arm_ctx.items():
        conv = conv_of[arm]
        k = f"{scene}__w{start:04d}__{conv}__" + '-'.join(str(i) for i in ids)
        c = contexts.setdefault(k, {'ctx_key': k, 'scene': scene, 'window_start': start, 'convention': conv, 'ctx_ids': ids, 'arms': []})
        c['arms'].append(arm)
    sr = sealed.get(key, {})
    report.append({
        'scene': scene, 'window_start': start, 'status': 'OK',
        'contexts': arm_ctx,
        'mem_on_changed_by_fix': arm_ctx['mem_on_orig'] != arm_ctx['mem_on_fix'],
        'mem_off_changed_by_fix': arm_ctx['mem_off_orig'] != arm_ctx['mem_off_fix'],
        'orig_reproduces_sealed_raw': {a: [int(x) for x in ro['raw_contexts'][a]] == [int(x) for x in sr.get('raw_contexts', {}).get(a, [])]
                                       for a in ('memory_nms_on_clean', 'memory_nms_off')},
    })
summary = {
    'windows_ok': sum(r['status'] == 'OK' for r in report),
    'mem_on_changed': sum(r.get('mem_on_changed_by_fix', False) for r in report),
    'mem_off_changed': sum(r.get('mem_off_changed_by_fix', False) for r in report),
    'orig_reproduces_sealed_both_arms': sum(all(r.get('orig_reproduces_sealed_raw', {}).values() or [False]) for r in report),
    'unique_contexts': len(contexts),
}
OUT.write_text(json.dumps({'schema': 's134-plan-v1', 'summary': summary, 'windows': report,
                           'contexts': sorted(contexts.values(), key=lambda c: c['ctx_key'])}, indent=1) + '\n')
print(json.dumps(summary, indent=1))
