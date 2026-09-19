# Addendum B: primary contrast, native-retrieval disclosure, failure handling

**Recorded 2026-09-17, after the fr1_room metadata feasibility gate returned
UNTESTABLE and before any generation job was submitted. Zero GPU was spent on
generation.**

Relates to, and does not modify:
- frozen protocol `bfcb5d98dc5ee89330a2adafcd077a08cf5de1d37c857678f3c8485b02191031`
- addendum A `7b28bb3c46ab235cec6ac0f8170c16218856df6ac1abe8e9fced982ba23c258d`

Data-contact status at the time of writing: fr1_room has been downloaded and its
pose/timestamp metadata read. No pixel was decoded. No arm was generated or
scored. Earlier development results on scene_13/scene_14 were already seen and
are disclosed.

`new_method_validated=false`; `novelty_authorization=NONE`.

---

## B1. Primary contrast, with a corrected rationale

| Status | Comparison | Use |
|---|---|---|
| **Sole primary** | `memory_nms_on − recency` | P1 and the F1/F2 preregistered readings |
| Secondary | `memory_nms_off − recency` | describes the other retrieval setting; cannot substitute for a failed primary |
| Secondary | `early_visit − recency` | describes fixed early context; cannot claim native-retrieval benefit |

**Corrected rationale.** The earlier wording "VMem default" was imprecise. The
accurate statement, verified against the pinned source:

- `configs/inference/inference.yaml:16` sets `use_non_maximum_suppression: true`
  and `:9` sets `context_num_frames: 4`
- the same pinned tree's `navigation.py:187` and `:236` explicitly pass
  `use_non_maximum_suppression=False` for some operations

So NMS-on is the **pinned configuration-file value**, not a property of every
upstream execution path. Both arms therefore record the configuration value and
the actual call parameter used.

Three metric families are reported side by side. That is not three independent
chances to declare success; the primary endpoint is fixed here, before scoring.

## B2. Native-retrieval execution path: this is a disclosed scope change

The earlier `execution_path_disclosure` (contract v15) states
`context_retrieval_executed: false` and
`cut3r_status: hash-verified only; never constructed, never loaded`.

**That remains a true description of the earlier S103 no-retrieval runs and is
not rewritten.** For the revisit diagnostic it is superseded, and the change is
declared here rather than absorbed silently:

| Aspect | Earlier S103 runs | Revisit diagnostic memory arms |
|---|---|---|
| `VMemPipeline.__init__` | not executed | **executed** |
| CUT3R | hash-verified only | **constructed and loaded** |
| surfel construction | not executed | **executed** |
| `get_context_info` | not executed | **executed** |
| context frames | manifest-fixed | **returned by retrieval** |

**Per-arm binding required in the run receipt:** history candidate pool and its
cutoff index -> surfel source -> retrieved frame IDs -> frame IDs actually
consumed by the generator. A constructed pipeline object is not evidence that
retrieval ran; the returned IDs must be recorded.

**Depth provenance, verified in the pinned source and in this project's code.**
`reset()` initialises `surfel_depths` to an empty list, and the revisit code
never populates it, so the first `construct_and_store_scene` call passes
`depths=None` and CUT3R estimates geometry from RGB; the second call passes back
CUT3R's own estimates written at pipeline.py:997. **No dataset-measured depth
enters selection.** The selector input condition is therefore RGB plus pose plus
CUT3R-estimated geometry. If a future variant supplies measured depth, that is
an input-condition change and must be declared before it runs.

**Scope name.** The bank is built from recorded history frames and there is no
post-generation write-back, so this is a *native-retrieval diagnostic over a
recorded-history bank*, not a complete VMem long-horizon memory validation. The
complete mechanism in the VMem paper updates memory after generation and
continues autoregressively; that behaviour is identified here and deliberately
not implemented.

**Determinism qualification applicability.** Receipt `N1_PASS` from job 594984
covers the no-retrieval consumer path under the updated instrumentation. It does
**not** cover the retrieval path, which adds CUT3R construction and a
query-dependent selection step. Before the memory arms may contribute to a
primary reading, a minimal same-seed, same-node replay qualification of the
retrieval path is required. Unaffected paths are not re-qualified.

## B3. Terminal failures in the primary contrast

Observed failure mode: `get_context_info` raises when no candidate is visible
(2 of 16 windows in earlier development runs). Logging it is not a statistical
policy.

The frozen protocol defines no failure score. Therefore, declared here and not
invented after data:

- **No penalty score is invented.**
- If the **primary** arm has a terminal failure in a window while `recency`
  succeeds, `d(window, seed)` does not exist for that pair. The pair is **not**
  dropped with a silent `nanmean`.
- When any such pair is missing, the full-sample P1/F1/F2 reading is recorded as
  **`NOT_EVALUABLE`**. The failure rate is reported in full, and any
  complete-case figure must be labelled "conditional on both arms succeeding"
  and may not be presented as the preregistered test.
- A **secondary** arm's failure does not block a complete primary reading.
- An algorithmic terminal failure must never become "retry with another seed,
  another window, or different retrieval parameters". Infrastructure retries are
  logged separately from algorithmic failures.

## B4. Isolation acceptance: the earlier ambiguity, resolved by measurement

Two statements looked contradictory. They were produced in different
environments, and the discriminating test has now been run.

| Environment | Child process reads the forbidden file? | Meaning |
|---|---|---|
| Plain interpreter, audit hook only (negative control) | **yes** | demonstrates that an audit hook is not a sandbox |
| **Formal Apptainer configuration, only window A's stage bound** | **no** | acceptance test |

Container acceptance receipt, Slurm job **595010**, COMPLETED 0:0 in 7 s:
`own_staged_history_readable=True`, `direct_read_forbidden=False`,
`child_process_read_forbidden=False`, `sequence_directory_listable=False`,
`isolation_status=PASS`.

Recorded rule: an observed successful forbidden read is `FAILED`, never
`UNMEASURED`. `UNMEASURED` applies only where the instrument cannot observe.

## B5. Corrections accepted

- **Episode count is necessary, not sufficient.** Reaching three episode IDs
  does not establish independence, statistical power, or generalisation. The
  dependency grouping governs: in the fr1_room manifest all revisit and control
  windows collapsed into a single dependency group, which is why the verdict is
  UNTESTABLE despite three nominal episodes.
- **Loop closure in a sequence does not imply usable revisits in the tested
  windows.** Demonstrated empirically: all 289 fr1_room revisit candidates lie
  in frames 982–1351 of 1352, i.e. one continuous return pass. This retires the
  earlier inference that a documented loop qualifies a sequence.
- **Training-exposure wording corrected.** Not "upstream training data is
  undisclosed": the VMem paper discloses training on SEVA with RealEstate10K.
  The accurate limitation is that **TUM-exposure verification of all upstream
  models actually used has not been completed**, so no claim is made that the
  models have not seen this data.
- **Disclosed implementation defect, not exploited.** The episode rule splits one
  continuous return into separate episodes when the nearest anchor drifts beyond
  the merge tolerance. It produced three nominal episodes from one return pass.
  The rule is **not** changed here, because changing a threshold after seeing
  data is precisely what the protocol forbids; the defect is reported and any
  correction requires prospective approval.

## B6. What remains unapproved

This addendum closes the three release conditions on the record. It does **not**
authorise anything by itself, and no signature is recorded here. Still requiring
explicit human approval:

1. the minimal same-seed replay qualification of the **retrieval** path (B2)
2. any correction to the episode rule, and any consequent re-judgement (B5)
3. any sequence change, threshold change, or task-list expansion

Current disposition for the revisit diagnostic on fr1_room remains
**`UNTESTABLE_UNDER_FROZEN_DESIGN`**. Budget spent on generation: zero.
