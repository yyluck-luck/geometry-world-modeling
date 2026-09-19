#!/usr/bin/env python3
"""S86 saved-output scoring only; NumPy emission check and exact int64 SSE."""
import csv
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
REGIONS = ("full", "support", "hole")
for key in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
            "VECLIB_MAXIMUM_THREADS", "NUMEXPR_NUM_THREADS", "BLIS_NUM_THREADS"):
    os.environ[key] = "1"


def utc():
    return datetime.now(timezone.utc).isoformat()


def sha(data):
    return hashlib.sha256(data).hexdigest()


def require(value, why):
    if not bool(value):
        raise RuntimeError(why)


def write_json(path, value):
    with path.open("x") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write("\n")


def quantize_raw(np, raw):
    """Independent reimplementation of the bound per-frame emission arithmetic."""
    image = raw.transpose(1, 2, 0)
    branch = bool(image.min() < -0.1)
    if branch:
        image = (image + 1) / 2.0
    emitted = np.clip(image * 255, 0, 255).astype(np.uint8)
    return emitted, branch


def main():
    contract_raw = (BASE / "SCORING_CONTRACT.json").read_bytes()
    cfg = json.loads(contract_raw)
    require(sha(Path(__file__).read_bytes()) == cfg["scorer_sha256"], "scorer identity")
    out = BASE / "scoring_01"
    require(str(out) == cfg["output_directory"], "score output directory")
    out.mkdir(exist_ok=False)
    began = time.monotonic()
    report = dict(status="STARTED", started_utc=utc(),
                  scoring_contract_sha256=sha(contract_raw), reads=[], emission_checks=[],
                  model_calls=0, original_RGB_reads=0, projection_calls=0,
                  new_method_validated=False, statistics="descriptive only")
    rows = []
    row_stream = None
    return_code = 1

    def read(path, kind, digest=None, size=None):
        path = Path(path)
        record = dict(path=str(path), kind=kind, started_utc=utc())
        report["reads"].append(record)
        data = path.read_bytes()
        record.update(bytes=len(data), sha256=sha(data), completed_utc=utc())
        require(digest is None or record["sha256"] == digest, "file SHA mismatch: " + str(path))
        require(size is None or len(data) == size, "file size mismatch: " + str(path))
        return data

    def budget():
        require(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss <= cfg["limits"]["peak_rss_bytes"],
                "sampled scoring RSS budget exceeded")
        require(sum(p.stat().st_size for p in out.iterdir() if p.is_file()) <= cfg["limits"]["output_bytes"],
                "scoring output budget exceeded")

    def timeout(signum, frame):
        raise TimeoutError("scoring wall budget exceeded")

    previous = signal.signal(signal.SIGALRM, timeout)
    signal.alarm(cfg["limits"]["seconds"])
    try:
        import numpy as np
        require(np.__version__ == cfg["numpy_version"], "NumPy version")
        gc = cfg["generation_contract"]
        generation_contract = json.loads(read(gc["path"], "generation_contract", gc["sha256"], gc["bytes"]))
        require(generation_contract["scoring"] == cfg["generation_scoring_rules"],
                "frozen generation scoring rules differ")
        require(generation_contract["scoring"]["frame_channel_denominator"] == 995328
                and generation_contract["scoring"]["total_channel_denominator"] == 3981312,
                "frozen full-frame denominators differ")
        require(generation_contract["controls"]["target_order"] == list(TARGETS), "target order")
        generation_dir = Path(generation_contract["output_directory"])
        require(str(generation_dir) == cfg["generation_directory"], "generation directory identity")
        generation_path = generation_dir / "RECEIPT.json"
        generation_bytes = read(generation_path, "final_generation_receipt")
        generation_sha = sha(generation_bytes)
        generation = json.loads(generation_bytes)
        require(generation["contract_sha256"] == gc["sha256"], "generation receipt contract identity")
        require(generation["status"] == "COMPLETE_FOUR_FIXED_CONSUMER_ARMS_PENDING_REVIEW",
                "generation is not complete and sealed")
        require(bool(generation.get("completed_utc")) and generation["unrun_arms"] == [],
                "generation has missing completion/arms")
        require(set(generation["arms"]) == set(ARMS), "four exact arms required")
        require(generation["full_chain_calls"] == 2
                and generation["shared_actual_random_stream"] is True
                and generation["G0_last_replay_exact"] is True
                and generation["derived_rng_unchanged"] is True,
                "generation prerequisite checks did not complete")
        arm_receipts = {}
        for arm in ARMS:
            item = generation["arms"][arm]
            expected_status = "COMPLETE_CHAIN" if arm in ("G0", "Gguide") else "COMPLETE_DERIVED"
            require(item["status"] == expected_status and bool(item.get("completed_utc")),
                    "arm incomplete: " + arm)
            arm_bytes = read(generation_dir / arm / "receipt.json", "completed_arm_receipt")
            require(json.loads(arm_bytes) == item, "arm/global receipt mismatch: " + arm)
            arm_receipts[arm] = sha(arm_bytes)
        binding = dict(recorded_utc=utc(), generation_receipt_path=str(generation_path),
                       generation_receipt_sha256=generation_sha,
                       generation_completed_utc=generation["completed_utc"],
                       generation_contract_sha256=gc["sha256"],
                       arm_receipt_sha256=arm_receipts,
                       prediction_descriptors={a: generation["arms"][a]["arrays"] for a in ARMS},
                       mask_descriptor=generation["image_mask"],
                       scope="Recorded before any scoring array/reference bytes are read")
        write_json(out / "INPUT_BINDING.json", binding)
        report["generation_final_sha256"] = generation_sha

        def generated_array(desc, expected_path, shape, dtype):
            require(desc["path"] == str(expected_path), "unexpected generated array path")
            data = read(expected_path, "sealed_generated_array", desc["file_sha256"])
            array = np.load(io.BytesIO(data), allow_pickle=False)
            require(isinstance(array, np.ndarray) and array.shape == shape
                    and str(array.dtype) == dtype and array.flags.c_contiguous, "generated schema")
            body = array.tobytes(order="C")
            info = dict(shape=list(array.shape), dtype=str(array.dtype), body_bytes=array.nbytes,
                        body_sha256=sha(body))
            require(all(desc[k] == value for k, value in info.items()), "generated body identity")
            array.flags.writeable = False
            budget()
            return array

        mask = generated_array(generation["image_mask"], generation_dir / "image_mask.npy",
                               (4, 1, 576, 576), "bool")[:, 0]
        emitted = {}
        for arm in ARMS:
            item = generation["arms"][arm]
            raw = generated_array(item["arrays"]["targets_fp32"],
                                  generation_dir / arm / "targets_fp32.npy", (4, 3, 576, 576), "float32")
            require(np.isfinite(raw).all(), "nonfinite raw emission: " + arm)
            actual = generated_array(item["arrays"]["targets_uint8"],
                                     generation_dir / arm / "targets_uint8.npy", (4, 576, 576, 3), "uint8")
            require(len(item["quantizer"]) == 4, "missing quantizer records")
            if arm == "Gpaste":
                require(((raw >= 0) & (raw <= 1)).all(), "Gpaste must already be RGB01")
            for i, target in enumerate(TARGETS):
                predicted, branch = quantize_raw(np, raw[i])
                mismatches = int(np.count_nonzero(predicted != actual[i]))
                record = dict(arm=arm, target_id=target, raw_min=float(raw[i].min()),
                              raw_max=float(raw[i].max()), maps_minus1_plus1=branch,
                              mismatching_channels=mismatches, exact_uint8_match=mismatches == 0)
                report["emission_checks"].append(record)
                require(mismatches == 0, "raw/uint8 emission mismatch")
                original = item["quantizer"][i]
                require(original["target_id"] == target
                        and original["raw_min"] == record["raw_min"]
                        and original["raw_max"] == record["raw_max"]
                        and original["maps_minus1_plus1"] is branch, "quantizer metadata mismatch")
            emitted[arm] = actual
            del raw
        require(len(report["emission_checks"]) == 16, "incomplete emission validation")
        require(sha(read(generation_path, "generation_receipt_recheck_before_reference")) == generation_sha,
                "generation receipt changed before reference read")
        ref = cfg["reference"]
        require(ref["path"] == generation_contract["scoring"]["reference_path"]
                and ref["bytes"] == generation_contract["scoring"]["reference_bytes"]
                and ref["sha256"] == generation_contract["scoring"]["reference_sha256"],
                "reference identity differs from generation contract")
        reference_bytes = read(ref["path"], "accepted_transformed_reference", ref["sha256"], ref["bytes"])
        reference = np.load(io.BytesIO(reference_bytes), allow_pickle=False)
        require(isinstance(reference, np.ndarray) and reference.shape == (4, 576, 576, 3)
                and reference.dtype == np.uint8 and reference.flags.c_contiguous, "reference schema")
        reference.flags.writeable = False
        del reference_bytes
        fields = ["arm", "target_id"]
        for region in REGIONS:
            fields += [region + "_" + key for key in ("pixels", "channels", "sse", "mse", "empty")]
        row_stream = (out / "FRAME_SCORES.csv").open("x", newline="")
        writer = csv.DictWriter(row_stream, fieldnames=fields)
        writer.writeheader()
        for arm in ARMS:
            for i, target in enumerate(TARGETS):
                difference = emitted[arm][i].astype(np.int64) - reference[i].astype(np.int64)
                square = difference * difference
                full_sse = int(square.sum(dtype=np.int64))
                support_sse = int(square[mask[i]].sum(dtype=np.int64))
                hole_sse = int(square[~mask[i]].sum(dtype=np.int64))
                support_pixels = int(mask[i].sum(dtype=np.int64))
                require(full_sse == support_sse + hole_sse, "SSE partition mismatch")
                row = dict(arm=arm, target_id=target)
                values = ((331776, full_sse), (support_pixels, support_sse),
                          (331776 - support_pixels, hole_sse))
                for region, (pixels, sse) in zip(REGIONS, values):
                    channels = pixels * 3
                    row.update({region + "_pixels": pixels, region + "_channels": channels,
                                region + "_sse": sse,
                                region + "_mse": None if channels == 0 else sse / (channels * 65025),
                                region + "_empty": channels == 0})
                rows.append(row)
                writer.writerow(row)
                row_stream.flush()
                budget()
        require(len(rows) == 16, "complete sixteen rows required")
        summary = {}
        for arm in ARMS:
            arm_rows = [row for row in rows if row["arm"] == arm]
            require(len(arm_rows) == 4, "four-target mean cannot drop frames")
            summary[arm] = {}
            for region in REGIONS:
                sse = sum(row[region + "_sse"] for row in arm_rows)
                channels = sum(row[region + "_channels"] for row in arm_rows)
                complete = all(not row[region + "_empty"] for row in arm_rows)
                if region == "full":
                    mean = sse / (3981312 * 65025)
                else:
                    mean = sum(row[region + "_mse"] for row in arm_rows) / 4 if complete else None
                summary[arm][region] = dict(total_sse=sse, total_channels=channels,
                                            complete_four_frames=complete, equal_frame_mean_mse=mean,
                                            pooled_mse=None if channels == 0 else sse / (channels * 65025))
        frame_contrasts, overall_contrasts = [], []
        indexed = {(r["arm"], r["target_id"]): r for r in rows}
        for control in ("Gterminal", "G0", "Gpaste"):
            overall = dict(comparison="Gguide-" + control, negative_favors="Gguide")
            for region in REGIONS:
                guide = summary["Gguide"][region]
                base = summary[control][region]
                overall[region + "_total_sse_difference"] = guide["total_sse"] - base["total_sse"]
                require(guide["total_channels"] == base["total_channels"], "pooled denominator mismatch")
                total_channels = guide["total_channels"]
                overall[region + "_pooled_mse_difference"] = (None if total_channels == 0 else
                    (guide["total_sse"] - base["total_sse"]) / (total_channels * 65025))
                gm, bm = guide["equal_frame_mean_mse"], base["equal_frame_mean_mse"]
                overall[region + "_mean_mse_difference"] = None if gm is None or bm is None else gm - bm
                if region == "full":
                    overall[region + "_mean_mse_difference"] = (guide["total_sse"] - base["total_sse"]) / (3981312 * 65025)
            overall_contrasts.append(overall)
            for target in TARGETS:
                pair = dict(comparison="Gguide-" + control, target_id=target)
                for region in REGIONS:
                    g, c = indexed["Gguide", target], indexed[control, target]
                    require(g[region + "_channels"] == c[region + "_channels"], "contrast denominator mismatch")
                    channels = g[region + "_channels"]
                    delta = g[region + "_sse"] - c[region + "_sse"]
                    pair[region + "_sse_difference"] = delta
                    pair[region + "_mse_difference"] = None if channels == 0 else delta / (channels * 65025)
                frame_contrasts.append(pair)
        write_json(out / "FRAME_SCORES.json", rows)
        write_json(out / "ARM_SUMMARY.json", summary)
        write_json(out / "CONTRASTS.json", dict(overall=overall_contrasts, per_target=frame_contrasts,
                   warning="Descriptive one-scene comparisons. Region total SSE differences describe pooled error; their sign need not equal the sign of an equally weighted four-frame regional mean."))
        require(sha(read(generation_path, "final_generation_receipt_recheck")) == generation_sha,
                "generation receipt changed during scoring")
        report.update(status="COMPLETE_DESCRIPTIVE_SCORES_PENDING_INDEPENDENT_REVIEW",
                      rows_completed=16, reference_is_historically_seen=True,
                      full_channel_denominator_per_frame=995328,
                      full_channel_denominator_all_four_frames=3981312,
                      empty_region_policy="MSE null/CSV blank; no reduced-frame equal mean")
        return_code = 0
    except BaseException as error:
        report.update(status="FAILED_INCOMPLETE_COMPARISON_PARTIAL_PRESERVED",
                      error_type=type(error).__name__, error=str(error), traceback=traceback.format_exc())
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, previous)
        if row_stream is not None:
            row_stream.close()
        report.update(completed_utc=utc(), elapsed_seconds=time.monotonic() - began,
                      rows_completed=len(rows),
                      peak_self_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
        report["artifacts"] = [
            dict(path=str(p), bytes=p.stat().st_size, sha256=sha(p.read_bytes()))
            for p in sorted(out.iterdir()) if p.is_file()]
        write_json(out / "RECEIPT.json", report)
    print(json.dumps(dict(status=report["status"], receipt=str(out / "RECEIPT.json"))))
    return return_code


if __name__ == "__main__":
    sys.exit(main())
