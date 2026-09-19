#!/usr/bin/env python3
"""Read saved S85 warp/mask only; export display copies, never project or score."""
import hashlib
import io
import json
import os
from pathlib import Path
import resource
import signal
import sys
import time
import traceback
from datetime import datetime, timezone

for name in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
             "VECLIB_MAXIMUM_THREADS", "NUMEXPR_NUM_THREADS", "BLIS_NUM_THREADS"):
    os.environ[name] = "1"

BASE = Path(__file__).resolve().parent


def utc():
    return datetime.now(timezone.utc).isoformat()


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    contract_raw = (BASE / "EXPORT_CONTRACT.json").read_bytes()
    contract = json.loads(contract_raw)
    if sha(Path(__file__).read_bytes()) != contract["exporter_sha256"]:
        raise RuntimeError("exporter identity mismatch")
    out = Path(contract["output_directory"])
    out.mkdir(exist_ok=False)
    started = time.monotonic()
    receipt = dict(status="STARTED", started_utc=utc(),
                   contract_sha256=sha(contract_raw), reads=[], artifacts=[],
                   targets=[], projection_calls=0, model_calls=0,
                   original_RGB_reads=0, target_RGB_reads=0, sensor_depth_reads=0,
                   geometry_accuracy_measured=False)

    def budget():
        rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        size = sum(p.stat().st_size for p in out.iterdir() if p.is_file())
        if rss > contract["limits"]["peak_rss_bytes"] or size > contract["limits"]["output_bytes"]:
            raise RuntimeError("sampled export resource budget exceeded")

    def read_bound(item, decoded_fields):
        raw = Path(item["path"]).read_bytes()
        receipt["reads"].append(dict(path=item["path"], bytes=len(raw),
                                    sha256=sha(raw), decoded_fields=decoded_fields))
        if len(raw) != item["bytes"] or sha(raw) != item["sha256"]:
            raise RuntimeError("source identity mismatch: " + item["path"])
        budget()
        return raw

    def save_png(im, name):
        path = out / name
        im.save(path, format="PNG")
        data = path.read_bytes()
        receipt["artifacts"].append(dict(path=str(path), bytes=len(data),
                                         sha256=sha(data), size=list(im.size), mode=im.mode))
        budget()

    def timeout(signum, frame):
        raise TimeoutError("120 second export budget reached")

    old_handler = signal.signal(signal.SIGALRM, timeout)
    signal.alarm(contract["limits"]["seconds"])
    exit_code = 1
    try:
        import numpy as np
        import PIL
        from PIL import Image, ImageDraw, ImageFont
        if np.__version__ != contract["versions"]["numpy"] or PIL.__version__ != contract["versions"]["Pillow"]:
            raise RuntimeError("runtime version mismatch")
        source_receipt = json.loads(read_bound(contract["source_receipt"], ["JSON metadata"]))
        receipt["source_receipt_recorded_science_status"] = source_receipt["status"]
        font_raw = read_bound(contract["font"], ["font"])
        font = ImageFont.truetype(io.BytesIO(font_raw), 20)
        title_font = ImageFont.truetype(io.BytesIO(font_raw), 27)
        overview = Image.new("RGB", (2364, 1346), "white")
        draw = ImageDraw.Draw(overview)
        draw.text((12, 9), "S85 | Historical RGB reprojected using predicted geometry",
                  font=title_font, fill="black")
        draw.text((12, 44),
                  "Top: checkerboard = no projected support. Bottom: white = support, black = hole. Neither is ground-truth visibility.",
                  font=font, fill="black")
        yy, xx = np.indices((576, 576))
        checker = np.where(((yy // 16 + xx // 16) % 2) == 0, 184, 224).astype(np.uint8)
        for column, item in enumerate(contract["targets"]):
            tid = item["target_id"]
            raw = read_bound(item, ["warp_rgb", "mask"])
            with np.load(io.BytesIO(raw), allow_pickle=False) as archive:
                rgb = archive["warp_rgb"]
                mask = archive["mask"]
            del raw
            if rgb.shape != (576, 576, 3) or rgb.dtype != np.float32:
                raise RuntimeError("unexpected warp_rgb schema")
            if mask.shape != (576, 576) or mask.dtype != np.bool_:
                raise RuntimeError("unexpected mask schema")
            if not np.isfinite(rgb).all() or np.any(rgb < 0) or np.any(rgb > 1):
                raise RuntimeError("warp_rgb outside finite RGB01")
            if np.any(rgb[~mask] != 0):
                raise RuntimeError("hole fill violates frozen scientific zero fill")
            rgb.flags.writeable = False
            mask.flags.writeable = False
            rgb8 = np.floor(rgb.astype(np.float64) * 255 + 0.5).astype(np.uint8)
            marked = rgb8.copy()
            marked[~mask] = checker[~mask, None]
            rgb_image = Image.fromarray(rgb8, "RGB")
            marked_image = Image.fromarray(marked, "RGB")
            mask_image = Image.fromarray(mask.astype(np.uint8) * 255, "L")
            save_png(rgb_image, f"target_{tid}_warp.png")
            save_png(mask_image, f"target_{tid}_mask.png")
            save_png(marked_image, f"target_{tid}_holes_marked.png")
            x = 12 + column * 588
            for row, im, label in (
                    (0, marked_image, "reprojected historical RGB"),
                    (1, mask_image, "predicted support mask")):
                y = 78 + row * 628
                draw.text((x, y + 7), f"Target {tid} | {label}", font=font, fill="black")
                overview.paste(im, (x, y + 40))
            support = int(mask.sum())
            receipt["targets"].append(dict(target_id=tid, support_pixels=support,
                                            hole_pixels=576 * 576 - support,
                                            target_pixel_denominator=576 * 576))
            budget()
        save_png(overview, "overview_2x4.png")
        receipt["status"] = "EXPORTED_VISUALS_NOT_GEOMETRY_VALIDATION"
        exit_code = 0
    except Exception:
        receipt["status"] = "FAILED_PARTIAL_OUTPUT_PRESERVED"
        (out / "TRACEBACK.txt").write_text(traceback.format_exc())
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old_handler)
        receipt["completed_utc"] = utc()
        receipt["elapsed_seconds"] = time.monotonic() - started
        receipt["peak_self_rss_bytes"] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        receipt["resource_enforcement"] = "SIGALRM time limit; RSS/output sampled between stages, not kernel hard caps"
        (out / "EXPORT_RECEIPT.json").write_text(json.dumps(receipt, indent=2) + "\n")
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
