"""Post-seal S24 trajectory scoring; importing this module reads no data.

Uses the S21 official evo wrapper and its separately implemented Sim(3)/SE(3)
matrix calculation. All lengths derive from the frozen manifest, never 300.
"""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import copy
import csv
import hashlib
import io
import json
import math
import platform
import sys
import traceback

ROOT = Path(__file__).resolve().parents[1]
W = ROOT / "work/S24_baseline_expansion"
B = ROOT / "results/S24_baseline_expansion"
CONTROL = ROOT / "work/S24_execution"
R = ROOT / "work/S21_baseline_preparation/ttt3r_original"
METHODS = {"cut3r", "ttt3r", "filt3r"}
ATOL, RTOL, BLOCK_SIZE = 1e-6, 1e-5, 100


def utc():
    return datetime.now(timezone.utc).isoformat()


def sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def write(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2,
                                     allow_nan=False) + "\n")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def validate_manifest(m):
    """Metadata only: no RGB, prediction or GT file access."""
    names = m["methods"]
    require(len(names) == 3 and set(names) == METHODS, "Require all three methods")
    frames = m["frames"]
    n = len(frames)
    require(n >= 3 and m["contract"]["frames"] == n, "Invalid frame count")
    require([f["index"] for f in frames] == list(range(n)), "Noncontiguous frame indices")
    require(m["contract"]["block_size"] == BLOCK_SIZE, "Unexpected block size")
    require(m["contract"]["metric_atol"] == ATOL and
            m["contract"]["metric_rtol"] == RTOL, "Frozen metric tolerance differs")
    require(m["contract"]["all_three_sealed_before_gt_coordinate_scoring"] is True,
            "Missing output-before-GT contract")
    for key in ("rgb_time", "gt_time"):
        times = [f[key] for f in frames]
        require(all(math.isfinite(t) for t in times), "Nonfinite timestamp")
        require(all(a < b for a, b in zip(times, times[1:])),
                "Timestamps must be unique and strictly increasing: " + key)
    require(all(abs(f["rgb_time"] - f["gt_time"]) < .02 for f in frames),
            "Association outside frozen 0.02 second bound")
    require(len({f["path"] for f in frames}) == n, "Duplicate RGB input identity")
    return n


def verified_prediction_seals(m, manifest_hash):
    """Hash archived bytes only; never decode pointmaps or GT here."""
    n = len(m["frames"])
    seals = {}
    for name in m["methods"]:
        base = B / name
        worker_path, caller_path = base / "receipt.json", CONTROL / name / "receipt.json"
        worker_data, caller_data = worker_path.read_bytes(), caller_path.read_bytes()
        worker, caller = json.loads(worker_data), json.loads(caller_data)
        require(worker["status"] == caller["status"] == "PASS", name + ": incomplete run")
        require(caller["returncode"] == 0 and "failure" not in caller, name + ": caller failed")
        require(worker["manifest_sha256"] == caller["manifest_sha256"] == manifest_hash,
                name + ": manifest mismatch")
        require(worker["mode"] == name and worker["gt_coordinates_used"] is False,
                name + ": wrong method or GT access contract")
        require(worker["frames_completed"] == worker["frames_expected"] == n,
                name + ": partial frames")
        require(Path(worker["actual_source"]).resolve() == Path(m["sources"][name]).resolve(),
                name + ": source differs from manifest")
        outputs = worker["outputs"]
        require(len(outputs) == n and [f["index"] for f in outputs] == list(range(n)),
                name + ": missing, reordered or duplicated output indices")
        require(len({f["file"] for f in outputs}) == n, name + ": duplicate output path")
        require({p.name for p in base.glob("*.npz")} == {f["file"] for f in outputs},
                name + ": unexpected or missing NPZ archive member")
        for item in outputs:
            p = Path(item["file"])
            require(p.name == str(p) and p.suffix == ".npz", name + ": invalid NPZ path")
            require(sha(base / p) == item["sha256"], name + ": NPZ SHA mismatch " + str(p))
        require(sha(base / "poses.npy") == worker["poses_sha256"], name + ": pose SHA mismatch")
        seals[name] = dict(worker_receipt_sha256=hashlib.sha256(worker_data).hexdigest(),
                           caller_receipt_sha256=hashlib.sha256(caller_data).hexdigest(),
                           poses_sha256=worker["poses_sha256"], frame_count=n,
                           outputs=outputs, npz_hash_checks=len(outputs))
    return seals


def matrix_metrics(P, G):
    """S21 Sim(3) position alignment and adjacent SE(3) error, in NumPy.

    Input rotations have already received the common SciPy normalization.
    The mathematical core matches score_s21_baseline.matrix_metrics.
    """
    import numpy as np
    require(P.shape == G.shape and P.ndim == 3 and P.shape[1:] == (4, 4),
            "Trajectory shape mismatch")
    require(len(P) >= 3 and np.isfinite(P).all() and np.isfinite(G).all(),
            "Invalid trajectory coordinates")
    X, Y = P[:, :3, 3], G[:, :3, 3]
    xc, yc = X - X.mean(0), Y - Y.mean(0)
    covariance = yc.T @ xc / len(X)
    require(np.linalg.matrix_rank(covariance) >= 2, "Sim(3) alignment is degenerate")
    U, s, Vt = np.linalg.svd(covariance)
    D = np.ones(3)
    D[-1] = np.linalg.det(U @ Vt)
    rot = U @ np.diag(D) @ Vt
    scale = float((s * D).sum() / (xc ** 2).sum() * len(X))
    require(math.isfinite(scale) and scale > 0, "Nonpositive Sim(3) scale")
    trans = Y.mean(0) - scale * rot @ X.mean(0)
    A = P.copy()
    A[:, :3, :3] = rot @ P[:, :3, :3]
    A[:, :3, 3] = (scale * rot @ X.T).T + trans
    ate = np.linalg.norm(A[:, :3, 3] - G[:, :3, 3], axis=1)
    rgt = np.linalg.inv(G[:-1]) @ G[1:]
    rest = np.linalg.inv(A[:-1]) @ A[1:]
    error = np.linalg.inv(rgt) @ rest
    et = np.linalg.norm(error[:, :3, 3], axis=1)
    er = np.rad2deg(np.arccos(np.clip(
        (np.trace(error[:, :3, :3], axis1=1, axis2=2) - 1) / 2, -1, 1)))
    values = [float(np.sqrt(np.mean(z * z))) for z in (ate, et, er)]
    require(np.isfinite(values).all(), "Nonfinite matrix metric")
    return values, dict(scale=scale, rotation=rot.tolist(), translation=trans.tolist()), A, ate, et, er


def block_metrics(ate, et, er):
    """One global alignment; RPE pairs belong to the block of their start frame."""
    import numpy as np
    n = len(ate)
    require(len(et) == len(er) == n - 1 and n > 0, "Wrong per-frame metric lengths")
    rows = []
    for start in range(0, n, BLOCK_SIZE):
        end = min(start + BLOCK_SIZE, n)
        pair_end = min(end, n - 1)
        def rms(x):
            return float(np.sqrt(np.mean(x * x))) if len(x) else None
        rows.append(dict(start=start, end_exclusive=end, frame_count=end-start,
                         ate_rmse_m=rms(ate[start:end]),
                         rpe_pair_start=start, rpe_pair_end_exclusive=pair_end,
                         rpe_pair_count=max(0, pair_end-start),
                         rpe_translation_rmse_m=rms(et[start:pair_end]),
                         rpe_rotation_rmse_deg=rms(er[start:pair_end])))
    return rows


def selected_groundtruth(text, frames):
    """Call only after the pre-score seal and the recorded GT-read start."""
    raw = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        fields = line.split()
        require(len(fields) == 8, "Invalid TUM trajectory row")
        timestamp = float(fields[0])
        require(math.isfinite(timestamp) and timestamp not in raw, "Invalid/duplicate GT timestamp")
        raw[timestamp] = fields
    return [raw[f["gt_time"]] for f in frames]


def score():
    manifest_path = W / "run_manifest.json"
    manifest_data = manifest_path.read_bytes()
    manifest_hash = hashlib.sha256(manifest_data).hexdigest()
    m = json.loads(manifest_data)
    n = validate_manifest(m)
    frozen_paths = [Path(__file__).resolve(), R / "eval/relpose/evo_utils.py",
                    R / "eval/relpose/utils.py"]
    identities = {}
    for path in frozen_paths:
        h = sha(path)
        require(m["identities"].get(str(path)) == h, "Unfrozen/changed scorer source: " + str(path))
        identities[str(path)] = h
    out = B / "scoring"
    require(not out.exists(), "Refuse existing scoring directory")
    seals = verified_prediction_seals(m, manifest_hash)
    out.mkdir()
    write(out / "pre_score_seal.json", dict(
        sealed_utc=utc(), manifest_sha256=manifest_hash, source_identities=identities,
        methods=seals, gt_coordinates_read_by_this_score=False, gt_bytes_read_by_this_score=False,
        prior_exposure=m.get("gt_access_note"), expected_gt_sha256=m["gt_sha256"],
        frame_count=n, all_three_predictions_complete=True))
    receipt = dict(status="RUNNING", started_utc=utc(), manifest_sha256=manifest_hash,
                   frame_count=n, gt_read_started=False, gt_coordinates_parsed=False)
    write(out / "receipt.json", receipt)
    try:
        sys.path.append(str(ROOT / "work/S17C_environment/site-packages"))
        sys.path.insert(0, str(R))
        import numpy as np
        import scipy
        import evo
        from scipy.spatial.transform import Rotation
        from eval.relpose.evo_utils import eval_metrics, load_traj
        from eval.relpose.utils import get_tum_poses

        # Validate every pose array before accessing any GT bytes in this score.
        poses = {}
        for name in m["methods"]:
            data = (B / name / "poses.npy").read_bytes()
            require(hashlib.sha256(data).hexdigest() == seals[name]["poses_sha256"],
                    name + ": pose changed after seal")
            p = np.load(io.BytesIO(data), allow_pickle=False).astype(np.float64)
            require(p.shape == (n, 4, 4) and np.isfinite(p).all(), name + ": invalid pose array")
            require(np.array_equal(p[:, 3, :], np.tile([0., 0., 0., 1.], (n, 1))),
                    name + ": invalid homogeneous bottom row")
            require(np.all(np.linalg.det(p[:, :3, :3]) > 0), name + ": invalid rotation handedness")
            normalized = p.copy()
            normalized[:, :3, :3] = Rotation.from_matrix(p[:, :3, :3]).as_matrix()
            poses[name] = (p, normalized)

        receipt.update(gt_read_started=True, gt_read_started_utc=utc())
        write(out / "receipt.json", receipt)  # Remains truthful if the following read fails.
        gt_data = Path(m["gt_file"]).read_bytes()
        require(hashlib.sha256(gt_data).hexdigest() == m["gt_sha256"], "GT SHA mismatch")
        chosen = selected_groundtruth(gt_data.decode("utf-8"), m["frames"])
        receipt.update(gt_coordinate_parse_started=True, gt_coordinate_parse_started_utc=utc())
        write(out / "receipt.json", receipt)
        gtarr = np.asarray(chosen, dtype=np.float64)
        receipt.update(gt_coordinates_parsed=True, gt_coordinates_parsed_utc=utc())
        write(out / "receipt.json", receipt)
        require(gtarr.shape == (n, 8) and np.isfinite(gtarr).all(), "Invalid selected GT")
        require(np.all(np.linalg.norm(gtarr[:, 4:8], axis=1) > 0), "Zero GT quaternion")
        G = np.repeat(np.eye(4)[None], n, axis=0)
        G[:, :3, 3] = gtarr[:, 1:4]
        G[:, :3, :3] = Rotation.from_quat(gtarr[:, 4:8]).as_matrix()
        gt_path = out / f"groundtruth_{n}.txt"
        gt_path.write_text("\n".join(" ".join(row) for row in chosen) + "\n")
        gt = load_traj(str(gt_path), traj_format="tum")
        receipt.update(gt_sha256=m["gt_sha256"])
        write(out / "receipt.json", receipt)
        report = dict(started_utc=receipt["started_utc"], manifest_sha256=manifest_hash,
                      scope="Previously exposed TUM fr1_xyz, complete additional timestamp-paired segment; real existing baselines, not blind evaluation, new method or video generation",
                      metrics=["ATE_RMSE_m", "RPE_translation_RMSE_m", "RPE_rotation_RMSE_deg"],
                      frame_count=n, rpe_pair_count=n-1, block_size=BLOCK_SIZE,
                      metric_tolerance=dict(atol=ATOL, rtol=RTOL), methods={},
                      new_method=False, blind_test=False, independent_author_review=False,
                      matrix_check_scope="Different matrix formula, same scorer author; static peer review is separate",
                      alignment_scope="One full-sequence GT Sim(3); all blocks share this alignment",
                      rpe_block_semantics="Adjacent pairs assigned by start-frame index; boundary-crossing pairs retained",
                      rotation_normalization="Original c2w -> SciPy Rotation.from_matrix for both official quaternion conversion and matrix route",
                      environment=dict(python=sys.version, executable=sys.executable, platform=platform.platform(),
                                       numpy=np.__version__, scipy=scipy.__version__, evo=evo.__version__))
        for name in m["methods"]:
            p, normalized = poses[name]
            official = list(map(float, eval_metrics(
                get_tum_poses(p), copy.deepcopy(gt), seq=f"fr1_xyz_{n}_{name}",
                filename=str(out / (name + "_evo.txt")))))
            require(len(official) == 3 and np.isfinite(official).all(), "Invalid official metrics")
            independent, alignment, A, ate, et, er = matrix_metrics(normalized, G)
            check = bool(np.allclose(official, independent, atol=ATOL, rtol=RTOL))
            np.savez_compressed(out / (name + "_aligned.npz"), pred=A, gt=G, ate_m=ate,
                                rpe_translation_m=et, rpe_rotation_deg=er)
            report["methods"][name] = dict(
                official=official, independent_matrix=independent, metric_check_passed=check,
                alignment=alignment, all_blocks=block_metrics(ate, et, er),
                worst_indices_descending=np.argsort(-ate, kind="stable").tolist()[:min(10, n)],
                frame_count=n, rpe_pair_count=n-1)
            with (out / (name + "_per_frame.csv")).open("w", newline="") as stream:
                writer = csv.writer(stream)
                writer.writerow(["index", "rgb_timestamp", "gt_timestamp", "ate_m",
                                 "rpe_to_next_translation_m", "rpe_to_next_rotation_deg"])
                for i, frame in enumerate(m["frames"]):
                    writer.writerow([i, frame["rgb_time"], frame["gt_time"], ate[i],
                                     et[i] if i < n-1 else "", er[i] if i < n-1 else ""])
        require(sha(manifest_path) == manifest_hash, "Manifest changed while scoring")
        for path, h in identities.items():
            require(sha(path) == h, "Scorer source changed while scoring")
        for name, seal in seals.items():
            require(sha(B / name / "receipt.json") == seal["worker_receipt_sha256"] and
                    sha(CONTROL / name / "receipt.json") == seal["caller_receipt_sha256"] and
                    sha(B / name / "poses.npy") == seal["poses_sha256"],
                    name + ": source artifact changed while scoring")
        report.update(completed_utc=utc(), passed=all(x["metric_check_passed"] for x in report["methods"].values()),
                      prediction_and_score_order="All three complete archives hashed and sealed before S24 GT coordinate parsing",
                      pre_score_seal_sha256=sha(out / "pre_score_seal.json"))
        write(out / "metrics.json", report)
        require(report["passed"], "Official/matrix mismatch retained; do not loosen tolerance")
        receipt.update(status="PASS", completed_utc=utc(), methods=list(m["methods"]),
                       metrics_sha256=sha(out / "metrics.json"))
        write(out / "receipt.json", receipt)
        print(json.dumps({name: values["official"] for name, values in report["methods"].items()}))
    except BaseException as error:
        receipt.update(status="FAILED", completed_utc=utc(), error=repr(error),
                       traceback=traceback.format_exc())
        write(out / "receipt.json", receipt)
        raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["score"])
    parser.parse_args()
    score()
