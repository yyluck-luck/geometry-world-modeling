"""Pre-Gate saved-output ghosting diagnostics.

This script only reads sealed S86/S87 uint8 outputs and the already-sealed
same-scene reference PNGs. It does not run a model, access held-out data, or
choose a method. The metrics are exploratory proxies, not perceptual or
geometric ground truth.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from PIL import Image


ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
S86 = ROOT / "work/S86_fixed_warp_consumer/execution_01"
S87 = ROOT / "work/S87_terminal_strength_audit/execution_01"
VIS = ROOT / "work/S86_fixed_warp_consumer/visuals_01"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def gray(arr: np.ndarray) -> np.ndarray:
    x = arr.astype(np.float64) / 255.0
    return 0.299 * x[..., 0] + 0.587 * x[..., 1] + 0.114 * x[..., 2]


def diagnostic(ref: np.ndarray, pred: np.ndarray) -> dict[str, float]:
    r = gray(ref)
    p = gray(pred)
    # Central differences keep the measurement simple and deterministic.
    rx = np.diff(r, axis=1)
    px = np.diff(p, axis=1)
    ry = np.diff(r, axis=0)
    py = np.diff(p, axis=0)
    rg = np.hypot(rx[:-1], ry[:, :-1])
    pg = np.hypot(px[:-1], py[:, :-1])
    edge_threshold = float(np.quantile(rg, 0.90))
    ref_edges = rg >= edge_threshold
    pred_edges = pg >= edge_threshold
    eps = 1e-12
    # Edge alignment at a threshold fixed by the reference, plus energy ratios.
    edge_precision = float((pred_edges & ref_edges).sum() / max(pred_edges.sum(), 1))
    edge_recall = float((pred_edges & ref_edges).sum() / max(ref_edges.sum(), 1))
    edge_f1 = 2 * edge_precision * edge_recall / max(edge_precision + edge_recall, eps)
    hf_ref = float(np.mean((r[:, 2:] - 2 * r[:, 1:-1] + r[:, :-2]) ** 2))
    hf_pred = float(np.mean((p[:, 2:] - 2 * p[:, 1:-1] + p[:, :-2]) ** 2))
    grad_ref = float(np.mean(rg))
    grad_pred = float(np.mean(pg))
    # Excess generated gradient near reference edges is a simple double-edge proxy.
    band = ref_edges
    excess = float(np.mean(np.maximum(pg[band] - rg[band], 0.0))) if band.any() else 0.0
    return {
        "mse_rgb01": float(np.mean((pred.astype(np.float64) - ref.astype(np.float64)) ** 2) / (255.0**2)),
        "edge_precision_ref_q90": edge_precision,
        "edge_recall_ref_q90": edge_recall,
        "edge_f1_ref_q90": edge_f1,
        "mean_gradient_ref": grad_ref,
        "mean_gradient_pred": grad_pred,
        "gradient_ratio_pred_over_ref": grad_pred / max(grad_ref, eps),
        "second_difference_energy_ref": hf_ref,
        "second_difference_energy_pred": hf_pred,
        "high_frequency_ratio_pred_over_ref": hf_pred / max(hf_ref, eps),
        "edge_band_excess_gradient_proxy": excess,
    }


def load_ref(i: int) -> np.ndarray:
    return np.asarray(Image.open(VIS / f"target_{20+i}_reference.png").convert("RGB"))


def load_arm(name: str) -> np.ndarray:
    locations = {
        "G0": S86 / "G0/targets_uint8.npy",
        "Gguide": S86 / "Gguide/targets_uint8.npy",
        "Gterminal_l075": S87 / "Gterminal_l075/targets_uint8.npy",
        "Gpaste_l075": S87 / "Gpaste_l075/targets_uint8.npy",
    }
    return np.load(locations[name], allow_pickle=False)


def main() -> None:
    arms = ["G0", "Gguide", "Gpaste_l075", "Gterminal_l075"]
    rows: list[dict[str, object]] = []
    inputs: list[dict[str, object]] = []
    for name in arms:
        path = {
            "G0": S86 / "G0/targets_uint8.npy",
            "Gguide": S86 / "Gguide/targets_uint8.npy",
            "Gpaste_l075": S87 / "Gpaste_l075/targets_uint8.npy",
            "Gterminal_l075": S87 / "Gterminal_l075/targets_uint8.npy",
        }[name]
        inputs.append({"role": "sealed_generated_output", "name": name, "path": str(path), "sha256": sha256(path)})
    for i in range(4):
        ref_path = VIS / f"target_{20+i}_reference.png"
        inputs.append({"role": "sealed_seen_reference", "target": 20 + i, "path": str(ref_path), "sha256": sha256(ref_path)})
    for name in arms:
        pred = load_arm(name)
        for i in range(4):
            metrics = diagnostic(load_ref(i), pred[i])
            rows.append({"arm": name, "target": 20 + i, **metrics})
    summary: dict[str, dict[str, float]] = {}
    for name in arms:
        sub = [r for r in rows if r["arm"] == name]
        keys = [k for k in sub[0] if k not in {"arm", "target"}]
        summary[name] = {k: float(np.mean([float(r[k]) for r in sub])) for k in keys}
    receipt = {
        "schema": "GHOSTING_DIAGNOSTIC_PRE_GATE_V1",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "status": "COMPLETE_SAVED_OUTPUT_ONLY",
        "scientific_scope": "Exploratory same-scene mechanism diagnostic; no held-out data, no new inference, no method validation.",
        "metric_warning": "Edge/high-frequency measures are proxies; they are not perceptual quality, geometry accuracy, or causal proof of ghosting.",
        "inputs": inputs,
        "rows": rows,
        "summary": summary,
        "sample_count": {"targets": 4, "arms": len(arms), "new_model_forwards": 0, "heldout_gt_reads": 0},
        "next_decision": "Use only to design a frozen held-out diagnostic; do not tune GRC or claim mechanism generality.",
    }
    (OUT / "RESULTS.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n")
    (OUT / "INPUT_SHA256.json").write_text(json.dumps(inputs, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"status": receipt["status"], "arms": arms, "rows": len(rows)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
