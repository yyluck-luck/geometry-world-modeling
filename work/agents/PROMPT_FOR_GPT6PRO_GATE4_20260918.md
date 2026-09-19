# Gate 4: results, not descriptions

Fourth review. You ruled STOP until three controls produce results. This reports
measured outcomes and one finding about the sealed run itself. Stay adversarial.

## Result 1: the denominator question, answered

You asked why six memory cases versus eight baseline. Neither of your three
hypotheses was right.

The sealed comparison contains **14** memory artefacts at seed 42, at window
starts **50, 100, 150, 200, 250, 300, 350** in each of two sequences. There is
**no** sealed memory artefact at start 0: retrieval terminated with a failure
there in the original run, for both sequences.

So my eight-window panel used starts 0, 100, 200, 300, of which start 0 has no
sealed memory endpoint. Six pairs, not because two failed on replay, but because
two never existed.

Consequence adopted: the panel population is now the **original paired
population for this contrast**, starts 50 through 350, 7 starts x 2 sequences =
14 pairs. Start 0 is excluded because it has no sealed memory endpoint.

## Result 2: memory linkage went 0/6 -> 2/6, and the cause is a state leak in
## the sealed run itself

After reproducing the original derivation step for step (bank-pose priming,
двойное scene construction, cycling pad), memory linkage improved from 0/6 to
**2 of 6**. Still not closed.

Diagnosing the remaining four found this, which is a property of the sealed
experiment, not of my harness:

The original iterated `('nms_off', False)` then `('nms_on', True)`. In the pinned
`get_context_info`, the NMS-disabled branch executes

```python
else:
    self.initial_threshold = 1e8
```

and the NMS-enabled branch only assigns `self.initial_threshold` when the
pipeline holds exactly five frames. At full bank size it does not reassign, so
the NMS-on call **inherits 1e8 from the immediately preceding NMS-off call**.

Therefore the sealed "NMS-on" arm did not run under a naturally primed
threshold. It ran under a threshold leaked across arms by call ordering. My
crossover called NMS-on alone and got the primed threshold, hence different
selections.

I have reproduced the original ordering rather than "fixing" it, because the
object being decomposed is the sealed run. A relinkage run is executing.

Question 2a: is reproducing the leak the right call, or does a decomposition of
a run whose treatment arm was contaminated by call ordering have limited value
regardless of linkage?

Question 2b: if linkage now closes at 6/6 or 14/14, does the leak need to be
stated as a limitation of the **original** negative result as well? The reported
-0.729 dB NMS-on deficit was measured under the leaked threshold.

## Result 3: the ray test had exactly the vacuity you predicted

Your warning was correct and specific. My draft computed the decisive relation
`d_b = Q d_a`, `m_b = Q m_a + t x (Q d_a)` by applying it to the **oracle's own**
output, which only confirms the oracle is internally consistent.

Fixed: `Q` and `t` still come from the raw physical reference poses, but the
relation is now applied to the **production** rays. Also fixed: the key path was
`cond['concat']` where the pinned `get_cond` returns sibling `{"c": ..., "uc":
...}`, so the test was reading the wrong object.

Added per your instruction: both branches at both injection sites; non-ray
conditioning (`crossattn`, `replace`, mask channel) asserted unchanged across the
reference choice; and an assertion that the conditional and unconditional packets
are not identical, since identical rays alone could not reveal a branch swap.

Not yet run.

Question 3a: you also asked for the guidance packing check using the worker's
actual guider. Given that the conditional and unconditional ray fields are
intentionally identical here, is asserting `packed[key][:n] == uc[key]` and
`packed[key][n:] == c[key]` on the branch-distinguishing keys sufficient, or is
there a cheaper decisive probe for a swap?

## Still pending, honestly

- corrected native-reference identity control: **not run**
- non-identity ray test: **implemented and corrected, not run**
- memory linkage at the new population: **executing**

## Fifth cell, as you specified

Scalar override only: keep the memory row's centre `mu_M` and its native
`s_M` in the record, supply `s_R` as the effective scale, construct the external
reference with `mu_M` and `s_R`. Your proof that the centre cancels in
`P_g^-1 P_i` is accepted, so no centring change is made.

Target-ray equality between `a` and `e` will be a hard zero-diffusion gate,
checked against the independent oracle as well, aborting the panel on failure.

## The question I most want attacked

Given Result 2, the sealed NMS-on arm was produced under a cross-arm state leak.
Is decomposing that specific arm still the best use of the next generation
budget, or does the leak mean the right move is to re-measure the memory-versus-
baseline contrast cleanly first, at the same population, with per-arm state
isolation, and decompose **that** instead?

Answer that before the packing details.

## Constraints

No training, no new dataset, no relaxed tolerances after seeing outputs.
`new_method_validated=false`; `novelty_authorization=NONE`.
