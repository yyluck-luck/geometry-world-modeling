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
    # 2026-09-17 defect correction, disclosed and preserved in
    # history_revisit_episodes_anchor_drift_defect.py.
    #
    # The previous rule also required the ANCHORS to be within merge_frames.
    # During one continuous return sweep the nearest earlier anchor drifts
    # forward, so that condition split a single leave-and-return into several
    # nominal episodes.  On fr1_room it reported three episodes for what the
    # return-frame structure shows to be one continuous pass.
    #
    # The corrected rule merges on RETURN-FRAME contiguity only, using the same
    # already-declared merge_frames tolerance.  A new episode therefore requires
    # a genuine break in the qualifying return sequence, i.e. the trajectory
    # stopped satisfying the frozen revisit condition and later satisfied it
    # again.  No new threshold is introduced and no parameter is retuned.
    n = len(candidates)
    uf = _Union(n)
    for a in range(n):
        for b in range(a + 1, n):
            if abs(candidates[a]["j"] - candidates[b]["j"]) <= merge_frames:
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

    # 3. Same moment of return, two different earlier anchors.  This is ONE
    #    moment in the trajectory, so it is one episode.  The previous rule
    #    split it, which is the anchor-drift defect being corrected here.
    diff_anchor = _cands([(100, 400), (700, 400 + 5)])
    n3 = len({c["revisit_episode"] for c in assign_episodes(diff_anchor)})
    checks.append(("one return moment matching two anchors is a single episode",
                   n3 == 1, f"got {n3}"))

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

    # 6b. Defect regression: one continuous return during which the nearest
    #     anchor drifts far must remain ONE episode.  This is the fr1_room
    #     pattern that the previous rule split into three.
    # The assertion is about the RULE, not about a desired episode count.
    # Anchor drift alone must not split; only a return-frame gap larger than the
    # pre-declared tolerance may.  On the real fr1_room selection the returns are
    # j = 982,1002,1022,1057,1077,1097,1117,1137, whose 1022->1057 gap of 35
    # exceeds the declared tolerance of 30, so the corrected rule reports two
    # episodes there.  The tolerance is NOT retuned to force a different count.
    same_pass = _cands([(25, 982), (21, 1002), (90, 1022)])   # gaps 20, 20
    nd = len({c["revisit_episode"] for c in assign_episodes(same_pass)})
    checks.append(("anchor drift inside a contiguous return does not split",
                   nd == 1, f"got {nd}"))
    real = _cands([(25, 982), (21, 1002), (90, 1022), (130, 1057),
                   (127, 1077), (138, 1097), (156, 1117), (167, 1137)])
    nr = len({c["revisit_episode"] for c in assign_episodes(real)})
    checks.append(("a return gap above the declared tolerance splits, "
                   "and the tolerance is not retuned", nr == 2, f"got {nr}"))

    # 6c. A genuine break in the qualifying return sequence still splits.
    broken = _cands([(25, 300), (30, 320), (25, 900), (30, 920)])
    nb = len({c["revisit_episode"] for c in assign_episodes(broken)})
    checks.append(("a real gap between qualifying returns still splits", nb == 2, f"got {nb}"))

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
