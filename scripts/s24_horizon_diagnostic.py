"""Read-only post-score S24 trajectory horizons; no alignment or model imports.

prepare reads only the frozen parent JSON and own control files.
run requires the exact child SHA and the parent PASS/metrics/manifest gate.
self-test uses only fixed artificial times and SE(3) matrices.
"""
from __future__ import annotations

import argparse
from bisect import bisect_left
import csv
from datetime import datetime, timezone
from decimal import Decimal, ROUND_FLOOR
import hashlib
import io
import json
import math
from pathlib import Path
import platform
import sys
import traceback

ROOT = Path(__file__).resolve().parents[1]
PREP = ROOT / "work/S24_horizon_preparation"
OUT = ROOT / "results/S24_horizon_diagnostic"
PARENT = ROOT / "work/S24_baseline_expansion/run_manifest.json"
SCORING = ROOT / "results/S24_baseline_expansion/scoring"
PROTOCOL = ROOT / "docs/S24_HORIZON_DIAGNOSTIC_PROTOCOL.md"
CHILD = PREP / "run_manifest.json"
EXPECTED_PARENT_SHA256 = "95b2c749fddefc432472b0aae56c1602fb3110940a86fedc5047b201049924b7"
METHODS = ("cut3r", "ttt3r", "filt3r")
HORIZONS = ("adjacent", "1s", "5s")
POSE_ATOL = 1e-7
ARTIFICIAL_ROTATION_ATOL_DEG = 2e-5  # acos round-off near zero; not a failure threshold


def utc():
    return datetime.now(timezone.utc).isoformat()


def require(ok, message):
    if not ok:
        raise ValueError(message)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def strict_json(data, decimal=False):
    def reject_constant(value):
        raise ValueError("Nonfinite JSON number: " + value)
    return json.loads(data, parse_constant=reject_constant,
                      parse_float=Decimal if decimal else float)


def write_json(path, value):
    with Path(path).open("x", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write("\n")


def replace_receipt(path, value):
    # Only this run's newly created receipt; never overwrite another run.
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(value, ensure_ascii=False, indent=2,
                              allow_nan=False) + "\n", encoding="utf-8")
    tmp.replace(path)


def decimal_time(value):
    require(not isinstance(value, bool) and isinstance(value, (Decimal, int, float)),
            "Timestamp must be a JSON number")
    result = value if isinstance(value, Decimal) else Decimal(str(value))
    require(result.is_finite(), "Nonfinite RGB timestamp")
    return result


def time_plan(parent):
    """Only frame indices, RGB times, count and methods are consulted."""
    require(parent["schema"] == "s24-full-sequence-v1", "Unexpected parent schema")
    require(parent["methods"] == list(METHODS), "All three methods in fixed order required")
    frames = parent["frames"]
    n = len(frames)
    require(n >= 2 and parent["contract"]["frames"] == n, "Invalid frame count")
    require(all(type(f["index"]) is int for f in frames), "Non-integer frame index")
    require([f["index"] for f in frames] == list(range(n)), "Noncontiguous frame indices")
    times = [decimal_time(f["rgb_time"]) for f in frames]
    require(all(a < b for a, b in zip(times, times[1:])), "RGB times must strictly increase")
    elapsed = [t - times[0] for t in times]
    bins = [int(e.to_integral_value(rounding=ROUND_FLOOR)) for e in elapsed]
    frame_metadata = [
        dict(index=i, rgb_time_decimal=str(t), elapsed_decimal=str(elapsed[i]),
             elapsed_seconds=float(elapsed[i]), start_bin_second=bins[i])
        for i, t in enumerate(times)]
    pairs = {}
    for name in HORIZONS:
        rows = []
        for i, t in enumerate(times):
            j = i + 1 if name == "adjacent" else bisect_left(
                times, t + Decimal(1 if name == "1s" else 5), lo=i + 1)
            valid = j < n
            dt = times[j] - t if valid else None
            rows.append(dict(
                i=i, j=j if valid else None,
                rgb_time_i_decimal=str(t),
                rgb_time_j_decimal=str(times[j]) if valid else None,
                elapsed_i_decimal=str(elapsed[i]), elapsed_i_seconds=float(elapsed[i]),
                start_bin_second=bins[i], actual_dt_decimal=str(dt) if valid else None,
                actual_dt_seconds=float(dt) if valid else None,
                status="VALID" if valid else "TAIL_NA_NO_ENDPOINT"))
        pairs[name] = rows
    bin_metadata = [
        dict(bin_second=k, nominal_end_second=k + 1,
             interval_complete=Decimal(k + 1) <= elapsed[-1],
             observed_end_seconds=float(min(Decimal(k + 1), elapsed[-1])),
             start_count=sum(b == k for b in bins))
        for k in range(bins[-1] + 1)]
    return dict(frame_count=n, frames=frame_metadata, pairs=pairs, bins=bin_metadata,
                span_decimal=str(elapsed[-1]))


def control_hashes():
    return {str(Path(__file__).resolve()): sha(__file__), str(PROTOCOL): sha(PROTOCOL)}


def prepare():
    require(not CHILD.exists(), "Refuse existing horizon manifest")
    require(not OUT.exists(), "Refuse preparation over existing diagnostic results")
    parent_bytes = PARENT.read_bytes()
    require(digest(parent_bytes) == EXPECTED_PARENT_SHA256, "Parent manifest changed")
    parent = strict_json(parent_bytes, decimal=True)
    plan = time_plan(parent)
    controls = control_hashes()
    manifest = dict(
        schema="s24-horizon-diagnostic-v1", frozen_utc=utc(),
        parent_manifest=str(PARENT), parent_manifest_sha256=digest(parent_bytes),
        methods=list(METHODS), horizons=list(HORIZONS), controls=controls,
        plan=plan,
        contract=dict(
            pair_rule="adjacent i+1; lag1/5: earliest j with RGBtime_j >= RGBtime_i+lag",
            time_arithmetic="Decimal from exact parent JSON numeric literals; no GT-time pairing",
            bins="floor(RGBtime_i-RGBtime_0), disjoint one-second bins by pair START",
            endpoint_policy="No endpoint is explicit tail NA; no error-based exclusions",
            statistics=["rmse", "median", "p90_linear", "max"],
            translations_unit="m", rotations_unit="deg",
            pose_validation_atol=POSE_ATOL,
            full_sequence_alignment_reused=True, refit_alignment=False,
            event_selection=False, failure_thresholds=False,
            new_model=False, new_method=False, blind_test=False,
            independent_experimental_confirmation=False))
    require(sha(PARENT) == digest(parent_bytes), "Parent changed during preparation")
    require(control_hashes() == controls, "Control source changed during preparation")
    PREP.mkdir(parents=True, exist_ok=True)
    write_json(CHILD, manifest)
    print(json.dumps(dict(action="prepare", manifest=str(CHILD), sha256=sha(CHILD),
                          frame_count=plan["frame_count"], frozen_utc=manifest["frozen_utc"])))


def validate_score_documents(receipt, metrics, parent_hash, n):
    require(receipt.get("status") == "PASS", "Parent scoring is not PASS")
    require(receipt.get("manifest_sha256") == parent_hash, "Score receipt parent mismatch")
    require(receipt.get("frame_count") == n, "Score receipt partial frame count")
    require(receipt.get("methods") == list(METHODS), "Score receipt missing method")
    require(metrics.get("passed") is True, "Parent metrics not passed")
    require(metrics.get("manifest_sha256") == parent_hash, "Metrics parent mismatch")
    require(metrics.get("frame_count") == n and metrics.get("rpe_pair_count") == n - 1,
            "Parent metrics incomplete")
    require(set(metrics.get("methods", {})) == set(METHODS), "Metrics methods differ")
    for name in METHODS:
        m = metrics["methods"][name]
        require(m.get("metric_check_passed") is True and m.get("frame_count") == n and
                m.get("rpe_pair_count") == n - 1, name + ": unverified/partial metrics")


def score_gate(parent_hash, n):
    """No aligned NPZ path is opened here. Verify receipt before metrics parsing."""
    receipt_path, metrics_path = SCORING / "receipt.json", SCORING / "metrics.json"
    rb = receipt_path.read_bytes()
    receipt = strict_json(rb)
    require(receipt.get("status") == "PASS", "Parent scoring is not PASS")
    require(receipt.get("manifest_sha256") == parent_hash, "Score receipt parent mismatch")
    mb = metrics_path.read_bytes()
    require(digest(mb) == receipt.get("metrics_sha256"), "Parent metrics SHA mismatch")
    metrics = strict_json(mb)
    validate_score_documents(receipt, metrics, parent_hash, n)
    return metrics, {str(receipt_path): digest(rb), str(metrics_path): digest(mb)}


def validate_poses(poses, n):
    import numpy as np
    require(isinstance(poses, np.ndarray) and poses.dtype == np.float64,
            "Aligned poses must be float64 arrays; no silent conversion")
    require(poses.shape == (n, 4, 4) and np.isfinite(poses).all(), "Invalid aligned pose array")
    require(np.array_equal(poses[:, 3, :], np.tile([0., 0., 0., 1.], (n, 1))),
            "Invalid homogeneous last row")
    r = poses[:, :3, :3]
    require(np.allclose(np.swapaxes(r, -1, -2) @ r, np.eye(3), atol=POSE_ATOL, rtol=0)
            and np.allclose(np.linalg.det(r), 1., atol=POSE_ATOL, rtol=0),
            "Pose rotation is not SO(3); refuse repair/normalization")


def errors_matrix(pred, gt, starts, ends):
    """Primary: independent 4x4 inversions and full relative-error matrices."""
    import numpy as np
    require(len(starts) == len(ends), "Pair index lengths differ")
    if not len(starts):
        return np.empty(0, dtype=np.float64), np.empty(0, dtype=np.float64)
    g = np.linalg.inv(gt[starts]) @ gt[ends]
    p = np.linalg.inv(pred[starts]) @ pred[ends]
    e = np.linalg.inv(g) @ p
    translation = np.linalg.norm(e[:, :3, 3], axis=1)
    cosine = (np.trace(e[:, :3, :3], axis1=1, axis2=2) - 1) / 2
    rotation = np.degrees(np.arccos(np.clip(cosine, -1., 1.)))
    require(np.isfinite(translation).all() and np.isfinite(rotation).all(),
            "Nonfinite relative errors")
    return translation, rotation


def errors_rigid_components(pred, gt, starts, ends):
    """Artificial check route: transpose/differences and atan2, no 4x4 inverse."""
    import numpy as np
    t_out, r_out = [], []
    for i, j in zip(starts, ends):
        rg = gt[i, :3, :3].T @ gt[j, :3, :3]
        tg = gt[i, :3, :3].T @ (gt[j, :3, 3] - gt[i, :3, 3])
        rp = pred[i, :3, :3].T @ pred[j, :3, :3]
        tp = pred[i, :3, :3].T @ (pred[j, :3, 3] - pred[i, :3, 3])
        re = rg.T @ rp
        te = rg.T @ (tp - tg)
        sine = np.linalg.norm([re[2, 1] - re[1, 2], re[0, 2] - re[2, 0],
                               re[1, 0] - re[0, 1]]) / 2
        cosine = (np.trace(re) - 1) / 2
        t_out.append(float(np.linalg.norm(te)))
        r_out.append(float(np.degrees(np.arctan2(sine, cosine))))
    return np.asarray(t_out), np.asarray(r_out)


def statistics(values):
    import numpy as np
    if not len(values):
        return dict(count=0, rmse=None, median=None, p90_linear=None, max=None)
    a = np.asarray(values, dtype=np.float64)
    require(a.ndim == 1 and np.isfinite(a).all(), "Invalid metric summary input")
    return dict(count=len(a), rmse=float(np.sqrt(np.mean(a * a))),
                median=float(np.median(a)), p90_linear=float(np.percentile(a, 90, method="linear")),
                max=float(np.max(a)))


def summarize_rows(rows, bin_metadata):
    def summary(subset):
        valid = [x for x in subset if x["status"] == "VALID"]
        return dict(start_count=len(subset), valid_pair_count=len(valid),
                    tail_na_count=len(subset) - len(valid),
                    translation_m=statistics([x["translation_m"] for x in valid]),
                    rotation_deg=statistics([x["rotation_deg"] for x in valid]),
                    actual_dt_seconds=statistics([x["actual_dt_seconds"] for x in valid]))
    return dict(all_pairs=summary(rows),
                bins=[dict(**b, **{k: v for k, v in summary(
                    [x for x in rows if x["start_bin_second"] == b["bin_second"]]).items()
                                 if k != "start_count"})
                      for b in bin_metadata])


def save_csv(path, rows, fields):
    with path.open("x", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: "NA" if row[k] is None else row[k] for k in fields})


def plot_curves(rows, out):
    # Local pre-existing plotting dependency; no model import or data access.
    sys.path.append(str(ROOT / "work/S17C_environment/site-packages"))
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np
    styles = {"cut3r": ("#1f77b4", "-"), "ttt3r": ("#d95f02", "--"),
              "filt3r": ("#1b9e77", "-.")}
    for metric, unit in (("translation_m", "m"), ("rotation_deg", "deg")):
        fig, axes = plt.subplots(3, 1, figsize=(12, 8), sharex=True, constrained_layout=True)
        for ax, horizon in zip(axes, HORIZONS):
            for name in METHODS:
                subset = [r for r in rows if r["method"] == name and r["horizon"] == horizon]
                x = [r["elapsed_i_seconds"] for r in subset]
                y = [r[metric] if r[metric] is not None else np.nan for r in subset]
                color, style = styles[name]
                ax.plot(x, y, color=color, linestyle=style, linewidth=.8, label=name)
                tail = sum(r["status"] != "VALID" for r in subset)
            ax.set_title(horizon + " pairs; tail NA starts=" + str(tail), loc="left", fontsize=10)
            ax.set_ylabel(unit)
            ax.grid(alpha=.2)
        axes[0].legend(ncol=3)
        axes[-1].set_xlabel("RGB elapsed seconds at pair START")
        fig.suptitle("S24 descriptive RPE: unchanged full-trajectory Sim(3) alignment")
        fig.savefig(out / (metric + "_all_pairs.png"), dpi=160)
        fig.savefig(out / (metric + "_all_pairs.pdf"))
        plt.close(fig)
    return matplotlib.__version__


def run(expected_child_sha):
    require(isinstance(expected_child_sha, str) and len(expected_child_sha) == 64,
            "run requires the frozen --manifest-sha256")
    require(not OUT.exists(), "Refuse existing result directory; retain previous run")
    child_bytes = CHILD.read_bytes()
    require(digest(child_bytes) == expected_child_sha, "Child manifest SHA mismatch")
    child = strict_json(child_bytes)
    require(child["schema"] == "s24-horizon-diagnostic-v1", "Wrong child schema")
    require(child["methods"] == list(METHODS) and child["horizons"] == list(HORIZONS),
            "Changed method/horizon domain")
    require(child["controls"] == control_hashes(), "Script or protocol changed since freeze")
    parent_bytes = PARENT.read_bytes()
    parent_hash = digest(parent_bytes)
    require(parent_hash == child["parent_manifest_sha256"] == EXPECTED_PARENT_SHA256,
            "Parent manifest mismatch")
    plan = time_plan(strict_json(parent_bytes, decimal=True))
    require(plan == child["plan"], "Frozen pair plan does not match parent RGB times")
    n = plan["frame_count"]
    metrics, input_hashes = score_gate(parent_hash, n)
    input_hashes.update({str(CHILD): expected_child_sha, str(PARENT): parent_hash,
                         **child["controls"]})
    # No aligned NPZ bytes/GT arrays have been accessed before all preceding checks.
    OUT.mkdir(parents=True, exist_ok=False)
    receipt = dict(status="RUNNING", started_utc=utc(), child_manifest_sha256=expected_child_sha,
                   parent_manifest_sha256=parent_hash, all_three_parent_scores_passed=True,
                   aligned_bytes_read=False, aligned_arrays_decoded=False, new_model=False)
    replace_receipt(OUT / "receipt.json", receipt)
    try:
        import numpy as np
        receipt.update(aligned_bytes_read_started_utc=utc())
        replace_receipt(OUT / "receipt.json", receipt)
        buffers = {}
        for name in METHODS:
            path = SCORING / (name + "_aligned.npz")
            buffers[name] = path.read_bytes()
            input_hashes[str(path)] = digest(buffers[name])
            receipt["aligned_bytes_read"] = True
        write_json(OUT / "input_seal.json", dict(
            snapshot_utc=utc(), identities=input_hashes,
            source_binding="Parent PASS binds metrics; aligned NPZ hashes first captured by this diagnostic, not previously sealed in parent receipt",
            aligned_arrays_decoded=False))
        receipt.update(aligned_array_decode_started_utc=utc())
        replace_receipt(OUT / "receipt.json", receipt)
        report = dict(
            schema="s24-horizon-results-v1", started_utc=receipt["started_utc"],
            parent_manifest_sha256=parent_hash, child_manifest_sha256=expected_child_sha,
            frame_count=n, methods={}, automatic_event_selection=False, failure_thresholds=None,
            memory_forgetting_established=False, new_method=False, generated_video=False,
            alignment="Use parent scoring pred/gt after the one full-sequence Sim(3); no new fit",
            interpretation="Descriptive overlapping-pair statistics, not independent trials or causal evidence",
            runtime=dict(python=sys.version, executable=sys.executable, platform=platform.platform(),
                         numpy=np.__version__))
        all_rows, all_bins = [], []
        common_gt = None
        for name in METHODS:
            with np.load(io.BytesIO(buffers[name]), allow_pickle=False) as data:
                expected_keys = {"pred", "gt", "ate_m", "rpe_translation_m", "rpe_rotation_deg"}
                require(len(data.files) == len(expected_keys) and set(data.files) == expected_keys,
                        name + ": unexpected aligned archive keys")
                pred, gt = data["pred"], data["gt"]
            receipt["aligned_arrays_decoded"] = True
            validate_poses(pred, n)
            validate_poses(gt, n)
            if common_gt is None:
                common_gt = gt.copy()
            else:
                require(np.array_equal(common_gt, gt), "GT differs between aligned archives")
            report["methods"][name] = {}
            for horizon in HORIZONS:
                template = plan["pairs"][horizon]
                valid = [p for p in template if p["j"] is not None]
                starts = np.asarray([p["i"] for p in valid], dtype=np.int64)
                ends = np.asarray([p["j"] for p in valid], dtype=np.int64)
                et, er = errors_matrix(pred, gt, starts, ends)
                measured = {p["i"]: (float(t), float(r))
                            for p, t, r in zip(valid, et, er)}
                rows = [dict(method=name, horizon=horizon, **p,
                             translation_m=measured[p["i"]][0] if p["i"] in measured else None,
                             rotation_deg=measured[p["i"]][1] if p["i"] in measured else None)
                        for p in template]
                summary = summarize_rows(rows, plan["bins"])
                report["methods"][name][horizon] = summary
                all_rows.extend(rows)
                for b in summary["bins"]:
                    item = {k: v for k, v in b.items()
                            if k not in {"translation_m", "rotation_deg", "actual_dt_seconds"}}
                    item.update(method=name, horizon=horizon)
                    for key in ("translation_m", "rotation_deg", "actual_dt_seconds"):
                        for stat, value in b[key].items():
                            item[key + "_" + stat] = value
                    all_bins.append(item)
                if horizon == "adjacent":
                    # A consistency guard, not a producer-time cryptographic seal.
                    ate = np.linalg.norm(pred[:, :3, 3] - gt[:, :3, 3], axis=1)
                    recomputed = [statistics(ate)["rmse"], statistics(et)["rmse"],
                                  statistics(er)["rmse"]]
                    require(np.allclose(recomputed, metrics["methods"][name]["independent_matrix"],
                                        atol=1e-6, rtol=1e-5),
                            name + ": aligned archive does not reconstruct parent scalar metrics")
            receipt.update(methods_completed=list(report["methods"]))
            replace_receipt(OUT / "receipt.json", receipt)
        fields = list(all_rows[0])
        save_csv(OUT / "all_pairs.csv", all_rows, fields)
        save_csv(OUT / "one_second_bins.csv", all_bins, list(all_bins[0]))
        report["runtime"]["matplotlib"] = plot_curves(all_rows, OUT)
        for path, expected in input_hashes.items():
            require(sha(path) == expected, "Input changed during diagnostic: " + path)
        report.update(completed_utc=utc(), input_identities=input_hashes,
                      input_seal_sha256=sha(OUT / "input_seal.json"))
        write_json(OUT / "metrics.json", report)
        outputs = {p.name: sha(p) for p in OUT.iterdir() if p.is_file() and p.name != "receipt.json"}
        receipt.update(status="PASS", completed_utc=utc(), frame_count=n,
                       metrics_sha256=sha(OUT / "metrics.json"), output_sha256=outputs,
                       meaning_of_pass="Diagnostic completed; no memory-failure or method-success claim")
        replace_receipt(OUT / "receipt.json", receipt)
        print(json.dumps(receipt, ensure_ascii=False))
    except BaseException as error:
        receipt.update(status="FAILED", completed_utc=utc(), error=repr(error),
                       traceback=traceback.format_exc())
        replace_receipt(OUT / "receipt.json", receipt)
        raise


def self_test():
    """Fixed small artificial checks only; never call prepare/run or open S24 data."""
    import numpy as np
    target = PREP / "artificial_checks_v1.json"
    require(not target.exists(), "Refuse overwriting artificial-check receipt")
    controls = control_hashes()
    checks = []

    def check(name, ok):
        require(bool(ok), "Artificial check failed: " + name)
        checks.append(dict(name=name, passed=True))

    def rejected(name, function):
        try:
            function()
        except (ValueError, KeyError):
            check(name, True)
        else:
            raise ValueError("Expected artificial rejection: " + name)

    def parent_for(times):
        return dict(schema="s24-full-sequence-v1", methods=list(METHODS),
                    frames=[dict(index=i, rgb_time=Decimal(t)) for i, t in enumerate(times)],
                    contract=dict(frames=len(times)))

    plan = time_plan(parent_for(["0", ".25", "1", "1.5", "4.999999", "5", "6"]))
    check("index_zero_retained", plan["pairs"]["1s"][0]["i"] == 0)
    check("exact_one_second_endpoint", plan["pairs"]["1s"][0]["j"] == 2)
    check("five_seconds_does_not_round_early", plan["pairs"]["5s"][0]["j"] == 5)
    check("actual_dt_overshoot_saved", plan["pairs"]["1s"][1]["actual_dt_decimal"] == "1.25")
    check("adjacent_last_is_tail_na", plan["pairs"]["adjacent"][-1]["j"] is None)
    check("every_start_retained_each_horizon", all(len(x) == 7 for x in plan["pairs"].values()))
    check("floor_bins_and_empty_bins", [f["start_bin_second"] for f in plan["frames"]] ==
          [0, 0, 1, 1, 4, 5, 6] and plan["bins"][2]["start_count"] == 0)
    check("terminal_exact_integer_bin_not_claimed_full", plan["bins"][-1]["interval_complete"] is False)
    epoch = time_plan(parent_for(["1305031102.175304", "1305031103.175303",
                                 "1305031103.175304", "1305031107.175304"]))
    check("epoch_decimal_lag_boundary", epoch["pairs"]["1s"][0]["j"] == 2 and
          epoch["pairs"]["5s"][0]["j"] == 3)
    short = time_plan(parent_for(["0", ".1"]))
    check("horizon_with_zero_endpoints", all(x["j"] is None for x in short["pairs"]["5s"]))
    rejected("duplicate_time_rejected", lambda: time_plan(parent_for(["0", "0"])))
    rejected("nonfinite_time_rejected", lambda: time_plan(parent_for(["0", "NaN"])))
    rejected("reversed_time_rejected", lambda: time_plan(parent_for(["1", "0"])))
    check("empty_statistics_are_na", statistics([])["rmse"] is None)
    check("zero_errors_not_na", statistics([0., 0.])["rmse"] == 0.)
    check("linear_p90", abs(statistics([0., 1., 2., 3.])["p90_linear"] - 2.7) < 1e-14)

    def pose(axis, angle, position):
        a = np.asarray(axis, dtype=np.float64)
        a /= np.linalg.norm(a)
        x, y, z = a
        k = np.array([[0., -z, y], [z, 0., -x], [-y, x, 0.]])
        r = np.eye(3) + math.sin(angle) * k + (1 - math.cos(angle)) * (k @ k)
        p = np.eye(4)
        p[:3, :3], p[:3, 3] = r, position
        return p

    identity = np.repeat(np.eye(4)[None], 3, axis=0)
    pure = identity.copy()
    pure[:, 0, 3] = [0., 1., 3.]
    et, er = errors_matrix(pure, identity, [0, 1], [1, 2])
    check("known_translation_norms", np.allclose(et, [1., 2.], atol=1e-12, rtol=0))
    check("known_translation_zero_rotation", np.allclose(er, 0., atol=ARTIFICIAL_ROTATION_ATOL_DEG))
    rotated = np.stack([pose([0, 0, 1], angle, [0, 0, 0]) for angle in (0, math.pi / 2, math.pi)])
    et, er = errors_matrix(rotated, identity, [0, 0], [1, 2])
    check("known_90_and_180_degree_errors", np.allclose(er, [90., 180.], atol=1e-12))
    g = np.stack([pose([1, 2, 3], .2, [1, 2, 3]), pose([2, -1, 1], -.7, [-1, .4, .8])])
    p0 = pose([3, 1, -2], .45, [.8, -.4, .2])
    expected_error = pose([0, 1, 0], .3, [.2, -.1, .4])
    p = np.stack([p0, p0 @ np.linalg.inv(g[0]) @ g[1] @ expected_error])
    et, er = errors_matrix(p, g, [0], [1])
    check("noncommuting_known_error_translation", abs(et[0] - np.linalg.norm([.2, -.1, .4])) < 1e-12)
    check("noncommuting_known_error_rotation", abs(er[0] - math.degrees(.3)) < 1e-10)
    cases = [(identity, identity, [0, 1], [1, 2]), (pure, identity, [0, 0], [1, 2]),
             (rotated, identity, [0, 0], [1, 2]), (p, g, [0], [1])]
    transform = pose([1, -1, 2], .8, [8, -3, 1])
    cases.append((transform @ g, g, [0], [1]))
    for index, (pred, gt, starts, ends) in enumerate(cases):
        a, b = errors_matrix(pred, gt, starts, ends)
        c, d = errors_rigid_components(pred, gt, starts, ends)
        check("two_math_paths_translation_" + str(index), np.allclose(a, c, atol=1e-12, rtol=1e-10))
        check("two_math_paths_rotation_" + str(index),
              np.allclose(b, d, atol=ARTIFICIAL_ROTATION_ATOL_DEG, rtol=1e-10))
    validate_poses(identity, 3)
    bad = identity.copy()
    bad[0, 3, 0] = 1.
    rejected("bad_homogeneous_row_rejected", lambda: validate_poses(bad, 3))
    bad_rotation = identity.copy()
    bad_rotation[0, 0, 0] = 2.
    rejected("non_SO3_rejected", lambda: validate_poses(bad_rotation, 3))
    nan_pose = identity.copy()
    nan_pose[0, 0, 3] = np.nan
    rejected("nonfinite_pose_rejected", lambda: validate_poses(nan_pose, 3))
    rows = [dict(**x, translation_m=None, rotation_deg=None) for x in short["pairs"]["5s"]]
    summary = summarize_rows(rows, short["bins"])
    check("all_tail_bin_not_zero_error", summary["all_pairs"]["valid_pair_count"] == 0 and
          summary["all_pairs"]["tail_na_count"] == 2 and
          summary["bins"][0]["translation_m"]["rmse"] is None)
    r = dict(status="PASS", manifest_sha256="fixture", frame_count=3, methods=list(METHODS))
    m = dict(passed=True, manifest_sha256="fixture", frame_count=3, rpe_pair_count=2,
             methods={name: dict(metric_check_passed=True, frame_count=3, rpe_pair_count=2)
                      for name in METHODS})
    validate_score_documents(r, m, "fixture", 3)
    rejected("incomplete_score_gate_rejected",
             lambda: validate_score_documents(dict(r, status="RUNNING"), m, "fixture", 3))
    rejected("wrong_parent_score_gate_rejected",
             lambda: validate_score_documents(r, m, "other", 3))
    rejected("missing_method_score_gate_rejected",
             lambda: validate_score_documents(dict(r, methods=["cut3r"]), m, "fixture", 3))
    require(controls == control_hashes(), "Control files changed during artificial tests")
    PREP.mkdir(parents=True, exist_ok=True)
    receipt = dict(recorded_utc=utc(), status="ARTIFICIAL_CHECKS_PASSED",
                   check_count=len(checks), checks=checks, control_sha256=controls,
                   python=sys.version, numpy=np.__version__,
                   rotation_comparison_atol_deg=ARTIFICIAL_ROTATION_ATOL_DEG,
                   scope="Fixed artificial times and SE3 only; no prepare/run, no real S24 arrays/GT/scores, no model",
                   independent_author_review=False, frozen=False)
    write_json(target, receipt)
    print(json.dumps(dict(receipt=str(target), sha256=sha(target), checks=len(checks))))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["prepare", "run", "self-test"])
    parser.add_argument("--manifest-sha256")
    arguments = parser.parse_args()
    if arguments.action == "prepare":
        prepare()
    elif arguments.action == "run":
        run(arguments.manifest_sha256)
    else:
        self_test()

