#!/usr/bin/env python3
"""Score the S106 development arms with the exact metric math of scorer_s103.py.

The transform, uint8 conversion and integer metric functions below are copied
verbatim from the contract-bound scorer (SHA 18e82e47...) so the numbers are
directly comparable with the formal baseline score of job 594155.

DEVELOPMENT ONLY.  Runs outside the signed chain.  The future RGB of this window
was already opened by the formal baseline scoring, so no new outcome is exposed.
"""
import hashlib, io, json, math, sys
from pathlib import Path
import numpy as np, torch
from PIL import Image

ARMDIR = Path(sys.argv[1])
SEQ = Path("/home/yliutz/datasets/heldout_3dmatch_scene13/extracted/rgbd-scenes-v2-scene_13/seq-01")
TARGETS = [60, 75, 90, 105]

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

refs = [future_rgb_to_model_grid((SEQ / f"frame-{f:06d}.color.png").read_bytes()) for f in TARGETS]
out = {}
for npy in sorted(ARMDIR.glob("*_target_rgb_fp32.npy")):
    arm = npy.name.replace("_target_rgb_fp32.npy", "")
    arr = np.load(npy)
    require(arr.shape == (4, 3, 576, 576), f"{arm}: unexpected shape {arr.shape}")
    frames, ta, ts, tn = [], 0, 0, 0
    for i, fid in enumerate(TARGETS):
        pred, resc = prediction_to_uint8(arr[i])
        m = integer_metrics(pred, refs[i]); m["frame_id"] = fid; m["rescaled"] = resc
        frames.append(m); ta += m["absolute_integer_sum"]; ts += m["squared_integer_sum"]; tn += m["channel_value_count"]
    agg_mse = ts / (tn * 255 * 255)
    out[arm] = {"frames": frames,
                "aggregate": {"channel_value_count": tn, "mae_0_1": ta / (tn * 255),
                              "mse_0_1": agg_mse, "psnr_db": -10.0 * math.log10(agg_mse)}}

result = {"schema": "s106-development-arm-scores-v1",
          "scope": "development only; metric math copied verbatim from contract-bound scorer 18e82e47",
          "formal_baseline_reference": {"job": 594155, "aggregate_psnr_db": 16.026457673022307,
                                        "aggregate_mae_0_1": 0.1030032951202922},
          "arms": out,
          "geometry_scored": False, "scientific_result": False,
          "new_method_validated": False, "novelty_authorization": "NONE"}
(ARMDIR / "ARM_SCORES.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
print(f"{'arm':24} {'MAE':>8} {'MSE':>10} {'PSNR dB':>9}")
for arm, v in sorted(out.items()):
    a = v["aggregate"]
    print(f"{arm:24} {a['mae_0_1']:8.4f} {a['mse_0_1']:10.6f} {a['psnr_db']:9.3f}")
print(f"{'[formal 594155]':24} {0.1030032951202922:8.4f} {0.024966302754859785:10.6f} {16.026457673022307:9.3f}")
