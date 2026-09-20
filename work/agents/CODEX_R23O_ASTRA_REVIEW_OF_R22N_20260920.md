# Round 23-O — Astra review of Round 22-N

**Review status:** completed as a repository-grounded adversarial review. The mandatory local
in-process `codex exec -m gpt-6-astra ...` fallback was attempted, but failed before model output
with `Operation not permitted`; that tooling failure is not evidence for or against the claim.

## Ruling

**DOWNGRADE — INSUFFICIENT.**

The four-tuple is a useful, conservative internal audit contract and may become a measurement
artifact. Round 22-N has not shown that it is a new oracle rather than a domain-specific
composition of existing state-pollution and order-dependence ideas. The two counterexamples show
that two simple heuristics are unsound; they do not by themselves establish a contribution. The
current evidence also does not establish external validity, a semantic lifecycle oracle, or a
measured consequence in one case containing all four tuple elements.

This downgrade does not say that the audit is useless. It says that `SHAPE-AVAILABLE` is too strong
as a claim that the shape is already defensible. The project flags remain unchanged:
`new_method_validated=false` and `novelty_authorization=NONE`.

## Scope and local verification

I read Round 22-N, `RESEARCH_PRINCIPLES.md`, `RESEARCH_MEMORY.md`,
`docs/report/TECHNICAL_REPORT_20260918.md`, `docs/IDEAS_SUMMARY_FOR_REPORT_20260920.md`, and
`docs/LIFECYCLE_AUDIT_CLOSEOUT_20260919.md`.

The three pinned VMem files are byte-identical: all have SHA-256
`90a45f452a4f734b3371fb526c566162026e5d900e0c8204709dd57f44ef1d7e`, and pairwise `cmp` passes.
Each has the requested calls at line 1249 (`get_context_info(target_c2ws,
use_non_maximum_suppression)`), line 1263 (`torch.cat([context_c2ws, target_c2ws])`), and line 1265
(`get_translation_scaling_factor(all_c2ws)`).

The source claim about `self.c2ws` needs the same precision that Round 22-N itself partly supplied:
there are two positive value-write sites, line 180 (`self.c2ws = [c2w]`) and line 1297
(`self.c2ws.append(...)`), and no property setter in the three pinned files. There is also a
state mutation at line 1360 (`self.c2ws.pop()`) inside `undo_latest_move`. Thus “two assignment /
append sites” is accurate; “only two mutations” is false. A lifecycle audit must count deletion and
rollback transitions as well as value writes.

The repository's evidence boundary is narrow. The main audit frame is a convenience frame of
20 candidates: static HIT 2/20 (VMem and GEN3C), NEAR 2/20, CLEAN 15/20, and
SUSPECT-UNTRACED 1/20; frozen-weight measured HIT is 0/20. The VMem `+0.245 dB` result is a
clean-versus-leaked contrast on an exposed 14-window panel with two seeds, not a memory-versus-
static result. GEN3C is a static released-code reachability case without an end-to-end released
run. The ledger explicitly says that the two surviving cases cannot be paired: GEN3C has an
oracle but no measured consequence, while VMem has a measured contrast but no defensible public
oracle.

There is also a governance inconsistency that should not be hidden: the closeout says C6 (method-
only contribution) was **not** relaxed (`docs/LIFECYCLE_AUDIT_CLOSEOUT_20260919.md:3-6`), while
the later ideas summary says the owner relaxed C6 (`docs/IDEAS_SUMMARY_FOR_REPORT_20260920.md:124-139`)
and Round 22-N says it is relaxed. This does not change the scientific ruling; it only means that
measurement authorization must be treated as unresolved until the owner records one current state.

## Q1 — Is the four-tuple novel?

The honest answer is **not demonstrated; on the current definition it is a domain-specific
composition of occupied software-engineering ideas**.

The four elements are:

```
(writer on call A, public A→B sequence, exact consumer on B,
 dominance check that no recompute/overwrite/reset covers the state)
```

The checked prior work maps onto most of this structure:

| Exact paper title | Venue / identifier | What it already covers that matters here |
|---|---|---|
| **Reliable Testing: Detecting State-Polluting Tests to Prevent Test Dependency** | ISSTA 2015, DOI [10.1145/2771783.2771793](https://doi.org/10.1145/2771783.2771793) | PolDet finds tests that modify shared heap or file state and reports access paths to the polluted location. This is already a writer/state-pollution oracle, even when a specific victim has not yet been identified. |
| **Empirically revisiting the test independence assumption** | ISSTA 2014, DOI [10.1145/2610384.2610404](https://doi.org/10.1145/2610384.2610404) | Formalizes dependence over ordered tests and execution environments and tests whether reordering changes outcomes. |
| **Practical Test Dependency Detection** | ICST 2018, DOI [10.1109/ICST.2018.00011](https://doi.org/10.1109/ICST.2018.00011) | PRADET combines data-flow information about writers/readers with executions in different orders to identify manifest dependencies. |
| **iFixFlakies: A Framework for Automatically Fixing Order-Dependent Flaky Tests** | ESEC/FSE 2019, DOI [10.1145/3338906.3338925](https://doi.org/10.1145/3338906.3338925) | Uses polluter/victim/helper concepts and searches for state-resetting helpers. |
| **Repairing Order-Dependent Flaky Tests via Test Generation** | ICSE 2022, DOI [10.1145/3510003.3510173](https://doi.org/10.1145/3510003.3510173) | Localizes the exact polluted shared state and generates reset sequences; this is close to the reset-coverage part of the proposed audit. |
| **Preempting Flaky Tests via Non-Idempotent-Outcome Tests** | ICSE 2022, DOI [10.1145/3510003.3510170](https://doi.org/10.1145/3510003.3510170) | Re-running the same test in one environment exposes self-pollution and ineffective cleanup, including pass-to-fail state carryover. |

These papers do not prove that the exact four-tuple string has appeared verbatim. I did not conduct
an exhaustive search over every software-testing paper, so “no prior paper has exactly this tuple” is
**UNVERIFIED**. Exact textual novelty is not the right burden anyway. A reviewer can reasonably
ask whether a PRADET/PolDet-style writer-to-consumer dependency, plus an ODRepair-style reset
search, has simply been renamed as a public model-call audit.

The strongest possible residual distinction is the **public lifecycle contract**: model-serving
calls can intentionally continue history, reset may cross service/model layers, a generated output
may lack a Boolean pass/fail oracle, and “no recomputation or overwrite dominates the consumer” may
be a useful source-level obligation. But R22-N supplies no experiment showing that this obligation
cannot be obtained by instantiating the existing tools, and no comparison of labels or failures
between the four-tuple and those baselines. Therefore the residual distinction is a hypothesis,
not a novelty result.

The accepted benchmark precedents cited by R22-N establish only that measurement can be a paper
shape:

- **VBench: Comprehensive Benchmark Suite for Video Generative Models** — CVPR 2024,
arXiv:2311.17982.
- **WorldModelBench: Judging Video Generation Models As World Models** — NeurIPS 2025 Datasets
and Benchmarks Track, arXiv:2502.20694.

Those papers provide a benchmark object, data/labels or human-aligned evaluation, baselines, and a
reusable protocol. Their acceptance does not establish that this particular four-tuple is new or
that the current static 20-case frame is an equivalent artifact.

A nearby world-model measurement paper further makes a broad “state validity is unoccupied” claim
unsafe: **Current World Models Lack a Persistent State Core**, arXiv:2606.20545, venue **UNVERIFIED**.
It evaluates persistence semantics rather than source-level reset auditing, so it does not occupy
the exact four-tuple; it does show that persistent-state validity is already an active measurement
object.

To support a positive novelty claim, the project would need a pre-registered comparison showing an
irreducible gap: run PolDet/PRADET/order-reordering/ODRepair-style baselines where applicable, then
show that the public-boundary and dominance contract finds a reproducible class they cannot label,
while not overflagging intentional history or recomputed state. Without that non-reducibility test,
Q1 is **INSUFFICIENT**.

## Q2 — Do the two naive-rule failures constitute a result?

They are valid counterexamples to two unsound heuristics, but the contribution does not follow from
their existence.

- “The field is absent from `reset()`” can be a false positive when the consumer recomputes the
  needed value on every call. The project records CausVid this way: its KV cache has no index fields
  and positions are recomputed per call.
- “There is an explicit reset call” can be a false negative when the reset covers an inner object
  but an outer admission or readiness state remains stale. The project records GEN3C this way:
  `clear_cache()` resets the inner `model_was_seeded`, while the outer `model_seeded` is not cleared.

I found no checked prior source that states the exact sentence “both naive rules fail” as a named
bidirectional theorem; that absence is **UNVERIFIED**. The underlying directions are unsurprising,
however. State pollution can exist before a known consumer (PolDet), a reader/order relation can be
identified dynamically (PRADET and the test-independence work), reset helpers can be incomplete
(ODRepair/iFixFlakies), and repeated execution can reveal self-pollution (NIO). Two project examples
therefore establish domain relevance, not novelty or prevalence.

To turn this into a result, freeze a finite counterexample suite before inspecting labels. Include,
at minimum: absent-but-recomputed state; reset-present-but-wrong-scope state; conditional/late
reset; overwrite-before-consume; intentional history continuation; and a genuine stale consumer.
For each case, report the truth label, both naive labels, the four-tuple label, and the labels from
applicable prior baselines. Then run the same protocol on a declared cross-system frame with blinded
labels and report false-positive/false-negative or reclassification rates. The key result must be an
improvement in validity decisions, not just two anecdotes.

## Q3 — Audit of Round 22-N's own reasoning

### (a) Complete claim from partial evidence

The broad claim at Round 22-N lines 176–181 quantifies over “stateful released video/world-model
systems,” but the file does not publish a case-level table containing all four tuple entries for
each reclassification. The text itself admits that external validity and conclusion impact are not
established (lines 15–19 and 196–203). The GEN3C trigger is also narrower than the broad claim:
the closeout limits the released trigger to `gpu_count == 1` and `model_name` in
`{cosmos, cosmos-predict1}` (`docs/LIFECYCLE_AUDIT_CLOSEOUT_20260919.md:78-83`). The correct
wording is therefore a scoped protocol hypothesis, not a demonstrated universal apparatus.

### (b) Structural pattern versus traced consumption

Round 22-N says it traced consumers, and the proposed tuple is designed to prevent the old mistake.
That is a sound repair in principle. It is not evidence that every case in the 20-system table
actually passed the repair. The project ledger records that CausVid was previously called a HIT
because branch asymmetry was mistaken for stale consumption; only later consumer tracing changed it
to CLEAN. A protocol should therefore publish the exact writer, sequence, consumer, and dominance
trace per case. R22-N does not do so. A structural “missing reset” pattern without that trace is
at most `SUSPECT-UNTRACED`, as the ledger itself requires.

### (c) Convenience sample and population language

The main disclaimer is honored. Round 22-N explicitly calls the 18-paper literature set a
balanced convenience sample, labels 2/18 fractions as sample-only, calls the 20-system panel a
convenience panel, and forbids interpreting 15/20 as prevalence. I find no direct population claim
in those passages.

Two cautions remain. First, the 18-paper contribution-shape corpus and the 20-system lifecycle
panel are different units and estimands; conclusions from one cannot validate the other. Second,
“accepted papers frequently change ... the validity apparatus” is a qualitative reading of a
deliberately balanced sample, not field frequency evidence. The file mostly states this limitation,
but the accepted benchmark precedents must not be used as indirect evidence that the four-tuple is
valid or novel.

### (d) Estimands

The separation is mostly correct: Round 22-N explicitly refuses to combine the GEN3C static oracle
with the VMem `+0.245 dB` contrast and says not to imply generated-video degradation from a static
case. That is good evidence discipline.

There is one material classification inconsistency. Lines 45–50 call VMem and GEN3C two static HITs,
while lines 183–187 foreground one static GEN3C HIT and place VMem in a separate measured bucket. The
latest closeout is more precise: GEN3C has a defensible lifecycle oracle but no measured consequence;
VMem has a real stale read and measured contrast but `NO-DEFENSIBLE-ORACLE`. Calling both “HIT” mixes
“candidate structural stale read” with “oracle-supported lifecycle defect.” VMem should be
`ORACLE-UNRESOLVED / measured contrast`, not a counted positive for a defect-prevalence estimand.

## Q4 — Are the six survival conditions sufficient and necessary?

No. They are useful publication safeguards, but they are neither jointly sufficient for soundness nor
all necessary for the narrow static audit claim.

| R22-N condition | Assessment | Required correction |
|---|---|---|
| 1. Freeze tuple, verdicts, dominance rule, manifests, paths, hashes, controls | Necessary for a reproducible audit, not sufficient for a correct oracle. | Add an explicit semantic lifecycle contract and pre-registered eligibility/scope rules. |
| 2. Independent blind reviewer and agreement against both naive rules | Not logically necessary for a single-case static proof, but necessary for a credible external reclassification result. As written it is currently unsatisfiable: the owner is the auditor and this Astra loop is not independent. | Obtain a reviewer outside the author/audit loop, or clearly downgrade to a replication/dual-implementation check. Blindness alone does not create independence. |
| 3. Two or three additional released systems, clean negative and positive cases, no prevalence without a frame | Needed for cross-system external validity, not needed to state one scoped worked example. It still does not create a sampling frame. | Pre-register the eligible population, version/configuration envelope, exclusions, and denominator; report out-of-scope systems separately. |
| 4. One positive case with end-to-end consequence or reproducible static invalid-state trace | Static trace is enough for a static-lifecycle claim if its semantic oracle is explicit; end-to-end generation is needed for a video-quality/consequence claim. | Do not present the alternatives as equivalent estimands. Name the result `static lifecycle defect` unless frozen-weight behavior is measured. |
| 5. CPU-runnable, one-command, immutable, traced, byte-identified artifact | Strongly needed for adoption and reproducibility, not logically necessary for the proposition “this path is stale.” | Treat this as artifact quality; add differential tests and a machine-readable per-case evidence bundle. |
| 6. Keep VMem measurement separate | Necessary for the current evidence because VMem lacks a defensible oracle, but not a universal condition of a lifecycle audit. | Retain it as evidence hygiene and forbid cross-case oracle/consequence aggregation. |

The most important missing condition is a **semantic oracle**. “Not in `reset()`” is only an
anomaly signal. The audit must state when the public boundary promises isolation, when persistence is
intentional history/autoregression, and which state is allowed to survive. A dominance proof also
needs a declared scope: exact commit, public API/configuration envelope, aliases, exceptions,
object swaps, failure paths, and dynamic dispatch. “No cover exists anywhere” is not a sound global
claim merely because a local source search found no assignment.

Other missing conditions are: (i) a preregistered sample frame and version/commit identity; (ii) a
baseline comparison against applicable PolDet/PRADET/order-reordering/ODRepair/NIO procedures; (iii)
mutation or finite-state controls that test known false positives and false negatives; (iv) independent
re-execution of the released artifact; and (v) an explicit error taxonomy separating static code
reachability, semantic defect, and measured output consequence.

Condition 2 does not make the entire idea logically impossible, but it does block the proposed
publishable validation package in the current setting. An owner-controlled relabel or another
in-loop model is not an independent blind reviewer. If no external reviewer can be obtained, the
claim must remain a scoped internal audit protocol and be marked `INSUFFICIENT`.

## Q5 — Final decision and minimal path to reconsideration

**Final decision: DOWNGRADE to `INSUFFICIENT`.**

The downgrade has four independent reasons:

1. Q1 novelty is unproven and presently looks like a domain transfer/composition of established
   test-pollution and order-dependence machinery.
2. Q2's bidirectional heuristic failures are counterexamples, not a contribution without a
   preregistered truth suite, baselines, and reclassification impact.
3. Q3 reveals a universal claim wider than the scoped evidence and a static-HIT classification that
   mixes VMem's unresolved oracle with GEN3C's static oracle.
4. Q4's independent-review condition cannot currently be met, and the six conditions omit the
   semantic lifecycle oracle and baseline non-reducibility test.

A future review could reconsider only after the project freezes a lifecycle contract and scope,
publishes all case-level four-tuples, separates `ORACLE-UNRESOLVED` from `HIT`, runs a blinded
external or genuinely independent review, compares against the named software-testing baselines,
and reports either a reproducible static artifact result or a same-case frozen-weight consequence.
Until then, the defensible label is **internal validity/audit apparatus hypothesis**, not a novel
measurement contribution or a validated method.
