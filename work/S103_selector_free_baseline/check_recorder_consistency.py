#!/usr/bin/env python3
"""Fail if the inlined access-recorder text drifts between its copies.

The recorder is inlined rather than imported so the frozen bundle stays
self-contained.  Inlining creates a drift risk, so this check is mandatory:
the delimited block must be byte-identical in every file that carries it, and
must match the standalone module used by the demonstration test.
"""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

BEGIN = "# --- GWM-ACCESS-RECORDER-V2-BEGIN"
END = "# --- GWM-ACCESS-RECORDER-V2-END ---"
CARRIERS = ("predictor_s103.py", "scorer_s103.py")


def block_of(path: Path) -> str:
    text = path.read_text()
    if BEGIN not in text or END not in text:
        raise SystemExit(f"{path.name}: recorder block markers missing")
    start = text.index(BEGIN)
    end = text.index(END) + len(END)
    return text[start:end]


def main() -> int:
    here = Path(__file__).resolve().parent
    digests = {}
    for name in CARRIERS:
        block = block_of(here / name)
        digests[name] = hashlib.sha256(block.encode()).hexdigest()
    unique = set(digests.values())
    ok = len(unique) == 1
    for name, digest in digests.items():
        print(f"  {name:24} {digest[:16]}")
    print(f"[{'PASS' if ok else 'FAIL'}] inlined recorder blocks are identical")
    if not ok:
        return 1

    # The standalone module must expose the same public behaviour names.
    module = (here / "access_recorder.py").read_text()
    required = ("class AccessRecorder", "not_observable", "sample_truncated",
                "boundary_clean", "exact_counts")
    missing = [token for token in required if token not in module]
    print(f"[{'PASS' if not missing else 'FAIL'}] access_recorder.py exposes the same contract"
          + (f" — missing {missing}" if missing else ""))
    return 0 if not missing else 1


if __name__ == "__main__":
    raise SystemExit(main())
