#!/usr/bin/env python3
"""Revisit-episode attribution for the frozen revisit protocol.

Implements the approved amendment (PROTOCOL_ADDENDUM_A_20260917.md, section A5):
every revisit window must carry the identity of the leave-and-return event it
belongs to, because windows drawn from a single loop closure are not
independent revisit events.

Design constraints taken from the frozen protocol and amendment:
  * the revisit definition itself is NOT changed here: a revisit candidate is a
    pair (i, j) with translation < 0.30 m, geodesic rotation < 20 deg and
    j - i > 150 frames
  * episodes must reflect the leave-and-return structure, so consecutive return
    frames belonging to one continuous pass share one episode; a sliding window
    must not become its own episode
  * episode identity is bookkeeping, not a proof of statistical independence;
    dependency groups are recorded separately for windows sharing history or
    targets
  * this module reads pose/timestamp metadata only, never pixels

Nothing here inspects predictions or scores, so no outcome can influence
episode assignment.
"""
from __future__ import annotations

import math

# Merge tolerance: two revisit candidates belong to the same leave-and-return
# event when their return passes are contiguous in time or their early anchors
# overlap.  Declared before any real-sequence data is read.
EPISODE_MERGE_FRAMES = 30


class _Union:
    def __init__(self, n):
        self.p = list(range(n))

    def find(self, a):
        while self.p[a] != a:
            self.p[a] = self.p[self.p[a]]
            a = self.p[a]
        return a

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.p[max(ra, rb)] = min(ra, rb)


def assign_episodes(candidates, merge_frames: int = EPISODE_MERGE_FRAMES):
    """Group revisit candidates into leave-and-return episodes.

    candidates: sequence of dicts with integer keys 'i' (early anchor) and
    'j' (return frame), already filtered by the frozen revisit criteria.

    Two candidates join the same episode when BOTH their return frames and
    their anchors are within merge_frames, or when either interval overlaps.
    That keeps one continuous return pass in one episode while separating a
    genuinely later, independent return to the same place.
    """
    n = len(candidates)
    uf = _Union(n)
    for a in range(n):
        for b in range(a + 1, n):
            ja, ia = candidates[a]["j"], candidates[a]["i"]
            jb, ib = candidates[b]["j"], candidates[b]["i"]
            same_return_pass = abs(ja - jb) <= merge_frames
            same_anchor_region = abs(ia - ib) <= merge_frames
            if same_return_pass and same_anchor_region:
                uf.union(a, b)
    roots = {}
    out = []
    for idx, cand in enumerate(candidates):
        r = uf.find(idx)
        if r not in roots:
            roots[r] = len(roots)
        members = [c for k, c in enumerate(candidates) if uf.find(k) == r]
        out.append({**cand,
                    "revisit_episode": f"episode_{roots[r]:02d}",
                    "episode_member_count": len(members),
                    "episode_return_span": [min(m["j"] for m in members),
                                            max(m["j"] for m in members)],
                    "episode_anchor_span": [min(m["i"] for m in members),
                                            max(m["i"] for m in members)]})
    return out


def dependency_groups(windows):
    """Mark windows that share history or target frames as mutually dependent.

    Different episode IDs alone do not license a large-sample standard error;
    this exposes the remaining overlap so the analysis can respect it.
    """
    n = len(windows)
    uf = _Union(n)
    keys = []
    for w in windows:
        keys.append((set(w.get("bank_indices", [])) | set(w.get("recency_indices", []))
                     | set(w.get("early_visit_indices", []) or []),
                     set(w.get("target_indices", []))))
    for a in range(n):
        for b in range(a + 1, n):
            ha, ta = keys[a]
            hb, tb = keys[b]
            if (ha & hb) or (ta & tb):
                uf.union(a, b)
    roots, out = {}, []
    for idx, w in enumerate(windows):
        r = uf.find(idx)
        if r not in roots:
            roots[r] = len(roots)
        out.append({**w, "dependency_group": f"depgroup_{roots[r]:02d}"})
    return out


def feasibility(windows, min_independent_episodes: int = 3):
    """Frozen metadata-only feasibility decision.

    Amendment A5 fixes the threshold at three independent loop-closure events.
    Reaching fewer is UNTESTABLE, which is not a scientific negative.
    """
    rev = [w for w in windows if w.get("kind") == "revisit"]
    ctrl = [w for w in windows if w.get("kind") == "control"]
    episodes = sorted({w.get("revisit_episode") for w in rev if w.get("revisit_episode")})
    depgroups = sorted({w.get("dependency_group") for w in rev if w.get("dependency_group")})
    ok = len(episodes) >= min_independent_episodes
    return {
        "revisit_windows": len(rev),
        "control_windows": len(ctrl),
        "independent_revisit_episodes": len(episodes),
        "episode_ids": episodes,
        "revisit_dependency_groups": len(depgroups),
        "min_independent_episodes_required": min_independent_episodes,
        "decision": "ELIGIBLE" if ok else "UNTESTABLE_INSUFFICIENT_INDEPENDENT_REVISITS",
        "note": ("Episode identity is bookkeeping for the leave-and-return structure. "
                 "It is not evidence that the returns are statistically independent, "
                 "and it is not evidence that old surfaces were actually re-observed; "
                 "the criterion is pose-defined proximity only."),
    }


# --------------------------------------------------------------------------
# Synthetic trajectory tests.  No real sequence is read.
# --------------------------------------------------------------------------
def _cands(pairs):
    return [{"i": i, "j": j} for i, j in pairs]


def self_test():
    checks = []

    # 1. One loop with many overlapping sliding windows -> a single episode.
    one_loop = _cands([(100 + k, 300 + k) for k in range(0, 25, 5)])
    ep1 = assign_episodes(one_loop)
    n1 = len({c["revisit_episode"] for c in ep1})
    checks.append(("one loop with overlapping windows stays one episode", n1 == 1, f"got {n1}"))

    # 2. Genuinely separated returns -> separate episodes.
    two_returns = _cands([(100, 300), (105, 305), (100, 900), (104, 906)])
    ep2 = assign_episodes(two_returns)
    n2 = len({c["revisit_episode"] for c in ep2})
    checks.append(("separated return passes split into distinct episodes", n2 == 2, f"got {n2}"))

    # 3. Same return time but a different anchor region -> distinct episodes,
    #    because the trajectory returned to a different earlier place.
    diff_anchor = _cands([(100, 400), (700, 400 + 5)])
    ep3 = assign_episodes(diff_anchor)
    n3 = len({c["revisit_episode"] for c in ep3})
    checks.append(("same return time, distant anchors are not merged", n3 == 2, f"got {n3}"))

    # 4. Continuous nearby motion without the required departure produces no
    #    candidates at all, because the frozen gap rule filters upstream.
    #    Here we assert the feasibility verdict on an empty revisit set.
    f_empty = feasibility([{"kind": "control"}] * 8)
    checks.append(("no revisit candidates is UNTESTABLE, not a negative",
                   f_empty["decision"].startswith("UNTESTABLE"), f_empty["decision"]))

    # 5. Deterministic under equivalent input ordering.
    shuffled = list(reversed(one_loop))
    a = [c["episode_member_count"] for c in assign_episodes(one_loop)]
    b = [c["episode_member_count"] for c in assign_episodes(shuffled)]
    checks.append(("episode sizes are order-independent", sorted(a) == sorted(b), f"{a} vs {b}"))

    # 6. Feasibility passes only with enough independent episodes.
    three = _cands([(100, 300), (100, 900), (100, 1500)])
    wins = [{"kind": "revisit", **c} for c in assign_episodes(three)]
    f3 = feasibility(wins)
    checks.append(("three independent episodes are ELIGIBLE", f3["decision"] == "ELIGIBLE",
                   f3["decision"]))
    two = _cands([(100, 300), (100, 900)])
    wins2 = [{"kind": "revisit", **c} for c in assign_episodes(two)]
    checks.append(("two episodes remain UNTESTABLE",
                   feasibility(wins2)["decision"].startswith("UNTESTABLE"), ""))

    # 7. Dependency grouping notices shared history even across episodes.
    w = [{"kind": "revisit", "bank_indices": [1, 2, 3], "target_indices": [50],
          "recency_indices": []},
         {"kind": "revisit", "bank_indices": [3, 4, 5], "target_indices": [60],
          "recency_indices": []},
         {"kind": "revisit", "bank_indices": [90, 91], "target_indices": [99],
          "recency_indices": []}]
    dg = dependency_groups(w)
    ngroups = len({x["dependency_group"] for x in dg})
    checks.append(("windows sharing a history frame land in one dependency group",
                   ngroups == 2, f"got {ngroups}"))

    bad = 0
    for name, ok, detail in checks:
        print(f"[{'PASS' if ok else 'FAIL'}] {name}" + (f" — {detail}" if not ok and detail else ""))
        bad += 0 if ok else 1
    print(f"\n{len(checks) - bad}/{len(checks)} checks passed")
    return 0 if bad == 0 else 1


if __name__ == "__main__":
    raise SystemExit(self_test())
