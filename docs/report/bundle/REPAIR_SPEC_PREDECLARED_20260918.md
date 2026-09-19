# Slot repair specification, declared before any repair output is scored

Recorded 2026-09-18, **before** any PSNR was computed on any repair output.
`new_method_validated=false`, `novelty_authorization=NONE`.

## Why this file exists

An external review identified that my first repair implementation
(`slot_utilisation_control.py`, job 595891, 24 outputs sealed and **unscored**) conflates two
interventions. Given a shipped selection `(a, a, b, c)` it produces `(a, b, c, d)`: it adds the
next distinct candidate `d` **and** moves `b` and `c` one slot earlier. A one-slot replacement
`(a, d, b, c)` changes only the redundant occurrence.

The objection is correct as an identification matter. The already-sealed arm is **not** deleted,
rewritten, or silently replaced; it is retained and reported. The specification below is fixed
now, while no repair output has been scored, and both variants will be reported whatever they show.

## The two arms

- **REFILL** (`memory_nms_off_dedup`, already generated, job 595891): `(a,a,b,c) -> (a,b,c,d)`.
  This is what the pinned source itself would have produced had the duplicate not consumed a slot:
  its fill step appends to the end of the selection. Faithful to the source's own logic.
- **INPLACE** (`memory_nms_off_inplace`, to be generated): `(a,a,b,c) -> (a,d,b,c)`. The redundant
  occurrence is replaced where it stands; every surviving entry keeps its slot.

## Primary and secondary

**INPLACE is the primary repair arm**, because it isolates the content change from the position
change. REFILL is reported alongside it as the source-faithful variant.

`INPLACE - REFILL` is a pure permutation of the same context multiset and is reported as the
order component of the repair.

## What was already measured that bears on this

The leak-regime decomposition (job 595887, scored before this file was written) gives the
PERMUTATION stratum as **-0.015 dB, sd 0.015, n=4**: reordering an identical context multiset
moved PSNR by a negligible amount in this regime. That makes a large REFILL/INPLACE divergence
unlikely, but it is measured rather than assumed, and it does not remove the identification
argument for preferring INPLACE.

## The prospective decision rule, unchanged

Retain the duplication explanation only if the **INPLACE** arm gains at least 0.20 dB in mean over
the affected windows **and** every no-op window reproduces the sealed shipped output
byte-identically. Below 0.20 dB the performance explanation is discarded. The threshold is not
lowered, the replacement policy is not changed, and no favourable subgroup is elevated, under any
outcome.

## Population

Of 14 windows: 8 are affected (a duplicate exists and a distinct replacement candidate exists),
4 are no-op internal controls (the shipped selection already has four distinct frames), and 2 are
`INSUFFICIENT_DISTINCT_CANDIDATES` (scene_13 w200, scene_14 w100 — the pipeline's entire ranked
candidate list holds only three distinct frames, so the duplicate is not a recoverable slot but a
genuine shortage of candidates). Those two windows are excluded from the repair arm by a rule
fixed before scoring, and are reported as excluded with the reason.

## Candidate-list provenance, to be verified before the primary arm is interpreted

The ranked candidate list is read from the pipeline rather than re-implemented. The review noted
that `pipeline.py:492` computes `num_retrieved_frames = min(context_num_frames + 10,
len(timestep_weights))`, so raising `context_num_frames` could in principle change the candidate
pool, and a matching four-element prefix would not certify the remainder.

The bank holds 12 frames, so `len(timestep_weights) <= 12 < 14`, and `min(14, T) = min(15, T) =
min(16, T) = min(17, T) = T` for all `T <= 12`. That argument is not accepted as evidence. It is
tested: the ranked list is obtained at `context_num_frames` 5, 6 and 7, which produce three
different `context_num_frames + 10` values, and the shorter list must be an exact prefix of the
longer one in every window, with the distinct-frame count never exceeding the bank size. If the
nesting fails anywhere, the repair arms are withdrawn rather than reinterpreted.

## What a passing repair would and would not establish

Would: replacing the colliding selection with the pipeline's next distinct native candidate
improved PSNR on the affected finite-panel cases.

Would not: that duplicate inputs intrinsically harm this generator; that removing a duplicate
helps without supplying new observation; that retrieval is or is not effective in general. An
absent-slot control `(a, -, b, c)` would be needed for the first two, and no such control exists
under a four-frame selection-only intervention that leaves the conditioning interface untouched.
It is not attempted, and no substitute is claimed.

Arithmetic consequence recorded in advance: with 8 affected windows out of 14 and a repair gain of
at least 0.20 dB, the repaired configuration's mean against fixed-offset context would be at least
`0.242 + (8/14)(0.20) = 0.356 dB`. A successful repair therefore **strengthens a positive**
finite-panel comparison for the repaired configuration. It cannot support a negative conclusion
about retrieval.
