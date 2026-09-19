"""Frozen single-anchor sensor-reference diagnostic; import does not read data.

Only root may invoke main after independent pre-review. No fitting or models.
"""
from datetime import datetime, timezone
import csv
import hashlib
import importlib.metadata
import io
import json
import os
from pathlib import Path
import resource
import signal
import sys
import time
import traceback

HERE = Path(__file__).resolve().parent
OUT = HERE / "execution_01"
sys.dont_write_bytecode = True


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def require(ok, label):
    if not ok:
        raise ValueError(label)


def score(np, initial, final, raw, c):
    """Pure FP64 arithmetic. Invalid reference and prediction rows stay present."""
    require(initial.shape == final.shape == (384, 512), "anchor shape")
    require(raw.shape == (480, 640), "sensor shape")
    v, u = np.indices((384, 512), dtype=np.int64)
    u, v = u.ravel(), v.ravel()
    x, y = u.astype(np.float64) * 1.25, v.astype(np.float64) * 1.25
    ix, iy = np.floor(x + .5).astype(np.int64), np.floor(y + .5).astype(np.int64)
    domain = (x >= 0) & (x <= 639) & (y >= 0) & (y <= 479)
    domain &= (ix >= 0) & (ix < 640) & (iy >= 0) & (iy < 480)
    sensor = np.full(len(u), -1, dtype=np.int64)
    sensor[domain] = raw[iy[domain], ix[domain]]
    valid = domain & (sensor > 0)
    ref = np.full(len(u), np.nan, dtype=np.float64)
    ref[valid] = sensor[valid].astype(np.float64) / 5000.
    rows = dict(index=np.arange(len(u)), u=u, v=v, native_u=x, native_v=y,
                sensor_u=ix, sensor_v=iy, in_domain=domain, sensor_raw=sensor,
                reference_valid=valid, reference_z_m=ref)
    count = int(valid.sum())
    summary = dict(N=len(u), V=count, V_over_N=count / len(u),
                   outside_domain=int((~domain).sum()),
                   missing_sensor_zero=int((domain & (sensor == 0)).sum()), stages={})
    require(summary["outside_domain"] + summary["missing_sensor_zero"] + count == len(u), "denominator partition")
    for name, depth in [("initial", initial), ("final", final)]:
        z = np.asarray(depth, dtype=np.float64).ravel()
        nonfinite = ~np.isfinite(z)
        nonpositive = np.isfinite(z) & (z <= 0)
        good = ~(nonfinite | nonpositive)
        error = np.full(len(u), np.nan, dtype=np.float64)
        relative = error.copy()
        evaluable = valid & good
        error[evaluable] = np.abs(z[evaluable] - ref[evaluable])
        relative[evaluable] = error[evaluable] / ref[evaluable]
        rows.update({name + "_z_m": z, name + "_nonfinite": nonfinite,
                     name + "_nonpositive": nonpositive, name + "_valid": good,
                     name + "_abs_error_m": error, name + "_absrel": relative})
        n_bad = int((valid & ~good).sum())
        complete = count > 0 and n_bad == 0
        summary["stages"][name] = dict(
            prediction_nonfinite_on_V=int((valid & nonfinite).sum()),
            prediction_nonpositive_on_V=int((valid & nonpositive).sum()),
            prediction_valid_on_V=int(evaluable.sum()), denominator=count,
            status="COMPLETE" if complete else ("NO_REFERENCE" if not count else "INVALID_PREDICTION"),
            mae_m=float(error[valid].mean(dtype=np.float64)) if complete else None,
            mae_extended="finite" if complete else ("undefined" if not count else "+Infinity"),
            absrel_mean=float(relative[valid].mean(dtype=np.float64)) if complete else None,
            absolute_error_median_m=float(np.median(error[valid])) if complete else None)
    paired = valid & rows["initial_valid"] & rows["final_valid"]
    delta = np.full(len(u), np.nan, dtype=np.float64)
    delta[paired] = rows["final_abs_error_m"][paired] - rows["initial_abs_error_m"][paired]
    rows["error_change_m"] = delta
    counts = dict(denominator=count, paired_valid=int(paired.sum()),
                  decreased=int((paired & (delta < 0)).sum()),
                  unchanged=int((paired & (delta == 0)).sum()),
                  increased=int((paired & (delta > 0)).sum()),
                  unavailable=int((valid & ~paired).sum()))
    require(sum(counts[k] for k in ["decreased", "unchanged", "increased", "unavailable"]) == count, "paired partition")
    summary["pixel_counts_descriptive_only"] = counts
    complete = all(s["status"] == "COMPLETE" for s in summary["stages"].values())
    d = summary["stages"]["final"]["mae_m"] - summary["stages"]["initial"]["mae_m"] if complete else None
    tol = c["numeric"]["decision_tolerance_m"]
    outcome = "UNSCORABLE" if d is None else ("REFERENCE_MAE_DECREASE" if d < -tol else (
        "REFERENCE_MAE_INCREASE" if d > tol else "NO_RESOLVABLE_CHANGE"))
    summary.update(delta_mae_m=d, decision_tolerance_m=tol, local_outcome=outcome,
                   independent_recompute_required=True, scientific_acceptance=False,
                   new_method_validated=False)
    return rows, summary


def main():
    cbytes = (HERE / "CONTRACT.json").read_bytes()
    c = json.loads(cbytes)
    require(sys.argv[1:] == ["--execute-contract-sha256", sha(cbytes)], "explicit frozen-contract invocation required")
    OUT.mkdir(exist_ok=False)
    started = time.monotonic()
    r = dict(status="RUNNING", started_utc=datetime.now(timezone.utc).isoformat(),
             contract_sha256=sha(cbytes), reads=[], outputs=[], rows_written=0,
             model_calls=0, optimizer_calls=0, sensor_png_decode_attempts=0, sensor_png_decodes=0,
             decoded_state_fields=[], scientific_acceptance=False, new_method_validated=False)

    def flush():
        r.update(elapsed_seconds=time.monotonic() - started,
                 peak_self_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
        temp = OUT / "RECEIPT.json.tmp"
        temp.write_text(json.dumps(r, ensure_ascii=False, indent=2, allow_nan=False) + "\n")
        temp.replace(OUT / "RECEIPT.json")

    def limit():
        flush()
        require(r["elapsed_seconds"] <= c["resources"]["wall_seconds"], "wall budget")
        require(r["peak_self_rss_bytes"] <= c["resources"]["rss_bytes"], "sampled self RSS budget")

    def timeout(*_):
        raise TimeoutError("S84 deadline; preserve partial output")

    allowed = {s["path"] for s in c["inputs"]}
    def guard(event, args):
        if event in {"socket.connect", "socket.getaddrinfo", "urllib.Request", "subprocess.Popen", "os.system"}:
            raise RuntimeError("network/subprocess forbidden")
        if event == "open" and isinstance(args[0], (str, bytes, os.PathLike)):
            p = Path(os.fsdecode(args[0])).resolve()
            mode, flags = args[1], args[2]
            writing = (isinstance(mode, str) and any(x in mode for x in "wax+")) or (
                isinstance(flags, int) and bool(flags & (os.O_WRONLY | os.O_RDWR)))
            require(not writing or p.is_relative_to(OUT), "write outside S84 output")
            if p.suffix.lower() in {".npz", ".npy", ".png", ".jpg", ".pt", ".pth", ".safetensors"}:
                require(p.is_relative_to(OUT) or str(p) in allowed, "unlisted scientific input")

    def load_bytes(spec):
        limit()
        p = Path(spec["path"])
        require(not any(x["path"] == str(p) for x in r["reads"]), "input read twice")
        require(p.stat().st_size == spec["bytes"], "input size")
        raw = p.read_bytes()
        r["reads"].append(dict(path=str(p), bytes=len(raw), sha256=sha(raw)))
        flush()
        require(len(raw) == spec["bytes"] and sha(raw) == spec["sha256"], "input hash")
        return raw

    def save_json(name, value):
        (OUT / name).write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n")

    try:
        sys.addaudithook(guard)
        flush()
        require(sys.platform == "darwin" and sys.executable == c["runtime"]["python"], "runtime path/platform")
        require(Path(c["output_directory"]) == OUT, "output directory")
        require(sha(Path(__file__).read_bytes()) == c["runner_sha256"], "runner hash")
        for spec in c["provenance_texts"]:
            require(sha(Path(spec["path"]).read_bytes()) == spec["sha256"], "provenance text hash")
        require(all(importlib.metadata.version(k) == v for k, v in c["runtime"]["versions"].items()), "library version")
        import numpy as np
        from PIL import Image
        signal.signal(signal.SIGALRM, timeout)
        signal.alarm(c["resources"]["wall_seconds"])
        # Both frozen predictions are read before the sensor reference.
        states = []
        for spec in c["inputs"][:2]:
            raw = load_bytes(spec)
            decoded = dict(path=spec["path"], fields_attempted=[], fields_decoded=[],
                           depth_maps_decoded=0, scored_history_id=19)
            r["decoded_state_fields"].append(decoded)
            with np.load(io.BytesIO(raw), allow_pickle=False) as z:
                require(len(z.files) == len(set(z.files)), "duplicate archive fields")
                arrays = {}
                for key in spec["decode_fields"]:
                    decoded["fields_attempted"].append(key)
                    arrays[key] = z[key]
                    decoded["fields_decoded"].append(key)
                    if key == "depth":
                        decoded["depth_maps_decoded"] = int(arrays[key].shape[0])
            for key, a in arrays.items():
                m = spec["tensors"][key]
                require(list(a.shape) == m["shape"] and str(a.dtype) == m["dtype"], "state shape/dtype")
                require(sha(a.tobytes(order="C")) == m["body_sha256"], "state tensor hash")
            require(arrays["history_ids"].tolist() == c["history_ids"], "history identity")
            require(np.isfinite(arrays["K"]).all() and np.isfinite(arrays["c2w"]).all(), "camera finite")
            require(np.max(np.abs(arrays["K"].astype(np.float64) - np.array(c["K_512_nominal"]))) <= c["numeric"]["K_atol_px"], "K convention")
            states.append((arrays["depth"][3].astype(np.float64), arrays["K"], arrays["c2w"]))
        require(np.array_equal(states[0][1], states[1][1]) and np.array_equal(states[0][2], states[1][2]), "fixed cameras differ")
        del raw, arrays
        raw = load_bytes(c["inputs"][2])
        require(raw[:8] == b"\x89PNG\r\n\x1a\n" and raw[12:16] == b"IHDR" and raw[24:26] == bytes([16, 0]), "16-bit grayscale PNG")
        r["sensor_png_decode_attempts"] += 1
        with Image.open(io.BytesIO(raw)) as im:
            require(im.format == "PNG" and im.size == (640, 480), "sensor image identity")
            sensor = np.array(im)
        r["sensor_png_decodes"] += 1
        require(sensor.dtype.kind in "iu" and sensor.shape == (480, 640) and
                bool((sensor >= 0).all()) and bool((sensor <= 65535).all()), "sensor uint16-value domain")
        limit()
        rows, summary = score(np, states[0][0], states[1][0], sensor, c)
        summary["proxy_receipt_context"] = c["proxy_receipt_context"]
        require(len(rows["index"]) == 196608, "full row count")
        with (OUT / "ALL_PIXELS.npz").open("xb") as f:
            np.savez(f, **rows)
        with (OUT / "ALL_PIXELS.csv").open("x", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(rows)
            for values in zip(*rows.values()):
                writer.writerow([format(float(x), ".17g") if isinstance(x, np.floating) else int(x) for x in values])
                r["rows_written"] += 1
                if r["rows_written"] % 16384 == 0:
                    limit()
        require(r["rows_written"] == 196608, "CSV complete")
        save_json("SUMMARY.json", summary)
        for name in ["ALL_PIXELS.npz", "ALL_PIXELS.csv", "SUMMARY.json"]:
            p = OUT / name
            r["outputs"].append(dict(path=str(p), bytes=p.stat().st_size, sha256=sha(p.read_bytes())))
        limit()
        r.update(status="COMPLETED_PENDING_INDEPENDENT_RECOMPUTE", local_outcome=summary["local_outcome"])
    except BaseException:
        r.update(status="FAILED", traceback=traceback.format_exc())
        raise
    finally:
        signal.alarm(0)
        r["completed_utc"] = datetime.now(timezone.utc).isoformat()
        flush()


if __name__ == "__main__":
    main()
