# Round 14 — Original Dynamic Blockworld v2 inference configuration

**Targeted static resolution complete; actual checkpoint schema remains unknown.** This supplements `dynamic_cpu_port_preparation/SOURCE_HANDOFF.md`; it does not repeat the CPU port design or certify execution. All new source bytes match their git-blob identities at FloWM commit **c909c54a3d58ae240de03f5ebbec222d3e6b1264**. No Hydra/package/model execution occurred.

The original [wiki command](https://github.com/hlillemark/flowm/wiki/Inference-and-Reproducing-Results) selects `shortcode=exp/blockworld/flowm/infer/metrics_140/dynamic_70ctx algorithm=flowm_video dataset=blockworld ckpt_map=default` plus a run name. This is a description of the author command, not a launch command for the unfinished local CPU port.

The relevant source chain is: `config.yaml` → selected `dataset/blockworld`→`base_video`→`base_dataset`; selected `algorithm/flowm_video`→`base_pytorch_algo`→`base_algo`; the shortcode includes `infer/base_inference`, which includes model-size `flow_vit_10m` (overrides backbone to `flow_vit`) and Blockworld `flowm/base`; its own fields then override those defaults. The final dynamic shortcode overrides the inherited placeholder split/length/batch. `ckpt_map/default` includes `base_ckpt_map` then supplies released paths. `unwrap_shortcuts` leaves the literal `shortcode=...`/`algorithm=...`/`dataset=...` selections intact; it only expands `@...` or direct `algorithm/backbone=...` arguments. No unprovided private secrets or additional CLI overrides are assumed.

| Resolved field | Original value | Defining/overriding source |
|---|---|---|
| dataset.resolution | `[128,128]` | `dataset/blockworld.yaml:13` |
| dataset.frame_skip | `1` | `dataset/blockworld.yaml:12`; no selected override |
| dataset.observation_shape / algorithm.x_shape | `[3,128,128]` | `base_video` interpolation through `flowm_video` |
| backbone.input_shape | string resolving to `(3,128,128)` | `algorithm/backbone/flow_vit`; existing factory parses it |
| dataset.max_frames / n_frames | `140 / 140` | final `metrics_140/dynamic_70ctx` |
| prediction.context_frames | `70` | final shortcode; therefore 70 future frames in the original full evaluation |
| validation split / batch / precision | `['sunday_v2_validation'] / 16 / 32` | final shortcode / inherited base inference |
| dataset.cond_alignment / data_cond_alignment | `t-1->t / t->t+1` | `flowm/base` / `dataset/blockworld` |
| cond_loading_style / external_cond_dim | `action_int / 5` | `flowm/base` / `dataset/blockworld` |
| dataset.latent.enable / use_depth | `false / false` | `flowm/base` / `dataset/blockworld` |
| algorithm.load_model_state | `null` | `base_pytorch_algo`, no selected override |
| algorithm.model_state_key / load_model_state_mode | `model_state / strict` | `base_pytorch_algo:27,30`; inactive manual-loader defaults |
| algorithm.checkpoint.strict | `true` | `base_pytorch_algo`; actual Lightning restore behavior not independently executed here |
| global load | `${algorithm.model_weights.flowm.blockworld.flowm.v2_dynamic}` | final dynamic shortcode |

The resolved global `load` string is **`downloaded_checkpoints/hf_models/blockworld-models/blockworld/dynamic/flowm/v2_dynamic.ckpt`**, from the existing frozen `ckpt_map/default.yaml`. It is a relative source-config path; its actual local absolute binding/file contents were not checked. The 280-total-frame shortcode preserves these model/context/split settings but sets `max_frames=n_frames=280`. Dataset `num_validation_clips=16` and inherited `num_default_clips=1000` are distinct configured fields; this review does not reinterpret them as verified episode counts.

**Critical loader distinction.** [`main.py:184–220`](https://github.com/hlillemark/flowm/blob/c909c54a3d58ae240de03f5ebbec222d3e6b1264/main.py#L184) rejects simultaneous global `load` and `algorithm.load_model_state`. For the original dynamic command, global `load` becomes `checkpoint_path`, reaches `BaseExperiment.ckpt_path`, and then [`trainer.validate(...ckpt_path=self.ckpt_path, weights_only=False)`](https://github.com/hlillemark/flowm/blob/c909c54a3d58ae240de03f5ebbec222d3e6b1264/experiments/base_exp.py#L387). The `flowm_video.py:79–96` manual loader is not entered. Accordingly, **`model_state` is not evidence that the released `.ckpt` contains that top-level key**; this review also does not assert `state_dict` from convention.

For the minimal standalone CPU model, preserve the previous handoff's exact constructor mapping and use these resolved input/data values. Later, once a real authorized checkpoint is available, inspect its actual schema, bind the actual model subtree/prefix transformation, and require complete strict learned-weight coverage. That adaptation must be documented as a standalone port of the original model, not an unchanged Lightning application. Choosing batch1/one future step is runtime qualification, not the original batch16/70-future-frame evaluation. The inactive manual defaults must not silently select a loader or accept missing weights.

**Remaining unknowns:** actual checkpoint top-level/state keys and tensor identities; local checkpoint presence/absolute path; successful strict loading and CPU numerical execution. The requested dataset resolution/frame skip, selected length/context, configured key/mode, released path and original loader route are now source-resolved. Placeholder VAE configuration remains in the application defaults, but latent use is off; this is not a request to load a VAE or other optional metric model.

Actual source review: 2026-09-09T04:20:54Z to 2026-09-09T04:26:14.928266+00:00. No weights, media, packages, scientific arrays or S70 outputs read; no protocol or launcher edits.
