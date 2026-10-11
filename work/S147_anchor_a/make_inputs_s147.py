#!/usr/bin/env python3
"""S147 source-only inputs (no target pixels read). usage: make_inputs_s147.py <S141 WARP_LOG dir> <S144 plan_dev_A.json> <S145 plan_s145.json> <out_dir>
INVALID_GEOMETRY.json: clips whose S141 training/monitor warp log has a non-finite KPS median reprojection (any record).
plan_dev_s147.json: all 32 S144 development contexts (mode none); per-package geometry validity is decided later from the
CPU warps' own receipts by prep_dev_s147.py (R273 §7 D), which writes plan_dev_s147_gen.json with geometry_valid flags. plan_chess_s147.json: the 24 S145/S141 chess mem_vmem contexts."""
import glob, json, math, sys
from pathlib import Path
LOGD, PDEV, PCH, OUT = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]), Path(sys.argv[4])
R = {}
for f in sorted(glob.glob(str(LOGD / 'WARP_LOG_*.jsonl'))):
    for l in open(f):
        if l.strip(): r = json.loads(l); R[r['id']] = r      # later shards overwrite earlier duplicates (as the warp files)
bad = sorted(k for k, r in R.items() if not all(isinstance(q.get('median_reproj_px'), (int, float)) and math.isfinite(q['median_reproj_px']) for q in r['kps']))
assert len(R) == 2032 and len(bad) == 47, (len(R), len(bad))
(OUT / 'INVALID_GEOMETRY.json').write_text(json.dumps({'rule': 'any KPS record with non-finite median_reproj_px (S141 warp logs)',
    'n_records': len(R), 'invalid_clip_ids': bad, 'n_train': sum(int(k[1:]) < 2000 for k in bad), 'n_monitor': sum(int(k[1:]) >= 2000 for k in bad)}, indent=1) + '\n')
dev = [c for c in json.loads(PDEV.read_text())['contexts'] if c['mode'] == 'none']; assert len(dev) == 32
(OUT / 'plan_dev_s147.json').write_text(json.dumps({'contexts': dev}, indent=1) + '\n')
ch = json.loads(PCH.read_text())['contexts']; assert len(ch) == 24 and all(c['mode'] == 'none' for c in ch)
(OUT / 'plan_chess_s147.json').write_text(json.dumps({'contexts': ch}, indent=1) + '\n')
print('invalid', len(bad), 'dev', len(dev), 'chess', len(ch))
