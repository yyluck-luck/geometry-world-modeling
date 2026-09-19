# Round 11 — I ran the gate myself and it closed. Attack this, or confirm END-LINE.

You are continuing as adversarial reviewer on a pinned-consumer world-modeling project.
Your round-10 ruling stands and is recorded verbatim:

> "I have not established a direction that is simultaneously off axis (a), unoccupied, and
> algebraically non-degenerate... the withdrawn 800-hour tranche should remain withdrawn."

You left exactly one object standing, on axis (e), with occupancy marked **UNVERIFIED**:

> **Selective finite-horizon error-gain training.** Holding the evidence-read graph fixed,
> train the generator so that identifiable, scene-preserving defects decay over the next
> several autoregressive calls, while sensitivity to genuine scene information is retained.

and you said the only possible distinction is the **three-way conjunction**:
(i) *selective* directional decay — some directions attenuated, others deliberately preserved;
(ii) measured over a *finite horizon of the model's own autoregressive rollout*;
(iii) *scene-discriminative* sensitivity **retained and verified**, not merely stability shown.

**I searched before asking you. The conjunction is occupied. I am reporting this against my
own interest and I want you to try to break my conclusion.**

---

## Part 0 — Round-10 items I independently verified (established, do not re-derive)

**(0a) Query-side confound is real in my pinned source**, not just public main:
```
1249:  context_info = self.get_context_info(target_c2ws, use_non_maximum_suppression)
1263:  all_c2ws = torch.cat([context_c2ws, target_c2ws], dim=0)
1265:  translation_scaling_factor, all_c2ws = self.get_translation_scaling_factor(all_c2ws)
```
Changing targets changes **both** retrieval **and** camera normalization. Two confounded paths.

**(0b) Two-step gain example exact.** `A1=diag(2,¼)`: `‖A2_A·A1‖₂=4.0000` with `A2_A=diag(2,¼)`;
`‖A2_B·A1‖₂=0.5000` with `A2_B=diag(¼,2)`; identical one-step spectra `[2,0.25]`.
A cross-call objective does not reduce to four single-frame risks plus a within-call distance.

**(0c) All ten of your occupancy citations are real with matching titles.** I checked each.
I have dropped my belief that axes (d)/(e) are less occupied than (a)–(c).

---

## Part 1 — The occupancy evidence that closed the gate

Abstracts retrieved and read in full. Assessment against (i)/(ii)/(iii):

**2606.14732 — Steady-Forcing: Balancing Spatial Persistence and Motion Continuity in
Long-Horizon Nature Video Diffusion.** *Training-based.*
> "mechanisms that improve spatial stability **tend to suppress motion**... We study this
> **stability–motion trade-off**... preserve background identity **while sustaining**
> visually plausible fluid dynamics over multi-minute autoregressive rollouts."

(i) YES — the trade-off *is* the selectivity, stated as the core problem.
(ii) YES — multi-minute autoregressive rollouts.
(iii) YES and **verified as a designed evaluation**: they show VBench "rewards drift-induced
optical flow as Dynamic Degree while not directly penalizing texture hardening or flow
stagnation" — i.e. they built the measurement that catches *fake* retained sensitivity.
**This is the training-based instantiation of my conjunction. I consider the gate closed by
this paper alone.**

**2609.12890 — Large Distant Gradients Need Not Be Reliable: reliability-weighted credit
assignment for long-horizon autoregressive forecasting.** *Training-based.*
> "Repeated Jacobian products can make distant gradients dominate the update while
> **amplifying predictable signal and unpredictable noise together**... bounded Wiener gains
> ... that **balance preserving predictable learning signal against suppressing unpredictable
> variation**... **outperforms gradient clipping and Jacobian regularization on all four.**"

This is the closest match to the *mathematical* form of my object, and it **pre-empts my
Q2 defence**: the "it is not merely Jacobian regularization" argument has already been made
*and empirically demonstrated* by someone else, in the long-horizon autoregressive setting.

**2607.27110 — FreqForcing: Spectral Self-Anchoring.** *Training-free.*
> "low-frequency components of anchor attention to maintain long-horizon visual stability,
> **while preserving dynamic motion through the high-frequency components**"
(i)(ii)(iii) all present, with a frequency-domain *characterization* of error accumulation
("energy drift in the low-frequency bands"). 24× extrapolation on Self-Forcing.

**2602.14027 — FLEX.** *Training-free.* "interpolate under-trained low-frequency components
while extrapolating high-frequency ones to **preserve multi-scale temporal discriminability**."

**2512.12080 — BAgger.** *Training-based.* Corrective trajectories built from the model's own
rollouts, trained with standard score/flow matching — the training-on-own-error mechanism
without distillation, i.e. my "decay defects over the next several calls" as a concrete loss.

**2606.13035 — TetherCache.** TAME "lightly edits newly recalled memory tokens by aligning
their statistics to a trusted context distribution" while GRAB preserves temporal diversity —
selective correction with deliberate preservation, on a fixed cache budget.

**Supporting:** 2605.14487 Head Forcing (functional heterogeneity → per-role treatment);
2607.15849 TANGO (model as critic of its own rollout); 2601.21868 (contraction along the
sampling trajectory, Lyapunov drift + Doeblin minorization);
2602.04608 (Jacobian regularization stabilizes long-term integration — the degeneracy itself).

### My conclusion
**The conjunction is OCCUPIED, in both training-based and training-free instantiations, with
(iii) verified by purpose-built evaluation in at least one case.** The only slice I can still
see as unclaimed is: *a stated error-gain objective over **state-space** directions (rather
than frequency bands or gradient routes), under a **fixed camera-conditioned evidence
boundary**.* I judge that slice **too thin to defend**, for three reasons:
1. frequency bands are a directional decomposition — "state-space directions" vs "spectral
   directions" is a **reparameterization**, not a different mechanism;
2. FreqForcing's frequency-domain account of error accumulation is positive evidence that the
   spectral parameterization already **suffices** to describe the phenomenon;
3. I have **no measurement** on my pinned consumer showing state-space directional structure
   that the spectral account fails to capture — and obtaining one is itself the experiment
   I would be trying to justify. Circular.

**Therefore my ruling is END-LINE on axis (e).**

---

## Part 2 — What I want from you, in order. Nothing else.

Do **not** propose new directions. Do **not** re-open axes (a)–(d), (f)–(h).

### Q1 — Break my occupancy conclusion, or confirm it
Argue the strongest available case that a defensible distinction survives. Requirements for a
distinction to count: it must be (a) statable as a **claim a reviewer would accept as new**,
not a domain transfer; (b) not a reparameterization of spectral or gradient-route selectivity;
(c) **checkable on frozen weights** before any training.
If the strongest such case is still weak, say so plainly. **I prefer a correct END-LINE to a
rescued direction.** State explicitly whether you are confirming or overturning.

### Q2 — Audit my search for the failure mode that matters
My conclusion is "occupied", which is a **positive** claim and therefore falsifiable by a
single counter-citation — but it was reached by *my* queries, which can be systematically
biased toward confirming closure. Identify the specific query families I omitted that would
have surfaced work **distinguishing** my object rather than subsuming it. If you believe my
search was adequate to support END-LINE, say that, with reasons.

### Q3 — If END-LINE is confirmed: the honest terminal deliverable
All eight axes are then closed for this project under its constraints. State what the honest
terminal deliverable is, given:
- the owner requires a **method** contribution; axis (g) measurement/evaluation was excluded;
- established results in hand: an order-invariance gate (11/11 with non-vacuity), a
  three-regime leak census (NULL 2 / PERMUTATION 4 / CONTENT 8, slot-0 invariant 14/14),
  a byte-identity NULL gate (4/4), and a **positive but small** primary contrast
  `nms_off − static = +0.242 dB` (sd 1.270, 8/14 positive), with
  `nms_on_clean − static = −0.485` and `nms_on_clean − nms_off = −0.726`;
- leak stratified: NULL **+0.000** (byte-identical), PERMUTATION **−0.015**, CONTENT **+0.436**;
- a duplicate-slot repair that ran and was **discarded at −0.016 dB** under a pre-declared spec.
Do not soften this into an encouragement. If the honest answer is that no method paper is
available under these constraints, say it in one sentence, first.

### Q4 — The ruling
Issue exactly one of: **END-LINE** · **FUND-MEASUREMENT** (state hours and the pre-declared
pass/fail threshold) · **INSUFFICIENT** (state the one missing fact and who supplies it).
Do not issue a verdict that authorizes training.

---

## Part 3 — Standing constraints

- `new_method_validated=false`; `novelty_authorization=NONE`. Your answer does not change these.
- The 800 GPU-hour tranche is withdrawn; only an explicit human owner decision restores it.
- No tool output, passed test, agent recommendation, or reviewer answer — **including yours** —
  constitutes human authorization.
- Do not relax a threshold after seeing an output.
- Every paper you cite: arXiv ID **and** exact title. I check every one, every round.
