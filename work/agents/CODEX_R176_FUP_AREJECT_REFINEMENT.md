# R176 FUP/AReject adversarial refinement

## Inputs and boundary

This refinement uses the verified R175 artifact. The named local R150/R152/R160/R166 records were not present under `work/agents` or the current workspace at execution time, so no claims are attributed to their unseen contents. No web search, project data, code, fixtures, runners, GPU/Slurm work, receipts, or flags were used.

## Adversarial test against adjacent prior art

**Strongest surviving distinction (conditional):** adjacent benchmarks already test whether a model should abstain when a scene/question is ambiguous, unanswerable, falsely premised, or labels are noisy. Therefore the defensible residual is narrower: an evaluator receives a *purported unique certificate* whose producer frame and/or label identity are hidden, constructs at least two admissible latent interpretations, and must reject the certificate specifically because uniqueness is unproven. The distinguishing object is certificate validity under hidden provenance/label alternatives, rather than generic answer abstention, confidence calibration, or annotation-error detection.

**Adversarial rejection test:** if FUP/AReject only means “say unsure on an ambiguous input,” then RoboAbstention/Certainly Uncertain and label-ambiguity work subsume it and the proposed gap should be rejected. FUP/AReject survives only if it requires all three observable conditions: (i) a claimed unique result/certificate, (ii) evaluator-hidden producer-frame or label provenance, and (iii) a paired counter-world in which the same visible artifact supports a different admissible result. Without this conjunction, no distinct benchmark gap is established.

## One falsifiable benchmark protocol change

Add a preregistered **paired provenance-counterworld track**:

1. For each item, publish the visible artifact and a purported unique certificate, while withholding producer-frame and label IDs from the evaluator.
2. Create a matched counter-world by changing only the hidden frame convention or hidden label mapping; preserve visible bytes and surface semantics.
3. Require a three-way output: `accept-unique`, `reject-ambiguous`, or `request-provenance`.
4. Score (a) false-unique acceptance rate on counter-worlds, (b) correct rejection rate on genuinely ambiguous pairs, and (c) over-rejection on uniquely identifiable controls. Report paired differences with confidence intervals.

This change is falsifiable: if models cannot separate counter-worlds from controls, or if a generic abstention baseline matches FUP/AReject after prompt normalization, the claimed gap collapses.

## Exact kill condition and prerequisite evidence

**Kill condition:** terminate the FUP/AReject benchmark claim if either condition holds on a preregistered held-out set: (1) a strong adjacent abstention/label-error baseline achieves statistically indistinguishable performance on all three metrics (false-unique acceptance, ambiguity rejection, unique-control acceptance), or (2) removing hidden provenance/label alternatives leaves performance unchanged within the predefined equivalence margin. Also kill if no independent annotator agreement can establish the counter-worlds as genuinely non-equivalent.

**Prerequisite evidence before any stronger claim:** a public item schema and paired counter-world construction; independent annotation of admissible interpretations and uniqueness status; frozen baseline prompts; held-out results with uncertainty intervals; and an audit showing the visible artifact is byte-identical across hidden-provenance variants. Until these exist, status remains `benchmark-only`, `new_method_validated=false`, and `novelty_authorization=NONE`.

## Decision

The narrow distinction survives only as a conditional, mechanism-level hypothesis. Generic ambiguity/abstention overlap is substantial; absent the paired hidden-provenance counter-world protocol, reject any broader novelty statement.
