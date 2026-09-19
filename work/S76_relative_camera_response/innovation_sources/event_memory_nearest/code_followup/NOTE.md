# ReMind: training anchors versus deployed selection

**The inspected public deployment path does not contain an event-based history selector. Event anchors are explicit training-data/curriculum constructs in the paper; deployment uses learned attention over its supplied cache. A cache replacement primitive nevertheless already exists.**

Official repository identity: commit `bf316a30b10f444e15adf5ddf710fa9f97e34ee9`, committer date 2026-09-08 22:14:08 UTC. The official project links this repository and distinguishes released 5B inference from forthcoming 1.3B/training code. This public 5B DMD route should not be silently treated as an exact implementation of every 1.3B experiment in the paper. [Official project](https://remind-applied.github.io/) · [repository](https://github.com/Applied-Intuition-Open-Source/ReMind)

| Exact source | What the inspected code actually does |
|---|---|
| [inference.py:16–20,74–87](https://github.com/Applied-Intuition-Open-Source/ReMind/blob/bf316a30b10f444e15adf5ddf710fa9f97e34ee9/inference.py#L16) | Calls `generate_from_preset`; no selector CLI argument. |
| [remind_inference.py:710–784](https://github.com/Applied-Intuition-Open-Source/ReMind/blob/bf316a30b10f444e15adf5ddf710fa9f97e34ee9/pipeline/remind_inference.py#L710) | Supplies one image or a video prefix, encodes it, builds a known-prefix mask, and invokes DMD rollout. |
| [known_context.py:11–26](https://github.com/Applied-Intuition-Open-Source/ReMind/blob/bf316a30b10f444e15adf5ddf710fa9f97e34ee9/pipeline/known_context.py#L11) | Marks the first `prefix_frames` latent positions known. It does not detect an event or rank historical candidates. |
| [dmd_rollout.py:59–118](https://github.com/Applied-Intuition-Open-Source/ReMind/blob/bf316a30b10f444e15adf5ddf710fa9f97e34ee9/pipeline/dmd_rollout.py#L59) | Iterates chunks in order, restores known entries, denoises, and appends every completed chunk to cache. |
| [cache_adapter.py:149–188,242–275](https://github.com/Applied-Intuition-Open-Source/ReMind/blob/bf316a30b10f444e15adf5ddf710fa9f97e34ee9/pipeline/cache_adapter.py#L149) | Appends cache entries and passes the whole accumulated token range to the generator; original chunk positions remain explicit. |
| [cache_adapter.py:190–240](https://github.com/Applied-Intuition-Open-Source/ReMind/blob/bf316a30b10f444e15adf5ddf710fa9f97e34ee9/pipeline/cache_adapter.py#L190) | `replace_chunk_in_cache` rewrites a caller-chosen old chunk at its original offset, preserves cache length, and re-encodes it through the generator. It is not called in the public rollout inspected above and supplies no event-selection policy. |

The paper's reference-cache training places clean anchors across temporal gaps; the public CLI does not expose that as an automatic sparse-reference selection rule. Protected event anchors are established by training construction, whereas the deployed network can attend to available older evidence. These are different claims. [Paper §§3.1,3.3–3.4](https://arxiv.org/html/2605.25333v2)

**Covered:** learning to favor reliable distant event history over corrupted recent history; preserving temporal addresses; rewriting an existing cache slot. None alone supports a new mechanism claim.

**Still unverified:** under equal historical frame count and denoiser computation, whether replacing a redundant observation with a visible dynamics-changing event improves prediction beyond recent motion pair + coverage and latest reliable anchor. The replacement helper itself invokes a generator, so equal cache length alone does not establish equal total computation. No inspected result establishes this proposed causal comparison, and absence from this bounded read does not prove novelty.

Scope: source inspection only. The optional sink/sliding-window implementation in `causal_inference.py` was read but is not the CLI's DMD rollout; it must not be mislabeled as an event selector. No model import, execution, media, weights, project scientific payload, or S76 result access occurred.
