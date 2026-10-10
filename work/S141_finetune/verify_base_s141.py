#!/usr/bin/env python3
"""R254 F11: the historical base outputs used as comparators must be the recorded ones. For every base cell (S139 TACC
static_recent / mem_vmem, S136 TACC static_gl on the RGB-D windows; seeds 3-6) recompute SHA-256 and compare with the
generator's RUNS_*.jsonl receipt. usage: verify_base_s141.py <s139_gen_dir> <s136_gen_dir> <plan_eval_A.json> <plan_rgbd_base.json> <out.json>"""
import hashlib, json, sys
from pathlib import Path
G139, G136, PA, PR, OUT = Path(sys.argv[1]), Path(sys.argv[2]), json.loads(Path(sys.argv[3]).read_text()), json.loads(Path(sys.argv[4]).read_text()), Path(sys.argv[5])
def receipts(d):
    r = {}
    for f in d.glob('RUNS_*.jsonl'):
        for l in f.read_text().splitlines():
            if l.strip(): x = json.loads(l); r[Path(x['output']['path']).name] = (x['output']['sha256'], x.get('gpu'))
    return r
rows, bad = [], []
for gdir, keys in ((G139, {c['base_ctx_key'] for c in PA['contexts']}), (G136, {c['base_ctx_key'] for c in PR['contexts']})):
    rec = receipts(gdir)
    for k in sorted(keys):
        for s in (3, 4, 5, 6):
            n = f'{k}__s{s}.npy'; p = gdir / n
            sha = hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None
            ok = sha is not None and n in rec and rec[n][0] == sha and '3090' in (rec[n][1] or '')
            rows.append({'file': str(p), 'sha256': sha, 'receipt': rec.get(n), 'ok': ok}); bad += [] if ok else [n]
OUT.write_text(json.dumps({'n': len(rows), 'n_bad': len(bad), 'bad': bad, 'rows': rows}, indent=1) + '\n')
print('base cells', len(rows), 'bad', len(bad), bad[:5])
