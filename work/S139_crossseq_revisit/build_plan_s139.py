#!/usr/bin/env python3
"""S139 plan: static_recent, mem_vmem (H800 step-A consumer contexts), mem_pose (CPU pose-NMS). gl convention.
usage: build_plan_s139.py <WINDOW_MANIFEST.json> <RETRIEVAL_RECEIPT.json> <POSE_ARMS.json> <plan_out.json>"""
import json, sys
from pathlib import Path
M, R, P = [json.loads(Path(p).read_text()) for p in sys.argv[1:4]]
OUT = Path(sys.argv[4])
rec = {r['window_id']: r for r in R['records']}; pose = {r['window_id']: r for r in P['rows']}
contexts, report = {}, []
for w in M['windows']:
    wid = w['window_id']; arms = {'static_recent': w['static_recent'], 'mem_pose': pose[wid]['mem_pose']}
    if rec.get(wid, {}).get('status') == 'OK':
        arms['mem_vmem'] = rec[wid]['consumer_contexts']['memory_nms_on_clean']
    for arm, refs in arms.items():
        k = f"{wid}__gl__" + '-'.join(r.replace('seq-', 's').replace('/', '_') for r in refs)
        c = contexts.setdefault(k, {'ctx_key': k, 'window_id': wid, 'convention': 'gl', 'ctx_refs': refs,
                                    'target_refs': w['targets'], 'arms': []})
        c['arms'].append(arm)
    report.append({'window_id': wid, 'blocked': rec.get(wid, {}).get('status') != 'OK',
                   'vmem_eq_pose': arms.get('mem_vmem') == arms['mem_pose'],
                   'vmem_eq_pose_set': sorted(arms.get('mem_vmem', [])) == sorted(arms['mem_pose'])})
summ = {'unique_contexts': len(contexts), 'blocked': sum(r['blocked'] for r in report),
        'vmem_eq_pose_exact': sum(r['vmem_eq_pose'] for r in report), 'vmem_eq_pose_set': sum(r['vmem_eq_pose_set'] for r in report)}
OUT.write_text(json.dumps({'schema': 's139-plan-v1', 'scene_dir': M['scene_dir'], 'summary': summ, 'windows': report,
                           'contexts': sorted(contexts.values(), key=lambda c: c['ctx_key'])}, indent=1) + '\n')
print(json.dumps(summ))
