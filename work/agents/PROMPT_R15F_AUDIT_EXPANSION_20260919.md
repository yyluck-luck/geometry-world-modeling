# Round 15-F — Expand the zero-GPU audit. Get M/N up, honestly.

This is a **survey expansion**, not a novelty review. A prior round audited ~10 systems under a
fixed predicate and found 2 HIT, 1 NEAR, 6 CLEAN, plus exclusions. Your job is to extend that
population **without weakening the predicate**.

## The predicate — fixed, do not modify it to fit what you find

A repository exhibits the defect class if **all five** hold:
1. an instance attribute is written on one branch or call path;
2. it is read on a different path whose own write is conditionally guarded and may not fire;
3. the documented `reset()` / `initialize()` / new-session path does not clear it;
4. the triggering mixed call sequence is reachable from the documented public API or shipped demo;
5. the behavioural difference would be measurable on frozen weights.

Conditions 1–4 are static. **Report 1–4 only. Mark 5 UNVERIFIED for everything — no GPU this round.**
Verdicts: **HIT** (1–4 hold) · **NEAR** (say which fail) · **CLEAN** (state handling complete —
a real, reportable, valuable result) · **OUT-OF-PREDICATE** (stateless across public calls, or
out of scope) · **NOT-INSPECTED** (could not fetch — say so rather than guessing).

## Already audited — do NOT redo these, build on them

HIT: VMem `39291e4f`; GEN3C `db2ffe12` (stale outer `model_seeded` while the model's own
`model_was_seeded` IS cleared by `clear_cache()`).
NEAR: MagicWorld v1 `a378d67d`.
CLEAN: Self-Forcing `33593df3`; LongLive v1 `e52d9ef6`; LongLive 2.0 `6b36d20e`;
Matrix-Game 1 `71c3cd7f`; FramePack `97fe5dbe`; MemFlow `7ed51477`.
NOT-INSPECTED: Cosmos umbrella. Excluded by modality: Voyager (MineDojo, arXiv:2305.16291).

## The highest-yield search heuristic, derived from both HITs

Both HITs have the same shape: **a long-lived object shared across user actions, plus a
lifecycle/reset path that clears *most* of the state.** In VMem it is a module-level global
`MODEL` in `app.py`; in GEN3C it is a persistent API server holding a model across HTTP requests.

So prioritise repositories that ship:
- a Gradio / Streamlit / FastAPI demo with a **module-level or app-level model object**;
- an **interactive or streaming** mode where the user issues repeated actions;
- an explicit `reset` / `clear` / `new session` / `new prompt` affordance.

Repositories with only a batch `python inference.py` entry point are far lower yield — say so and
do not spend time on them.

## Candidate population to work through

Verify rather than assume; a system may not have public code. Suggested, not exhaustive:
WorldMem (arXiv:2504.12369 — a prior round claimed it does not meet the instance-state target;
**check this, do not inherit it**), Cosmos-Predict2 / Predict2.5, Matrix-Game 2.0 / 3.5,
StreamingT2V, SkyReels-V2, CogVideoX, HunyuanVideo / HunyuanWorld, Wan 2.1 / 2.2 interactive,
Genie-style / playable world models with public code, NVIDIA Isaac / physical-AI world models,
CausVid, Pyramid Flow, Open-Sora streaming paths, Hunyuan-GameCraft, Yume, Aether, TrajectoryCrafter,
ViewCrafter, SEVA / Stable Virtual Camera, ReCamMaster, and any interactive 3D/4D scene generators
with released servers.

**Add systems I have not listed if your search finds better candidates.** Explain why each was
chosen or skipped.

## Questions

**Q1 — The extended table.** For every newly inspected system: repository URL, commit SHA read,
arXiv ID and exact title, per-condition verdict with file paths and line numbers, overall verdict.

**Q2 — The running M/N.** Combining prior and new results, state the count of HIT / NEAR / CLEAN /
excluded over the total inspected, and state precisely what population that fraction describes.
**Do not present it as a prevalence estimate for "video world models" in general** unless you can
defend the sampling frame — say what the frame actually is.

**Q3 — Does a pattern emerge among the HITs?** Both current HITs involve a lifecycle path that
clears most state but misses one flag/field. Is that the signature, or an artefact of two cases?
What would falsify the pattern?

**Q4 — Saturation.** At what point does further auditing stop adding evidence? State the number of
systems beyond which you expect diminishing returns, and why.

## Output
Write to exactly one new file: `work/agents/CODEX_R15F_AUDIT_EXPANSION_20260919.md`.
Do not modify any existing file. No GPU, no training, no generation, no weight downloads.
Shallow-cloning public source into a temp directory is fine.
Every code claim: repository, commit SHA, path, line numbers. Every paper: arXiv ID and exact title.
**Do not fabricate line numbers.** NOT-INSPECTED is an acceptable and useful answer.
