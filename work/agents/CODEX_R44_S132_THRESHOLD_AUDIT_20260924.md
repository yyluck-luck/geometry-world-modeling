# R44 S132 threshold audit: RCA/BRD CPU contract

Date: 2026-09-24 (Asia/Shanghai)  
Scope: adversarial audit of the S132 design and the R43 thresholds; no GPU, Slurm,
adapter, model execution, or validation-flag change.  
Status remains `new_method_validated=false`; `novelty_authorization=NONE`.

## Decision

**Reject the four R43 numbers as evidence-grade acceptance thresholds in their current form.**
They are usable as explicitly labelled *pilot screening rules* after denominator and metric
definitions are repaired, but none of them can support a population-level method claim with only
eight episodes. The S132 schema also sets `future_scoring_permitted=false`, so the third-camera
threshold cannot be evaluated in S132 itself. It belongs to a later, separately authorized
post-contract pilot.

The revised policy is:

1. keep exact integer counts and confidence intervals in the CPU routing audit;
2. treat the eight-episode numbers as feasibility screens, never validation evidence;
3. use exact/hash conservation for state packets rather than an unsupported absolute tolerance;
4. move all future-camera gain thresholds behind S132 prerequisites and require a paired effect
   estimate with a predeclared practical margin.

## What S132 currently freezes

The S132 design is a contract-only artifact. It freezes eight episode roles, four RCA labels per
episode, a 32-case intention-to-treat routing denominator, immutable evidence, independent masks,
future-query sealing, and a `future_scoring_permitted=false` schema constant. It explicitly says a
CPU pass proves contract arithmetic, provenance, and mask behavior only. These facts limit what a
threshold can mean: the pass may falsify routing/provenance mechanics, but cannot validate generated
RGB/depth quality or a novel world-model mechanism.

## Adversarial audit of the four thresholds

### 1. Scene-route recall `>= 0.75`

With one `scene_surface` case per episode, eight episodes give `n=8`. The R43 rule is exactly
`6/8`, so it is a convenient count, not a measured effect-size or a justified operating point. A
two-sided 95% Clopper–Pearson interval for 6/8 is approximately `[0.349, 0.968]`; its lower bound is
far below 0.75. Even 8/8 episodes would have a lower bound of only about 0.631. To have a 95% exact
lower bound above 0.75 with all episodes correct requires at least 13 independent scene cases.

**Revision.** Keep `6/8` only as a *development stop screen* and report the exact count plus a
Clopper–Pearson interval. For a claim that true scene-route recall is at least 0.75, expand the
number of independent scene cases (at least 13 all-correct cases for the stated exact bound) or
state that the result is exploratory. Do not call 6/8 validation.

### 2. False scene-write rate `<= 0.10`

The S132 text says the full routing denominator is 32 cases, but a false scene write is defined on
non-scene cases. The denominator must therefore be explicit: eight episodes × three non-scene
labels (`camera_gauge`, `transient_sensor`, `depth_corruption`) = **24**, excluding true reveals.
The R43 number `0.10` is not an integer rule on this denominator: `2/24=0.0833` passes and
`3/24=0.125` fails. With two false writes, the exact 95% upper bound is about 0.270; even zero
false writes in 24 cases has an upper bound about 0.142. Thus this sample cannot establish a true
false-write rate of 0.10 at 95% confidence.

**Revision.** Report `k/24` and its exact interval. For an exploratory S132 screen, use the
predeclared integer rule `k <= 2`, explicitly labelled as a stop rule rather than a rate claim. If
the project needs a 95% upper bound of 0.10, collect at least 36 non-scene cases and require zero
false writes (or increase the denominator and predeclare an equivalent binomial rule). Fix this
denominator in the contract before scoring; never use the 32-case all-label denominator for a
false-positive estimand.

### 3. Outside-support change `<= 1e-6`

The value `1e-6` has no S132 calibration, scale convention, or representation justification. An
absolute threshold is unit-dependent and can be too loose for normalized logits or too strict for
metric-depth values. Existing project tolerances are context-specific and combine absolute and
relative terms; they do not justify importing `1e-6` here. The phrase “exact identity where the
representation permits it” in R43 is the stronger requirement and should be primary.

**Revision.** For immutable evidence, measured regions, and untouched hidden-state packets, require
byte-level serialized hash equality outside the support and report the changed-element count. For a
representation that cannot provide byte identity, first run deterministic replay controls, estimate
the 99th-percentile numerical drift in the same units, and freeze
`tau_out = max(replay_q99, declared machine floor)` before method scoring. Report both absolute and
relative drift; do not silently substitute `1e-6`. Any nonzero change in an immutable packet is a
contract failure even when it is below a numeric tolerance.

### 4. Third-camera gain on at least `6/8` episodes

This threshold is not evaluable in S132 because `future_scoring_permitted` is fixed to `false` and
the design requires future references to remain sealed until arm hashes are committed. It is also
statistically weak as a post-contract method gate: under a no-effect sign null, observing at least
6 positive paired episodes out of 8 has one-sided binomial probability about 0.145. A 6/8 sign count
therefore does not reject no effect at the usual 0.05 level, even before accounting for metric choice,
camera multiplicity, or adaptive episode selection.

**Revision.** Retain `6/8` only as a post-contract feasibility screen, never as evidence of a
third-camera benefit. For promotion, predeclare the paired estimand (for example, a
difference-in-differences geometry/depth error in a fixed support), a practical margin derived from
append-only replay noise, and a paired confidence or randomization interval. A simple sign-only
screen should be at least `7/8` for a one-sided 0.05 binomial screen, but it still requires an
effect-size interval and does not replace it. No third-camera number may be scored before S132
prerequisites and owner review are complete.

## BRD-specific consequence

S132 has no BRD numerical threshold, which is appropriate for a contract-only artifact. BRD should
not inherit RCA's scene-recall or false-write numbers: its primary estimand is a paired positive vs
negative reveal effect on ghost-surface precision/recall and future-query depth. Before any BRD
pilot, freeze the support denominator, measured-region drift rule, and an effect-size margin against
append-only and generic-completion controls. If those margins cannot be set from replay variance and
task utility before opening future RGB-D references, mark BRD `UNTESTABLE_SUPPORT` rather than invent
a percentage.

## Revised threshold sheet (what may be used next)

| Item | R43 number | R44 disposition |
|---|---:|---|
| RCA scene recall | `>=0.75` (6/8) | Pilot screen only: `>=6/8`; report exact interval; claim-level target requires more cases (13 all-correct for 95% lower bound >0.75) |
| RCA false scene writes | `<=0.10` | Define denominator as 24 non-scene cases; pilot screen `k<=2`; claim-level 95% upper bound needs at least 36 non-scene cases with 0 errors |
| Outside-support state | `<=1e-6` | Replace with exact hash equality for immutable/untouched packets; otherwise replay-calibrated absolute+relative tolerance |
| Third-camera gain | `>=6/8` | Not allowed in S132; later pilot screen only; promotion requires paired effect size, practical margin, and interval; sign-only screen `>=7/8` |

## Stop decision

Do not edit validation flags or authorize a GPU pilot from these thresholds. Repair the S132
denominator/metric language, run only schema/hash/self-consistency checks after the listed
prerequisites, and keep future-camera scoring blocked. If owner review rejects the revised
denominator or no independent replay noise floor can be measured, stop with
`BLOCKED_OWNER_REVIEW` or `UNTESTABLE_SUPPORT`; do not tune thresholds after seeing outcomes.

The R43 ranking remains unchanged (RCA primary, BRD secondary, CGLR/CRR evaluation operator), but
the numeric gates are now explicitly feasibility screens rather than evidence for novelty or model
quality.

