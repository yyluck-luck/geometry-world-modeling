# Round 14-C — Is the "reset-semantics audit" reframing occupied?

This is an **occupancy investigation** of one specific reframing. Do not propose new directions,
do not rank, do not issue a funding verdict. Answer with evidence and cite everything.

## The reframing under test

Prior rounds closed every method axis. A diagnostic reframing survived, and its occupancy is the
gate. Stated precisely, the candidate contribution is:

> **Claim.** Released stateful video / world-memory generation systems have *incomplete reset and
> state-isolation semantics*: instance state written on one call path is read on another, and the
> documented reset/initialize path does not clear it. This is a **defect class**, not one bug.
> **Artifact.** A pre-specified static + dynamic audit predicate that detects members of the
> class in a released repository without training and without access to the authors.
> **Evidence.** The audit applied to N released systems, reporting how many exhibit the class,
> with a measured behavioural consequence where the system can be run.

The audit predicate, stated so you can check whether it is already published:
1. an instance attribute is written on one branch/call path;
2. it is read on a different path whose own write is *conditionally guarded* and may not fire;
3. the documented `reset()`/`initialize()`/new-session path does not clear it;
4. the mixed call sequence that triggers (1)→(3) is reachable from the documented public API or
   shipped demo;
5. the resulting behavioural difference is measurable on frozen weights.

## The single most dangerous prior work — read it in full, not the abstract

**arXiv:2607.21686 — "Persistent Computational State: A Session-Centric Runtime for Generative
World Models."** This is the nearest neighbour I know of. It treats request-centric serving
discarding world-model runtime state as a measurable failure and runs recovery experiments on
Cosmos3, WorldMem, and Matrix-Game 2.0.

**Fetch and read the actual paper**, not just the abstract. Determine, with section references:
(a) Does it identify state-handling defects **inside the released model implementations**, or only
    in the **serving/runtime layer around them**? These are different claims.
(b) Does it supply an **audit or detection predicate** others can apply to a new repository, or
    does it supply a **runtime/system design** (checkpoint/restore) that fixes the problem?
(c) Does it examine `reset()`/`initialize()` completeness within the model classes themselves?
(d) Does it report any instance of "attribute written by branch A, read by branch B, not cleared
    by reset" — i.e. the exact predicate above?
If it does all of these, the reframing is occupied and you should say so plainly.

## Other occupancy directions you must check

- **Software-engineering / MLOps literature on state leakage and test isolation in ML code.**
  Search for: flaky tests from shared state, test pollution, global-state bugs in ML libraries,
  static analysis for stale-state reads, non-determinism/reproducibility bug taxonomies in deep
  learning frameworks. This is where an "audit predicate for stale instance state" would most
  likely already exist, possibly outside the ML-venue literature.
- **Empirical bug studies of deep-learning systems.** Papers that mine and taxonomise real bugs in
  ML repositories. Does "incomplete reset / stale instance state" already appear as a named
  category with prevalence numbers? If it does, our claim is a re-instantiation, not a discovery.
- **Reproducibility-audit protocols that were themselves the contribution** — e.g. algorithmic
  unit tests (arXiv:2310.17867), rliable (arXiv:2108.13264). What made those count as artifacts?
- **Anything auditing memory/state in video or world models specifically** beyond the benchmarks
  already known to me: arXiv:2606.20545, arXiv:2606.00793, arXiv:2606.27537.

## Questions

**Q1 — Is the defect-class claim occupied?** Has anyone published the claim that released
stateful generative systems have incomplete reset/state-isolation semantics, as a *class* with
*prevalence* evidence? Give arXiv IDs / DOIs and exact titles, or state that you found none.

**Q2 — Is the audit predicate occupied?** Does an equivalent detection procedure already exist,
in ML venues or in software-engineering venues? Be specific about how close each candidate is.

**Q3 — What is left unoccupied, if anything?** State it as a sentence a reviewer would have to
accept as new. If nothing survives, say so first and plainly.

**Q4 — The strongest objection a reviewer would raise**, assuming the reframing is not occupied.
Not a generic "needs more experiments" — the specific structural objection.

## Output
Write to exactly one new file: `work/agents/CODEX_R14C_RESET_AUDIT_OCCUPANCY_20260919.md`.
Do not modify any existing file. No GPU, no training, no generation.
Every source: arXiv ID / DOI / URL **and** exact title. I check every one.
Mark anything you could not verify as UNVERIFIED. A correct negative is worth more to me than an
encouraging answer.
