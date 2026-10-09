# R172 Minimum Action-Required Package for Branch-A Readiness

**Access date:** 2026-09-24  
**Evidence boundary:** R171 Branch-B handoff, R170 local audit, and the current local ledger only. No SSH, broader search, protected data, code/fixture/runner execution, GPU, Slurm, evaluation replay, receipt, or flag mutation.

## Current blocker

R171/R170 select Branch B: local evidence contains only drafts/proposals and no signed owner/reviewer packet or instantiated P2/P3/P4 evidence. The smallest external delivery that could permit a Branch-A readiness audit is the package below. Delivery alone does not authorize benchmark execution.

## Minimum externally supplied package

### 1. Signed packet cover and index

One signed cover object must include:

- `packet_id`, revision, creation time, and packet content SHA-256;
- named owner, named independent reviewer, and their signatures/IDs;
- explicit scope `synthetic_only` and exclusion of protected data, current R140 runner paths, GPU/Slurm, receipts, and flags;
- owner decision token `READY_FOR_SEPARATE_BENCHMARK_CONSTRUCTION` or an explicit failed stop branch;
- an index of the P2, P3, P4 objects and every referenced manifest/hash;
- a statement that all R164 checklist fields were reviewed, with unresolved fields listed rather than assumed PASS.

### 2. Instantiated P2 metadata-audit object

Deliver the R162 P2 schema as an actual instance, not a template, with:

- real public-manifest and oracle-manifest SHA-256 values;
- a complete surface inventory for paths, filenames, map headers, source metadata, logs, exceptions, outputs, and hash conventions;
- retained evidence hash for every surface and `oracle_fields_absent=true` where required;
- auditor ID, independent reviewer ID, review timestamp, review digest, and result;
- fixed stop branch `LEAKAGE_STOP`.

The referenced public manifest and oracle manifest must be supplied separately and preserve the public/oracle split; a P2 JSON containing placeholders is insufficient.

### 3. Instantiated P3 chronology/access object

Deliver the R162 P3 schema as an actual instance, with:

- real oracle/scorer/reviewer custodian IDs;
- real oracle commit, scorer config, and prediction-seal hashes;
- raw ordered events with event IDs, actor roles, event types, object hashes, UTC timestamps, oracle-access values, and evidence hashes;
- chronology satisfying `oracle_commit < scorer_freeze < prediction_seal < oracle_release`;
- reviewer checks for pre-seal oracle inaccessibility, release order, no post-release regeneration, and monotonic chronology;
- reviewer ID/timestamp/digest and fixed stop branch `HIDDEN_LABEL_CUSTODY_STOP`.

### 4. Instantiated P4 trusted-wrapper/oracle object

Deliver the R162 P4 schema as an actual instance, with:

- trusted-wrapper source SHA-256 and revision;
- transform-spec SHA-256;
- oracle-manifest SHA-256 and pre-call commit SHA-256 with UTC commit time;
- producer call ID;
- real hidden `h` values, fixed hypothesis set `H`, and four disjoint strata;
- `producer_declared_tag_role=comparator_only`;
- reviewer checks for wrapper/source match, oracle commit before producer call, producer tag independence, and scorer pre-seal isolation;
- reviewer ID/timestamp/digest and fixed stop branch `ORACLE_INDEPENDENCE_STOP`.

### 5. Cross-object integrity evidence

The package must include a checksum/index record binding the cover, public manifest, oracle manifest, P2, P3, P4, wrapper/transform sources, and reviewer digests. Hashes must be recomputed by the incoming reviewer during the readiness audit; a sender-provided hash list alone is not acceptance evidence.

## Branch-A acceptance criteria

Branch A may be selected only after a fresh local audit confirms all of the following:

1. Every package path exists and hashes match the signed cover/index.
2. P2/P3/P4 are instantiated objects with real values, not `string`, `sha256`, `rfc3339`, or unchecked placeholders.
3. Owner and independent reviewer identities/signatures are present and independent custody chronology is valid.
4. Public artifacts contain no frame label, stratum, units/schema truth, or label-bearing metadata.
5. P3 event order and no-preseal-access checks pass.
6. P4 oracle truth is wrapper-generated before the producer call and producer self-description is comparator-only.
7. All remaining R164 fields—source pinning, map immutability, held-out asymmetric geometry, scorer freeze, four strata, fixed denominators, uncertainty, and rerun plan—have evidence references and no unknown hard stops.
8. The owner explicitly signs `READY_FOR_SEPARATE_BENCHMARK_CONSTRUCTION`; this is a readiness state only.

Only after these checks may the coordinator perform the documented Branch-A readiness audit and assign its one bounded Innovation Agent packet-only adversarial review. No fixture/runner/scorer implementation or benchmark execution follows automatically.

## Stop conditions

- Missing cover/signature/index or any package object => `NOT_READY_OWNER_PACKET`.
- P2 absent, incomplete, hash mismatch, or public metadata leak => `LEAKAGE_STOP`.
- P3 absent, chronology violation, missing access log, or pre-seal oracle access => `HIDDEN_LABEL_CUSTODY_STOP`.
- P4 absent, missing wrapper/pre-call evidence, or oracle dependence on producer tag => `ORACLE_INDEPENDENCE_STOP`.
- Unknown producer API, frame tag, depth units, schema, or source revision => `NOT_READY_SOURCE_PINNING`.
- Map hash/call-count or branch regeneration failure => `MAP_IMMUTABILITY_STOP`.
- Held-out geometry/split or denominator failure => `GEOMETRY_SPLIT_STOP`, `ESTIMAND_STOP`, or `STRATUM_STOP`.
- Scorer/tolerance/query mutation after freeze => `SCORER_FREEZE_STOP`.
- Independent rerun disagreement => `RERUN_STOP`.

## Unrelated historical packets

- `work/agents/CODEX_R162_MISSING_SCHEMA_PROPOSAL.md` and `work/agents/CODEX_R164_FINAL_PACKET_DRAFT.md` are the current schema proposal and final draft, but both contain placeholders/draft text and no signed instantiated evidence; they are not external packet arrival.
- Older owner/H2/schema artifacts for other historical candidates (for example the R91–R99 CGLR/H2 sequence) do not define the P2/P3/P4 benchmark objects and cannot satisfy this request.
- R168/R170 are handoff and local-audit records, not owner/reviewer authorization.

## Branch-B continuation if package is absent or incomplete

Remain at `NOT_READY_OWNER_PACKET`; wait for the exact package above. Do not assign the Branch-A Innovation Agent, do not search remotely, and do not create or execute benchmark artifacts. Preserve method END-LINE, `new_method_validated=false`, and `novelty_authorization=NONE`.
