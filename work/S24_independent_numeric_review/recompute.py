#!/usr/bin/env python3
"""Recompute sealed S24 pose metrics with scalar quaternion SE(3).

No original scoring module is imported; no alignment is fitted. This author wrote
the horizon diagnostic, but did not write the primary S24 scorer. See receipt.
"""
import os
for _name in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "VECLIB_MAXIMUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ[_name] = "1"
import csv
from datetime import datetime, timezone
from decimal import Decimal, ROUND_FLOOR
import hashlib
import json
import math
from pathlib import Path
import signal
import sys
import time

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
MAIN = ROOT / "results/S24_baseline_expansion/scoring"
HORIZON = ROOT / "results/S24_horizon_diagnostic"
METHODS = ("cut3r", "ttt3r", "filt3r")
HORIZONS = ("adjacent", "1s", "5s")
ATOL, RTOL = 1e-6, 1e-5
FAILURES, CHECKS, DELTAS, IDENTITIES = [], {}, {}, {}


def utc():
    return datetime.now(timezone.utc).isoformat()


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def save(p, x):
    Path(p).write_text(json.dumps(x, ensure_ascii=False, indent=2, allow_nan=False) + "\n")


def read_json(p, decimal=False):
    data = Path(p).read_bytes()
    IDENTITIES[str(p)] = hashlib.sha256(data).hexdigest()
    return json.loads(data, parse_float=Decimal if decimal else float)


def read_csv(p):
    IDENTITIES[str(p)] = sha(p)
    with Path(p).open() as f:
        return list(csv.DictReader(f))


def check(group, ok, location):
    c = CHECKS.setdefault(group, {"checked": 0, "failed": 0})
    c["checked"] += 1
    if not ok:
        c["failed"] += 1
        if len(FAILURES) < 100:
            FAILURES.append({"group": group, "location": location})


def near(group, actual, expected, location):
    if actual is None or expected is None:
        check(group, actual is None and expected is None, location)
        return
    a, b = float(actual), float(expected)
    delta = abs(a - b)
    d = DELTAS.setdefault(group, {"max_abs_difference": 0., "max_tolerance_fraction": 0., "largest_difference_at": None})
    if delta > d["max_abs_difference"]:
        d["max_abs_difference"], d["largest_difference_at"] = delta, location
    d["max_tolerance_fraction"] = max(d["max_tolerance_fraction"], delta / (ATOL + RTOL * abs(b)))
    check(group, math.isfinite(a) and math.isfinite(b) and delta <= ATOL + RTOL * abs(b), location)


def tree(group, actual, expected, location=""):
    if isinstance(actual, dict):
        check(group, isinstance(expected, dict) and set(actual) == set(expected), location + "/keys")
        for k in actual:
            if isinstance(expected, dict) and k in expected:
                tree(group, actual[k], expected[k], location + "/" + k)
    elif isinstance(actual, list):
        check(group, isinstance(expected, list) and len(actual) == len(expected), location + "/length")
        for i, (a, b) in enumerate(zip(actual, expected)):
            tree(group, a, b, location + "/" + str(i))
    elif isinstance(actual, float):
        near(group, actual, expected, location)
    else:
        check(group, type(actual) is type(expected) and actual == expected, location)


def qmul(a, b):
    w, x, y, z = a; v, i, j, k = b
    return (w*v-x*i-y*j-z*k, w*i+x*v+y*k-z*j, w*j-x*k+y*v+z*i, w*k+x*j-y*i+z*v)


def qconj(q):
    return (q[0], -q[1], -q[2], -q[3])


def rotate(q, t):
    return qmul(qmul(q, (0., *t)), qconj(q))[1:]


def rotation_quaternion(r):
    """Branch-stable matrix-to-unit-quaternion; no SVD or pose refit."""
    tr = float(r[0, 0] + r[1, 1] + r[2, 2])
    if tr > 0:
        s = 2 * math.sqrt(1 + tr)
        q = (s / 4, (r[2, 1]-r[1, 2])/s, (r[0, 2]-r[2, 0])/s, (r[1, 0]-r[0, 1])/s)
    else:
        i = max(range(3), key=lambda k: r[k, k]); j = (i + 1) % 3; k = (i + 2) % 3
        s = 2 * math.sqrt(1 + float(r[i, i]-r[j, j]-r[k, k]))
        v = [0., 0., 0.]
        v[i] = s / 4; v[j] = (r[j, i]+r[i, j])/s; v[k] = (r[k, i]+r[i, k])/s
        q = ((r[k, j]-r[j, k])/s, *v)
    norm = math.sqrt(math.fsum(float(x*x) for x in q))
    return tuple(float(x / norm) for x in q)


def inverse(transform):
    q, t = transform
    qi = qconj(q)
    return qi, rotate(qi, tuple(-x for x in t))


def compose(a, b):
    q1, t1 = a; q2, t2 = b
    rt = rotate(q1, t2)
    return qmul(q1, q2), tuple(x+y for x, y in zip(t1, rt))


def error(pred, gt, i, j):
    grel = compose(inverse(gt[i]), gt[j])
    prel = compose(inverse(pred[i]), pred[j])
    q, t = compose(inverse(grel), prel)
    return math.sqrt(math.fsum(x*x for x in t)), math.degrees(2 * math.atan2(math.sqrt(math.fsum(x*x for x in q[1:])), abs(q[0])))


def stats(values):
    if not values:
        return {"count": 0, "rmse": None, "median": None, "p90_linear": None, "max": None}
    a = sorted(float(x) for x in values); n = len(a)
    def quantile(p):
        position = p * (n - 1); lo = math.floor(position); hi = math.ceil(position)
        return a[lo] + (position - lo) * (a[hi] - a[lo])
    return {"count": n, "rmse": math.sqrt(math.fsum(x*x for x in a) / n), "median": quantile(.5), "p90_linear": quantile(.9), "max": a[-1]}


def pairs_from_times(times):
    """Linear earliest-endpoint search, independently of original bisect path."""
    result = {}
    for horizon in HORIZONS:
        rows = []
        for i, start in enumerate(times):
            endpoint = None
            for j in range(i + 1, len(times)):
                if horizon == "adjacent" or times[j] - start >= Decimal(1 if horizon == "1s" else 5):
                    endpoint = j
                    break
            elapsed = start - times[0]
            dt = None if endpoint is None else times[endpoint] - start
            rows.append({"i": i, "j": endpoint, "rgb_time_i_decimal": str(start), "rgb_time_j_decimal": None if endpoint is None else str(times[endpoint]),
                         "elapsed_i_decimal": str(elapsed), "elapsed_i_seconds": float(elapsed), "start_bin_second": int(elapsed.to_integral_value(rounding=ROUND_FLOOR)),
                         "actual_dt_decimal": None if dt is None else str(dt), "actual_dt_seconds": None if dt is None else float(dt),
                         "status": "TAIL_NA_NO_ENDPOINT" if endpoint is None else "VALID"})
        result[horizon] = rows
    return result


def summarize(rows):
    valid = [r for r in rows if r["j"] is not None]
    return {"start_count": len(rows), "valid_pair_count": len(valid), "tail_na_count": len(rows)-len(valid),
            **{key: stats([r[key] for r in valid]) for key in ("translation_m", "rotation_deg", "actual_dt_seconds")}}


def artificial_checks():
    identity = ((1., 0., 0., 0.), (0., 0., 0.))
    quarterturn = ((math.sqrt(.5), 0., 0., math.sqrt(.5)), (1., 2., 3.))
    q, t = compose(inverse(quarterturn), quarterturn)
    check("artificial", all(abs(x) < 1e-14 for x in t) and abs(abs(q[0])-1) < 1e-14, "SE3_inverse_identity")
    et, er = error([identity, quarterturn], [identity, identity], 0, 1)
    check("artificial", abs(et-math.sqrt(14)) < 1e-14 and abs(er-90) < 1e-12, "known_translation_and_angle")
    for axis in range(3):
        r = -np.eye(3); r[axis, axis] = 1
        q = rotation_quaternion(r)
        check("artificial", abs(q[0]) < 1e-14 and abs(abs(q[axis+1])-1) < 1e-14, "halfturn_axis_"+str(axis))
    times = [Decimal(x) for x in ("1305031102.175304", "1305031103.175303", "1305031103.175304", "1305031107.175304")]
    p = pairs_from_times(times)
    check("artificial", p["1s"][0]["j"] == 2 and p["5s"][0]["j"] == 3 and p["1s"][-1]["j"] is None, "Decimal_endpoint_and_tail")
    check("artificial", stats([])["rmse"] is None and stats([0., 1., 2., 3.])["p90_linear"] == 2.7, "quantile_empty_vs_zero")


def run():
    signal.signal(signal.SIGALRM, lambda *_: (_ for _ in ()).throw(TimeoutError("180-second numeric limit")))
    signal.alarm(180)
    start = time.monotonic()
    receipt_path = OUT / "receipt.json"
    if receipt_path.exists():
        raise FileExistsError("Refuse existing numeric review")
    receipt = {"status": "RUNNING", "started_utc": utc(), "resource_contract": {"cpu_threads": 1, "timeout_seconds": 180, "rss_limit_bytes": 1073741824},
               "author_relation": "Different author from primary S24 scorer; SAME author as s24_horizon_diagnostic.py, using a new quaternion/SE3 implementation. Not an independent-author audit of horizon code.",
               "alignment_refitted": False, "new_models": 0, "sensor_gt_bytes_read": 0, "pose_gt_from_published_aligned_archives": True}
    save(receipt_path, receipt)
    try:
        artificial_checks()
        parent_path = ROOT / "work/S24_baseline_expansion/run_manifest.json"
        child_path = ROOT / "work/S24_horizon_preparation/run_manifest.json"
        parent = read_json(parent_path, decimal=True); child = read_json(child_path)
        mr = read_json(MAIN / "receipt.json"); mm = read_json(MAIN / "metrics.json")
        hr = read_json(HORIZON / "receipt.json"); hm = read_json(HORIZON / "metrics.json")
        hs = read_json(HORIZON / "input_seal.json")
        check("seals", mr["status"] == hr["status"] == "PASS", "score_receipts")
        check("seals", mr["metrics_sha256"] == sha(MAIN / "metrics.json"), "main_metrics_SHA")
        check("seals", hr["metrics_sha256"] == sha(HORIZON / "metrics.json"), "horizon_metrics_SHA")
        check("seals", child["parent_manifest_sha256"] == mr["manifest_sha256"] == hr["parent_manifest_sha256"] == sha(parent_path), "parent_SHA")
        check("seals", hr["child_manifest_sha256"] == hm["child_manifest_sha256"] == sha(child_path), "child_SHA")
        check("seals", hr["output_sha256"]["input_seal.json"] == hm["input_seal_sha256"] == sha(HORIZON / "input_seal.json"), "horizon_input_seal_SHA")
        for name in ("all_pairs.csv", "one_second_bins.csv"):
            check("seals", hr["output_sha256"][name] == sha(HORIZON / name), name)
        for path, expected in child["controls"].items():
            check("seals", sha(path) == expected, path)
            IDENTITIES[path] = expected
        check("contract", float(parent["contract"]["metric_atol"]) == ATOL and float(parent["contract"]["metric_rtol"]) == RTOL, "frozen_tolerance")
        n = len(parent["frames"]); times = [r["rgb_time"] for r in parent["frames"]]
        check("contract", n == 796 and parent["methods"] == list(METHODS), "full_domain")
        check("contract", [r["index"] for r in parent["frames"]] == list(range(n)) and all(a < b for a, b in zip(times, times[1:])), "index_time_order")
        plan = pairs_from_times(times)
        tree("frozen_pairs", plan, child["plan"]["pairs"])
        frames = [{"index": i, "rgb_time_decimal": str(t), "elapsed_decimal": str(t-times[0]), "elapsed_seconds": float(t-times[0]),
                   "start_bin_second": int((t-times[0]).to_integral_value(rounding=ROUND_FLOOR))} for i, t in enumerate(times)]
        tree("frozen_frames", frames, child["plan"]["frames"])
        span = times[-1] - times[0]
        bins = [{"bin_second": k, "nominal_end_second": k+1, "interval_complete": Decimal(k+1) <= span,
                 "observed_end_seconds": float(min(Decimal(k+1), span)), "start_count": sum(r["start_bin_second"] == k for r in frames)} for k in range(int(span)+1)]
        tree("frozen_bins", bins, child["plan"]["bins"])
        check("frozen_frames", child["plan"]["frame_count"] == n and child["plan"]["span_decimal"] == str(span), "count_span")
        csv_pairs = read_csv(HORIZON / "all_pairs.csv"); csv_bins = read_csv(HORIZON / "one_second_bins.csv")
        check("pair_csv_domain", len(csv_pairs) == n*9, "row_count")
        check("bin_csv_domain", len(csv_bins) == len(bins)*9, "row_count")
        pair_lookup = {(r["method"], r["horizon"], int(r["i"])): r for r in csv_pairs}
        bin_lookup = {(r["method"], r["horizon"], int(r["bin_second"])): r for r in csv_bins}
        check("pair_csv_domain", len(pair_lookup) == len(csv_pairs), "no_duplicates")
        check("bin_csv_domain", len(bin_lookup) == len(csv_bins), "no_duplicates")
        if FAILURES:
            raise ValueError("Metadata or hash gate failed before pose array decoding")
        rows_all, summary, common_gt = [], {}, None
        receipt["aligned_pose_decode_started_utc"] = utc(); save(receipt_path, receipt)
        for method in METHODS:
            path = MAIN / (method + "_aligned.npz")
            h = sha(path); IDENTITIES[str(path)] = h
            check("aligned_SHA", h == hs["identities"][str(path)] == hm["input_identities"][str(path)], method)
            if CHECKS["aligned_SHA"]["failed"]:
                raise ValueError("Aligned pose hash mismatch")
            with np.load(path, allow_pickle=False) as z:
                check("array_schema", set(z.files) == {"pred", "gt", "ate_m", "rpe_translation_m", "rpe_rotation_deg"}, method)
                arrays = {k: z[k] for k in z.files}
            for name in ("pred", "gt"):
                a = arrays[name]
                check("array_schema", a.shape == (n, 4, 4) and a.dtype == np.float64 and np.isfinite(a).all(), method+"/"+name)
                check("rotation_schema", np.allclose(a[:, :3, :3].transpose(0, 2, 1) @ a[:, :3, :3], np.eye(3), rtol=0, atol=1e-7) and np.allclose(np.linalg.det(a[:, :3, :3]), 1, rtol=0, atol=1e-7), method+"/"+name)
                check("array_schema", np.array_equal(a[:, 3, :], np.tile([0.,0.,0.,1.], (n,1))), method+"/"+name+"/last_row")
            if common_gt is None: common_gt = arrays["gt"].copy()
            else: check("same_GT", np.array_equal(common_gt, arrays["gt"]), method)
            pred, gt = [[(rotation_quaternion(a[:3,:3]), tuple(float(x) for x in a[:3,3])) for a in arrays[name]] for name in ("pred", "gt")]
            ate = [math.dist(p[1], g[1]) for p, g in zip(pred, gt)]
            for i, value in enumerate(ate): near("main_perframe_ATE", value, arrays["ate_m"][i], method+"/"+str(i))
            summary[method] = {}
            for horizon in HORIZONS:
                rows = []
                for metadata in plan[horizon]:
                    et, er = (None, None) if metadata["j"] is None else error(pred, gt, metadata["i"], metadata["j"])
                    row = {"method": method, "horizon": horizon, **metadata, "translation_m": et, "rotation_deg": er}
                    rows.append(row); rows_all.append(row)
                    saved = pair_lookup.get((method, horizon, metadata["i"]))
                    check("pair_csv_domain", saved is not None, method+"/"+horizon+"/"+str(metadata["i"]))
                    if saved is not None:
                        for key, value in row.items():
                            loc = method+"/"+horizon+"/"+str(metadata["i"])+"/"+key
                            if isinstance(value, float): near("pair_csv_"+key, value, None if saved[key] == "NA" else float(saved[key]), loc)
                            else: check("pair_csv_metadata", saved[key] == ("NA" if value is None else str(value)), loc)
                global_summary = summarize(rows)
                bin_summaries = []
                for b in bins:
                    sub = summarize([r for r in rows if r["start_bin_second"] == b["bin_second"]])
                    merged = {**b, **sub}; bin_summaries.append(merged)
                    saved = bin_lookup[(method, horizon, b["bin_second"])]
                    flat = {"method":method,"horizon":horizon}
                    for key, value in merged.items():
                        if isinstance(value,dict): flat.update({key+"_"+k:v for k,v in value.items()})
                        else: flat[key] = value
                    for key,value in flat.items():
                        loc=method+"/"+horizon+"/"+str(b["bin_second"])+"/"+key
                        if isinstance(value,float): near("bin_csv_numeric",value,None if saved[key] == "NA" else float(saved[key]),loc)
                        else: check("bin_csv_metadata",saved[key] == ("NA" if value is None else str(value)),loc)
                summary[method][horizon] = {"all_pairs":global_summary,"bins":bin_summaries}
                tree("horizon_summary",summary[method][horizon],hm["methods"][method][horizon],method+"/"+horizon)
                if horizon == "adjacent":
                    ts=[r["translation_m"] for r in rows[:-1]]; rs=[r["rotation_deg"] for r in rows[:-1]]
                    for key, values in (("rpe_translation_m",ts),("rpe_rotation_deg",rs)):
                        check("array_schema",arrays[key].shape == (n-1,) and arrays[key].dtype == np.float64,method+"/"+key)
                        for i, value in enumerate(values): near("main_"+key,value,arrays[key][i],method+"/"+str(i))
                    three=[stats(ate)["rmse"],stats(ts)["rmse"],stats(rs)["rmse"]]
                    for ref in ("official","independent_matrix"):
                        for k in range(3):near("main_summary",three[k],mm["methods"][method][ref][k],method+"/"+ref+"/"+str(k))
                    block_rows=[]
                    for lo in range(0,n,100):
                        hi=min(lo+100,n); pend=min(hi,n-1)
                        block_rows.append({"start":lo,"end_exclusive":hi,"frame_count":hi-lo,"ate_rmse_m":stats(ate[lo:hi])["rmse"],
                            "rpe_pair_start":lo,"rpe_pair_end_exclusive":pend,"rpe_pair_count":pend-lo,
                            "rpe_translation_rmse_m":stats(ts[lo:pend])["rmse"],"rpe_rotation_rmse_deg":stats(rs[lo:pend])["rmse"]})
                    tree("main_100frame_blocks",block_rows,mm["methods"][method]["all_blocks"],method)
                    perframe=read_csv(MAIN/(method+"_per_frame.csv"));check("main_csv_domain",len(perframe)==n,method)
                    for i,row in enumerate(perframe):
                        check("main_csv_metadata",int(row["index"])==i and Decimal(row["rgb_timestamp"])==times[i] and Decimal(row["gt_timestamp"])==parent["frames"][i]["gt_time"],method+"/"+str(i))
                        near("main_csv_ATE",ate[i],float(row["ate_m"]),method+"/"+str(i))
                        for key,value in (("rpe_to_next_translation_m",ts[i] if i<n-1 else None),("rpe_to_next_rotation_deg",rs[i] if i<n-1 else None)):
                            near("main_csv_RPE",value,None if row[key] in ("","NA") else float(row[key]),method+"/"+str(i)+"/"+key)
            receipt["methods_completed"]=list(summary);save(receipt_path,receipt)
        save(OUT/"independent_summary.json",summary)
        with (OUT/"independent_all_pairs.csv").open("w",newline="") as f:
            writer=csv.DictWriter(f,fieldnames=list(rows_all[0]));writer.writeheader();writer.writerows(rows_all)
        for path,expected in IDENTITIES.items():check("before_after_SHA",sha(path)==expected,path)
        receipt.update(status="PASS" if not FAILURES else "FAIL",completed_utc=utc(),elapsed_seconds=time.monotonic()-start,
            check_groups=CHECKS,numeric_differences=DELTAS,failures_first_100=FAILURES,input_sha256_before_after=IDENTITIES,
            frame_count=n,paired_rows=len(rows_all),valid_pair_evaluations=sum(r["j"] is not None for r in rows_all),
            valid_pair_counts_per_method={h:sum(r["j"] is not None for r in plan[h]) for h in HORIZONS},
            tail_NA_counts_per_method={h:sum(r["j"] is None for r in plan[h]) for h in HORIZONS},
            bins_per_method_horizon=len(bins),metric_tolerance={"atol":ATOL,"rtol":RTOL},
            formula="q-error=conj(conj(qGi)*qGj)*(conj(qPi)*qPj); SE3 inverse translation=-rotate(conj(q),t); angle=2 atan2(norm(qvec),abs(qw)); no matrix inverse/trace-acos or alignment fit",
            quaternion_note="Input SO(3) checked at original 1e-7; unit quaternion normalized for scalar representation roundoff, no scene alignment or matrix SVD correction",
            python=sys.version,numpy=np.__version__,source_sha256=sha(__file__),
            outputs={p.name:sha(p) for p in [OUT/"independent_summary.json",OUT/"independent_all_pairs.csv"]},
            limits=["Recomputes saved, already globally aligned trajectories; does not independently establish raw prediction-to-GT alignment or model provenance",
                    "Aligned NPZs first received their own hashes at horizon postprocessing, not in the primary score receipt",
                    "Same author as horizon implementation; a new mathematical path, not external or different-author horizon replication",
                    "No sensor depth, model, new method, generation result, event selection or forgetting conclusion"])
        save(receipt_path,receipt)
        print(json.dumps({k:receipt[k] for k in ("status","completed_utc","elapsed_seconds","frame_count","paired_rows","valid_pair_evaluations","valid_pair_counts_per_method","tail_NA_counts_per_method","source_sha256","failures_first_100")},indent=2))
        return 0 if receipt["status"]=="PASS" else 1
    except BaseException as e:
        receipt.update(status="FAIL",completed_utc=utc(),error=repr(e),check_groups=CHECKS,failures_first_100=FAILURES,source_sha256=sha(__file__))
        save(receipt_path,receipt)
        raise


if __name__ == "__main__":
    sys.exit(run())
