#!/usr/bin/env python3
"""Access recording with an explicit, honest channel model.

Replaces the previous inline hook in predictor_s103.py, which had three defects
found on 2026-09-17:

  D-1  It filtered ``if event != 'open': return``.  PEP 578 raises many other
       events that are relevant to a boundary claim (``mmap.__new__``,
       ``subprocess.Popen``, ``socket.connect``, ``ctypes.dlopen``, ...).  A
       child process's reads are not visible through ``open`` at all.

  D-2  It capped the recorded list at 64 entries and then reported
       ``len(list)`` under the field name ``outside_allowlist_open_count``.
       Past 64 distinct paths the receipt silently under-reported: a run with
       ten thousand out-of-root opens would still certify "64".  This is a
       false-certification class, not a cosmetic issue.

  D-3  It declared no channel model, so "no unauthorized reads" read as a
       stronger claim than the instrument could support.

This module fixes D-1 and D-2 and makes D-3 explicit.  It does NOT claim to be
a sandbox: PEP 578 auditing is an in-process observation facility and cannot
observe reads performed by a child process or by native code that bypasses the
CPython layer.  Enforcement remains the container mount whitelist.
"""
from __future__ import annotations

import collections
import os
from pathlib import Path

# Events that indicate a file-content channel.
FILE_EVENTS = ("open", "mmap.__new__", "os.truncate", "shutil.copyfile")
# Events that indicate a channel this in-process hook cannot follow: whatever
# happens next is outside the recorder's visibility.
OPAQUE_EVENTS = (
    "subprocess.Popen", "os.system", "os.exec", "os.posix_spawn", "os.fork",
    "socket.connect", "socket.getaddrinfo", "socket.gethostbyname",
    "urllib.Request", "ctypes.dlopen", "ctypes.dlsym", "ctypes.call_function",
)
# Events that enumerate the filesystem without reading content.
LISTING_EVENTS = ("os.listdir", "os.scandir", "glob.glob", "pathlib.Path.glob")

CHANNEL_MODEL = {
    "instrument": "CPython sys.addaudithook, PEP 578",
    "observed_event_classes": {
        "file_content": list(FILE_EVENTS),
        "directory_listing": list(LISTING_EVENTS),
        "opaque_delegation": list(OPAQUE_EVENTS),
    },
    "not_observable": [
        "reads performed inside a child process after an opaque event",
        "reads performed by native code that does not traverse the CPython layer",
        "reads through a file descriptor inherited before the hook was installed",
        "any channel that is not raised as a Python audit event",
    ],
    "enforcement_is_elsewhere": (
        "The container mount whitelist is the enforcing boundary. This recorder "
        "observes and reports; it does not enforce and is not a sandbox."
    ),
}


class AccessRecorder:
    """Record audit events with exact counts and explicitly bounded samples."""

    def __init__(self, allowed_roots, forbidden_roots, sample_cap: int = 64):
        self.allowed = tuple(str(Path(p)) for p in allowed_roots)
        self.forbidden = tuple(str(Path(p)) for p in forbidden_roots)
        self.sample_cap = int(sample_cap)
        # Exact counts.  These are never truncated, which is the whole point.
        self.counts = collections.Counter()
        self.event_counts = collections.Counter()
        # Bounded samples, with explicit truncation flags.
        self.samples = {"forbidden": [], "outside": [], "opaque": [], "listing": []}
        self._seen = {k: set() for k in self.samples}
        self.truncated = {k: False for k in self.samples}

    def _bucket_path(self, target: str) -> str | None:
        if target.startswith(self.forbidden):
            return "forbidden"
        if target.startswith(self.allowed):
            return None
        return "outside"

    def _record(self, bucket: str, value: str) -> None:
        self.counts[bucket] += 1
        seen = self._seen[bucket]
        if value in seen:
            return
        if len(self.samples[bucket]) < self.sample_cap:
            seen.add(value)
            self.samples[bucket].append(value)
        else:
            self.truncated[bucket] = True

    def hook(self, event, args):
        # Count every event class we see, so the receipt can state what the
        # runtime actually raised rather than what we assumed it would raise.
        self.event_counts[event] += 1
        if event in OPAQUE_EVENTS:
            self._record("opaque", event)
            return
        if event in LISTING_EVENTS:
            try:
                target = os.fspath(args[0]) if args else ""
            except (TypeError, ValueError):
                target = ""
            if isinstance(target, str) and target.startswith("/"):
                bucket = self._bucket_path(target)
                if bucket == "forbidden":
                    self._record("forbidden", target)
                else:
                    self._record("listing", target)
            return
        if event not in FILE_EVENTS:
            return
        try:
            target = os.fspath(args[0]) if args else ""
        except (TypeError, ValueError, IndexError):
            return
        if not isinstance(target, str) or not target.startswith("/"):
            return
        bucket = self._bucket_path(target)
        if bucket is not None:
            self._record(bucket, target)

    def report(self) -> dict:
        """Counts are exact; sample lists are bounded and say so."""
        return {
            "access_accounting_method": (
                "CPython sys.addaudithook over the full PEP 578 event stream; "
                "counts are exact and never truncated; sample lists are capped "
                "and carry an explicit truncation flag"
            ),
            "channel_model": CHANNEL_MODEL,
            "sample_cap": self.sample_cap,
            "exact_counts": {
                "forbidden_root_events": self.counts["forbidden"],
                "outside_allowlist_events": self.counts["outside"],
                "opaque_delegation_events": self.counts["opaque"],
                "directory_listing_events": self.counts["listing"],
            },
            "samples": {k: sorted(v) for k, v in self.samples.items()},
            "sample_truncated": dict(self.truncated),
            "observed_event_names": dict(sorted(self.event_counts.items())),
            "boundary_clean": (
                self.counts["forbidden"] == 0 and self.counts["opaque"] == 0
            ),
        }
