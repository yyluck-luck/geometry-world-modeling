"""S103: decompose sealed S100 low-vs-confidence output changes.

This script intentionally reads no future GT.  It is a retrospective diagnostic of
the saved geometric consumer output, not a method evaluation.
"""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, math
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
S100 = ROOT / "work/S100_context_matched_swap"
BASE = Path(__file__).resolve().parent

def utc():
    return datetime.now(timezone.utc).isoformat()

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def write(path, obj):
    Path(path).write_text(json.dumps(obj, ensure_ascii=False, indent=2, allow_nan=False) + "\n")

def finite_positive(x):
    return np.isfinite(x) & (x > 0)

def percentile(x, q):
    x = np.asarray(x, dtype=float)
    return None if x.size == 0 else float(np.percentile(x, q))

def adjacent_gradient(z, mask):
    """Mean absolute 4-neighbour gradient on pairs valid in the same arm."""
    vals = []
    for a, b in [(z[:, 1:], z[:, :-1]), (z[1:, :], z[:-1, :])]:
        m = mask[:, 1:] & mask[:, :-1] if a.shape == z[:, 1:].shape else mask[1:, :] & mask[:-1, :]
        if np.any(m):
            vals.append(np.abs(a[m] - b[m]))
    if not vals:
        return {"count": 0, "mean": None, "p95": None}
    x = np.concatenate(vals)
    return {"count": int(x.size), "mean": float(x.mean()), "p95": percentile(x, 95)}

def corr(a, b):
    if a.size < 3:
        return None
    a = np.asarray(a, dtype=float); b = np.asarray(b, dtype=float)
    sa = float(a.std()); sb = float(b.std())
    if sa == 0 or sb == 0:
        return None
    return float(np.corrcoef(a, b)[0, 1])

def load_inputs():
    sel = json.loads((S100 / "select_01/SELECTION.json").read_text())
    pred = np.load(S100 / "predict_01/predictions.npz", allow_pickle=False)
    for key in ("depth_m", "source_pixel_identity"):
        if key not in pred.files:
            raise ValueError(f"missing prediction field: {key}")
    depth, ident = pred["depth_m"], pred["source_pixel_identity"]
    if depth.shape != (len(sel["conditions"]), 4, 224, 224):
        raise ValueError(f"unexpected depth shape {depth.shape}")
    if ident.shape != depth.shape or not np.issubdtype(ident.dtype, np.integer):
        raise ValueError(f"unexpected identity shape/dtype {ident.shape} {ident.dtype}")
    if len(sel["conditions"]) % 2:
        raise ValueError("conditions are not arm pairs")
    # Conditions were frozen as [low, conf] for each (pair, context). Rebuild by keys
    # rather than trusting array adjacency.
    groups = {}
    for idx, rec in enumerate(sel["conditions"]):
        key = (int(rec["pair_id"]), int(rec["source"]), int(rec["context"]))
        arm = str(rec["arm"])
        if arm in groups.setdefault(key, {}):
            raise ValueError(f"duplicate arm for {key}")
        groups[key][arm] = idx
    for key, arms in groups.items():
        if set(arms) != {"low", "conf"}:
            raise ValueError(f"incomplete arms for {key}: {arms}")
    return sel, depth.astype(float), ident.astype(np.int64), groups

def row_metrics(low, conf, ilow, iconf):
    vl, vc = finite_positive(low), finite_positive(conf)
    union, inter = vl | vc, vl & vc
    support_flip = float(np.count_nonzero(vl ^ vc) / np.count_nonzero(union)) if np.any(union) else None
    same_id = inter & (ilow == iconf) & (ilow >= 0)
    id_flip = inter & (ilow != iconf) & (ilow >= 0) & (iconf >= 0)
    common_id = int(np.count_nonzero(inter & (ilow >= 0) & (iconf >= 0)))
    id_flip_ratio = float(np.count_nonzero(id_flip) / common_id) if common_id else None
    same_delta = np.abs(low[same_id] - conf[same_id])
    common_delta = np.abs(low[inter] - conf[inter])
    rel = same_delta / np.maximum((np.abs(low[same_id]) + np.abs(conf[same_id])) * 0.5, 1e-12)
    common_rel = common_delta / np.maximum((np.abs(low[inter]) + np.abs(conf[inter])) * 0.5, 1e-12)
    same_l1 = float(same_delta.sum())
    common_l1 = float(common_delta.sum())
    depth_fraction = float(same_l1 / common_l1) if common_l1 else None
    return {
        "support_low": int(vl.sum()), "support_conf": int(vc.sum()),
        "support_union": int(union.sum()), "support_intersection": int(inter.sum()),
        "support_flip": support_flip, "identity_flip": id_flip_ratio,
        "identity_common_count": common_id, "same_identity_count": int(same_id.sum()),
        "same_identity_abs_delta_mean_m": float(same_delta.mean()) if same_delta.size else None,
        "same_identity_abs_delta_p90_m": percentile(same_delta, 90),
        "same_identity_relative_delta_median": float(np.median(rel)) if rel.size else None,
        "common_support_abs_delta_mean_m": float(common_delta.mean()) if common_delta.size else None,
        "common_support_abs_delta_p90_m": percentile(common_delta, 90),
        "common_support_relative_delta_median": float(np.median(common_rel)) if common_rel.size else None,
        "same_identity_l1_fraction_of_common_depth_change": depth_fraction,
        "gradient_low": adjacent_gradient(low, vl), "gradient_conf": adjacent_gradient(conf, vc),
    }

def run():
    out = BASE / "run_01"
    if out.exists():
        raise RuntimeError("fresh output required")
    out.mkdir()
    sel, depth, ident, groups = load_inputs()
    manifest = {
        "created_utc": utc(), "gt_read": False, "model_calls": 0,
        "inputs": {
            "selection": {"path": str(S100 / "select_01/SELECTION.json"), "sha256": sha(S100 / "select_01/SELECTION.json")},
            "predictions": {"path": str(S100 / "predict_01/predictions.npz"), "sha256": sha(S100 / "predict_01/predictions.npz")},
        },
        "shape": list(depth.shape), "numpy_version": np.__version__,
    }
    rows = []
    by_key = {}
    for key, arms in sorted(groups.items()):
        pair, source, context = key
        for target in range(4):
            m = row_metrics(depth[arms["low"], target], depth[arms["conf"], target], ident[arms["low"], target], ident[arms["conf"], target])
            row = {"pair_id": pair, "source": source, "context": context, "target": 20 + target, **m}
            rows.append(row); by_key[(pair, source, context, target)] = row
    # Compare the low-vs-conf perturbation itself across the two fixed contexts.
    context_rows = []
    for pair, source, _ in sorted(groups):
        contexts = sorted(c for (p, s, c) in groups if p == pair and s == source)
        if len(contexts) != 2:
            continue
        for target in range(4):
            g0, g1 = groups[(pair, source, contexts[0])], groups[(pair, source, contexts[1])]
            dl = depth[g0["low"], target] - depth[g0["conf"], target]
            d1 = depth[g1["low"], target] - depth[g1["conf"], target]
            valid = finite_positive(depth[g0["low"], target]) & finite_positive(depth[g0["conf"], target]) & finite_positive(depth[g1["low"], target]) & finite_positive(depth[g1["conf"], target])
            x, y = dl[valid], d1[valid]
            changed0, changed1 = np.abs(x) > 1e-12, np.abs(y) > 1e-12
            jaccard = float(np.count_nonzero(changed0 & changed1) / np.count_nonzero(changed0 | changed1)) if np.any(changed0 | changed1) else None
            context_rows.append({"pair_id": pair, "source": source, "target": 20 + target, "context0": contexts[0], "context1": contexts[1], "common_pixels": int(x.size), "delta_pearson": corr(x, y), "delta_cosine": float(np.dot(x, y) / (np.linalg.norm(x) * np.linalg.norm(y))) if np.linalg.norm(x) and np.linalg.norm(y) else None, "changed_mask_jaccard": jaccard, "delta_abs_difference_median": float(np.median(np.abs(x-y))) if x.size else None})
    write(out / "INPUT_MANIFEST.json", manifest)
    write(out / "METRICS_PER_TARGET.json", {"rows": rows, "context_consistency": context_rows})
    # Aggregate descriptive evidence; no p-values and no independence claim.
    def mean(field, subset):
        vals = [r[field] for r in subset if r.get(field) is not None and math.isfinite(r[field])]
        return float(np.mean(vals)) if vals else None
    source_summary = {}
    for source in sorted({r["source"] for r in rows}):
        rr = [r for r in rows if r["source"] == source]
        source_summary[str(source)] = {k: mean(k, rr) for k in ["support_flip", "identity_flip", "same_identity_abs_delta_p90_m", "same_identity_l1_fraction_of_common_depth_change"]}
    write(out / "AGGREGATES.json", {"row_count": len(rows), "context_row_count": len(context_rows), "source_summary": source_summary, "target_summary": {str(t): {k: mean(k, [r for r in rows if r["target"] == t]) for k in ["support_flip", "identity_flip", "same_identity_l1_fraction_of_common_depth_change"]} for t in range(20,24)}})
    # The labels are deliberately conservative: thresholded descriptive diagnostics, not novelty.
    ss = list(source_summary.values())
    support_ok = sum((x["support_flip"] is not None and x["support_flip"] >= 0.30) or (x["identity_flip"] is not None and x["identity_flip"] >= 0.30) for x in ss) >= math.ceil(2 * len(ss) / 3) if ss else False
    depth_ok = sum((x["identity_flip"] is not None and x["identity_flip"] < 0.10 and x["same_identity_l1_fraction_of_common_depth_change"] is not None and x["same_identity_l1_fraction_of_common_depth_change"] > 0.50) for x in ss) >= math.ceil(2 * len(ss) / 3) if ss else False
    decision = "H_support" if support_ok and not depth_ok else "H_depth" if depth_ok and not support_ok else "MECHANISM_UNRESOLVED"
    write(out / "MECHANISM_DECISION.json", {"decision": decision, "support_threshold": 0.30, "depth_threshold": {"identity_flip_lt": 0.10, "same_identity_l1_fraction_gt": 0.50}, "source_count": len(ss), "gt_read": False, "scientific_boundary": "renderer provenance is not geometric ground truth; no future improvement or causal claim"})
    write(out / "RUN.json", {"started_utc": manifest["created_utc"], "completed_utc": utc(), "status": "PASS", "gt_read": False, "model_calls": 0, "row_count": len(rows)})

if __name__ == "__main__":
    run()
