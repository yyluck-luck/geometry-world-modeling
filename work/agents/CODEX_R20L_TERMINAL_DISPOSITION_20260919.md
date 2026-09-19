# Round 20-L — Terminal disposition (2026-09-19)

**STOP.** The owner still requires a method contribution. The verified record contains no surviving,
validated method direction, and no remaining check would turn the two partial assets below into a
method. No new GPU run, training, weight download, upstream message, or candidate search is justified
under the current scope. This is a terminal disposition, not a claim that the underlying code cannot
be studied in a different project.

Evidence for the stopping condition: the project records `new_method_validated=false` and
`novelty_authorization=NONE` and says the C6 constraint is not relaxed (`RESEARCH_MEMORY.md:2151-2159`);
the proposal alignment says the only implemented intervention did not meet its predeclared threshold
and that all other mechanism candidates were closed (`proposal_alignment_20260919.md:23-36`);
the closeout section explicitly rules out further candidate search, training, and new generation
(`proposal_alignment_20260919.md:151-169`; `RESEARCH_MEMORY.md:1106-1162`).

## Verification boundary

The three pinned VMem copies are byte-identical (SHA-256
`90a45f452a4f734b3371fb526c566162026e5d900e0c8204709dd57f44ef1d7e`). In each copy, the consumer
sequence is `get_context_info(target_c2ws, ...)` at line 1249, concatenation of context and target
cameras at line 1263, and `get_translation_scaling_factor(all_c2ws)` at line 1265. The relevant
source locations are:

- `work/S17C_interface_preparation/isolated_vmem_source/modeling/pipeline.py:1249-1265`
- `work/S17_cpu_preflight/original/modeling/pipeline.py:1249-1265`
- `work/S102_gate0_3dmatch/adapter_v1/sources/vmem_pipeline.py:1249-1265`

A repository-wide assignment search finds `self.c2ws = [c2w]` only at line 180 in all three copies;
the generated camera is appended at line 1297 and removed with the other state lists at line 1360.
There is no setter or retained-frame camera relabelling path in the pinned source. This verifies the
feasibility premise, but feasibility is not a contribution (`.../pipeline.py:180`, `:1297`, `:1360`).

## Q1 — GEN3C upstream disclosure check

### What was searched

The target was the released GEN3C tree at commit
`db2ffe12ced12ddafcec5e0422ee46ce8520746b`, the commit named by the predeclared audit
(`work/S120_lifecycle_audit/E1_SPEC_PREDECLARED_20260919.md:7-14`). On 2026-09-19 I checked the public
GitHub issue/PR search, commit search, the repository history, and NVIDIA security pages. Exact
GitHub REST searches returned zero issue/PR matches for `model_seeded`, `seed_model`, `clear_cache`,
and `model_was_seeded`; exact commit searches returned zero matches for those terms. HTML searches
covered the stale-seeding and admission variants below. The query URLs are:

- <https://api.github.com/search/issues?q=repo%3Anv-tlabs%2FGEN3C%20model_seeded>
- <https://api.github.com/search/issues?q=repo%3Anv-tlabs%2FGEN3C%20seed_model>
- <https://api.github.com/search/issues?q=repo%3Anv-tlabs%2FGEN3C%20clear_cache>
- <https://api.github.com/search/issues?q=repo%3Anv-tlabs%2FGEN3C%20model_was_seeded>
- <https://api.github.com/search/commits?q=repo%3Anv-tlabs%2FGEN3C%20model_seeded>
- <https://api.github.com/search/commits?q=repo%3Anv-tlabs%2FGEN3C%20seed_model>
- <https://api.github.com/search/commits?q=repo%3Anv-tlabs%2FGEN3C%20clear_cache>
- <https://api.github.com/search/commits?q=repo%3Anv-tlabs%2FGEN3C%20model_was_seeded>
- <https://api.github.com/search/commits?q=repo%3Anv-tlabs%2FGEN3C%20request-inference>

HTML searches for `stale seeding`, `failed seed`, `admission`, `after failed`, `cache reset`, and
`model_was_seeded` also returned “No results” in the GEN3C issue pages; representative query URLs are
<https://github.com/nv-tlabs/GEN3C/issues?q=is%3Aissue+is%3Apr+%22model_seeded%22> and
<https://github.com/nv-tlabs/GEN3C/issues?q=is%3Aissue+is%3Apr+%22stale-seeding%22>. For
`request-inference`, the issue/PR search returned only PR #62 and an unrelated OOM issue
(#9), and the exact commit search returned zero; neither is a stale-seeding report. See <https://github.com/nv-tlabs/GEN3C/issues/9> and
<https://github.com/nv-tlabs/GEN3C/pull/62>.

The only relevant public PR/commit finding is the unauthenticated pickle-deserialization fix. PR #62
says that `/request-inference` and `/seed-model` accepted unsafe pickle bodies and records coordinated
reporting to NVIDIA PSIRT; it does not mention stale seeding or admission after a failed seed
(<https://github.com/nv-tlabs/GEN3C/pull/62#L208-L231>). NVIDIA's fix was merged as PR #63 and commit
`db2ffe12ced12ddafcec5e0422ee46ce8520746b`; the public diff is about serialization and API debug
support, not `model_seeded`, `clear_cache`, or the cache lifecycle
(<https://github.com/nv-tlabs/GEN3C/pull/63>, <https://github.com/nv-tlabs/GEN3C/commit/db2ffe12ced12ddafcec5e0422ee46ce8520746b>).

No GEN3C-specific stale-seeding advisory surfaced on the NVIDIA security bulletin page or archive
searched on this date: <https://www.nvidia.com/en-us/security-test/> and
<https://www.nvidia.com/en-us/security/archive/>. This is a negative result about publicly indexed
material, not proof that no private discussion exists. **UNVERIFIED:** GitHub indexing and public
advisory pages can lag or omit private reports.

### What the released code actually says

The static path is real and narrowly scoped. At the pinned commit, `InferenceModel.__init__` sets
`model_seeded = False` and `request_inference` checks that flag before admitting a task
(<https://github.com/nv-tlabs/GEN3C/blob/db2ffe12ced12ddafcec5e0422ee46ce8520746b/gui/api/server_base.py#L59-L60>,
<https://github.com/nv-tlabs/GEN3C/blob/db2ffe12ced12ddafcec5e0422ee46ce8520746b/gui/api/server_base.py#L121-L131>). `CosmosBaseModel.seed_model` clears the model cache and histories, calls the seeding
method, and sets the outer flag only after the call returns
(<https://github.com/nv-tlabs/GEN3C/blob/db2ffe12ced12ddafcec5e0422ee46ce8520746b/gui/api/server_cosmos_base.py#L46-L71>).
A multi-frame seed without depth or mask raises before success
(<https://github.com/nv-tlabs/GEN3C/blob/db2ffe12ced12ddafcec5e0422ee46ce8520746b/cosmos_predict1/diffusion/inference/gen3c_persistent.py#L206-L210>),
while the model's `clear_cache()` sets `cache=None` and `model_was_seeded=False`
(<https://github.com/nv-tlabs/GEN3C/blob/db2ffe12ced12ddafcec5e0422ee46ce8520746b/cosmos_predict1/diffusion/inference/gen3c_persistent.py#L551-L553>).
The HTTP seed route catches a seed exception and returns an error response
(<https://github.com/nv-tlabs/GEN3C/blob/db2ffe12ced12ddafcec5e0422ee46ce8520746b/gui/api/server.py#L165-L172>).

The source path therefore supports a **static server-contract oracle**: a successful seed followed
by a failed seed can leave the outer admission flag true while the inner cache is cleared
(`work/S120_lifecycle_audit/E1_SPEC_PREDECLARED_20260919.md:16-33`). This is not an executed runtime
result: the sealed zero-GPU stub specification was later judged insufficient for a downstream
consequence and should not be treated as frozen-weight evidence
(`work/agents/CODEX_R16H_E1_SPEC_REVIEW_20260919.md:11-17`, `:43-70`, `:248-259`). It does **not**
support a frozen-weight generation consequence; the original specification explicitly excludes
weights, video generation, and image-quality claims (`work/S120_lifecycle_audit/E1_SPEC_PREDECLARED_20260919.md:84-98`).
The current accepted scope is `gpu_count == 1` and `model_name` in `{cosmos, cosmos-predict1}`
(`RESEARCH_MEMORY.md:1980-1985`).

### Does responsible disclosure plausibly arise?

Conditionally, yes, but no mandatory security classification is established. If an unauthenticated
or remotely reachable deployment can trigger the failed-seed sequence and produce material
availability, integrity, or isolation impact, private maintainer/PSIRT disclosure before public
technical detail is conventional. NVIDIA's PSIRT policy describes coordinated vulnerability
handling and private reporting (<https://www.nvidia.com/en-us/security/psirt-policies/>); the existing
GEN3C pickle-RCE PR is a concrete example of that practice
(<https://github.com/nv-tlabs/GEN3C/pull/62#L208-L231>). The present GEN3C finding is static and
unexecuted, with no demonstrated privilege escalation, data disclosure, or frozen-weight output
impact; calling it a security vulnerability would therefore be **UNVERIFIED**. It is presently more
responsible to call it a possible robustness/admission defect and seek owner guidance. Outbound
messages are not authorized by the repository rules (`AGENTS.md:15`), so no issue or PSIRT report was
sent.

## Q2 — Why the two assets cannot be assembled into a complete claim

The pairing is not a legitimate method result. GEN3C supplies a defensible public admission
invariant and a cross-layer monotone-latch/static-resource mismatch, but no measured frozen-weight
consequence. VMem supplies a real stale read and a measured `nms_on_clean − nms_on(leaked) = +0.245`
dB (SD 0.711; 6/14) but no defensible public oracle that the compared states should be equivalent.
These are the project’s own final asset boundaries (`RESEARCH_MEMORY.md:2048-2057` and `:2151-2157`);
the measured VMem contrast and its estimand are also in the result ledger
(`docs/RETRIEVAL_ARMS_RESULT_20260918.md:40-47`, `:87-99`).

Logically, `(oracle, no consequence)` plus `(consequence, no oracle)` is not
`(oracle and consequence)` for either system. The experiments have different consumers, state
owners, public contracts, and intervention sequences. A VMem measurement cannot validate GEN3C's
cache-admission path; a GEN3C admission oracle cannot retroactively turn VMem's harness-defined
clean arm into a public metamorphic relation. Treating the union as one defect class would be the
same occupancy error the four-tuple was introduced to prevent: a writer on call A, public sequence
A→B, exact consumer on B, and a dominance check must all belong to the same case
(`RESEARCH_MEMORY.md:2020-2031`). A paired document is legitimate only as a clearly labelled audit or
worked-example report. It cannot be presented as a method, a general stale-state prevalence claim,
or evidence that stale state causes quality loss across world models (`RESEARCH_MEMORY.md:2033-2046`).

## Q3 — Decision-value ranking

The ranking below is conditional on the current method requirement. Costs marked **UNVERIFIED** are
planning estimates, not measured budgets.

### 1. (e) Owner decision to relax the method-contribution requirement

This is the only item that changes the terminal disposition immediately. It would make available a
finite-panel audit/case-study deliverable containing: the four-tuple procedure; the VMem measured
worked example with its oracle limitation; the GEN3C static server-contract case with its missing
consequence; the negative duplicate-slot intervention; and the explicit prevalence boundary. Those
assets are already documented (`RESEARCH_MEMORY.md:2048-2057`; `docs/report/TECHNICAL_REPORT_20260918.md:1-21,
542-547`). It would **not** unlock a new method, a prevalence estimate, or a causal claim joining
GEN3C to VMem. Cost: one owner/supervisor scope decision and no new compute. This is a conditional
route only; the owner has not made that decision.

### 2. (b) Owner-supplied, genuinely pre-registered public relation R for VMem

If the owner supplies a public contract or relation R before a new test, and the test compares that
relation on the released call sequence, it could repair VMem's missing oracle. It would not make the
existing `+0.245 dB` result retroactively valid, and it would still be a measurement/defect case,
not a method. The relation must be stronger than the rejected inference from `initialize()`,
`reset()`, or “Choose New Image” (`RESEARCH_MEMORY.md:2106-2127`); the rejected candidate is recorded
as `NO-DEFENSIBLE-ORACLE` (`RESEARCH_MEMORY.md:2106-2157`). **UNVERIFIED cost estimate:** approximately
10–40 H800 GPU-hours for a clean public-sequence rerun plus independent recomputation, assuming the
relation and data contract are already available; this is the planning range, not a measurement
(`work/agents/CODEX_R14D_SECOND_CONSUMER_FEASIBILITY_20260919.md:112-121`), and no such budget is authorized
(`RESEARCH_MEMORY.md:2131-2138`, `:2159`). It would unlock a VMem oracle test, not a method contribution.

### 3. (a) Measured frozen-weight consequence for GEN3C

A real frozen-weight run could show whether the failed-seed admission state produces a downstream
inference failure, empty-cache output, or quality change. The zero-GPU E1 stub would only measure the
server contract, not this requested consequence (`work/S120_lifecycle_audit/E1_SPEC_PREDECLARED_20260919.md:42-49,
:84-98`). **UNVERIFIED cost estimate:** roughly 10–40 H800 GPU-hours including loading, failure-path
controls, and independent reruns; weights and deployment access would be prerequisites. The planning
range is recorded as 10–40 GPU-hours, not a measurement (`work/agents/CODEX_R14D_SECOND_CONSUMER_FEASIBILITY_20260919.md:112-121`).
It would complete GEN3C's consequence column only. It would not repair VMem's missing oracle and would not
become a method by itself.

### 4. (c) Independent second auditor re-deriving the four-tuple

A second auditor would materially improve confidence in the audit record and could catch another
false positive, as happened when CausVid was reclassified. It would not create an oracle, a measured
GEN3C consequence, or a method. **UNVERIFIED cost estimate:** roughly 2–5 person-days of read-only
source review and ledger reconciliation, with no GPU; this is an UNVERIFIED estimate made for this
review, not a recorded budget. It is valuable quality control but does not fill either scientific gap while the owner insists on a method.

### 5. (d) Upstream maintainer confirmation

A maintainer statement could clarify whether a relation is an intended public contract or whether the
GEN3C admission behavior is considered a bug. It cannot supply the missing measured consequence and
cannot make two consumers one method. It is also outside the current authorization: no maintainer
contact has been made and outbound messages are forbidden (`AGENTS.md:15`).
**UNVERIFIED cost estimate:** no GPU but an unpredictable response delay of days to weeks. A non-response
would unlock nothing; a reply that merely acknowledges the code would still not validate behavior.

## Q4 — Terminal ruling

**STOP.** No specific next artifact changes the picture under the stated scope. The only conditional
future is a human C6 decision to accept an audit/measurement deliverable; that decision has not been
made, and it would not turn the work into a method. Until then, preserve the existing negative and
partial results exactly as recorded: no method validated, no novelty authorized, no prevalence claim,
and no further GPU work (`RESEARCH_MEMORY.md:1110-1162`, `:2033-2057`, `:2151-2159`; `AGENTS.md:45`).

## Q5 — What this project should tell its supervisor

The project audited context selection and lifecycle state in released, frozen world-model code. It
established a VMem stale read with a measured `+0.245 dB` clean-versus-leaked contrast on a finite,
exposed 14-window panel, but the public oracle needed to call that contrast a defect was not found;
it established a GEN3C server-admission/latch mismatch in released code, but did not measure a
frozen-weight downstream consequence. The audit four-tuple survived adversarial rechecking and
reclassified CausVid; the constructor-equivalence oracle, the cross-layer near-name oracle, the
successor-implementation declaration, the “Choose New Image” oracle, and the zero-GPU retrieval-set
assumption were retracted (`RESEARCH_MEMORY.md:2005-2057`, `:2106-2157`). The convenience
panel is not a prevalence sample, the frozen-weight measured-HIT count is 0/20, and no method has
been validated (`RESEARCH_MEMORY.md:1987-2003`; `docs/report/TECHNICAL_REPORT_20260918.md:542-547`).
The unresolved items are a genuine public R for VMem, a frozen-weight GEN3C consequence, and any
maintainer confirmation; under the unchanged method-contribution requirement, the recorded terminal disposition is STOP.

## Sources checked

- Project rules and authorization: `AGENTS.md:15,43-45`; `RESEARCH_PRINCIPLES.md` (research evidence and
  scope rules).
- Current state and corrections: `RESEARCH_MEMORY.md:1987-2057`, `:2106-2187`.
- VMem result ledger: `docs/RETRIEVAL_ARMS_RESULT_20260918.md:40-47`, `:62-113`.
- Technical report and governance flags: `docs/report/TECHNICAL_REPORT_20260918.md:1-21`, `:497-547`.
- GEN3C predeclared scope: `work/S120_lifecycle_audit/E1_SPEC_PREDECLARED_20260919.md:7-33`, `:84-104`.
- Public GEN3C source at commit `db2ffe12ced12ddafcec5e0422ee46ce8520746b`: `server_base.py:59-60,121-131`,
  `server_cosmos_base.py:46-71`, `gen3c_persistent.py:206-210,551-553`, `server.py:165-172`.
- Public disclosure practice: <https://github.com/nv-tlabs/GEN3C/pull/62>,
  <https://github.com/nv-tlabs/GEN3C/pull/63>,
  <https://www.nvidia.com/en-us/security/psirt-policies/>,
  <https://www.nvidia.com/en-us/security/report-vulnerability/>.
