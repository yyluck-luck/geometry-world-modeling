# Round 13-A — Is the state leak reachable by ordinary users of the PUBLIC release?

This is a **factual reachability investigation**, not a novelty review. Do not rank directions,
do not propose methods, do not issue a funding verdict. Answer the questions with evidence.

## Background: what we found, stated precisely

In the pinned VMem source (`arXiv:2506.18903`, public repo `runjiali-rl/vmem`; three
byte-identical copies in this repo, SHA-256 `90a45f452a4f734b3371fb526c566162026e5d900e0c8204709dd57f44ef1d7e`,
e.g. `work/S17C_interface_preparation/isolated_vmem_source/modeling/pipeline.py`):

`get_context_info` has two branches. **The NMS-disabled branch assigns
`self.initial_threshold = 1e8`.** The NMS-enabled branch assigns `initial_threshold` only when
the frame count is exactly 5. **`reset()` does not clear it.** Therefore a pipeline object that
has taken any NMS-disabled call retains `initial_threshold = 1e8` into later NMS-enabled calls,
and `reset()` does not restore the clean state.

In `navigation.py` there are three call sites: line 185 (`move_backward`) and line 234
(`move_forward`) both pass `use_non_maximum_suppression=False`; **line 321 (`_turn`) passes no
argument and therefore takes the config default.** Verify this yourself, including the config
default value.

We measured the effect on a 14-window panel with a frozen generator:
`nms_on_clean − nms_on(leaked) = +0.245 dB` (sd 0.711, 6/14 positive), stratified by a
zero-diffusion census taken before any score existed: NULL 2 windows `+0.000` (byte-identical
outputs, sha256-verified 4/4), PERMUTATION 4 windows `−0.015`, CONTENT 8 windows `+0.436`.
Weighted mean `3.428/14 = 0.24486 → +0.245`, reconciling exactly.

## What I need you to establish

### Q1 — Is the defect present in the current public release?
Fetch the current public `runjiali-rl/vmem` (GitHub, network is enabled). Determine, with file
paths and line numbers **as they exist today**:
(a) whether the `initial_threshold` assignment asymmetry between the two branches is still present;
(b) whether `reset()` still fails to clear it;
(c) whether the three `navigation.py` call sites still have the same NMS arguments, and what the
    shipped config default for `use_non_maximum_suppression` is;
(d) the commit SHA and date of the version you inspected.
If the public code has diverged from our pinned copy, say exactly how.

### Q2 — Is it reachable on an ordinary user path?
A defect that requires a bespoke harness is far weaker than one a normal user hits. Determine:
(a) does the shipped demo / app / README quickstart path execute `_turn`?
(b) does any documented usage produce a **mixed** sequence — an NMS-disabled call followed by an
    NMS-enabled call on the same object — which is the condition that triggers the leak?
(c) is `reset()` documented or used as the way to start a fresh sequence?
Give the concrete call chain from the user-facing entry point down to `get_context_info`.

### Q3 — Has it been reported or fixed upstream?
Search the repo's issues, pull requests, and commit history for `initial_threshold`,
`get_context_info`, `non_maximum_suppression`, `reset`. Report what exists, with URLs. If nothing
exists, say so explicitly — "no issue found" is a useful and reportable result.

### Q4 — Does it plausibly touch the paper's reported numbers?
Determine whether the evaluation scripts in the public repo drive generation through a path that
could produce the mixed sequence. **Be careful and conservative here:** do not assert that
published numbers are affected unless the code path shows it. If the evaluation path only ever
uses one NMS setting per object, say that, and the correct conclusion is that the defect affects
*users of the interactive/navigation path*, not the paper's benchmark table.

### Q5 — Prior art on the *finding type*
Are there published papers whose contribution is the identification and quantification of a
state-dependency or reset defect in a released generative/world model, with a measured effect
size? Give arXiv IDs and exact titles. If you find none in this specific area, say so, and give
the closest analogues from adjacent areas (reproducibility studies, evaluation audits).

## Output
Write to exactly one new file: `work/agents/CODEX_R13A_LEAK_REACHABILITY_20260919.md`.
Do not modify any existing file. Do not run GPU jobs, training, or generation.
Every paper: arXiv ID and exact title. Every code claim: path, line, and the version you read.
State clearly what you could NOT verify.
