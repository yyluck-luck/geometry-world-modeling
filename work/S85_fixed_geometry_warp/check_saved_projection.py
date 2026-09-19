"""Independent S85 saved-output review. Main requires root's exact receipt SHA.

No projector import, model, optimizer, image, sensor, or rendering entry point.
Reconstructs original geometry; validates candidate completeness and adjacent
ordering instead of calling or duplicating the author's lexsort pipeline.
"""
import os
for name in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
             "VECLIB_MAXIMUM_THREADS", "NUMEXPR_NUM_THREADS", "BLIS_NUM_THREADS"):
    os.environ[name] = "1"
import argparse
import datetime as dt
import gc
import hashlib
import io
import json
from pathlib import Path
import resource
import signal
import sys
import time
import traceback
import numpy as np

HERE = Path(__file__).resolve().parent
N, H, W, TOTAL = 384 * 512, 576, 576, 576 * 576
HISTORY = [12, 13, 18, 19]
TARGETS = [20, 21, 22, 23]
STATUS = dict(VALID=0, SOURCE_NONFINITE=1, SOURCE_NONPOSITIVE=2,
              TARGET_NONFINITE=3, TARGET_NONPOSITIVE=4, OUTSIDE=5)
ATOL, RTOL = 1e-10, 1e-12


def demand(ok, message):
    if not bool(ok):
        raise AssertionError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def body(a):
    return sha(np.ascontiguousarray(a).tobytes())


def compare(actual, expected, label, report, approximate=False):
    demand(actual.shape == expected.shape and actual.dtype == expected.dtype,
           label + ": shape/dtype")
    if approximate:
        demand(np.array_equal(np.isnan(actual), np.isnan(expected)), label + ": NaN mask")
        demand(np.array_equal(np.isposinf(actual), np.isposinf(expected)), label + ": +Inf mask")
        demand(np.array_equal(np.isneginf(actual), np.isneginf(expected)), label + ": -Inf mask")
        finite = np.isfinite(expected)
        delta = np.abs(actual[finite] - expected[finite])
        limit = ATOL + RTOL * np.abs(expected[finite])
        demand(np.all(delta <= limit), label + ": numerical mismatch")
        report["float_max_abs_diff"][label] = float(delta.max(initial=0))
    else:
        demand(np.array_equal(actual, expected, equal_nan=True), label + ": exact mismatch")
    report["array_fields_checked"] += 1


def load_archive(path, identity, fields, report, exact_keys):
    data = Path(path).read_bytes()
    event = dict(path=str(path), bytes=len(data), sha256=sha(data), decoded_fields=[])
    report["scientific_archive_reads"].append(event)
    demand(event["bytes"] == identity["bytes"] and event["sha256"] == identity["sha256"],
           str(path) + ": archive identity")
    arrays = {}
    with np.load(io.BytesIO(data), allow_pickle=False) as archive:
        demand(len(archive.files) == len(set(archive.files)), "duplicate archive key")
        if exact_keys:
            demand(set(archive.files) == set(fields), str(path) + ": exact keys")
        for key, meta in fields.items():
            a = archive[key]
            event["decoded_fields"].append(key)
            demand(not a.dtype.hasobject, key + ": object array")
            demand(list(a.shape) == meta["shape"] and str(a.dtype) == meta["dtype"],
                   key + ": schema")
            if "body_sha256" in meta:
                demand(body(a) == meta["body_sha256"], key + ": original field identity")
            arrays[key] = a
    return arrays


def reference_geometry(state, target_P, target_K):
    """Re-derive each scalar camera equation in frozen FP64 operation order.

    Separate masks build states; no saved UV/status/footprint is used here.
    Matrix coefficients are explicit to avoid a BLAS reassociation at edges.
    """
    pixel = np.arange(N, dtype=np.int32)
    uv = np.column_stack((pixel % 512, pixel // 512))
    status = np.zeros((4, N), np.uint8)
    xyz = np.full((4, N, 3), np.nan, np.float64)
    q = np.full((4, N, 2), np.nan, np.float64)
    index = np.full((4, N, 4), -1, np.int32)
    weight = np.zeros((4, N, 4), np.float64)
    for row in range(4):
        z = state["depth"][row].reshape(N).astype(np.float64)
        K = state["K"][row].astype(np.float64)
        P = state["c2w"][row].astype(np.float64)
        good_z = np.isfinite(z) & (z > 0)
        status[row, ~np.isfinite(z)] = 1
        status[row, np.isfinite(z) & (z <= 0)] = 2
        ids = np.flatnonzero(good_z)
        source = np.empty((len(ids), 3), np.float64)
        source[:, 0] = (uv[ids, 0].astype(np.float64) - K[0, 2]) / K[0, 0]
        source[:, 1] = (uv[ids, 1].astype(np.float64) - K[1, 2]) / K[1, 1]
        source[:, 2] = 1
        with np.errstate(over="ignore", divide="ignore", invalid="ignore"):
            source *= z[ids, None]
            world = np.empty_like(source)
            for axis in range(3):
                world[:, axis] = (P[axis, 0] * source[:, 0] + P[axis, 1] * source[:, 1]
                                  + P[axis, 2] * source[:, 2] + P[axis, 3])
            centered = world - target_P[:3, 3]
            for axis in range(3):
                xyz[row, ids, axis] = (target_P[0, axis] * centered[:, 0]
                                      + target_P[1, axis] * centered[:, 1]
                                      + target_P[2, axis] * centered[:, 2] + 0.0)
            finite_xyz = np.isfinite(xyz[row]).all(axis=1)
            status[row, good_z & ~finite_xyz] = 3
            status[row, good_z & finite_xyz & (xyz[row, :, 2] <= 0)] = 4
            front = good_z & finite_xyz & (xyz[row, :, 2] > 0)
            for axis in range(2):
                q[row, front, axis] = (target_K[axis, axis]
                                       * (xyz[row, front, axis] / xyz[row, front, 2])
                                       + target_K[axis, 2])
        finite_q = np.isfinite(q[row]).all(axis=1)
        status[row, front & ~finite_q] = 3
        outside = (q[row, :, 0] < 0) | (q[row, :, 0] > 575) | (q[row, :, 1] < 0) | (q[row, :, 1] > 575)
        status[row, front & finite_q & outside] = 5
        valid_ids = np.flatnonzero(status[row] == 0)
        base = np.floor(q[row, valid_ids]).astype(np.int64)
        fractional = q[row, valid_ids] - base
        for slot in range(4):
            dx, dy = slot % 2, slot // 2
            x, y = base[:, 0] + dx, base[:, 1] + dy
            wx = fractional[:, 0] if dx else 1 - fractional[:, 0]
            wy = fractional[:, 1] if dy else 1 - fractional[:, 1]
            product = wx * wy
            eligible = (product > 0) & (x >= 0) & (x < W) & (y >= 0) & (y < H)
            at = valid_ids[eligible]
            index[row, at, slot] = y[eligible] * W + x[eligible]
            weight[row, at, slot] = product[eligible]
    demand(np.array_equal((index >= 0).any(axis=2), status == 0), "reference valid footprint equivalence")
    return dict(history_ids=np.array(HISTORY, np.int64), source_pixel_id=pixel,
                source_uv=uv, source_status=status, target_xyz=xyz, target_uv=q,
                footprint_target_index=index, footprint_weight=weight)


def review_target(saved, expected, state, tid, report):
    prefix = str(tid) + "/"
    for key, value in expected.items():
        compare(saved[key], value, prefix + key, report,
                key in ("target_xyz", "target_uv", "footprint_weight"))
    compare(saved["target_id"], np.array(tid, np.int64), prefix + "target_id", report)
    r, p, s = saved["candidate_source_row"], saved["candidate_pixel_id"], saved["candidate_slot"]
    C = len(r)
    demand(np.all((r >= 0) & (r < 4)) and np.all((p >= 0) & (p < N)) and np.all(s < 4),
           prefix + "candidate identity bounds")
    key = (r.astype(np.int64) * N + p) * 4 + s
    eligible_keys = np.flatnonzero(expected["footprint_target_index"].reshape(-1) >= 0)
    demand(np.array_equal(np.sort(key), eligible_keys), prefix + "complete unique candidate permutation")
    t = expected["footprint_target_index"][r, p, s]
    z = expected["target_xyz"][r, p, 2]
    wt = expected["footprint_weight"][r, p, s]
    compare(saved["candidate_target_index"], t, prefix + "candidate_target_index", report)
    compare(saved["candidate_Z"], z, prefix + "candidate_Z", report, True)
    compare(saved["candidate_weight"], wt, prefix + "candidate_weight", report, True)
    demand(np.all(np.isfinite(z) & (z > 0) & np.isfinite(wt) & (wt > 0)), prefix + "candidate positivity")
    # Adjacent tuples prove the full sorted order, without invoking lexsort.
    priority = np.array([3, 2, 1, 0], np.int8)[r]
    equal_prefix = np.ones(max(C - 1, 0), bool)
    ascending = np.zeros(max(C - 1, 0), bool)
    for values in (t, z, priority, p, s):
        ascending |= equal_prefix & (values[:-1] < values[1:])
        equal_prefix &= values[:-1] == values[1:]
    demand(ascending.all(), prefix + "strict adjacent complete tuple order")
    first = np.ones(C, bool)
    first[1:] = t[1:] != t[:-1]
    positions = np.arange(C, dtype=np.int64)
    starts = np.maximum.accumulate(np.where(first, positions, 0)) if C else positions
    ranks = (positions - starts).astype(np.int32)
    compare(saved["candidate_rank"], ranks, prefix + "candidate_rank", report)
    compare(saved["candidate_winner"], first, prefix + "candidate_winner", report)
    count = np.zeros(TOTAL, np.int32)
    np.add.at(count, t, 1)
    mask = count > 0
    compare(saved["candidate_count"], count.reshape(H, W), prefix + "candidate_count", report)
    compare(saved["mask"], mask.reshape(H, W), prefix + "mask", report)
    rgb = np.zeros((TOTAL, 3), np.float32)
    colors = state["colors"].reshape(4, N, 3)
    rgb[t[first]] = colors[r[first], p[first]]
    compare(saved["warp_rgb"], rgb.reshape(H, W, 3), prefix + "warp_rgb", report)
    footprints_won = np.zeros((4, N, 4), bool)
    footprints_won[r[first], p[first], s[first]] = True
    compare(saved["footprint_winner"], footprints_won, prefix + "footprint_winner", report)
    for title, chosen in (("winner", first), ("second_candidate", ranks == 1)):
        pixels = t[chosen]
        for suffix, values, dtype in (("source_row", r, np.int8), ("pixel_id", p, np.int32),
                                      ("slot", s, np.int8), ("history_id", np.array(HISTORY)[r], np.int16)):
            a = np.full(TOTAL, -1, dtype)
            a[pixels] = values[chosen]
            compare(saved[title + "_" + suffix], a.reshape(H, W), prefix + title + "_" + suffix, report)
        a = np.full(TOTAL, np.nan, np.float64)
        a[pixels] = z[chosen]
        compare(saved[title + "_Z"], a.reshape(H, W), prefix + title + "_Z", report, True)
    pairs = []
    for row, hid in enumerate(HISTORY):
        statuses = expected["source_status"][row]
        counts = {name: int(np.count_nonzero(statuses == code)) for name, code in STATUS.items()}
        demand(sum(counts.values()) == N, prefix + "source denominator")
        footprint_n = int(np.count_nonzero(expected["footprint_target_index"][row] >= 0))
        won = int(np.count_nonzero(footprints_won[row]))
        pairs.append(dict(history_id=hid, N=N, status_counts=counts,
                          eligible_footprints=footprint_n, winning_footprints=won,
                          losing_footprints=footprint_n - won,
                          source_points_with_any_win=int(np.count_nonzero(footprints_won[row].any(axis=1)))))
    occupied = int(np.count_nonzero(mask))
    return dict(source_points=4 * N, target_pixels=TOTAL, valid_footprints=C,
                winners=occupied, losers=C - occupied, holes=TOTAL - occupied,
                coverage=occupied / TOTAL, pixels_with_multiple_candidates=int(np.count_nonzero(count >= 2)),
                pairs=pairs, target_id=tid)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--receipt-sha256", required=True)
    args = parser.parse_args()
    out = HERE / "INDEPENDENT_OUTPUT_REVIEW.json"
    demand(not out.exists(), "review output exists; no automatic retry/overwrite")
    begin = time.perf_counter()
    report = dict(status="STARTED", started_utc=dt.datetime.now(dt.timezone.utc).isoformat(),
                  checker_sha256=sha(Path(__file__).read_bytes()), scientific_archive_reads=[],
                  array_fields_checked=0, float_max_abs_diff={}, reviewed_targets=[],
                  model_calls=0, optimizer_calls=0, image_decodes=0, sensor_depth_reads=0,
                  author_projector_imports=0, numerical_tolerance=dict(atol=ATOL, rtol=RTOL))
    def timeout(_sig, _frame):
        raise TimeoutError("independent review 300s bound")
    old_handler = signal.signal(signal.SIGALRM, timeout)
    signal.setitimer(signal.ITIMER_REAL, 300)
    try:
        review_raw = (HERE / "OUTPUT_REVIEW_CONTRACT.json").read_bytes()
        review_contract = json.loads(review_raw)
        report["review_contract_sha256"] = sha(review_raw)
        demand(report["checker_sha256"] == review_contract["checker_sha256"], "checker identity")
        raw = (HERE / "CONTRACT.json").read_bytes()
        demand(sha(raw) == review_contract["projection_contract_sha256"], "projection contract identity")
        contract = json.loads(raw)
        demand(sha((HERE / "project_fixed_geometry.py").read_bytes()) == review_contract["projection_runner_sha256"], "projector source identity")
        folder = HERE / "execution_01"
        raw = (folder / "RECEIPT.json").read_bytes()
        demand(sha(raw) == args.receipt_sha256, "explicit root receipt identity")
        report["projection_receipt_sha256"] = sha(raw)
        receipt = json.loads(raw)
        demand(receipt["status"] == "COMPLETED_PENDING_INDEPENDENT_REVIEW", "actual completion")
        demand(receipt["contract_sha256"] == review_contract["projection_contract_sha256"], "receipt contract")
        demand(receipt["completed_targets"] == TARGETS, "all four targets completed")
        for k in ("model_calls", "optimizer_calls", "target_RGB_reads", "sensor_depth_reads"):
            demand(receipt[k] == 0, "receipt prohibited input/action: " + k)
        demand(receipt["new_method_validated"] is False, "novelty boundary")
        demand(sys.platform == "darwin" and np.__version__ == "1.26.4", "review runtime")
        demand(len(receipt["reads"]) == 2, "two original inputs")
        for actual, spec in zip(receipt["reads"], contract["inputs"]):
            demand(all(actual[k] == spec[k] for k in ("path", "bytes", "sha256")), "actual input identity")
            demand(actual["decoded_fields"] == list(spec["fields"]), "actual input decode scope")
        original = [load_archive(spec["path"], spec, spec["fields"], report, False) for spec in contract["inputs"]]
        state, camera = original
        demand(state["history_ids"].tolist() == HISTORY, "source identity/order")
        demand(camera["ids"].tolist() == contract["camera_archive_ids"], "camera IDs")
        target_rows = [camera["ids"].tolist().index(t) for t in TARGETS]
        target_P = camera["c2ws"][target_rows]
        target_K = np.array(contract["target_K"], np.float64)
        demand(receipt["camera_archive_selection"] == dict(archive_ids=camera["ids"].tolist(), selected_rows=target_rows,
               consumed_ids=TARGETS, non_target_camera_rows_used=False), "actual target camera selection")
        expected_input = dict(source_depth=state["depth"], source_colors=state["colors"], source_K_saved=state["K"],
                              source_c2w_saved=state["c2w"], history_ids=state["history_ids"], target_ids=np.array(TARGETS, np.int64),
                              target_c2w=target_P, target_K=target_K)
        artifacts = {Path(a["path"]).name: a for a in receipt["artifacts"]}
        names = ["INPUT_GEOMETRY.npz"] + [f"TARGET_{t}.npz" for t in TARGETS]
        demand(len(receipt["artifacts"]) == 5 and set(artifacts) == set(names), "five complete output archives")
        for name, artifact in artifacts.items():
            demand(artifact["path"] == str(folder / name), "fixed artifact path")
        a = artifacts["INPUT_GEOMETRY.npz"]
        fixed_schema = {k: dict(shape=list(v.shape), dtype=str(v.dtype)) for k, v in expected_input.items()}
        demand(a["fields"] == fixed_schema, "input copy independent schema")
        copied = load_archive(a["path"], a, fixed_schema, report, True)
        for k, expected in expected_input.items():
            compare(copied[k], expected, "input_copy/" + k, report)
            demand(body(copied[k]) == body(expected), "input copy exact body bytes: " + k)
        del copied
        summary_raw = (folder / "SUMMARY.json").read_bytes()
        demand(sha(summary_raw) == receipt["summary_sha256"], "summary identity")
        report["projection_summary_sha256"] = sha(summary_raw)
        summary = json.loads(summary_raw)
        demand(summary["status"] == "COMPLETED_PENDING_INDEPENDENT_REVIEW" and summary["source_point_rows"] == 16 * N,
               "summary state/fixed denominator")
        demand(summary["status_codes"] == STATUS and len(summary["targets"]) == 4, "summary schema")
        schema = contract["outputs"]["TARGET_{20,21,22,23}.npz"]["fields"]
        for ti, tid in enumerate(TARGETS):
            a = artifacts[f"TARGET_{tid}.npz"]
            C = a["fields"]["candidate_target_index"]["shape"][0]
            demand(isinstance(C, int) and 0 <= C <= 4 * 4 * N, "candidate count bound")
            fixed_schema = {k: dict(shape=[C if v == "C" else v for v in m["shape"]], dtype=m["dtype"])
                            for k, m in schema.items()}
            demand(a["fields"] == fixed_schema, "target independent schema")
            saved = load_archive(a["path"], a, fixed_schema, report, True)
            expected = reference_geometry(state, target_P[ti], target_K)
            numerical_summary = review_target(saved, expected, state, tid, report)
            demand(numerical_summary == summary["targets"][ti], "all pair/target summary fields exact: " + str(tid))
            report["reviewed_targets"].append(numerical_summary)
            del saved, expected
            gc.collect()
            demand(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss < 8 * 1024**3, "review sampled RSS limit")
        report["source_point_rows_checked"] = 16 * N
        report["source_target_pairs_checked"] = 16
        report["status"] = "PASS_FIXED_SAVED_PROJECTION_RECOMPUTATION"
        report["conclusion_boundary"] = "All numerical storage/selection checks passed for one exposed scene. No visibility truth, accuracy, generation benefit, or innovation is established."
    except BaseException as exc:
        report["status"] = "FAILED"
        report["error"] = dict(type=type(exc).__name__, message=str(exc), traceback=traceback.format_exc())
        raise
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, old_handler)
        report["completed_utc"] = dt.datetime.now(dt.timezone.utc).isoformat()
        report["elapsed_seconds"] = time.perf_counter() - begin
        report["peak_self_rss_bytes"] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        with out.open("x") as stream:
            json.dump(report, stream, ensure_ascii=False, indent=2, allow_nan=False)
            stream.write("\n")


if __name__ == "__main__":
    main()
