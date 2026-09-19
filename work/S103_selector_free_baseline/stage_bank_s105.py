#!/usr/bin/env python3
"""Stage a 12-frame memory bank for the retrieval-active configuration.

Bank frames are 0,5,...,55 -- all strictly earlier than the first target (60),
so no future information enters the bank.  Target cameras 60/75/90/105 are
staged as pose-only: their RGB and depth are NOT copied, so the retrieval probe
physically cannot read a future image.
"""
import hashlib, json, shutil, sys
from pathlib import Path

SRC = Path("/home/yliutz/datasets/heldout_3dmatch_scene13/extracted/rgbd-scenes-v2-scene_13")
SEQ = SRC / "seq-01"
OUT = Path("/home/yliutz/gwm_stages/S105_SCENE13_BANK12_20260917")
BANK = list(range(0, 60, 5))          # 0,5,...,55  -> 12 frames
TARGETS = [60, 75, 90, 105]           # identical to the S103 window

def sha(p):
    h = hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""): h.update(b)
    return h.hexdigest()

def ref(p):
    return {"path": str(p), "bytes": p.stat().st_size, "sha256": sha(p)}

def main():
    assert max(BANK) < min(TARGETS), "bank must be strictly before targets"
    if OUT.exists():
        raise SystemExit(f"refusing to overwrite existing stage: {OUT}")
    (OUT / "bank").mkdir(parents=True)
    (OUT / "query").mkdir()
    records = []
    for fid in BANK:
        for suffix, role in (("color.png", "bank_rgb"), ("pose.txt", "bank_pose")):
            src = SEQ / f"frame-{fid:06d}.{suffix}"
            dst = OUT / "bank" / src.name
            shutil.copy2(src, dst)
            records.append({"role": role, "frame_id": fid, "file": ref(dst),
                            "source": ref(src)})
    for fid in TARGETS:
        src = SEQ / f"frame-{fid:06d}.pose.txt"
        dst = OUT / "query" / src.name
        shutil.copy2(src, dst)
        records.append({"role": "command_camera", "frame_id": fid, "file": ref(dst),
                        "source": ref(src)})
    k = SRC / "camera-intrinsics.txt"
    kd = OUT / "camera-intrinsics.txt"
    shutil.copy2(k, kd)
    manifest = {
        "schema": "s105-retrieval-bank-stage-v1",
        "purpose": ("Development feasibility stage for the retrieval-active VMem "
                    "configuration. Bank is larger than k so retrieval is not forced."),
        "dataset_id": "rgbd-scenes-v2",
        "scene_id": "rgbd-scenes-v2-scene_13",
        "sequence": "seq-01",
        "bank_frame_ids": BANK,
        "bank_size": len(BANK),
        "target_frame_ids": TARGETS,
        "selection_k": 4,
        "bank_strictly_before_targets": True,
        "future_rgb_staged": False,
        "future_depth_staged": False,
        "note": ("Target frames are staged as pose only. Their RGB and depth are not "
                 "present in this stage, so a probe running against it cannot read them."),
        "intrinsics_ref": ref(kd),
        "records": records,
    }
    (OUT / "BANK_MANIFEST.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"stage": str(OUT), "bank_size": len(BANK),
                      "targets": TARGETS, "files": len(records),
                      "manifest": ref(OUT / "BANK_MANIFEST.json")}, indent=2))

if __name__ == "__main__":
    raise SystemExit(main())
