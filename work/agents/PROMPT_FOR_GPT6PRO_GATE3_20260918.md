# Gate 3: linkage split, derivation deviation found, ray oracle implemented

Third review. Your ruling was STOP until three conditions are met. This reports
progress on all three and asks whether the gate now moves. Stay adversarial.

## Condition 1: original-output hash linkage — SPLIT RESULT

You required h(A) = h(O) against the original sealed comparison, not merely
h(A) = h(Q) against a later qualification job. Checked directly against the
sealed artefacts of the original run, same seed, per window:

| arm | result |
|---|---|
| baseline context [0,15,30,45] | **8 of 8 byte-identical to the sealed original** |
| native memory arm | **0 of 6 — all differ** |

The baseline match establishes that weights, seeds, sampler, consumer path and
the harness reproduce the original exactly. The failure is localised to how the
memory context is derived.

Reading the original script against the crossover draft found three deviations,
all mine:

| step | original sealed run | crossover draft |
|---|---|---|
| NMS threshold priming query | pose of a **bank** frame (bank[4]) | **target** poses |
| surfel scene construction | **twice**: first 5 frames, then full bank | once, full bank |
| padding a short retrieval | `(retrieved * 4)[:4]` cycling | repeat last element |

The priming deviation is the one I consider most serious: it fed commanded
target poses into the threshold assignment, where the original deliberately used
an in-bank pose. Target poses are declared commands rather than withheld
outcomes, so this is not an outcome leak, but it is a different procedure.

The derivation has been rewritten to match the original step for step and a
re-linkage run is executing. **No formal panel has been launched.**

Question 1a: if the memory arm now matches 6 of 6, is condition 1 satisfied, or
does the earlier deviation require any further disclosure beyond recording it?

Question 1b: the baseline arm already matches. Does a partial linkage permit
anything, or is it all-or-nothing for decomposing the sealed result?

## Condition 3: non-identity ray test — implemented, not yet run

Implemented exactly as you specified, zero diffusion:

- oracle in FP64 computed from raw physical poses, `D = diag(1,-1,-1)`,
  `Q_i = R_i D`, `A_{g,i} = [[Q_g^T Q_i, s Q_g^T (t_i - t_g)],[0,1]]`; the
  centring offset cancels, so the oracle does not reuse the override's recovered
  offset logic
- pixel centres at +0.5, normalised directions, channel order direction then
  moment, moment as `o x d`
- reference B is non-degenerate: 37 degrees about z **and** translation
  (0.20, -0.10, 0.30)
- decisive relation checked from the oracle: `d_b = Q d_a` and
  `m_b = Q m_a + t x (Q d_a)` with `H = E_b E_a^{-1}`
- tolerances predeclared: max direction error <= 1e-5, relative moment error
  <= 1e-5
- checks that the override fires exactly once when installed and zero times when
  disabled
- checks scale is unchanged by the reference choice
- checks both ray injection sites

Question 3a: I can locate the conditional ray fields, but I have not confirmed
the exact key path for the unconditional branch in this pinned checkout. If
`uc` is not a nested dict under the returned `cond`, what is the minimal correct
way to obtain the unconditional conditioning for verification without running
the denoiser?

Question 3b: you asked for verification of the packed guidance input as well.
Is verifying both branches at both injection sites sufficient, or is the packing
step a genuinely separate failure mode worth its own check?

## Condition 2: corrected identity control — pending

Will run through the same external-reference constructor used for non-native
references, with no special case that short-circuits when the ids match.

## Your fifth cell

Accepted in principle: `e = Y(C_M, s_R, g_R)`, giving the ordered-path
decomposition `d - a = (e - a) + (c - e) + (d - c)`, with the bridge implemented
through the normal scale input so all scale-dependent geometry follows it, not
by rescaling moment channels.

Question 5a: implementing `s_R` inside the memory row means passing a scale that
did not come from that row's own `get_translation_scaling_factor` call. Is
overriding the returned scalar the intervention you intended, or should the
centring also move to the baseline row's centre so that the whole normalisation,
not only the scalar, is shared?

Question 5b: you noted target ray maps in `a` and `e` should agree within
tolerance. Should that be a hard gate before spending the panel, i.e. compute it
with zero diffusion and abort if it fails?

## Population disclosure

The eight windows were **not** selected after examining per-window effects; they
are the fixed starts 0, 100, 200, 300 in two sequences, declared before the
original comparison. The original aggregate used additional windows at starts
50, 150, 250, 350 for some arms. So this panel decomposes a **subset** of the
original population.

Question 6: should the panel be extended to the full original window set before
any decomposition claim, or is decomposing the declared subset acceptable if
reported as such?

## Constraints

No training, no new dataset, no new sequence search, no relaxed tolerances after
seeing outputs. `new_method_validated=false`; `novelty_authorization=NONE`.
