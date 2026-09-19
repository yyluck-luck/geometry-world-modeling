#!/usr/bin/env python3
"""Build revisit and control windows for S113, strictly per the frozen protocol.

Protocol: work/S112_heldout_qualification/REVISIT_PROTOCOL_FROZEN_20260917.md
          sha256 bfcb5d98dc5ee89330a2adafcd077a08cf5de1d37c857678f3c8485b02191031

This reads ONLY timestamps and poses.  No image or depth pixel is opened, so
window selection cannot be influenced by appearance.  Every discard is counted.
"""
import argparse, hashlib, json, sys
from pathlib import Path
import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
from tum_rgbd import (read_timestamp_file, read_trajectory, associate_rgb_depth,  # noqa: E402
                      CameraIntrinsics)
sys.path.insert(0, str(Path(__file__).resolve().parent))
import revisit_episodes  # noqa: E402

PROTOCOL_SHA = "bfcb5d98dc5ee89330a2adafcd077a08cf5de1d37c857678f3c8485b02191031"
TOL = 0.02          # 20 ms association tolerance
TRANS_M = 0.30      # revisit translation threshold
ROT_DEG = 20.0      # revisit rotation threshold
MIN_GAP = 150       # minimum frame separation for a revisit
N_WINDOWS = 8

def quat_to_R(q):
    x, y, z, w = q
    n = np.sqrt(x * x + y * y + z * z + w * w)
    if n == 0: raise ValueError("zero quaternion")
    x, y, z, w = x / n, y / n, z / n, w / n
    return np.array([
        [1 - 2 * (y * y + z * z), 2 * (x * y - z * w),     2 * (x * z + y * w)],
        [2 * (x * y + z * w),     1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
        [2 * (x * z - y * w),     2 * (y * z + x * w),     1 - 2 * (x * x + y * y)]])

def geodesic_deg(Ra, Rb):
    c = (np.trace(Ra.T @ Rb) - 1.0) / 2.0
    return float(np.degrees(np.arccos(np.clip(c, -1.0, 1.0))))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    root = Path(args.root); out = Path(args.out)
    if out.exists(): raise SystemExit(f"refusing to overwrite {out}")

    rgb = read_timestamp_file(root / "rgb.txt")
    depth = read_timestamp_file(root / "depth.txt")
    traj = read_trajectory(root / "groundtruth.txt")
    matches = associate_rgb_depth(rgb, depth, max_difference=TOL)

    frames, dropped_no_pose = [], 0
    for m in matches:
        t = m.rgb.timestamp
        idx = int(np.argmin(np.abs(traj.timestamps - t)))
        if abs(traj.timestamps[idx] - t) >= TOL:
            dropped_no_pose += 1
            continue
        frames.append({"rgb_t": t, "rgb_path": m.rgb.path, "depth_path": m.depth.path,
                       "pose_t": float(traj.timestamps[idx]),
                       "xyz": traj.translations[idx].tolist(),
                       "quat": traj.quaternions_xyzw[idx].tolist()})
    N = len(frames)
    pos = np.array([f["xyz"] for f in frames])
    rots = [quat_to_R(f["quat"]) for f in frames]

    # Revisit detection.  Scan every admissible (i, j) and keep the earliest j
    # for each accepted revisit so selection is deterministic.
    revisits, used_j = [], set()
    for j in range(MIN_GAP, N):
        best = None
        for i in range(0, j - MIN_GAP):
            d = float(np.linalg.norm(pos[i] - pos[j]))
            if d >= TRANS_M: continue
            a = geodesic_deg(rots[i], rots[j])
            if a >= ROT_DEG: continue
            if best is None or d < best[0]: best = (d, a, i)
        if best is not None:
            revisits.append({"j": j, "i": best[2], "trans_m": best[0], "rot_deg": best[1]})

    def window(j, i, kind):
        tg = [j, j + 5, j + 10, j + 15]
        if max(tg) >= N: return None
        early = [i + o for o in (-15, -5, 5, 15)] if i is not None else []
        recent = [j + o for o in (-20, -15, -10, -5)]
        bank = sorted({k for k in
                       ([i + o for o in range(-30, 31, 5)] if i is not None else []) +
                       list(range(max(0, j - 60), j - 4, 5))
                       if 0 <= k < j})
        if any(k >= j for k in bank + early + recent): return None
        if min(recent) < 0 or (early and min(early) < 0): return None
        if len(bank) < 5: return None
        return {"kind": kind, "j": j, "i": i, "target_indices": tg,
                "bank_indices": bank, "recency_indices": recent,
                "early_visit_indices": early}

    # Amendment A5: attribute every revisit candidate to its leave-and-return
    # episode BEFORE window selection, so that selection cannot silently draw
    # every window from one loop closure.  Episode assignment uses only the
    # frozen pose criteria already applied above.
    revisits = revisit_episodes.assign_episodes(revisits)

    rev_windows, seen = [], set()
    for r in revisits:
        if len(rev_windows) >= N_WINDOWS: break
        if any(abs(r["j"] - s) < 20 for s in seen): continue   # avoid overlap
        w = window(r["j"], r["i"], "revisit")
        if w is None: continue
        w.update({"trans_m": r["trans_m"], "rot_deg": r["rot_deg"],
                  "revisit_episode": r["revisit_episode"],
                  "episode_member_count": r["episode_member_count"],
                  "episode_return_span": r["episode_return_span"],
                  "episode_anchor_span": r["episode_anchor_span"],
                  "revisit_kind": "pose_defined_proximity_only"})
        rev_windows.append(w); seen.add(r["j"])

    revisit_js = {r["j"] for r in revisits}
    ctrl_windows, seen_c = [], set()
    for j in range(MIN_GAP, N):
        if len(ctrl_windows) >= N_WINDOWS: break
        if j in revisit_js: continue
        if any(abs(j - s) < 20 for s in seen_c): continue
        w = window(j, None, "control")
        if w is None: continue
        ctrl_windows.append(w); seen_c.add(j)

    # Dependency grouping and the frozen feasibility decision are computed on the
    # selected windows, from metadata only.  No pixel is decoded anywhere above.
    all_windows = revisit_episodes.dependency_groups(rev_windows + ctrl_windows)
    feas = revisit_episodes.feasibility(all_windows)

    manifest = {
        "schema": "s113-revisit-window-manifest-v1",
        "protocol_sha256": PROTOCOL_SHA,
        "selection_inputs": "timestamps and poses only; no image or depth pixel was opened",
        "sequence_root": str(root),
        "association_tolerance_s": TOL,
        "counts": {"rgb_rows": len(rgb), "depth_rows": len(depth),
                   "groundtruth_rows": int(len(traj.timestamps)),
                   "rgb_depth_matches": len(matches),
                   "dropped_no_pose_within_tolerance": dropped_no_pose,
                   "usable_frames": N,
                   "revisit_candidates": len(revisits),
                   "revisit_windows": len(rev_windows),
                   "control_windows": len(ctrl_windows)},
        "revisit_criteria": {"translation_m": TRANS_M, "rotation_deg": ROT_DEG,
                             "min_frame_gap": MIN_GAP},
        "selection_rule_version": "frozen-protocol-bfcb5d98 + addendum-A-7b28bb3c",
        "episode_merge_frames": revisit_episodes.EPISODE_MERGE_FRAMES,
        "feasibility": feas,
        "windows": all_windows,
        "frames": frames,
        "new_method_validated": False, "novelty_authorization": "NONE",
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print(json.dumps({k: v for k, v in manifest.items() if k not in ("windows", "frames")},
                     indent=2, sort_keys=True))
    print(f"\nrevisit windows: {len(rev_windows)}   control windows: {len(ctrl_windows)}")
    print(f"feasibility: {feas['decision']}  "
          f"(independent episodes {feas['independent_revisit_episodes']} / "
          f"required {feas['min_independent_episodes_required']})")
    for w in rev_windows[:3]:
        print(f"  revisit j={w['j']} i={w['i']} trans={w['trans_m']:.3f}m rot={w['rot_deg']:.1f}deg "
              f"bank={len(w['bank_indices'])}")

if __name__ == "__main__":
    main()
