# Leak attribution, entry-path check, and the regime decomposition (2026-09-18)

> **SECOND CORRECTION, 2026-09-18.** Claims in this file that the released interface disables
> retrieval NMS at *every* call site, that the config default is unreachable, that "NMS-on is not
> the method as shipped", or that the threshold leak belongs only to comparative harnesses, are
> **false and retracted**. `navigation.py` has **three** `generate_trajectory_frames` call sites;
> the third (`_turn`, line 321, reached from `app.py:208/210` via `turn_left`/`turn_right`) passes
> **no** NMS argument and therefore resolves to the config default `true`. The released demo mixes
> both settings on one pipeline object, so the leak is **natively reachable**. Static reachability
> only — not measured on the demo, and it says nothing about the paper's evaluation.
> See `docs/ENTRY_PATH_CORRECTION_20260918.md`.


Status: `DIAGNOSTIC_ESTABLISHED`. `new_method_validated=false`, `novelty_authorization=NONE`.
No human approval is claimed or implied by anything in this file.

## 0. What this file settles

An external adversarial review (GPT-6 Astra, relayed 2026-09-18) made two claims that
decide what is claimable from the `initial_threshold` finding. Both are static, checkable
properties of the pinned source. Both were checked here rather than accepted. One is
confirmed, one is extended into a stronger correction against my own prior framing.

## 1. Gate result: order invariance PASSES (job 595599)

`arm_state_isolation_test.py`, zero diffusion, exercised the generation worker's real
`isolate_arm_state` routine in three circumstances (A clean NMS-on alone; B NMS-off →
isolate → NMS-on; C the sealed run's contaminated order). Result **11/11 PASS**, including
both self-checks that keep the test from being vacuous:

- `a freshly constructed pipeline has no initial_threshold, so the isolation routine
  restores the real post-construction state`
- `the test can detect the contaminated ordering it is guarding against`

Equality held for the effective threshold, the ordered frame ids, and the padding
multiplicities. The isolation comes from the routine the worker itself calls; no test-only
assignment restores the threshold. The clean-contrast run is therefore unblocked.

## 2. Confirmed: the leak cannot move the ray-reference camera

Astra asserted that slot 0 is selected before the NMS threshold is applied. Checked in
`vendor/vmem_snapshot/modeling/pipeline.py`
(sha256 `90a45f452a4f734b3371fb526c566162026e5d900e0c8204709dd57f44ef1d7e`), lines 709-716:

```python
selected_indices = []
current_threshold = self.initial_threshold
selected_indices.append(sorted_frames[0])          # unconditional, pre-loop
if not use_non_maximum_suppression:
    selected_indices.append(len(self.c2ws) - 1)
while len(selected_indices) < max_frames and current_threshold >= 1e-5 and use_non_maximum_suppression:
```

`sorted_frames` is `argsort` over surfel-relevance candidates by geodesic distance and does
not read `initial_threshold`. So within a fixed bank, slot 0 is threshold-invariant.

**Consequence: the hypothesis that the state leak acts through the slot-0 ray gauge (M3) is
dead.** `get_plucker_coordinates` takes its reference from `extrinsics_src=all_w2cs[:1]`,
which the leak provably cannot change. This kills the "M5 x M3 via slot-0" combination I had
proposed as my strongest direction. Measured confirmation follows in §4: slot 0 was identical
in every window tested.

Scope: this holds for a fixed bank. In a sequential run where generated frames are written
back, a changed selection could change the bank and hence slot 0 at a later step. That case is
not established here and must not be asserted.

## 3. Correction against my own framing: the shipped interface never enables NMS

Astra warned that an incomplete `reset()` does not by itself establish that native execution
is contaminated. Checking that objection produced a stronger result than the objection itself.

In the released interface, `app.py` (sha256 `02144b51...`) builds `Navigator(MODEL, ...)`, and
`navigation.py` (sha256 `6d267365...`) is the only caller of the generation entry point. Both
of its call sites pass the flag explicitly:

```python
new_frames = self.pipeline.generate_trajectory_frames(interpolated_poses,
                                                      interpolated_Ks,
                                                      use_non_maximum_suppression=False)
```

`navigation.py:187` and `navigation.py:236`. There is no other caller of
`generate_trajectory_frames` in the snapshot, and `get_context_info` has exactly one internal
caller (`pipeline.py:1249`). Meanwhile `configs/inference/inference.yaml:16` declares
`use_non_maximum_suppression: true`.

Three consequences, all of which cut against claims I was moving toward:

1. **The leak is not a defect of native VMem inference.** With a single setting the NMS-off
   branch rewrites `1e8` on every call, so nothing stale is ever consumed. The leak requires
   evaluating two settings on one pipeline object. That is my comparative harness, and anyone
   else's that does the same. It is **not** evidence that the VMem paper's reported results
   are contaminated, and that must not be claimed.
2. **"NMS on" is not VMem-as-shipped.** The shipped path is NMS-off. My `memory_nms_off` arm
   is the operative configuration and `memory_nms_on` is a config value the interface
   overrides. Any writing that treated NMS-on as the method's default retrieval is wrong.
3. **The config default is unreachable through the released interface.** The
   `is_second_step` threshold assignment in the enabled branch is dead code on that path.

Item 3 is a real, checkable observation about the release. It is an implementation-provenance
note, not a research contribution, and is recorded as such.

## 4. The regime decomposition (job 595599, three scene_13 windows)

The leak's effect on the selection is not uniform. On the padded context ids that actually
reach the consumer:

| window | clean NMS-on | leaked NMS-on (thr 1e8) | regime |
|---|---|---|---|
| w100 | [140, 110, 100, 120] | [140, 100, 110, 115] | CONTENT (120 -> 115), reordered |
| w200 | [255, 240, 250, 245] | [255, 240, 250, 245] | NULL, identical |
| w300 | [355, 340, 320, 305] | [355, 305, 340, 320] | PERMUTATION, same multiset |

Slot 0 identical in all three, as §2 predicts.

This decomposition is more useful than the undifferentiated "the leak changed the selection"
claim, because the three regimes support different inferences:

- **NULL** windows contribute exactly zero to any leaked-minus-clean contrast, and their two
  arms must produce byte-identical output. They are a free determinism control.
- **PERMUTATION** windows hold the context multiset, the cameras, the intrinsics, the
  normalisation input and the slot-0 gauge all fixed. Any output difference there is a pure
  slot-order effect and **cannot** be attributed to which frames were retrieved. This is a
  naturally occurring intervention: it needs no artificial scale exchange, no reference
  override, and no mismatched image-camera pairing, so it avoids every kill criterion Astra
  attached to an injected-scale design.
- **CONTENT** windows are the only ones where retrieved image content differs.

`leak_regime_census.py` (job 595614) extends this census to the full sealed panel
(scene_13 + scene_14, starts 0..350) using retrieval metadata only: zero diffusion, no ground
truth, no target decode. It is pre-registration input, collected before any PSNR is computed,
which is the ordering the review required.

## 5. Ruling accepted, with the parts I am not taking

Accepted and acted on:

- Ceiling declared as a bounded evaluation case study, conditional on the measurements below.
  Not a method paper. Not a benchmark paper.
- Stop SOCF-A and FGB-SI development; stop coverage/gating/cache-policy design work.
- Stop treating generic camera-gauge sensitivity as an innovation candidate. PRoPE
  (arXiv 2507.10496) and EscherNet (arXiv 2402.03908) occupy it; §2 independently kills the
  slot-0 route for this project.
- Stop analysing M6 as a negative memory result. It remains only as the contaminated
  observation whose interpretation was withdrawn.
- Stop expanding metric and reproducibility infrastructure as though it were the contribution.
- Drop "geometry-aware world modelling" as the description of what current results support.

Not taken as given, held for verification:

- The prior-art verdicts are relayed claims. TTAB (arXiv 2306.03536) and PRoPE must be read at
  primary source before any distinction paragraph is written, per RESEARCH_PRINCIPLES v2.13.
  Nothing here asserts priority or novelty.
- The proposed 0.20 dB deadband is a prospective project decision threshold, not a statistical
  or perceptual claim, and is recorded before any contrast is computed.

## 6. What the census decides

If most windows are NULL, the leak cannot have materially changed the sealed comparison, the
distortion hypothesis dies cheaply, and the correct output is a correction plus the clean
measurement. If PERMUTATION windows exist in both sequences, they carry the one claim that is
both cheap and not obviously occupied. The census is what selects windows, and it is fixed
before any score is seen.
