#!/usr/bin/env python3
"""Per-window input isolation for the revisit diagnostic.

Amendment A7: permission belongs to a WINDOW, not to a sequence.  A frame can be
future RGB for window A and permitted history for window B; B's permission must
never imply A's.

Trust boundary, stated plainly:

  PRIMARY ENFORCEMENT is staging.  Each run unit gets its own directory that
  physically contains only that window's approved files, and only that
  directory is mounted into the predictor container.  A file that was never
  staged cannot be opened because it is not present in the mount namespace.

  SECONDARY, IN-PROCESS telemetry and fail-closed guard is a Python audit hook.
  Per the CPython documentation this is NOT a sandbox: an audit hook is an
  in-process observation facility and native code or a child process can act
  outside it.  It is used here to turn an attempted forbidden read into an
  immediate, recorded failure during development, not to prove absence of all
  channels.

Anything the guard cannot observe is reported as UNMEASURED.  A denial claim is
backed by an observed raise, never by an intended configuration.
"""
from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path


class WindowPermission:
    """The frozen set of files one run unit may read from the dataset."""

    def __init__(self, window_id: str, history_files, camera_files,
                 calibration_files=(), forbidden_files=()):
        self.window_id = window_id
        self.history = {str(Path(p).resolve()) for p in history_files}
        self.cameras = {str(Path(p).resolve()) for p in camera_files}
        self.calibration = {str(Path(p).resolve()) for p in calibration_files}
        # Declared explicitly so the canary can assert on them.
        self.forbidden = {str(Path(p).resolve()) for p in forbidden_files}

    @property
    def allowed(self):
        return self.history | self.cameras | self.calibration

    def permits(self, path) -> bool:
        return str(Path(path).resolve()) in self.allowed

    def summary(self):
        return {"window_id": self.window_id,
                "n_history": len(self.history), "n_cameras": len(self.cameras),
                "n_calibration": len(self.calibration),
                "n_declared_forbidden": len(self.forbidden)}


def stage_window(permission: WindowPermission, stage_root) -> dict:
    """Copy only the approved files into a private staging directory.

    This is the enforcing step.  Target RGB, target depth, other windows'
    artifacts and the sequence directory itself are never copied, so they are
    not reachable from the mounted namespace.
    """
    root = Path(stage_root) / permission.window_id
    if root.exists():
        raise RuntimeError(f"refusing to reuse an existing stage: {root}")
    (root / "history").mkdir(parents=True)
    (root / "camera").mkdir()
    (root / "calib").mkdir()
    staged = []
    for src in sorted(permission.history):
        dst = root / "history" / Path(src).name
        shutil.copy2(src, dst); staged.append(str(dst))
    for src in sorted(permission.cameras):
        dst = root / "camera" / Path(src).name
        shutil.copy2(src, dst); staged.append(str(dst))
    for src in sorted(permission.calibration):
        dst = root / "calib" / Path(src).name
        shutil.copy2(src, dst); staged.append(str(dst))
    return {"window_id": permission.window_id, "stage_root": str(root),
            "staged_files": staged, "staged_count": len(staged),
            "enforcement": "only these files exist inside the window stage"}


class WindowAccessGuard:
    """Fail-closed in-process guard, scoped to one window.

    Raises on an attempted read of a dataset path this window does not own, so
    an upstream leak surfaces as a loud failure during development instead of a
    silent contamination.  Reads outside the watched dataset roots are recorded
    but not denied, and that limitation is reported rather than hidden.
    """

    def __init__(self, permission: WindowPermission, watched_roots):
        self.permission = permission
        self.watched = tuple(str(Path(r).resolve()) for r in watched_roots)
        self.denied, self.allowed_hits, self.unwatched = [], [], 0
        self._installed = False

    def hook(self, event, args):
        if event != "open":
            return
        try:
            target = os.fspath(args[0]) if args else ""
        except (TypeError, ValueError):
            return
        if not isinstance(target, str) or not target.startswith("/"):
            return
        resolved = str(Path(target).resolve())
        if not resolved.startswith(self.watched):
            self.unwatched += 1
            return
        if self.permission.permits(resolved):
            self.allowed_hits.append(resolved)
            return
        self.denied.append(resolved)
        raise PermissionError(
            f"window {self.permission.window_id} may not read {resolved}")

    def install(self):
        sys.addaudithook(self.hook)
        self._installed = True
        return self

    def report(self):
        return {"window_id": self.permission.window_id,
                "installed": self._installed,
                "denied_attempts": sorted(set(self.denied)),
                "permitted_reads": len(set(self.allowed_hits)),
                "reads_outside_watched_roots": self.unwatched,
                "enforcement_note": (
                    "staging is the enforcing boundary; this hook is in-process "
                    "telemetry and a development fail-closed check, not a sandbox"),
                "unmeasured": (
                    "native reads that bypass the CPython file API, reads inside a "
                    "child process, and descriptors inherited before installation")}
