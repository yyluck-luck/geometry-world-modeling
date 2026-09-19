#!/usr/bin/env python3
"""Score the independently initialised NMS-on arm and settle what the leak changed.

Runs only after S113's prediction seal exists.  Order of operations is fixed:

  1. verify every S113 output against the sha256 recorded at generation time;
  2. verify every reused S111 output against its own sealed sha256;
  3. run the NULL-window byte-identity check, which needs no ground truth and
     decides whether the reuse of sealed outputs is admissible at all;
  4. only then open target RGB and score.

Step 3 is the load-bearing validity gate.  The census (job 595614) found two
windows where the clean and leaked thresholds select exactly the same padded
context ids.  For those windows the two arms receive identical consumer input, so
their outputs must be byte-identical.  If they are not, some uncontrolled
difference exists between the S111 and S113 harnesses and every reused sealed
output is suspect; the contrast is then reported as INVALID_REUSE rather than as a
result.

Aggregation follows RESEARCH_PRINCIPLES v2.14: seeds are controlled stochastic
replications and are folded within a window before any window-level statistic.
"""
import io, json, math, os, sys, hashlib
import statistics as st
from collections import defaultdict
from pathlib import Path
import numpy as np
import torch
from PIL import Image

DATA = Path(os.environ['DATA_ROOT'])
NEW = Path(os.environ['S113_DIR'])          # clean NMS-on run dir
OLD = Path(os.environ['S111_DIR'])          # sealed job-594957 run dir
CENSUS = Path(os.environ['CENSUS_JSON'])
OUT = Path(os.environ['ARM_OUT'])
REL = {"scene_13": "heldout_3dmatch_scene13/extracted/rgbd-scenes-v2-scene_13",
       "scene_14": "heldout_3dmatch_scene14/extracted/rgbd-scenes-v2-scene_14"}

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
    require(rgb.shape == (480, 640, 3), f"native shape {rgb.shape}")
    t = torch.from_numpy(rgb.transpose(2, 0, 1).copy()).float().unsqueeze(0) / 255.0
    t = torch.nn.functional.interpolate(t, size=(576, 768), mode="area", antialias=False)[:, :, :, 96:672]
    return np.clip(t[0].permute(1, 2, 0).numpy() * 255.0, 0, 255).astype(np.uint8)

def pred_u8(frame):
    img = frame.transpose(1, 2, 0)
    if float(img.min()) < -0.1: img = (img + 1.0) / 2.0
    return np.clip(img * 255.0, 0, 255).astype(np.uint8)

new_receipt = json.loads((NEW / "NMS_ON_CLEAN_RECEIPT.json").read_text())
old_receipt = json.loads((OLD / "NMS_RECEIPT.json").read_text())
census = json.loads(CENSUS.read_text())
regime = {(w['scene'], w['window_start']): w['regime']
          for w in census['windows'] if w['status'] == 'OK'}

# ---- 1 & 2: seal verification, before any ground truth is opened ------------
seal = {'s113_checked': 0, 's113_mismatch': [], 's111_checked': 0, 's111_mismatch': []}
for run in new_receipt['runs']:
    if run.get('status') != 'OK': continue
    got = sha_file(NEW / f"{run['tag']}.npy")
    seal['s113_checked'] += 1
    if got != run['output']['sha256']: seal['s113_mismatch'].append(run['tag'])
for run in old_receipt['runs']:
    got = sha_file(OLD / f"{run['tag']}.npy")
    seal['s111_checked'] += 1
    if got != run['output']['sha256']: seal['s111_mismatch'].append(run['tag'])
require(not seal['s113_mismatch'], f"S113 seal broken: {seal['s113_mismatch']}")
require(not seal['s111_mismatch'], f"S111 seal broken: {seal['s111_mismatch']}")
print(f"[seal] S113 {seal['s113_checked']} outputs verified, S111 {seal['s111_checked']} verified")

# ---- 3: NULL-window byte identity, no ground truth needed -------------------
new_sha = {(r['scene'], r['window_start'], r['seed']): r['output']['sha256']
           for r in new_receipt['runs'] if r.get('status') == 'OK'}
old_sha = {(r['scene'], r['window_start'], r['seed']): r['output']['sha256']
           for r in old_receipt['runs'] if r['arm'] == 'memory_nms_on'}
null_checks = []
for (sc, ws), reg in sorted(regime.items()):
    if reg != 'NULL': continue
    for seed in new_receipt['seeds']:
        k = (sc, ws, seed)
        if k in new_sha and k in old_sha:
            null_checks.append({'scene': sc, 'window_start': ws, 'seed': seed,
                                'identical': new_sha[k] == old_sha[k],
                                'clean_sha': new_sha[k][:16], 'leaked_sha': old_sha[k][:16]})
reuse_valid = bool(null_checks) and all(c['identical'] for c in null_checks)
for c in null_checks:
    print(f"[null-identity] {c['scene']} w{c['window_start']:03d} s{c['seed']}: "
          f"{'IDENTICAL' if c['identical'] else 'DIFFERENT'} "
          f"clean={c['clean_sha']} leaked={c['leaked_sha']}")
print(f"[reuse] sealed-output reuse {'ADMISSIBLE' if reuse_valid else 'NOT ADMISSIBLE'}")

# ---- 4: scoring -------------------------------------------------------------
cache, rows = {}, []
def score_run(run, rundir, arm):
    scene, tgts = run['scene'], run['target_frame_ids']
    seq = DATA / REL[scene] / "seq-01"
    arr = np.load(rundir / f"{run['tag']}.npy")
    require(arr.shape == (4, 3, 576, 576), f"{run['tag']}: shape {arr.shape}")
    a = s = n = 0
    for i, fid in enumerate(tgts):
        key = (scene, fid)
        if key not in cache:
            cache[key] = ref_grid(seq / f"frame-{fid:06d}.color.png")
        d = pred_u8(arr[i]).astype(np.int64) - cache[key].astype(np.int64)
        a += int(np.abs(d).sum()); s += int((d * d).sum()); n += int(d.size)
    mse = s / (n * 255 * 255)
    rows.append({'tag': run['tag'], 'scene': scene, 'window_start': run['window_start'],
                 'arm': arm, 'seed': run['seed'],
                 'unique_context_frames': run['unique_context_frames'],
                 'context_frame_ids': run['context_frame_ids'],
                 'regime': regime.get((scene, run['window_start'])),
                 'mae_0_1': a / (n * 255), 'mse_0_1': mse, 'psnr_db': -10.0 * math.log10(mse)})

for run in new_receipt['runs']:
    if run.get('status') == 'OK': score_run(run, NEW, 'memory_nms_on_clean')
for run in old_receipt['runs']:
    score_run(run, OLD, run['arm'])

# ---- 5: window-level aggregation (v2.14: fold seeds inside a window first) ---
cell = defaultdict(dict)
for r in rows: cell[(r['scene'], r['window_start'], r['seed'])][r['arm']] = r['psnr_db']
win = defaultdict(lambda: defaultdict(list))
for (sc, ws, sd), arms in cell.items():
    for a, v in arms.items(): win[(sc, ws)][a].append(v)

def contrast(a, b, keys=None):
    ds = []
    for k, arms in sorted(win.items()):
        if keys is not None and k not in keys: continue
        if a in arms and b in arms and len(arms[a]) == len(arms[b]) == 2:
            ds.append((k, st.mean(arms[a]) - st.mean(arms[b])))
    if not ds: return None
    v = [d for _, d in ds]
    m = st.mean(v); sd = st.stdev(v) if len(v) > 1 else 0.0
    return {'n_windows': len(v), 'mean_db': m, 'sd_db': sd,
            'se_db': sd / len(v) ** 0.5 if len(v) > 1 else 0.0,
            'n_positive': sum(1 for x in v if x > 0),
            'per_window': [{'scene': k[0], 'window_start': k[1], 'delta_db': d} for k, d in ds]}

per_arm = {}
by_arm = defaultdict(list)
for r in rows: by_arm[r['arm']].append(r['psnr_db'])
for a, v in by_arm.items():
    per_arm[a] = {'n_runs': len(v), 'mean_psnr_db': st.mean(v),
                  'sd_db': st.stdev(v) if len(v) > 1 else 0.0}

results = {}
for name, (a, b) in {
        'clean_nms_on_minus_static': ('memory_nms_on_clean', 'static'),
        'clean_nms_on_minus_nms_off': ('memory_nms_on_clean', 'memory_nms_off'),
        'leaked_nms_on_minus_static': ('memory_nms_on', 'static'),
        'nms_off_minus_static': ('memory_nms_off', 'static'),
        'leak_effect_clean_minus_leaked': ('memory_nms_on_clean', 'memory_nms_on'),
}.items():
    c = contrast(a, b)
    if c: results[name] = c

# the leak effect, split by what the leak actually changed
by_regime = {}
for reg in ('NULL', 'PERMUTATION', 'CONTENT'):
    keys = {k for k, v in regime.items() if v == reg}
    c = contrast('memory_nms_on_clean', 'memory_nms_on', keys)
    if c: by_regime[reg] = c

print(f"\n{'contrast':40} {'n':>3} {'mean':>8} {'sd':>7} {'se':>7} {'pos':>6}")
for k, c in results.items():
    print(f"{k:40} {c['n_windows']:3d} {c['mean_db']:+8.3f} {c['sd_db']:7.3f} "
          f"{c['se_db']:7.3f} {c['n_positive']:3d}/{c['n_windows']}")
print("\nleak effect (clean minus leaked) split by what the leak changed:")
for reg, c in by_regime.items():
    print(f"  {reg:12} n={c['n_windows']:2d}  mean {c['mean_db']:+7.3f} dB  "
          f"sd {c['sd_db']:6.3f}  positive {c['n_positive']}/{c['n_windows']}")

out = {'schema': 's113-clean-nms-on-scores-v1',
       'scope': 'development only; RGB only; exposed development sequences',
       'aggregation': 'seeds folded within window before window-level statistics (v2.14)',
       'seal_verification': seal,
       'null_window_byte_identity': null_checks,
       'sealed_output_reuse_admissible': reuse_valid,
       'regime_census': census['regime_census'],
       'per_arm_run_level': per_arm,
       'window_level_contrasts': results,
       'leak_effect_by_regime': by_regime,
       'rows': rows,
       'new_method_validated': False, 'novelty_authorization': 'NONE'}
(OUT / 'S113_SCORES.json').write_text(json.dumps(out, indent=2, sort_keys=True) + '\n')
print(f"\nscored {len(rows)} runs -> {OUT / 'S113_SCORES.json'}")
