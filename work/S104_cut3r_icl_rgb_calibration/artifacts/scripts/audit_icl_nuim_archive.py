#!/usr/bin/env python3
"""Structural-only audit of the official ICL-NUIM TUM-compatible archive.

Reads archive member names, associations, pose text, and PNG IHDR headers.
It does not decode image pixels or run a model.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import struct
import tarfile
from pathlib import Path


def png_header(fobj):
    head = fobj.read(29)
    if len(head) < 29 or head[:8] != b"\x89PNG\r\n\x1a\n" or head[12:16] != b"IHDR":
        return None
    w, h, depth, color, comp, filt, interlace = struct.unpack(">IIBBBBB", head[16:29])
    return {"width": w, "height": h, "bit_depth": depth, "color_type": color,
            "compression": comp, "filter": filt, "interlace": interlace}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("archive", type=Path)
    ap.add_argument("output", type=Path)
    args = ap.parse_args()
    sha = hashlib.sha256(args.archive.read_bytes()).hexdigest()
    with tarfile.open(args.archive, "r:gz") as tf:
        members = [m for m in tf.getmembers() if m.isfile()]
        names = {m.name: m for m in members}
        rgb = sorted(m.name for m in members if m.name.startswith("rgb/") and m.name.endswith(".png"))
        depth = sorted(m.name for m in members if m.name.startswith("depth/") and m.name.endswith(".png"))
        assoc_text = tf.extractfile(names["associations.txt"]).read().decode("utf-8", "replace")
        assoc = []
        for line in assoc_text.splitlines():
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            cols = line.split()
            if len(cols) >= 4:
                assoc.append({"depth_index": int(cols[0]), "depth_path": cols[1],
                              "rgb_index": int(cols[2]), "rgb_path": cols[3]})
        pose_name = next((n for n in names if n.endswith(".gt.freiburg")), None)
        pose_text = tf.extractfile(names[pose_name]).read().decode("utf-8", "replace") if pose_name else ""
        pose_rows = [ln for ln in pose_text.splitlines() if ln.strip() and not ln.lstrip().startswith("#")]
        samples = {}
        for kind, paths in (("rgb", rgb), ("depth", depth)):
            seen = sorted(set(paths))
            sample = []
            for p in seen[:5]:
                hdr = png_header(tf.extractfile(names[p]))
                sample.append({"path": p, "bytes": names[p].size, "png_ihdr": hdr})
            samples[kind] = sample
        paired = [(x["depth_path"], x["rgb_path"]) for x in assoc
                  if x["depth_path"] in names and x["rgb_path"] in names]
        result = {
            "schema": "ICL_NUIM_ARCHIVE_STRUCTURAL_AUDIT_v1",
            "archive": str(args.archive),
            "archive_sha256": sha,
            "archive_bytes": args.archive.stat().st_size,
            "member_count": len(members),
            "rgb_png_count": len(rgb),
            "depth_png_count": len(depth),
            "association_rows": len(assoc),
            "association_existing_pairs": len(paired),
            "association_unique_depth": len({x[0] for x in paired}),
            "association_unique_rgb": len({x[1] for x in paired}),
            "pose_member": pose_name,
            "pose_rows": len(pose_rows),
            "sample_headers": samples,
            "timestamp_semantics": "frame_index_only; official TUM-compatible archive has no sensor timestamp column",
            "depth_semantics": "requires official ICL-NUIM conversion; calibration page specifies z-coordinate conversion and negative fy",
            "license_source": "official page states CC BY 3.0",
            "pixel_decode": False,
            "model_execution": False,
            "gate0_status": "BLOCKED_TIMESTAMP_AND_EXPOSURE_AUDIT_PENDING",
            "notes": [
                "Structural counts only; no image pixels decoded.",
                "A frame-index/30Hz rule is not the same as a hardware timestamp.",
                "GT pose text is present for qualification but must remain inaccessible to selector until prediction seal."
            ]
        }
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
