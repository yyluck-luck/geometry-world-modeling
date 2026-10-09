# R156 Packet-Adversarial Check of R154

**Access date:** 2026-09-24  
**Allowed evidence:** R154 and its cited-source boundary only. No broader search, code/data/fixture/runner execution, GPU, Slurm, evaluation replay, receipt, or flag mutation was used.

## Finding

R154 is directionally sound, but four requirements can still make `FUP`/`AReject` look identifiable while hidden-label custody is not actually demonstrated. The fixes below are protocol evidence requirements; they do not authorize implementation or execution.

## Fix 1 — Separate the oracle manifest from all scorer-visible artifacts

R154 asks the manifest to bind frame labels, units, schema, and map metadata while also requiring hidden labels. If the scorer receives frame metadata, filenames, map headers, source paths, or deterministic hashes that encode the label, the hidden-label rule is circular.

**Required fix:** create two pre-committed manifests:

- **Public manifest:** anonymized case ID, producer revision, visible geometry/camera inputs, map hash, dimensions, and scorer inputs; no frame tag, hidden category, label-bearing path, or label-derived metadata.
- **Oracle manifest:** hidden `h`, declared hypothesis set `H`, units/schema truth, and out-of-hypothesis category, held by an independent custodian and sealed before scorer release.

Map metadata exposed to the scorer must be sanitized or split so that frame/unit/schema truth cannot be read from headers, filenames, exceptions, or hash conventions. A reviewer must verify that a public-map hash remains identical without revealing oracle fields.

**Stop:** any public artifact deterministically reveals `h` or its category => `LEAKAGE_STOP`.

## Fix 2 — Make hidden-label custody auditable rather than asserted

R154 says the scorer cannot access hidden labels until predictions are sealed, but that is not independently verifiable by a checklist tick alone.

**Required fix:** pre-register a two-custodian procedure. The oracle custodian commits the encrypted/opaque oracle manifest and its hash before scorer freeze; the scorer custodian receives only the public manifest and submits a prediction hash. Release of the oracle occurs only after prediction sealing. Preserve access logs, commit times, and hash comparisons for independent review.

The independent reviewer checks that predictions, scorer configuration, and public artifacts were committed before oracle release, and that no scorer output was regenerated after label reveal.

**Stop:** missing commit order, access log, or independent custody => `HIDDEN_LABEL_CUSTODY_STOP`.

## Fix 3 — Stratify the conditioning population

R154 defines FUP over a mixture of wrong, undocumented, and out-of-hypothesis frames. These are different causes and can have different denominators. A single aggregate can hide a denominator change or make an apparent reduction in false certification non-identifiable.

**Required fix:** pre-register disjoint oracle strata and report each separately:

- `in_H_correct`: true frame is in `H` and declared correctly;
- `in_H_misdeclared`: true frame is in `H` but declaration is wrong;
- `out_H_canonical`: true frame is outside `H` with a known canonical/common frame;
- `out_H_unknown`: true frame is intentionally undocumented but generator truth remains known.

Report `FUP_s` and `AReject_s` for each stratum, with case counts, numerators, exclusions, and confidence intervals. An aggregate may be secondary only after all strata are shown.

**Stop:** mixed or outcome-dependent strata, undefined category membership, or changing denominators => `STRATUM_STOP`.

## Fix 4 — Decouple the oracle from producer self-description and rerun evidence

R154 requires source-pinned producer output semantics. If the same producer declaration supplies both the visible frame tag and hidden `h`, the benchmark can certify its own documentation rather than test false certification. Likewise, an independent rerun that receives source hashes or map hashes may infer labels from deterministic producer details.

**Required fix:** generate `h` and out-of-hypothesis status from a trusted synthetic wrapper or controlled transform whose label is committed before the producer call; treat producer-declared tags as a visible input or separate comparator, never as oracle truth. The reviewer reruns from public manifests only and receives oracle labels after sealing; any deterministic source detail that can reveal `h` is withheld until then.

**Stop:** hidden truth derived from scorer-visible producer self-description, or reviewer can infer `h` before sealing => `ORACLE_INDEPENDENCE_STOP`.

## Disposition

With these four fixes, FUP/AReject can remain conditional estimands for a separately authorized synthetic-only benchmark. Without them, R154's checklist is vulnerable to circular labels, metadata leakage, and mixed denominators, so no identifiability claim is valid.

Keep method END-LINE and preserve `new_method_validated=false` and `novelty_authorization=NONE`. Do not implement or execute the packet in the current research line.
