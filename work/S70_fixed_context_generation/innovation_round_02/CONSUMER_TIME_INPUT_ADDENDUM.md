# Consumer trace addendum: explicit physical time is not all temporal information

UTC: 2026-09-09T02:58:20.879383+00:00. Author: `/root/negative_result_question_triage`. Supplements the unchanged problem card SHA `eec95d3371726ac67f59e5b4c87a4b4ada64376f4e486307ac2eb992064c56dc` and original source receipt. Source-only; no import, inference, numerical payload read, or new paper retrieval.

The complete inspected path supports only the narrow missing-input statement. `context_time_indices` is unpacked but omitted from `get_cond` and `do_sample`, then used by reconstruction. `do_sample` gives the denoiser `num_frames=T` and gives the sampler c2w/K/mask. The denoiser converts the current diffusion sigma to an index and passes this as network `t`. Therefore this network's `time_embed(t)` is a **diffusion-noise-step embedding**, not an acquisition timestamp or requested physical elapsed time.

The network also has genuine cross-frame computation. `TransformerBlockTimeMix` reshapes the frame axis and applies attention across it; `MultiviewTransformer` groups frames using `num_frames`, mixes spatial and frame-axis outputs, and obtains context from the first grouped slot. This is not evidence of an absence of temporal modeling. The supplied images, masks, slots, cameras, T, learned conventions, and denoising trajectory can contain useful order or motion cues. I do not claim permutation invariance, no temporal signal, or inability to generate any motion.

The symbolic collision must consequently hold **the entire actual ordered input, all frame grouping/counts, masks, c/uc, cameras/K, configuration, model state, diffusion schedule and full random stream fixed**. Only an externally requested physical time gap changes, with no representation in that input. Then the conditional output law is unchanged; deterministic executions must match. If a proposed real task instead changes T, inserts frames, changes reference motion or any temporal positional feature, it does not meet this collision premise. Fixed-rate target slots may legitimately encode an elapsed interval, so the example is not a failure claim about the original fixed-step contract.

A useful real witness would need timestamped dynamic RGB with enough visible motion to estimate its state, accurate poses and visibility, a later independent observation of its continuation, and an explicit map from acquisition/query time to the consumer. Last-state copying and a timestamp-aware constant-velocity baseline are ordinary controls; any annotations unavailable to the video model must be marked as extra information. The current TUM records do not certify this witness. No extra arm or dataset acquisition follows from this source result.

| Source | Actual inspected range | Whole source SHA256 |
|---|---|---|
| `work/S20_environment/isolated_vmem_source/modeling/pipeline.py` | 1089–1195, 1245–1316 | `680da1c14db8a6780a37fca3a8bac5bb59f0aa7d395db96d4360b352eb7f2255` |
| `work/S20_environment/isolated_vmem_source/utils/util.py` | 676–735 | `30a97451f7a895e99ab881e97249f564e6b97eca2b5ea4d8f83953c26c4cf65e` |
| `work/S20_environment/isolated_vmem_source/modeling/sampling.py` | 138–184,194–221,276–296 | `dc07ca0ba571ba5fb48f9856515d2cb7dea25254008a6f8b315538817f352b24` |
| `work/S20_environment/isolated_vmem_source/modeling/network.py` | 19–175,178–237 | `9ed21c2d804734d7ca2d81b1e596858835ca70a4a04abb9b5540b872515d4c9b` |
| `work/S20_environment/isolated_vmem_source/modeling/modules/transformer.py` | 114–248 | `5f0d152a2f6464076cb0ee5aca725b3445420a5f37ac571d3daa77e580e65764` |
| `work/S20_environment/isolated_vmem_source/modeling/modules/layers.py` | 12–32; call-dispatch identifiers inspected | `98f481aa59f8289e430018dbdbe928d8732b08fb977b14c22f6d7cb28bae5c38` |

These are source identities, not hashes of loaded model weights. Hashing each whole text file does not mean every line was semantically read. The source interpretation uses the idea-evaluator evidence/feasibility checks and the existing critical-thinking distinction between a missing variable and a learned failure.
