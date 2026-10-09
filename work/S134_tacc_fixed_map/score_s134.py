#!/usr/bin/env python3
"""S134 scorer: metric functions unchanged from work/S132_C9_convention/score_c9.py (which copies
score_arms_s106.py / scorer_s103.py, SHA 18e82e47...). Separate CPU process; the only S134 reader of target RGB.
usage: score_s134.py <gen_dir> <datasets_root>
"""
import hashlib, io, json, math, sys
from pathlib import Path
import numpy as np, torch
from PIL import Image
RUN, DS = Path(sys.argv[1]), Path(sys.argv[2])
REL = {"scene_13": "heldout_3dmatch_scene13/extracted/rgbd-scenes-v2-scene_13",
       "scene_14": "heldout_3dmatch_scene14/extracted/rgbd-scenes-v2-scene_14"}
TARGET_OFFSETS = [60, 75, 90, 105]

def require(v, m):
    if not v: raise RuntimeError(m)

def future_rgb_to_model_grid(raw):
    with Image.open(io.BytesIO(raw)) as image:
        rgb = np.asarray(image.convert("RGB"), dtype=np.uint8)
    require(rgb.shape == (480, 640, 3), f"future RGB native shape differs: {rgb.shape}")
    tensor = torch.from_numpy(rgb.transpose(2, 0, 1).copy()).float().unsqueeze(0) / 255.0
    transformed = torch.nn.functional.interpolate(
        tensor, size=(576, 768), mode="area", antialias=False)[:, :, :, 96:672]
    require(tuple(transformed.shape) == (1, 3, 576, 576), "reference transform shape differs")
    return np.clip(transformed[0].permute(1, 2, 0).numpy() * 255.0, 0, 255).astype(np.uint8)

def prediction_to_uint8(frame):
    require(frame.shape == (3, 576, 576), f"prediction frame shape differs: {frame.shape}")
    image = frame.transpose(1, 2, 0)
    rescaled = bool(float(image.min()) < -0.1)
    if rescaled: image = (image + 1.0) / 2.0
    return np.clip(image * 255.0, 0, 255).astype(np.uint8), rescaled

def integer_metrics(prediction, reference):
    require(prediction.shape == reference.shape == (576, 576, 3), "score shape differs")
    delta = prediction.astype(np.int64) - reference.astype(np.int64)
    a = int(np.abs(delta).sum(dtype=np.int64)); s = int((delta * delta).sum(dtype=np.int64))
    n = int(delta.size); mse = s / (n * 255 * 255)
    return {"channel_value_count": n, "absolute_integer_sum": a, "squared_integer_sum": s,
            "mae_0_1": a / (n * 255), "mse_0_1": mse,
            "psnr_db": float("inf") if mse == 0 else -10.0 * math.log10(mse)}


out = {}
for npy in sorted(RUN.glob("scene_1?__w????__*__s*.npy")):
    if npy.name.endswith(".tmp.npy"): continue
    key, s = npy.stem.rsplit("__s", 1); scene, w = key.split("__")[:2]; start = int(w[1:]); seed = int(s)
    seq = DS / REL[scene] / "seq-01"
    arr = np.load(npy); require(arr.shape == (4, 3, 576, 576), f"{npy.name}: shape {arr.shape}")
    ta = ts = tn = 0; frames = []
    for i, off in enumerate(TARGET_OFFSETS):
        ref = future_rgb_to_model_grid((seq / f"frame-{start + off:06d}.color.png").read_bytes())
        pred, resc = prediction_to_uint8(arr[i]); m = integer_metrics(pred, ref)
        m["frame_id"] = start + off; m["rescaled"] = resc; frames.append(m)
        ta += m["absolute_integer_sum"]; ts += m["squared_integer_sum"]; tn += m["channel_value_count"]
    mse = ts / (tn * 255 * 255)
    out[npy.stem] = {"ctx_key": key, "scene": scene, "window_start": start, "seed": seed,
                     "aggregate": {"mae_0_1": ta / (tn * 255), "mse_0_1": mse,
                                   "psnr_db": float("inf") if mse == 0 else -10.0 * math.log10(mse)},
                     "frames": frames}
(RUN / "S134_SCORES.json").write_text(json.dumps({"schema": "s134-scores-v1", "runs": out,
    "new_method_validated": False, "novelty_authorization": "NONE"}, indent=2, sort_keys=True) + "\n")
print(f"scored {len(out)} runs")
