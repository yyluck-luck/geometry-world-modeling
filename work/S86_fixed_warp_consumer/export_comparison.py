#!/usr/bin/env python3
"""S86 fixed full comparison export after root binds completed generation/scoring."""
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

BASE = Path(__file__).resolve().parent
ARMS = ("G0", "Gpaste", "Gterminal", "Gguide")
TARGETS = (20, 21, 22, 23)
LABELS = {
    "reference": "真实参考 | Real reference",
    "warp": "历史投影 | Fixed history warp",
    "warp_zero": "历史投影，孔洞为零 | Warp with zero holes",
    "mask": "预测支持掩码：白=支持，黑=孔洞 | White=support; black=hole",
    "G0": "G0 原生成 | Original generation",
    "Gpaste": "Gpaste 末端贴图 | RGB paste",
    "Gterminal": "Gterminal 末步融合 | Terminal fusion",
    "Gguide": "Gguide 采样引导 | Sampling guidance",
}
for key in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
            "VECLIB_MAXIMUM_THREADS", "NUMEXPR_NUM_THREADS", "BLIS_NUM_THREADS"):
    os.environ[key] = "1"


def utc():
    return datetime.now(timezone.utc).isoformat()


def sha(data):
    return hashlib.sha256(data).hexdigest()


def require(condition, message):
    if not bool(condition):
        raise RuntimeError(message)


def write_json(path, obj):
    with path.open("x") as stream:
        json.dump(obj, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write("\n")


def main():
    contract_bytes = (BASE / "EXPORT_CONTRACT.json").read_bytes()
    cfg = json.loads(contract_bytes)
    require(sha(Path(__file__).read_bytes()) == cfg["exporter_sha256"], "exporter SHA")
    output = BASE / "visuals_01"
    require(str(output) == cfg["output_directory"], "output directory")
    output.mkdir(exist_ok=False)
    started = time.monotonic()
    report = dict(status="STARTED", started_utc=utc(), reads=[], images=[],
                  export_contract_sha256=sha(contract_bytes), model_calls=0,
                  projection_calls=0, score_calls=0, new_method_validated=False)
    exit_code = 1

    def read(path, kind, digest=None, size=None):
        path = Path(path)
        record = dict(path=str(path), kind=kind, started_utc=utc())
        report["reads"].append(record)
        raw = path.read_bytes()
        record.update(bytes=len(raw), sha256=sha(raw), completed_utc=utc())
        require(digest is None or record["sha256"] == digest, "input SHA: " + str(path))
        require(size is None or len(raw) == size, "input bytes: " + str(path))
        return raw

    def bound(spec, kind):
        return read(spec["path"], kind, spec["sha256"], spec["bytes"])

    def budget():
        require(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss <= cfg["limits"]["peak_rss_bytes"],
                "sampled export RSS budget")
        require(sum(p.stat().st_size for p in output.iterdir() if p.is_file()) <= cfg["limits"]["output_bytes"],
                "export output budget")

    def timeout(signum, frame):
        raise TimeoutError("export wall budget")

    previous = signal.signal(signal.SIGALRM, timeout)
    signal.alarm(cfg["limits"]["seconds"])
    try:
        import numpy as np
        import PIL
        from PIL import Image, ImageDraw, ImageFont, PngImagePlugin
        require(np.__version__ == cfg["versions"]["numpy"] and PIL.__version__ == cfg["versions"]["Pillow"],
                "export runtime versions")
        generation_contract = json.loads(bound(cfg["generation_contract"], "generation_contract"))
        scoring_contract = json.loads(bound(cfg["scoring_contract"], "scoring_contract"))
        approval_raw = read(cfg["root_binding_path"], "root_export_binding")
        approval = json.loads(approval_raw)
        require(approval["schema"] == "S86_ROOT_EXPORT_BINDING_V1"
                and approval["accepted"] is True and bool(approval["accepted_utc"]),
                "root has not bound accepted completed results")
        generation_dir = Path(generation_contract["output_directory"])
        scoring_dir = Path(scoring_contract["output_directory"])
        generation_path, scoring_path = generation_dir / "RECEIPT.json", scoring_dir / "RECEIPT.json"
        generation_raw = read(generation_path, "accepted_generation_receipt",
                              approval["generation_receipt_sha256"])
        scoring_raw = read(scoring_path, "accepted_scoring_receipt",
                           approval["scoring_receipt_sha256"])
        generation, scoring = json.loads(generation_raw), json.loads(scoring_raw)
        require(generation["contract_sha256"] == cfg["generation_contract"]["sha256"]
                and generation["status"] == "COMPLETE_FOUR_FIXED_CONSUMER_ARMS_PENDING_REVIEW"
                and generation["unrun_arms"] == [] and set(generation["arms"]) == set(ARMS),
                "generation completion/identity")
        require(scoring["scoring_contract_sha256"] == cfg["scoring_contract"]["sha256"]
                and scoring["generation_final_sha256"] == sha(generation_raw)
                and scoring["status"] == "COMPLETE_DESCRIPTIVE_SCORES_PENDING_INDEPENDENT_REVIEW"
                and scoring["rows_completed"] == 16, "scoring completion/identity")
        require(len(scoring["emission_checks"]) == 16
                and all(r["exact_uint8_match"] is True for r in scoring["emission_checks"]),
                "incomplete emission verification")
        require(generation_contract["controls"]["target_order"] == list(TARGETS)
                and scoring_contract["target_order"] == list(TARGETS)
                and scoring_contract["reference"] == cfg["reference"], "fixed target/reference identities")
        for arm in ARMS:
            expected = "COMPLETE_CHAIN" if arm in ("G0", "Gguide") else "COMPLETE_DERIVED"
            require(generation["arms"][arm]["status"] == expected, "incomplete arm")
        write_json(output / "INPUT_BINDING.json", dict(recorded_utc=utc(),
                   root_export_binding_sha256=sha(approval_raw), root_acceptance=approval,
                   generation_receipt_sha256=sha(generation_raw),
                   scoring_receipt_sha256=sha(scoring_raw),
                   scope="Bound before any display array/reference bytes are read"))

        def load_generated(desc, expected_path, shape, dtype, must_be_scored=False):
            require(desc["path"] == str(expected_path), "unexpected generated path")
            if must_be_scored:
                require(any(r["path"] == str(expected_path)
                            and r.get("sha256") == desc["file_sha256"] for r in scoring["reads"]),
                        "display input was not bound in completed scoring")
            data = read(expected_path, "saved_display_array", desc["file_sha256"])
            array = np.load(io.BytesIO(data), allow_pickle=False)
            require(isinstance(array, np.ndarray) and array.shape == shape
                    and str(array.dtype) == dtype and array.flags.c_contiguous, "display array schema")
            require(desc["shape"] == list(shape) and desc["dtype"] == dtype
                    and desc["body_bytes"] == array.nbytes
                    and desc["body_sha256"] == sha(array.tobytes(order="C")), "display array body identity")
            array.flags.writeable = False
            return array

        methods = {arm: load_generated(
            generation["arms"][arm]["arrays"]["targets_uint8"],
            generation_dir / arm / "targets_uint8.npy", (4, 576, 576, 3), "uint8", True) for arm in ARMS}
        warp = load_generated(generation["warp_rgb"], generation_dir / "warp_rgb01.npy",
                              (4, 3, 576, 576), "float32").transpose(0, 2, 3, 1)
        mask = load_generated(generation["image_mask"], generation_dir / "image_mask.npy",
                              (4, 1, 576, 576), "bool", True)[:, 0]
        require(np.isfinite(warp).all() and ((warp >= 0) & (warp <= 1)).all()
                and (warp[~mask] == 0).all(), "saved warp RGB01/zero holes")
        require(any(r["path"] == cfg["reference"]["path"]
                    and r.get("sha256") == cfg["reference"]["sha256"] for r in scoring["reads"]),
                "reference was not consumed by accepted scoring")
        reference = np.load(io.BytesIO(bound(cfg["reference"], "accepted_transformed_reference")),
                            allow_pickle=False)
        require(isinstance(reference, np.ndarray) and reference.shape == (4, 576, 576, 3)
                and reference.dtype == np.uint8 and reference.flags.c_contiguous, "reference schema")
        reference.flags.writeable = False
        warp8 = np.floor(warp.astype(np.float64) * 255 + 0.5).astype(np.uint8)
        yy, xx = np.indices((576, 576))
        checker = np.where(((yy // 16 + xx // 16) % 2) == 0, 184, 224).astype(np.uint8)
        font_bytes = bound(cfg["font"], "display_font")
        font = ImageFont.truetype(io.BytesIO(font_bytes), 20)
        title_font = ImageFont.truetype(io.BytesIO(font_bytes), 30)
        overview = Image.new("RGB", (3540, 2720), (245, 245, 245))
        draw = ImageDraw.Draw(overview)
        draw.text((12, 8), "S86：四个目标、全部四种方法 | Four targets, all four methods",
                  font=title_font, fill="black")
        draw.text((12, 49), "参考=已保存真实图；投影=历史颜色与预测几何；灰格=无投影支持，不是真实可见性。",
                  font=font, fill="black")
        draw.text((12, 79), "Reference: saved real image. Warp: historical RGB with predicted geometry. Checkerboard: no support, not GT visibility.",
                  font=font, fill="black")

        def save_png(image, filename, target, role):
            path = output / filename
            description = (f"目标 {target} | Target {target}; " if target is not None else "") + LABELS.get(role, role)
            metadata = PngImagePlugin.PngInfo()
            metadata.add_itxt("Description", description)
            image.save(path, format="PNG", pnginfo=metadata)
            raw = path.read_bytes()
            with Image.open(io.BytesIO(raw)) as reopened:
                reopened.load()
                require(reopened.mode == image.mode and reopened.size == image.size
                        and reopened.tobytes() == image.tobytes(), "export pixel readback mismatch")
            report["images"].append(dict(path=str(path), target_id=target, role=role,
                label=description, bytes=len(raw), sha256=sha(raw), size=list(image.size),
                mode=image.mode, pixel_sha256=sha(image.tobytes()), pixel_readback_exact=True))
            budget()

        columns = ("reference", "warp") + ARMS
        for row, target in enumerate(TARGETS):
            marked = warp8[row].copy()
            marked[~mask[row]] = checker[~mask[row], None]
            images = {"reference": Image.fromarray(reference[row], "RGB"),
                      "warp": Image.fromarray(marked, "RGB")}
            images.update({arm: Image.fromarray(methods[arm][row], "RGB") for arm in ARMS})
            save_png(images["reference"], f"target_{target}_reference.png", target, "reference")
            save_png(Image.fromarray(warp8[row], "RGB"), f"target_{target}_warp_zero.png", target, "warp_zero")
            save_png(images["warp"], f"target_{target}_warp_holes_marked.png", target, "warp")
            save_png(Image.fromarray(mask[row].astype(np.uint8) * 255, "L"),
                     f"target_{target}_mask.png", target, "mask")
            for arm in ARMS:
                save_png(images[arm], f"target_{target}_{arm}.png", target, arm)
            for column, role in enumerate(columns):
                x, y = 12 + column * 588, 108 + row * 650
                draw.text((x, y + 3), f"目标 {target} | Target {target}", font=font, fill="black")
                draw.text((x, y + 31), LABELS[role], font=font, fill="black")
                overview.paste(images[role], (x, y + 62))
        save_png(overview, "overview_4targets_6columns.png", None, "全部目标固定对照 | All fixed target comparisons")
        require(len(report["images"]) == 33, "all32 native images and one overview required")
        write_json(output / "IMAGE_INDEX.json", report["images"])
        require(sha(read(generation_path, "generation_final_recheck")) == sha(generation_raw)
                and sha(read(scoring_path, "scoring_final_recheck")) == sha(scoring_raw),
                "accepted receipt changed during export")
        report["status"] = "COMPLETE_FIXED_COMPARISON_EXPORT_PENDING_VISUAL_QA"
        exit_code = 0
    except BaseException as error:
        report.update(status="FAILED_PARTIAL_EXPORT_PRESERVED", error_type=type(error).__name__,
                      error=str(error), traceback=traceback.format_exc())
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, previous)
        report.update(completed_utc=utc(), elapsed_seconds=time.monotonic() - started,
                      peak_self_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                      native_pngs=sum(i["size"] == [576, 576] for i in report["images"]),
                      total_pngs=len(report["images"]))
        report["other_artifacts"] = [dict(path=str(p), bytes=p.stat().st_size, sha256=sha(p.read_bytes()))
                                     for p in sorted(output.iterdir()) if p.suffix == ".json"]
        write_json(output / "EXPORT_RECEIPT.json", report)
    print(json.dumps(dict(status=report["status"], receipt=str(output / "EXPORT_RECEIPT.json"))))
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
