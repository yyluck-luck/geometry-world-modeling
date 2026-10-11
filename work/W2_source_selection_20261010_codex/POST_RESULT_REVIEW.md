# W2 bounded post-result interpretation review

Workspace: Local Mac.
Review date: 2026-10-10 UTC; review began at 14:35:58 UTC, verified with the current clock.
Verdict: **CONFIRM STOP_TESTED_SELECTOR under the frozen protocol.** The saved measurements show positive geometric evidence on this panel, but the selector fails the predeclared concentration requirement against c0. These statements are compatible and must both be retained.

## Evidence inspected and verification scope

Directly inspected these files under `/Users/rocket/Documents/Codex/2026-10-10/i-m-sharing-my-github-repo/work/week1-wt/work/W2_source_selection_20261010_codex`:

- `PROTOCOL.md`, `FREEZE.json`, and `MANIFEST.json`.
- `CANDIDATE_SEAL.json` and every candidate array/receipt named by that seal, checked as bytes against their recorded hashes.
- `selection/SELECTION_SEAL.json` and every match array/receipt named by that seal, checked as bytes against their recorded hashes.
- `scores/RESULTS.json`, including all window-level primary errors and saved comparisons.

Every listed frozen file matched its frozen hash. Both seals and the result bind to the same freeze, protocol and manifest. All sealed artifact hashes matched, and selected identities in the selection seal matched the scored identities. The planned and scored window sets matched, with no empty primary support. These are direct file-integrity and arithmetic checks, not merely acceptance of the root agent's summary.

MEASURED artifact inventory: 64 candidate records, 16 sealed selections and 16 scored windows across the four planned scenes. The recorded order is freeze at 14:07:36.817279 UTC, candidate seal at 14:34:51.844534 UTC, selection seal at 14:34:57.647343 UTC, and result at 14:35:04.032282 UTC, all on 2026-10-10. Evidence: the corresponding freeze/seal/result files above. The earlier acquisition interruption is not the current result state; the inspected result is COMPLETE.

Freeze SHA-256: `7febdcdd47860a19d828e73b725a48ef8443fdffa092ae32afd3830d29f286c5`.
Result SHA-256: `9e569d98aa4f71a09ad3ce60bc1e4b287e1d6251c7e7007b714a45f0ed041d76`.

I independently recomputed aggregate errors, scene effects, window contributions, concentration shares and leave-top-two effects from the saved window errors without importing the evaluator. I did not decode new-scene RGB/depth images, rerun SIFT or reconstruction, or independently reconstruct the per-tuple geometric measurements. Separate numerical verification must not be attributed to this review.

## What the measurements support

MEASURED primary mean capped sensor-relative correspondence errors are c0 **7.893042 px**, fusion **7.883958 px**, and selected geometry **5.714834 px**. Source: [scores/RESULTS.json](/Users/rocket/Documents/Codex/2026-10-10/i-m-sharing-my-github-repo/work/week1-wt/work/W2_source_selection_20261010_codex/scores/RESULTS.json), `summary_capped_epe_pixels.primary` and `rows[].arms.primary`.

The following DERIVED values were independently reproduced from those window errors; frozen requirements come from [PROTOCOL.md](/Users/rocket/Documents/Codex/2026-10-10/i-m-sharing-my-github-repo/work/week1-wt/work/W2_source_selection_20261010_codex/PROTOCOL.md):

| Required comparison | Against c0 | Against fusion | Frozen decision |
|---|---:|---:|---|
| Aggregate relative error reduction | 27.5966% | 27.5131% | Both exceed 5% |
| Scene mean reduction positive | All four scenes | All four scenes | Pass |
| Reduction after removing comparator-specific top two windows, retaining equal scene weighting | 14.8515% | 23.3941% | Both exceed 2.5% |
| Top-two positive contributions / net signed gain | **59.6497%** | 31.4863% | **c0 fails the 50% ceiling** |

MEASURED/DERIVED abstention: one planned window fell back to c0, giving 6.25%, below the 25% ceiling. It remained in the analysis. Evidence: the selection seal and `scores/RESULTS.json` (`abstention_fraction`, `rows[].abstained`).

The c0 concentration failure comes from `scene_02__w0120` and `scene_03__w0360`. The frozen denominator is net signed improvement, including harmful windows. Replacing it with positive gains only would change the protocol; even that descriptive denominator gives 52.7096% here. Source: `scores/RESULTS.json`, `comparisons.primary.c0`.

The saved sole failed gate, `c0:top_two_dominate_net_gain_or_nonpositive_net`, is correct. Its cause here is excessive concentration, not nonpositive net gain. Every other registered gate passes. The leave-top-two result does not override the concentration gate: the frozen protocol requires both.

## Interpretation and stopping decision

This is evidence that the fixed source-only selection rule can identify geometries with lower future-view sensor-relative correspondence error on the tested panel. It is stronger evidence than the previous GT-oracle opportunity because the selected identity was saved before sensor-depth evaluation. It remains a geometry endpoint under supplied dataset poses and the frozen sensor-defined support.

It is incorrect to call the result no effect, uniformly worse geometry, failure on every scene, or benefit only in two windows. Every scene mean improves and the prescribed deletion sensitivity retains positive, material gains. It is equally incorrect to call the selector a protocol success: its improvement over c0 is more concentrated than the explicit pre-run rule permits. The faithful report is **measured improvement with a failed concentration gate; STOP_TESTED_SELECTOR**.

Do not relax the ceiling, substitute the secondary stratum, alter the denominator, remove windows from the main result, or retrospectively make the leave-top-two condition sufficient. Preserve all measurements and the original stop verdict. No further selector, new experiment, architecture change, training, or automatic pivot is recommended or authorized by this review.

The result establishes neither video-generation improvement nor novelty, posterior calibration, general population effectiveness, or equal compute cost with standalone c0. Keep `new_method_validated=false` and `novelty_authorization=NONE`. The bounded post-result interpretation task is complete.

Changed file: this review only. No GPU, network, model execution, new image/depth decoding, or alteration of the frozen experiment occurred in this review.
