# R177 Counter-world benchmark sanity check

## Input

Inspected only the text of `CODEX_R176_FUP_AREJECT_REFINEMENT.md`. No web, project data, code, fixtures, runners, or evaluation were used.

## Concrete failure modes

1. **Non-identifiability / circular oracle.** The protocol calls one hidden-frame or hidden-label world “different” and asks annotators to certify the admissible interpretations. If the visible artifact and certificate are byte-identical, the evaluator has no observable basis to distinguish worlds; “correct rejection” then depends entirely on hidden metadata supplied by the benchmark author. This can turn FUP/AReject into a label-reading task or a circular gold oracle rather than a measurable reasoning ability.

2. **Leakage through certificate surface form.** Changing the hidden mapping may alter certificate wording, IDs, ordering, serialization, or confidence formatting. A model can reject based on these artifacts without detecting genuine ambiguity. Conversely, aggressively normalizing them may erase the only evidence that the two worlds differ.

3. **Impossible control claim.** “Preserve visible bytes and surface semantics” while changing producer-frame convention is not guaranteed: coordinate-frame changes can alter projected geometry, depth interpretation, or downstream labels. Byte identity alone does not establish semantic equivalence or a valid counter-world.

## Repair / rejection rules

- **Reject the protocol as non-identifiable** unless each pair has two independently specified latent worlds, a pre-registered mapping from world state to allowed answer sets, and an adjudication procedure that does not expose the hidden world to the model.
- Add a **leakage audit**: canonicalize IDs, ordering, whitespace, confidence fields, and certificate templates; run a metadata-only classifier. If it predicts the world above the preregistered chance margin, discard the pair.
- Replace “byte-identical implies equivalent” with a two-part control: (a) byte-level identity after canonicalization, and (b) blinded human/independent geometric or semantic audit confirming that only the declared latent convention changes. If either fails, remove the item.
- Require a third **known-unique control** sharing the same certificate surface form and provenance formatting. If rejection rates differ due to formatting alone, do not attribute the effect to FUP/AReject.

## Status

`benchmark-only`, `new_method_validated=false`, `novelty_authorization=NONE`. The paired counter-world idea is currently **not acceptance-ready**; it remains a conditional hypothesis until non-identifiability and leakage controls pass. If those controls cannot be implemented without revealing the latent world or changing observable semantics, apply the kill condition and reject the proposed benchmark distinction.
