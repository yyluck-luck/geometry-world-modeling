#!/usr/bin/env python3
"""Two-window canary for per-window isolation.

The decisive property: one physical frame is window A's FUTURE TARGET and at the
same time window B's PERMITTED HISTORY.  B's permission must not grant A access.

Every denial asserted here is backed by an observed exception or an observed
absence on disk, never by an intended configuration.  Runs entirely on synthetic
files in a temporary directory; no dataset is touched.
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from window_isolation import WindowPermission, WindowAccessGuard, stage_window  # noqa: E402


def build_fixture(root: Path):
    seq = root / "seq"
    seq.mkdir()
    for k in range(0, 60, 10):
        (seq / f"frame-{k:06d}.color.png").write_bytes(b"RGB" + bytes([k]))
        (seq / f"frame-{k:06d}.depth.png").write_bytes(b"DEPTH" + bytes([k]))
        (seq / f"frame-{k:06d}.pose.txt").write_text(f"pose {k}\n")
    (seq / "camera-intrinsics.txt").write_text("K\n")
    return seq


def main() -> int:
    checks = []
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        seq = build_fixture(root)
        shared = seq / "frame-000030.color.png"       # A's target, B's history

        a = WindowPermission(
            window_id="window_A",
            history_files=[seq / "frame-000000.color.png", seq / "frame-000010.color.png"],
            camera_files=[seq / "frame-000030.pose.txt"],
            calibration_files=[seq / "camera-intrinsics.txt"],
            forbidden_files=[shared, seq / "frame-000030.depth.png"])
        b = WindowPermission(
            window_id="window_B",
            history_files=[seq / "frame-000020.color.png", shared],
            camera_files=[seq / "frame-000050.pose.txt"],
            calibration_files=[seq / "camera-intrinsics.txt"],
            forbidden_files=[seq / "frame-000050.color.png"])

        # --- permission logic ------------------------------------------------
        checks.append(("the shared frame is permitted history for B", b.permits(shared)))
        checks.append(("the same frame is NOT permitted for A", not a.permits(shared)))
        checks.append(("A may read its own commanded camera pose",
                       a.permits(seq / "frame-000030.pose.txt")))
        checks.append(("A may not read its target depth",
                       not a.permits(seq / "frame-000030.depth.png")))
        checks.append(("A may not read B's exclusive history",
                       not a.permits(seq / "frame-000020.color.png")))

        # --- staging is the enforcing boundary -------------------------------
        stage_root = root / "stages"
        sa = stage_window(a, stage_root)
        sb = stage_window(b, stage_root)
        a_files = {Path(p).name for p in sa["staged_files"]}
        checks.append(("A's stage physically lacks the shared frame",
                       "frame-000030.color.png" not in a_files))
        checks.append(("B's stage physically contains the shared frame",
                       "frame-000030.color.png" in {Path(p).name for p in sb["staged_files"]}))
        checks.append(("A's stage contains no depth file at all",
                       not any(n.endswith(".depth.png") for n in a_files)))
        checks.append(("the two stages are separate directories",
                       sa["stage_root"] != sb["stage_root"]))

        # --- in-process fail-closed guard, observed not assumed --------------
        guard = WindowAccessGuard(a, watched_roots=[seq]).install()

        allowed_ok = False
        try:
            (seq / "frame-000000.color.png").read_bytes()
            allowed_ok = True
        except PermissionError:
            allowed_ok = False
        checks.append(("guard allows A's own permitted history", allowed_ok))

        denied_direct = False
        try:
            shared.read_bytes()
        except PermissionError:
            denied_direct = True
        checks.append(("guard DENIES A reading the shared frame directly", denied_direct))

        denied_relative = False
        try:
            (seq / "sub" / ".." / "frame-000030.color.png").read_bytes()
        except PermissionError:
            denied_relative = True
        except FileNotFoundError:
            denied_relative = False
        checks.append(("guard denies the same file via a relative path", denied_relative))

        denied_depth = False
        try:
            (seq / "frame-000030.depth.png").read_bytes()
        except PermissionError:
            denied_depth = True
        checks.append(("guard denies A's target depth", denied_depth))

        # --- honest limit: a child process is outside the hook ---------------
        child = subprocess.run([sys.executable, "-c",
                                f"print(open({str(shared)!r},'rb').read()[:3])"],
                               capture_output=True, text=True)
        child_read = child.returncode == 0
        checks.append(("documented limit: a CHILD PROCESS still reads it "
                       "(hook is not a sandbox)", child_read))

        rep = guard.report()
        checks.append(("guard recorded the denials it raised", len(rep["denied_attempts"]) >= 2))
        checks.append(("guard reports what it cannot measure", bool(rep["unmeasured"])))

    bad = 0
    for name, ok in checks:
        print(f"[{'PASS' if ok else 'FAIL'}] {name}")
        bad += 0 if ok else 1
    print(f"\n{len(checks) - bad}/{len(checks)} checks passed")
    print("\nTrust boundary: staging removes the file from the mount namespace and is the "
          "enforcing mechanism; the audit hook is development telemetry and fails closed "
          "in-process only. Child-process and native reads remain UNMEASURED by the hook.")
    return 0 if bad == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
