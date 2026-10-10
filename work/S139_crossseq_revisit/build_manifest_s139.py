#!/usr/bin/env python3
"""S139 window manifest, exactly as PROTOCOL.md (no data read). usage: build_manifest_s139.py <out.json>"""
import json, sys
PAIRS = [('seq-01', 'seq-02'), ('seq-04', 'seq-03'), ('seq-06', 'seq-05')]
STARTS = [150, 250, 350, 450, 550, 650, 750, 850]
ref = lambda s, f: f'{s}/{f:06d}'
wins = []
for h, c in PAIRS:
    for s in STARTS:
        bank = [ref(h, f) for f in range(0, 1000, 50)] + [ref(c, s + o) for o in range(0, 60, 5)]
        wins.append({'window_id': f'{c}_from_{h}_s{s:04d}', 'pair': f'{h}->{c}', 'history_seq': h, 'current_seq': c,
                     'start': s, 'bank': bank, 'targets': [ref(c, s + o) for o in (60, 75, 90, 105)],
                     'static_recent': [ref(c, s + o) for o in (0, 15, 30, 45)], 'priming_chunks': [15, 12]})
assert all(len(w['bank']) == 32 for w in wins)
json.dump({'schema': 's139-manifest-v1', 'scene_dir': 'chess', 'intrinsics': [585.0, 585.0, 320.0, 240.0],
           'windows': wins}, open(sys.argv[1], 'w'), indent=1)
print(len(wins), 'windows')
