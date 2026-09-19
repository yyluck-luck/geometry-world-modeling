#!/usr/bin/env python3
"""Score the slot repair arms against the sealed shipped arm.

Decision rule was fixed in `REPAIR_SPEC_PREDECLARED_20260918.md` before any repair output
was scored: retain the duplication explanation only if INPLACE gains >= 0.20 dB in mean over
the affected windows AND every no-op window reproduces the sealed shipped output byte-identically.

Arms:
  shipped   sealed `memory_nms_off` (job 594957)
  INPLACE   (a,a,b,c) -> (a,d,b,c)   primary; isolates the content change
  REFILL    (a,a,b,c) -> (a,b,c,d)   source-faithful variant; also shifts surviving slots
INPLACE - REFILL is a pure permutation of the same multiset: the order component.
"""
import io, json, math, os, hashlib
import statistics as st
from collections import defaultdict
from pathlib import Path
import numpy as np, torch
from PIL import Image

DATA = Path(os.environ['DATA_ROOT'])
OLD = Path(os.environ['S111_DIR'])
INP = Path(os.environ['INPLACE_DIR'])
REF = Path(os.environ['REFILL_DIR'])
OUT = Path(os.environ['ARM_OUT'])
REL = {"scene_13": "heldout_3dmatch_scene13/extracted/rgbd-scenes-v2-scene_13",
       "scene_14": "heldout_3dmatch_scene14/extracted/rgbd-scenes-v2-scene_14"}
THRESHOLD_DB = 0.20

def require(v, m):
    if not v: raise RuntimeError(m)
def sha_file(p):
    h = hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''): h.update(b)
    return h.hexdigest()
def ref_grid(path):
    with Image.open(io.BytesIO(Path(path).read_bytes())) as im:
        rgb = np.asarray(im.convert("RGB"), dtype=np.uint8)
    t = torch.from_numpy(rgb.transpose(2, 0, 1).copy()).float().unsqueeze(0) / 255.0
    t = torch.nn.functional.interpolate(t, size=(576, 768), mode="area", antialias=False)[:, :, :, 96:672]
    return np.clip(t[0].permute(1, 2, 0).numpy() * 255.0, 0, 255).astype(np.uint8)
def pred_u8(frame):
    img = frame.transpose(1, 2, 0)
    if float(img.min()) < -0.1: img = (img + 1.0) / 2.0
    return np.clip(img * 255.0, 0, 255).astype(np.uint8)

old = json.loads((OLD / "NMS_RECEIPT.json").read_text())
inp = json.loads((INP / "SLOT_CONTROL_RECEIPT.json").read_text())
ref = json.loads((REF / "SLOT_CONTROL_RECEIPT.json").read_text())

# provenance gates, before any ground truth is opened
for name, r in (('INPLACE', inp), ('REFILL', ref)):
    print(f"[{name}] prefixes_agree={r.get('all_oracle_prefixes_agree')} "
          f"nested={r.get('all_oracle_lists_nested')} within_bank={r.get('all_oracle_distinct_within_bank')}")
require(inp.get('all_oracle_prefixes_agree') and inp.get('all_oracle_lists_nested')
        and inp.get('all_oracle_distinct_within_bank'),
        'INPLACE candidate provenance unverified; repair arm withdrawn')

shipped_sha = {(r['scene'], r['window_start'], r['seed']): r['output']['sha256']
               for r in old['runs'] if r['arm'] == 'memory_nms_off'}
shipped_ctx = {(r['scene'], r['window_start']): r['context_frame_ids']
               for r in old['runs'] if r['arm'] == 'memory_nms_off'}

# no-op gate: REFILL generated the already-distinct windows; they must be byte-identical
noop = []
for r in ref['runs']:
    if r.get('status') != 'OK': continue
    k = (r['scene'], r['window_start'], r['seed'])
    if r.get('is_noop_window'):
        noop.append({'scene': r['scene'], 'window_start': r['window_start'], 'seed': r['seed'],
                     'identical': r['output']['sha256'] == shipped_sha.get(k)})
for c in noop:
    print(f"[noop-identity] {c['scene']} w{c['window_start']:03d} s{c['seed']}: "
          f"{'IDENTICAL' if c['identical'] else 'DIFFERENT'}")
noop_ok = bool(noop) and all(c['identical'] for c in noop)
print(f"[noop gate] {'PASS' if noop_ok else 'FAIL'}  ({len(noop)} runs)")

cache, rows = {}, []
def score(run, rundir, arm):
    scene, tgts = run['scene'], run['target_frame_ids']
    seq = DATA / REL[scene] / "seq-01"
    arr = np.load(rundir / f"{run['tag']}.npy")
    require(arr.shape == (4, 3, 576, 576), f"{run['tag']}: shape {arr.shape}")
    a = s = n = 0
    for i, fid in enumerate(tgts):
        key = (scene, fid)
        if key not in cache: cache[key] = ref_grid(seq / f"frame-{fid:06d}.color.png")
        d = pred_u8(arr[i]).astype(np.int64) - cache[key].astype(np.int64)
        a += int(np.abs(d).sum()); s += int((d * d).sum()); n += int(d.size)
    mse = s / (n * 255 * 255)
    rows.append({'tag': run['tag'], 'scene': scene, 'window_start': run['window_start'],
                 'arm': arm, 'seed': run['seed'],
                 'context_frame_ids': run.get('context_frame_ids'),
                 'unique_context_frames': run.get('unique_context_frames'),
                 'psnr_db': -10.0 * math.log10(mse)})

for r in old['runs']:
    if r['arm'] in ('memory_nms_off', 'static'): score(r, OLD, r['arm'])
for r in inp['runs']:
    if r.get('status') == 'OK': score(r, INP, 'inplace')
for r in ref['runs']:
    if r.get('status') == 'OK': score(r, REF, 'refill')

cellv = defaultdict(dict)
for r in rows: cellv[(r['scene'], r['window_start'], r['seed'])][r['arm']] = r['psnr_db']
win = defaultdict(lambda: defaultdict(list))
for (sc, ws, sd), arms in cellv.items():
    for a, v in arms.items(): win[(sc, ws)][a].append(v)

affected = sorted({(r['scene'], r['window_start']) for r in rows if r['arm'] == 'inplace'})
def contrast(a, b, keys):
    ds = []
    for k in keys:
        arms = win[k]
        if a in arms and b in arms and len(arms[a]) == len(arms[b]) == 2:
            ds.append((k, st.mean(arms[a]) - st.mean(arms[b])))
    if not ds: return None
    v = [d for _, d in ds]
    return {'n_windows': len(v), 'mean_db': st.mean(v),
            'sd_db': st.stdev(v) if len(v) > 1 else 0.0,
            'n_positive': sum(1 for x in v if x > 0),
            'per_window': [{'scene': k[0], 'window_start': k[1], 'delta_db': round(d, 4)}
                           for k, d in ds]}

res = {'inplace_minus_shipped': contrast('inplace', 'memory_nms_off', affected),
       'refill_minus_shipped': contrast('refill', 'memory_nms_off', affected),
       'inplace_minus_refill': contrast('inplace', 'refill', affected),
       'inplace_minus_static': contrast('inplace', 'static', affected)}

print(f"\naffected windows: {len(affected)}")
print(f"{'contrast':30} {'n':>3} {'mean':>8} {'sd':>7} {'pos':>7}")
for k, c in res.items():
    if c: print(f"{k:30} {c['n_windows']:3d} {c['mean_db']:+8.3f} {c['sd_db']:7.3f} "
                f"{c['n_positive']:3d}/{c['n_windows']}")
if res['inplace_minus_shipped']:
    print('\nper-window INPLACE - shipped:')
    for w in res['inplace_minus_shipped']['per_window']:
        print(f"  {w['scene']} w{w['window_start']:03d}  {w['delta_db']:+7.3f}")

gain = res['inplace_minus_shipped']['mean_db'] if res['inplace_minus_shipped'] else float('nan')
verdict = ('RETAINED' if (gain >= THRESHOLD_DB and noop_ok) else 'DISCARDED')
print(f"\nprospective rule: gain >= {THRESHOLD_DB} dB AND no-op byte-identity")
print(f"  measured gain = {gain:+.3f} dB, no-op gate = {'PASS' if noop_ok else 'FAIL'}")
print(f"  duplication-as-performance-explanation: {verdict}")

out = {'schema': 'slot-repair-scores-v1',
       'scope': 'development only; exposed development sequences; RGB PSNR only',
       'aggregation': 'seeds folded within window before window-level statistics (v2.14)',
       'no_inferential_statistics': ('windows are a finite panel; no SE, t, CI, significance or '
                                     'equivalence test is reported'),
       'prospective_threshold_db': THRESHOLD_DB,
       'noop_byte_identity': noop, 'noop_gate_pass': noop_ok,
       'affected_windows': [{'scene': s, 'window_start': w} for s, w in affected],
       'contrasts': res, 'verdict': verdict, 'rows': rows,
       'new_method_validated': False, 'novelty_authorization': 'NONE'}
(OUT / 'SLOT_REPAIR_SCORES.json').write_text(json.dumps(out, indent=2, sort_keys=True) + '\n')
print(f"\nscored {len(rows)} runs")
