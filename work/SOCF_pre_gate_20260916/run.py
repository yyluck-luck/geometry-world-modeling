"""SOCF-A pre-Gate source-conflict diagnostic.

Reads only sealed S100 low/conf predictions and candidate-pair metadata.
No future RGB/depth/pose/GT is opened and no model is called.  This is a
descriptive pre-Gate diagnostic, not a method evaluation.
"""
from datetime import datetime, timezone
from pathlib import Path
import csv
import hashlib
import json
import math
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
S100 = ROOT / "work/S100_context_matched_swap"
BASE = Path(__file__).resolve().parent


def utc():
    return datetime.now(timezone.utc).isoformat()


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_json(path, obj):
    Path(path).write_text(
        json.dumps(obj, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    )


def percentile(values, q):
    values = np.asarray(values, dtype=float)
    return None if values.size == 0 else float(np.percentile(values, q))


def finite_depth(x):
    return np.isfinite(x) & (x > 0)


def load():
    selection_path = S100 / "select_01/SELECTION.json"
    prediction_path = S100 / "predict_01/predictions.npz"
    selection = json.loads(selection_path.read_text())
    prediction = np.load(prediction_path, allow_pickle=False)
    required = {"depth_m", "source_pixel_identity"}
    if not required.issubset(prediction.files):
        raise ValueError(f"missing fields: {sorted(required - set(prediction.files))}")
    depth = np.asarray(prediction["depth_m"], dtype=float)
    identity = np.asarray(prediction["source_pixel_identity"], dtype=np.int64)
    if depth.shape != identity.shape:
        raise ValueError("depth and source identity shapes differ")
    if depth.ndim != 4 or depth.shape[1] != 4:
        raise ValueError(f"unexpected prediction shape {depth.shape}")
    groups = {}
    for idx, condition in enumerate(selection["conditions"]):
        key = (
            int(condition["pair_id"]),
            int(condition["source"]),
            int(condition["context"]),
        )
        arm = str(condition["arm"])
        groups.setdefault(key, {})[arm] = idx
    if not groups or any(set(arms) != {"low", "conf"} for arms in groups.values()):
        raise ValueError("selection does not contain complete low/conf groups")
    return selection_path, prediction_path, selection, depth, identity, groups


def conflict_metrics(low_depth, conf_depth, low_id, conf_id):
    low_valid = finite_depth(low_depth)
    conf_valid = finite_depth(conf_depth)
    common = low_valid & conf_valid
    support_flip = low_valid ^ conf_valid
    id_known = common & (low_id >= 0) & (conf_id >= 0)
    id_flip = id_known & (low_id != conf_id)
    depth_change = common & (np.abs(low_depth - conf_depth) > 1e-12)
    conflict = support_flip | id_flip
    changed_and_conflict = depth_change & conflict
    changed_not_conflict = depth_change & ~conflict
    conflict_count = int(conflict.sum())
    changed_count = int(depth_change.sum())
    return {
        "valid_low": int(low_valid.sum()),
        "valid_conf": int(conf_valid.sum()),
        "common_support": int(common.sum()),
        "support_flip_count": int(support_flip.sum()),
        "identity_flip_count": int(id_flip.sum()),
        "identity_flip_rate_on_common": (
            float(id_flip.sum() / id_known.sum()) if id_known.any() else None
        ),
        "depth_change_count": changed_count,
        "source_conflict_count": conflict_count,
        "source_conflict_rate_on_union": (
            float(conflict_count / (low_valid | conf_valid).sum())
            if (low_valid | conf_valid).any()
            else None
        ),
        "depth_change_rate_explained_by_conflict": (
            float(changed_and_conflict.sum() / changed_count)
            if changed_count
            else None
        ),
        "depth_change_count_without_conflict": int(changed_not_conflict.sum()),
        "conflict_depth_abs_delta_mean_m": (
            float(np.abs(low_depth[changed_and_conflict] - conf_depth[changed_and_conflict]).mean())
            if changed_and_conflict.any()
            else None
        ),
        "nonconflict_depth_abs_delta_mean_m": (
            float(np.abs(low_depth[changed_not_conflict] - conf_depth[changed_not_conflict]).mean())
            if changed_not_conflict.any()
            else None
        ),
    }


def mean(rows, key):
    values = [
        float(row[key]) for row in rows
        if row.get(key) is not None and math.isfinite(float(row[key]))
    ]
    return float(np.mean(values)) if values else None


def main():
    out = BASE / "run_01"
    if out.exists():
        raise RuntimeError(f"refusing to overwrite {out}")
    out.mkdir()
    started = utc()
    selection_path, prediction_path, selection, depth, identity, groups = load()
    manifest = {
        "protocol": "SOCF-A pre-Gate source-conflict diagnostic v1",
        "started_utc": started,
        "gt_read": False,
        "future_rgb_read": False,
        "future_depth_read": False,
        "future_pose_read": False,
        "model_calls": 0,
        "heldout_split_used": False,
        "scientific_status": "PRE_GATE_DESCRIPTIVE_ONLY",
        "inputs": {
            "selection": {"path": str(selection_path), "sha256": sha(selection_path)},
            "predictions": {"path": str(prediction_path), "sha256": sha(prediction_path)},
        },
        "forbidden_inputs": [
            "future_rgb",
            "future_depth",
            "future_pose",
            "future_gt_metrics",
        ],
        "prediction_shape": list(depth.shape),
        "numpy_version": np.__version__,
    }
    write_json(out / "INPUT_MANIFEST.json", manifest)

    rows = []
    for (pair_id, source, context), arms in sorted(groups.items()):
        for target_index in range(depth.shape[1]):
            metrics = conflict_metrics(
                depth[arms["low"], target_index],
                depth[arms["conf"], target_index],
                identity[arms["low"], target_index],
                identity[arms["conf"], target_index],
            )
            rows.append(
                {
                    "pair_id": pair_id,
                    "source": source,
                    "context": context,
                    "target": 20 + target_index,
                    **metrics,
                }
            )

    with (out / "METRICS_PER_TARGET.csv").open("w", newline="") as handle:
        fields = list(rows[0].keys())
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

    source_summary = {}
    for source in sorted({row["source"] for row in rows}):
        source_rows = [row for row in rows if row["source"] == source]
        source_summary[str(source)] = {
            "row_count": len(source_rows),
            "mean_identity_flip_rate_on_common": mean(
                source_rows, "identity_flip_rate_on_common"
            ),
            "mean_source_conflict_rate_on_union": mean(
                source_rows, "source_conflict_rate_on_union"
            ),
            "mean_depth_change_rate_explained_by_conflict": mean(
                source_rows, "depth_change_rate_explained_by_conflict"
            ),
            "p90_conflict_depth_abs_delta_m": percentile(
                [
                    row["conflict_depth_abs_delta_mean_m"]
                    for row in source_rows
                    if row["conflict_depth_abs_delta_mean_m"] is not None
                ],
                90,
            ),
        }

    context_stability = []
    for pair_id, source in sorted(
        {(row["pair_id"], row["source"]) for row in rows}
    ):
        contexts = sorted(
            {
                row["context"]
                for row in rows
                if row["pair_id"] == pair_id and row["source"] == source
            }
        )
        if len(contexts) != 2:
            continue
        for target in range(20, 24):
            a = next(
                row
                for row in rows
                if (row["pair_id"], row["source"], row["context"], row["target"])
                == (pair_id, source, contexts[0], target)
            )
            b = next(
                row
                for row in rows
                if (row["pair_id"], row["source"], row["context"], row["target"])
                == (pair_id, source, contexts[1], target)
            )
            x = a["source_conflict_rate_on_union"]
            y = b["source_conflict_rate_on_union"]
            context_stability.append(
                {
                    "pair_id": pair_id,
                    "source": source,
                    "target": target,
                    "context0": contexts[0],
                    "context1": contexts[1],
                    "conflict_rate_context0": x,
                    "conflict_rate_context1": y,
                    "absolute_rate_difference": (
                        abs(x - y) if x is not None and y is not None else None
                    ),
                    "both_nonzero": bool(
                        x is not None and y is not None and x > 0 and y > 0
                    ),
                }
            )

    aggregate = {
        "row_count": len(rows),
        "source_summary": source_summary,
        "context_stability": {
            "row_count": len(context_stability),
            "mean_absolute_rate_difference": mean(
                context_stability, "absolute_rate_difference"
            ),
            "both_nonzero_fraction": mean(context_stability, "both_nonzero"),
        },
        "interpretation": (
            "Descriptive source-conflict evidence only. Renderer provenance is "
            "not geometric ground truth; no future prediction, calibrated risk, "
            "abstention benefit, causal effect, or novelty claim is authorized."
        ),
    }
    write_json(out / "AGGREGATES.json", aggregate)
    with (out / "CONTEXT_STABILITY.csv").open("w", newline="") as handle:
        fields = list(context_stability[0].keys()) if context_stability else []
        if fields:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            writer.writerows(context_stability)

    decision = {
        "status": "DIAGNOSTIC_COMPLETE",
        "socf_pre_gate_signal": "DESCRIPTIVE_ONLY",
        "gt_read": False,
        "method_validated": False,
        "novelty_authorization": "NONE",
        "next_gate": (
            "Freeze legal held-out RGB-D/pose manifest, then test incremental "
            "future-state prediction against matched same-pool baselines."
        ),
    }
    write_json(out / "DECISION.json", decision)
    write_json(
        out / "RUN.json",
        {
            "started_utc": started,
            "completed_utc": utc(),
            "status": "PASS",
            "rows": len(rows),
            "context_rows": len(context_stability),
            "gt_read": False,
            "model_calls": 0,
        },
    )


if __name__ == "__main__":
    main()
