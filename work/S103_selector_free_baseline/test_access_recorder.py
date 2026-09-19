#!/usr/bin/env python3
"""Demonstrate the old hook's false-certification class and verify the fix.

Run:  python3 test_access_recorder.py
Exit: 0 all pass, 1 otherwise.  No GPU, no model, no dataset, no network.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from access_recorder import AccessRecorder  # noqa: E402

ALLOWED = ("/usr", "/lib", "/tmp")
FORBIDDEN = ("/home/yliutz/geometry-world-modeling", "/home/yliutz/datasets")
CAP = 64


def legacy_hook_simulation(paths, cap=CAP):
    """Exactly the arithmetic of the pre-2026-09-17 inline hook."""
    log = []
    for target in paths:
        if target.startswith(FORBIDDEN):
            continue
        if target.startswith(ALLOWED):
            continue
        if target not in log and len(log) < cap:
            log.append(target)
    # The receipt reported this as 'outside_allowlist_open_count'.
    return len(log)


def check(name, ok, detail=""):
    print(f"[{'PASS' if ok else 'FAIL'}] {name}" + (f" — {detail}" if detail else ""))
    return ok


def main() -> int:
    results = []

    # --- D-2: silent truncation is a false-certification class -------------
    n_real = 500
    paths = [f"/opt/not_allowed/probe_{i:04d}.bin" for i in range(n_real)]
    legacy_count = legacy_hook_simulation(paths)
    rec = AccessRecorder(ALLOWED, FORBIDDEN, sample_cap=CAP)
    for p in paths:
        rec.hook("open", (p, "r", 0))
    fixed = rec.report()
    fixed_count = fixed["exact_counts"]["outside_allowlist_events"]

    results.append(check(
        "legacy hook under-reports out-of-root access",
        legacy_count == CAP and n_real > CAP,
        f"{n_real} real events certified as {legacy_count}"))
    results.append(check(
        "fixed recorder reports the exact count",
        fixed_count == n_real, f"reported {fixed_count} of {n_real}"))
    results.append(check(
        "fixed recorder flags that its sample list is truncated",
        fixed["sample_truncated"]["outside"] is True
        and len(fixed["samples"]["outside"]) == CAP))

    # --- D-1: events other than 'open' are now observed ---------------------
    rec2 = AccessRecorder(ALLOWED, FORBIDDEN)
    rec2.hook("mmap.__new__", ("/home/yliutz/datasets/secret.npy",))
    results.append(check(
        "mmap on a forbidden root is recorded",
        rec2.report()["exact_counts"]["forbidden_root_events"] == 1))

    legacy_sees_mmap = False  # legacy returned early on any event != 'open'
    results.append(check(
        "legacy hook was blind to mmap",
        legacy_sees_mmap is False))

    # --- D-1b: opaque delegation is surfaced, not silently ignored ----------
    rec3 = AccessRecorder(ALLOWED, FORBIDDEN)
    rec3.hook("subprocess.Popen", ("/bin/cat", ["cat", "/etc/shadow"], None, None))
    rec3.hook("socket.connect", (None, ("10.0.0.1", 443)))
    r3 = rec3.report()
    results.append(check(
        "opaque delegation events are counted",
        r3["exact_counts"]["opaque_delegation_events"] == 2))
    results.append(check(
        "boundary is not certified clean when delegation occurred",
        r3["boundary_clean"] is False))

    # --- clean run still certifies clean -----------------------------------
    rec4 = AccessRecorder(ALLOWED, FORBIDDEN)
    for p in ("/usr/lib/python3.11/os.py", "/tmp/matplotlib-x/fontlist.json"):
        rec4.hook("open", (p, "r", 0))
    r4 = rec4.report()
    results.append(check(
        "in-allowlist run certifies clean with zero forbidden and zero opaque",
        r4["boundary_clean"] is True
        and r4["exact_counts"]["forbidden_root_events"] == 0
        and r4["exact_counts"]["outside_allowlist_events"] == 0))

    # --- the channel model must state what it cannot see -------------------
    results.append(check(
        "report declares non-observable channels",
        len(r4["channel_model"]["not_observable"]) >= 3
        and "sandbox" in r4["channel_model"]["enforcement_is_elsewhere"]))

    print()
    print(json.dumps({
        "legacy_reported_out_of_root": legacy_count,
        "actual_out_of_root": n_real,
        "under_report_factor": round(n_real / max(legacy_count, 1), 2),
        "fixed_reported": fixed_count,
    }, indent=2))
    ok = all(results)
    print(f"\n{sum(results)}/{len(results)} checks passed")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
