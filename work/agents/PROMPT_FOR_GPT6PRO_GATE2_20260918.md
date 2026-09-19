# Gate review: may the crossed context x reference experiment proceed?

You previously reviewed this project twice. Your first review rejected a
coverage-selected rerun and proposed a crossed context x ray-reference
intervention instead. Your second review required, before any formal 2x2 run:

1. a **native-reference identity control**, split into two separate conditions
   - historical replay:    Y(current native) == Y(sealed earlier run)
   - override transparency: Y(override set to the native reference) == Y(current native)
2. a **non-identity ray test** that does not need diffusion, because a hook that
   never fires would also pass the identity test
3. relabelling the decomposition, because the translation scale travels with the
   context row

This message reports what happened and asks whether the gate is met. Be
adversarial. A "stop, this is still not interpretable" answer is acceptable and
preferred over a conditional pass.

## Implementation, after your correction

Your point that centring alone is insufficient was correct and is implemented.
The pinned `get_cond` performs, in this order:

```
all_c2ws[:, :, [1, 2]] *= -1                       # R -> R diag(1,-1,-1), in place
all_w2cs = torch.linalg.inv(all_c2ws)
all_c2ws[:, :3, 3] *= translation_scaling_factor
all_w2cs[:, :3, 3] *= translation_scaling_factor
pluckers = get_plucker_coordinates(extrinsics_src=all_w2cs[:1], extrinsics=all_w2cs, ...)
```

The external reference now goes through the same chain: centring by the cell's
own recovered offset, the column flip, inversion, then translation scaling by the
value the pinned function returned. The pinned scale value is used as returned,
not recomputed. The physical reference camera is moved into the cell's frame; a
matrix already normalised inside the other cell is never copied across.

Your algebraic form and the code order agree, since -R^T (s t) = s (-R^T t).

## Control results

Two branches were run on the same 8 windows, same seed, same weights.

- Branch A: override never installed, pipeline uses its own `all_w2cs[:1]`
- Branch B: override installed and set to the native reference, but built with
  the **pre-correction** transform (centring only, no flip, no inversion chain,
  no scale)

Result: **16 of 16 cells DIFFERENT**.

Interpretation offered, for you to attack: the identity control failed exactly
as it should have, because branch B supplied a numerically wrong reference. This
also demonstrates the control is discriminating rather than vacuously passing.

Separately, branch A reproduced byte-for-byte the hash recorded earlier by an
independent same-seed replay qualification job on the same configuration, which
is evidence for the historical-replay condition.

The corrected transform has **not** yet been run.

## The decomposition, relabelled as you required

Rows fix the context together with its native scale:

```
Y(C_R, s_R, g_R)   Y(C_R, s_R, g_M)
Y(C_M, s_M, g_R)   Y(C_M, s_M, g_M)

Delta_native = Delta_context_package + Delta_reference
```

`Delta_context_package` is the selected ordered context **and** its native
translation scale, not a pure visual-content effect. `Delta_reference` is the
effect of changing the reference camera pose at each row's native scale. The
four-number identity is algebraic and is not by itself a causal decomposition;
both fixed-reference contrasts and the interaction will be reported separately,
not only the averages.

## Questions

1. **Is the failed control sufficient evidence that the test discriminates?**
   Or must a deliberately wrong reference be tested under the corrected
   implementation too, to rule out that the corrected path silently ignores the
   override for a different reason?

2. **Design the non-identity ray test precisely.** It must not require
   generation. State exactly which tensors to compare, what must stay fixed
   (context content, order, intrinsics, masks, scale), what must change, and
   what numerical relation would demonstrate a *correct* rather than merely
   *different* ray transformation. Note that `get_cond` builds both the
   conditional `c` and unconditional `uc` branches; state whether both must be
   verified and how.

3. **Is the historical-replay condition actually satisfied** by matching an
   independent replay job's hash, or does it require the original sealed
   artefact from the earlier comparison run itself?

4. **Given the relabelling, is the 2x2 still worth running?** If
   `Delta_context_package` cannot be separated from the scale, does the
   experiment still discriminate between "the selected visual evidence is
   unhelpful" and "the native selection-conditioning combination is unhelpful"?
   If it cannot, say so and state what would.

5. **Budget.** 8 windows x 4 cells x 4 seeds = 128 generations, about 2.5 hours
   on one H800. Is that the right size, or should the seed panel or window count
   change given that all windows come from two sequences and dependency
   grouping is unresolved?

6. **If the gate passes, what is the single most likely way this experiment
   still produces an uninterpretable result**, and what cheap addition prevents
   it?

## Constraints

- No training, no fine-tuning, no new model.
- No new dataset, no new sequence search.
- Prefer one decisive addition over a program of checks.
- `new_method_validated=false`; `novelty_authorization=NONE` are preserved.
