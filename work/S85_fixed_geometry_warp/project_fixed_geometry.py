"""S85: fixed cached geometry, positive bilinear footprints, hard depth winner.

Importing defines pure arithmetic only. The __main__ entry reads frozen real
inputs once and creates execution_01; it must only be launched after review.
"""
import os
for _name in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
              "VECLIB_MAXIMUM_THREADS", "NUMEXPR_NUM_THREADS", "BLIS_NUM_THREADS"):
    os.environ[_name] = "1"

import datetime as dt
import hashlib
import io
import json
from pathlib import Path
import platform
import resource
import signal
import sys
import time
import traceback
import numpy as np

HERE = Path(__file__).resolve().parent
STATUS = {"VALID": 0, "SOURCE_NONFINITE": 1, "SOURCE_NONPOSITIVE": 2,
          "TARGET_NONFINITE": 3, "TARGET_NONPOSITIVE": 4, "OUTSIDE": 5}
PRIORITY = {19: 0, 18: 1, 13: 2, 12: 3}


def require(ok, message):
    if not ok:
        raise ValueError(message)


def digest_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def digest_array(a):
    return hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()


def pinhole_check(K):
    require(K.shape == (3, 3) and np.isfinite(K).all(), "invalid K")
    require(K[0, 0] > 0 and K[1, 1] > 0 and K[2, 2] == 1,
            "invalid pinhole diagonal")
    require(np.array_equal(K[[0, 1, 2, 2], [1, 0, 0, 1]], np.zeros(4)),
            "non-pinhole off-diagonal; do not silently simplify")


def pose_check(P):
    require(P.shape == (4, 4) and np.isfinite(P).all(), "invalid c2w")
    require(np.array_equal(P[3], [0, 0, 0, 1]), "invalid homogeneous row")
    # Explicit scalar dot products avoid a threaded BLAS kernel.
    for i in range(3):
        for j in range(3):
            dot = sum(float(P[k, i]) * float(P[k, j]) for k in range(3))
            require(abs(dot - float(i == j)) <= 1e-5, "rotation not orthogonal")
    a, b, c = P[:3, :3]
    det = a[0]*(b[1]*c[2]-b[2]*c[1])-a[1]*(b[0]*c[2]-b[2]*c[0])+a[2]*(b[0]*c[1]-b[1]*c[0])
    require(abs(float(det) - 1) <= 1e-5, "rotation not right-handed")


def transform_rows(xyz, R, translation):
    """Row storage, mathematical result R*x+t; no BLAS/einsum."""
    return np.stack([R[k, 0]*xyz[:, 0] + R[k, 1]*xyz[:, 1] +
                     R[k, 2]*xyz[:, 2] + translation[k]
                     for k in range(3)], axis=1)


def project_points(uv, z, Ki, Ps, Pt, Kt, target_hw):
    """FP64 camera transform. Invalid/behind points never undergo division."""
    uv, z = np.asarray(uv, np.float64), np.asarray(z, np.float64)
    Ki, Ps, Pt, Kt = [np.asarray(x, np.float64) for x in (Ki, Ps, Pt, Kt)]
    require(uv.shape == (len(z), 2) and np.isfinite(uv).all(), "invalid source grid")
    pinhole_check(Ki); pinhole_check(Kt); pose_check(Ps); pose_check(Pt)
    n = len(z)
    status = np.full(n, STATUS["VALID"], np.uint8)
    status[~np.isfinite(z)] = STATUS["SOURCE_NONFINITE"]
    status[np.isfinite(z) & (z <= 0)] = STATUS["SOURCE_NONPOSITIVE"]
    xyz = np.full((n, 3), np.nan, np.float64)
    target_uv = np.full((n, 2), np.nan, np.float64)
    src = np.flatnonzero(status == STATUS["VALID"])
    with np.errstate(over="ignore", invalid="ignore", divide="ignore"):
        rays = np.stack([(uv[src, 0]-Ki[0, 2])/Ki[0, 0],
                         (uv[src, 1]-Ki[1, 2])/Ki[1, 1],
                         np.ones(len(src))], axis=1)
        world = transform_rows(rays*z[src, None], Ps[:3, :3], Ps[:3, 3])
        xyz[src] = transform_rows(world-Pt[:3, 3], Pt[:3, :3].T, np.zeros(3))
        bad = src[~np.isfinite(xyz[src]).all(axis=1)]
        status[bad] = STATUS["TARGET_NONFINITE"]
        remaining = np.flatnonzero(status == STATUS["VALID"])
        status[remaining[xyz[remaining, 2] <= 0]] = STATUS["TARGET_NONPOSITIVE"]
        front = np.flatnonzero(status == STATUS["VALID"])
        target_uv[front, 0] = Kt[0, 0]*(xyz[front, 0]/xyz[front, 2])+Kt[0, 2]
        target_uv[front, 1] = Kt[1, 1]*(xyz[front, 1]/xyz[front, 2])+Kt[1, 2]
    status[front[~np.isfinite(target_uv[front]).all(axis=1)]] = STATUS["TARGET_NONFINITE"]
    front = np.flatnonzero(status == STATUS["VALID"])
    h, w = target_hw
    outside = ((target_uv[front, 0] < 0) | (target_uv[front, 0] > w-1) |
               (target_uv[front, 1] < 0) | (target_uv[front, 1] > h-1))
    status[front[outside]] = STATUS["OUTSIDE"]
    return status, xyz, target_uv


def footprints(uv, valid, target_hw):
    """Dense slots (00,10,01,11); no snap/epsilon, strict positive weights."""
    h, w = target_hw
    index = np.full((len(uv), 4), -1, np.int32)
    weight = np.zeros((len(uv), 4), np.float64)
    rows = np.flatnonzero(valid)
    require(np.isfinite(uv[rows]).all(), "nonfinite eligible UV")
    require(((uv[rows] >= 0) & (uv[rows] <= [w-1, h-1])).all(), "eligible UV outside")
    lo = np.floor(uv[rows]).astype(np.int64)
    frac = uv[rows] - lo
    for slot, (dx, dy) in enumerate(((0, 0), (1, 0), (0, 1), (1, 1))):
        x, y = lo[:, 0]+dx, lo[:, 1]+dy
        value = (frac[:, 0] if dx else 1-frac[:, 0]) * (frac[:, 1] if dy else 1-frac[:, 1])
        keep = (value > 0) & (x >= 0) & (x < w) & (y >= 0) & (y < h)
        index[rows[keep], slot] = (y[keep]*w+x[keep]).astype(np.int32)
        weight[rows[keep], slot] = value[keep]
    require(np.array_equal((index >= 0).any(axis=1), valid), "valid point without footprint")
    return index, weight


def hard_buffer(target_index, target_z, source_row, pixel_id, slot, weight,
                history_ids, colors, target_hw):
    """Complete stable candidate ordering, direct winner RGB, second may tie."""
    total = int(np.prod(target_hw))
    require(np.isfinite(target_z).all() and (target_z > 0).all(), "bad candidate Z")
    require(np.isfinite(weight).all() and (weight > 0).all(), "bad candidate weight")
    require(((target_index >= 0) & (target_index < total)).all(), "bad target index")
    priorities = np.array([PRIORITY[int(x)] for x in history_ids], np.int8)[source_row]
    # Last lexsort key is primary; slot is a final deterministic duplicate guard.
    order = np.lexsort((slot, pixel_id, priorities, target_z, target_index))
    fields = dict(candidate_target_index=target_index[order],
                  candidate_Z=target_z[order], candidate_source_row=source_row[order],
                  candidate_pixel_id=pixel_id[order], candidate_slot=slot[order],
                  candidate_weight=weight[order])
    t = fields["candidate_target_index"]
    count = np.bincount(t, minlength=total).astype(np.int32)
    starts = np.cumsum(count, dtype=np.int64)-count
    occupied = np.flatnonzero(count)
    winner = starts[occupied]
    rank = np.arange(len(t), dtype=np.int64)-np.repeat(starts[occupied], count[occupied])
    fields["candidate_rank"] = rank.astype(np.int32)
    fields["candidate_winner"] = rank == 0
    mask = count > 0
    rgb = np.zeros((total, 3), colors.dtype)
    rgb[occupied] = colors[fields["candidate_source_row"][winner],
                           fields["candidate_pixel_id"][winner]]
    fields.update(mask=mask.reshape(target_hw),
                  candidate_count=count.reshape(target_hw),
                  warp_rgb=rgb.reshape((*target_hw, 3)))
    for prefix, pixels, selected in (
            ("winner", occupied, winner),
            ("second_candidate", np.flatnonzero(count >= 2),
             starts[np.flatnonzero(count >= 2)]+1)):
        for suffix, dtype, values in (
                ("source_row", np.int8, fields["candidate_source_row"]),
                ("pixel_id", np.int32, fields["candidate_pixel_id"]),
                ("slot", np.int8, fields["candidate_slot"])):
            a = np.full(total, -1, dtype)
            a[pixels] = values[selected]
            fields[prefix+"_"+suffix] = a.reshape(target_hw)
        z = np.full(total, np.nan, np.float64)
        z[pixels] = fields["candidate_Z"][selected]
        fields[prefix+"_Z"] = z.reshape(target_hw)
        ids = np.full(total, -1, np.int16)
        ids[pixels] = history_ids[fields["candidate_source_row"][selected]]
        fields[prefix+"_history_id"] = ids.reshape(target_hw)
    return fields


def project_target(depth, colors, source_K, source_P, history_ids, target_P, target_K,
                   target_hw=(576, 576)):
    """One target containing all four source-target pairs and all candidates."""
    histories, h, w = depth.shape
    require(histories == 4 and list(history_ids) == [12, 13, 18, 19], "history identity")
    require(colors.shape == (histories, h, w, 3), "color shape")
    require(np.isfinite(colors).all() and ((colors >= 0) & (colors <= 1)).all(), "color values")
    n = h*w
    pix = np.arange(n, dtype=np.int32)
    uv = np.stack([pix % w, pix // w], axis=1)
    status, xyz, q, indices, weights = [], [], [], [], []
    for row in range(histories):
        s, x, u = project_points(uv, depth[row].reshape(n), source_K[row],
                                  source_P[row], target_P, target_K, target_hw)
        idx, wt = footprints(u, s == STATUS["VALID"], target_hw)
        status.append(s); xyz.append(x); q.append(u); indices.append(idx); weights.append(wt)
    status, xyz, q = np.stack(status), np.stack(xyz), np.stack(q)
    indices, weights = np.stack(indices), np.stack(weights)
    rows, pixels, slots = np.nonzero(indices >= 0)
    out = hard_buffer(indices[rows, pixels, slots], xyz[rows, pixels, 2],
                      rows.astype(np.int8), pixels.astype(np.int32), slots.astype(np.uint8),
                      weights[rows, pixels, slots], history_ids,
                      colors.reshape(histories, n, 3), target_hw)
    winner = np.zeros(indices.shape, bool)
    keep = out["candidate_winner"]
    winner[out["candidate_source_row"][keep], out["candidate_pixel_id"][keep],
           out["candidate_slot"][keep]] = True
    out.update(history_ids=np.asarray(history_ids, np.int64), source_pixel_id=pix,
               source_uv=uv, source_status=status, target_xyz=xyz, target_uv=q,
               footprint_target_index=indices, footprint_weight=weights,
               footprint_winner=winner)
    pairs = []
    for row, hid in enumerate(history_ids):
        valid_footprints = int((indices[row] >= 0).sum())
        won = int(winner[row].sum())
        pairs.append(dict(history_id=int(hid), N=n,
                          status_counts={name: int((status[row] == code).sum())
                                         for name, code in STATUS.items()},
                          eligible_footprints=valid_footprints, winning_footprints=won,
                          losing_footprints=valid_footprints-won,
                          source_points_with_any_win=int(winner[row].any(axis=1).sum())))
    count = out["candidate_count"]
    summary = dict(source_points=histories*n, target_pixels=int(count.size),
                   valid_footprints=int(count.sum()), winners=int((count > 0).sum()),
                   losers=int(count.sum()-(count > 0).sum()), holes=int((count == 0).sum()),
                   coverage=float((count > 0).mean()),
                   pixels_with_multiple_candidates=int((count >= 2).sum()), pairs=pairs)
    return out, summary


def main():
    contract_path = HERE/"CONTRACT.json"
    contract = json.loads(contract_path.read_text())
    output = HERE/"execution_01"
    require(str(output) == contract["output_directory"], "fixed output path")
    output.mkdir(exist_ok=False)  # Never overwrite or automatically rerun.
    start = time.perf_counter()
    rec = dict(status="STARTED", started_utc=dt.datetime.now(dt.timezone.utc).isoformat(),
               contract_sha256=digest_file(contract_path), reads=[], artifacts=[],
               completed_targets=[], model_calls=0, optimizer_calls=0,
               target_RGB_reads=0, sensor_depth_reads=0, new_method_validated=False)
    def write_json(name, obj):
        tmp = output/(name+".tmp")
        tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=2, allow_nan=False)+"\n")
        tmp.replace(output/name)
    def checkpoint(stage):
        rec["stage"] = stage
        rec["elapsed_seconds"] = time.perf_counter()-start
        rec["peak_self_rss_bytes"] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        rec["output_bytes_current"] = sum(p.stat().st_size for p in output.iterdir() if p.is_file())
        write_json("RECEIPT.json", rec)
        require(rec["elapsed_seconds"] < contract["resources"]["wall_seconds"], "time limit")
        require(rec["peak_self_rss_bytes"] < contract["resources"]["rss_bytes"], "RSS limit")
        require(rec["output_bytes_current"] < contract["resources"]["output_bytes"], "output limit")
    def alarm(_sig, _frame):
        raise TimeoutError("S85 300-second runtime limit")
    def save(name, arrays):
        require(all(not x.dtype.hasobject for x in arrays.values()), "object output forbidden")
        # np.savez is uncompressed ZIP: fixed upper estimate plus 16MiB receipt reserve.
        estimate = sum(x.nbytes+1024 for x in arrays.values())+65536
        used = sum(p.stat().st_size for p in output.iterdir() if p.is_file())
        require(used+estimate+16*1024**2 < contract["resources"]["output_bytes"], "output preflight limit")
        path = output/name
        with path.open("xb") as stream:
            np.savez(stream, **arrays)
        rec["artifacts"].append(dict(path=str(path), bytes=path.stat().st_size,
                                     sha256=digest_file(path),
                                     fields={k: dict(shape=list(v.shape), dtype=str(v.dtype))
                                             for k, v in arrays.items()}))
        checkpoint("saved "+name)
    def read_input(spec):
        path = Path(spec["path"])
        raw = path.read_bytes()
        identity = dict(path=str(path), bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest(),
                        decoded_fields=[])
        rec["reads"].append(identity); checkpoint("input hashed "+spec["role"])
        require(identity["bytes"] == spec["bytes"] and identity["sha256"] == spec["sha256"], "input identity")
        result = {}
        with np.load(io.BytesIO(raw), allow_pickle=False) as archive:
            for key, meta in spec["fields"].items():
                a = archive[key]
                identity["decoded_fields"].append(key)
                require(list(a.shape) == meta["shape"] and str(a.dtype) == meta["dtype"], "input schema "+key)
                require(digest_array(a) == meta["body_sha256"], "input body "+key)
                result[key] = a
        checkpoint("input decoded "+spec["role"])
        return result
    previous_handler = signal.signal(signal.SIGALRM, alarm)
    signal.setitimer(signal.ITIMER_REAL, contract["resources"]["wall_seconds"])
    try:
        require(digest_file(__file__) == contract["runner_sha256"], "runner identity")
        require(sys.platform == "darwin" and np.__version__ == contract["runtime"]["numpy"], "runtime")
        rec["runtime"] = dict(python=platform.python_version(), numpy=np.__version__,
                              geometry_dtype="float64", worker_threads=1,
                              thread_env={k: os.environ[k] for k in os.environ if k.endswith("_NUM_THREADS")
                                          or k == "VECLIB_MAXIMUM_THREADS"})
        checkpoint("source verified")
        state = read_input(contract["inputs"][0])
        cameras = read_input(contract["inputs"][1])
        require(np.array_equal(state["history_ids"], contract["history_ids"]), "source IDs")
        require(np.array_equal(cameras["ids"], contract["camera_archive_ids"]), "camera archive IDs")
        targets = np.array(contract["target_ids"], np.int64)
        rows = [int(np.flatnonzero(cameras["ids"] == t)[0]) for t in targets]
        target_P = cameras["c2ws"][rows].copy()
        target_K = np.array(contract["target_K"], np.float64)
        require(np.isfinite(state["colors"]).all() and
                ((state["colors"] >= 0) & (state["colors"] <= 1)).all(), "invalid input color")
        for K, P in zip(state["K"], state["c2w"]):
            pinhole_check(K); pose_check(P)
        for P in target_P:
            pose_check(P)
        pinhole_check(target_K)
        used = dict(source_depth=state["depth"], source_colors=state["colors"],
                    source_K_saved=state["K"], source_c2w_saved=state["c2w"],
                    history_ids=state["history_ids"], target_ids=targets,
                    target_c2w=target_P, target_K=target_K)
        save("INPUT_GEOMETRY.npz", used)
        rec["camera_archive_selection"] = dict(archive_ids=cameras["ids"].tolist(),
                                                selected_rows=rows, consumed_ids=targets.tolist(),
                                                non_target_camera_rows_used=False)
        for a in (*state.values(), target_P, target_K):
            a.flags.writeable = False
        source_K, source_P = state["K"].astype(np.float64), state["c2w"].astype(np.float64)
        summaries = []
        for i, tid in enumerate(targets):
            checkpoint("projecting target "+str(tid))
            arrays, summary = project_target(state["depth"], state["colors"], source_K, source_P,
                                             state["history_ids"], target_P[i], target_K)
            summary["target_id"] = int(tid)
            arrays["target_id"] = np.array(tid, np.int64)
            save(f"TARGET_{tid}.npz", arrays)
            summaries.append(summary)
            rec["completed_targets"].append(int(tid))
            write_json("SUMMARY.json", dict(status="PARTIAL", targets=summaries))
            checkpoint("target complete "+str(tid))
            del arrays
        require(len(summaries) == 4 and sum(len(x["pairs"]) for x in summaries) == 16, "all pairs")
        write_json("SUMMARY.json", dict(status="COMPLETED_PENDING_INDEPENDENT_REVIEW",
                   source_point_rows=16*384*512, targets=summaries, status_codes=STATUS,
                   meaning="Predicted footprint support, not visibility, accuracy, or generation benefit"))
        rec["status"] = "COMPLETED_PENDING_INDEPENDENT_REVIEW"
    except BaseException as exc:
        rec["status"] = "FAILED"
        rec["error"] = dict(type=type(exc).__name__, message=str(exc))
        (output/"TRACEBACK.txt").write_text(traceback.format_exc())
        raise
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous_handler)
        rec["completed_utc"] = dt.datetime.now(dt.timezone.utc).isoformat()
        rec["elapsed_seconds"] = time.perf_counter()-start
        rec["peak_self_rss_bytes"] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        if (output/"SUMMARY.json").exists():
            rec["summary_sha256"] = digest_file(output/"SUMMARY.json")
        rec["output_bytes_before_final_receipt"] = sum(
            p.stat().st_size for p in output.iterdir() if p.is_file())
        write_json("RECEIPT.json", rec)


if __name__ == "__main__":
    main()
