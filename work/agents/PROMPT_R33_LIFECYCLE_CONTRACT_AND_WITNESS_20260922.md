# Round 33 — Is the VMem initial_threshold residue a contract violation, and can we exhibit a witness?

A reviewer concluded the only near-term publishable object is a narrow forensic study of retrieval-state validity in VMem, and set this precondition, which I accept:

> You must first show that the two histories SHOULD be equivalent under a declared experimental contract, not merely end at the same camera position. A memory system may legitimately depend on history. Calling legitimate history dependence a bug destroys the paper.

## Task 1 — the contract argument
Using the pinned source, the VMem paper (arXiv:2506.18903, read it), config defaults, and navigation.py / app.py call sites:
- Enumerate every piece of state that retrieval is ALLOWED to depend on (memory bank, surfels, c2ws, frame count...) and argue from the paper and code what the authors intend.
- Classify `self.initial_threshold` precisely. Is it (a) scene memory the method is meant to accumulate, (b) per-call control state that should be derived fresh from the current call's arguments, or (c) something else? Argue from evidence: where it is written, what it means semantically (an NMS pose-distance threshold), whether the paper describes it, whether reset() is meant to restore a fresh-instance state.
- Give the strongest argument that the residue is LEGITIMATE history dependence, then decide whether it survives. Do not skip this.

## Task 2 — the witness
The reviewer wants: two legal, reachable executions that should be equivalent under the declared contract but produce DIFFERENT ORDERED CONTEXT lists (context_time_indices) handed to the generator.
- Trace get_context_info end to end (roughly :630-:755). Reconstruct precisely how the selected indices are built: candidate multiplicity from surfel counts (:657), sort purely by pose geodesic distance (:665), max_frames = min(context_num_frames, len(candidates), len(latents)) (:671), first append (:711), the NMS-off second append of len(self.c2ws)-1 (:713), the relaxing-threshold NMS loop, and the fallback at :745. Verify or correct every one of those line claims.
- Determine: given the inherited value 1e8 versus a fresh value, does the NMS loop select a different set or order, and under what candidate/pose conditions? Is it possible that the inherited value is NEVER consumed in a way that changes output (e.g. if the loop always relaxes to the same result)? Be exact.
- Determine whether this can be demonstrated WITHOUT GPU and WITHOUT modifying source: e.g. by calling get_context_info's selection logic on saved c2ws/frame_count from sealed artifacts in this repo, with a faithful stub only for the surfel render. State exactly what saved inputs exist in the repo (search work/ for saved c2ws, frame counts, context indices from jobs 594957 / 595887 / S111). If the needed intermediates were not saved, say so plainly: then no witness exists yet.
- If feasible, actually construct the CPU witness in your output (show the code you ran and its output), with the stub boundary labelled.

## Task 3 — a separate observation to check
I noticed that :711 and :713 append sorted_frames[0] and len(self.c2ws)-1 with no identity check between them. During forward motion the closest-pose frame is often the most recent frame, which would put the same frame into two slots on the NMS-off (movement) path. The technical report says duplication arises because "two independently seeded selections return the same frame". Which explanation matches the code and the sealed context lists? One may be wrong — possibly mine.

## Output
Write to exactly one new file: work/agents/CODEX_R33_LIFECYCLE_CONTRACT_AND_WITNESS_20260922.md. End with a verdict: CONTRACT VIOLATION ESTABLISHED / LEGITIMATE HISTORY DEPENDENCE / UNDECIDED, and WITNESS EXHIBITED / FEASIBLE BUT NOT BUILT / NOT FEASIBLE WITH SAVED ARTIFACTS.
