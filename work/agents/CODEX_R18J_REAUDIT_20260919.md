# Round 18-J 复核：按“实际消费点”更正后的审计

日期：2026-09-19。本文只做源码审计；没有 GPU、训练、微调、权重下载或包安装。所有行号都是固定 commit 的源码行号。`C5`（冻结权重下的可测行为差异）在本轮仍没有运行，因此下文的 HIT 是“静态路径 HIT”，不是已经完成的行为验证。

## 判定规则和分母

本轮把原先的 C1–C3 改成下面的可审计版本：

1. **持久状态识别。** 在同一个公开调用所有权边界上，定位具体的状态单元（实例字段、类字段、模块/用户字典、wrapper/server 字段均可，但必须说明所有权边界）；证明调用 A 写入了它，并且该对象在调用 B 仍然存活。
2. **消费点证明。** 继续追踪调用 B 的实际 consumer：证明调用 A 写入的值在 B 被读取，并且从 A 写入到 B 读取之间没有先重算、覆盖、重新建 cache 或换成另一对象。只看到“初始化路径和 reset 路径不对称”不够。
3. **生命周期覆盖证明。** 检查 B 读取路径上每一个相关字段、别名和外层 admission/gating flag；证明公开的重置、失败路径或新会话边界没有覆盖其中某个读字段。若没有可达的旧值消费，不能判 HIT；若只缺少 reset 证据，最多是 `SUSPECT-UNTRACED`。

“旧值是有意的 autoregressive/history 状态”与“旧值是 reset 缺陷”分开记录。原先的固定 benchmark 包络仍作为主分母规则；若放宽到公开 API 的配置不匹配，单独报告敏感性。

R15-F 的全审计框是 32 行：20 个非 OUT、非 modality 的 video/world-model 候选，10 个 OUT-OF-PREDICATE，2 个 modality exclusion。主问题的分母是前者的 **N=20**，不是“所有视频模型”的总体。

## Q1：逐系统 old → new

| 系统；固定 commit | R15-F 旧 verdict → R18-J 新 verdict | 消费点和生命周期证据 |
|---|---|---|
| **VMem**；`runjiali-rl/vmem@39291e4f272f6b4f270691d930926ab5930f942e`；项目内三份 `pipeline.py` 字节一致，例：`work/S17C_interface_preparation/isolated_vmem_source/modeling/pipeline.py` | **HIT → HIT** | `pipeline.py:674-708`：NMS/step 分支条件性写 `initial_threshold`，NMS 关闭分支 `:704-705` 写 `1e8`，之后无条件读 `:707-708`。公开 app 的 move 路径在 `app.py:610-641`，turn 路径在 `:494-515`；move→move→turn 时，turn 的 `is_second_step` 不再写新阈值而读取旧阈值。消费继续发生在 `:716-750` 的阈值循环/候选选择中，没有先覆盖。`reset()` `:135-147` 漏掉 `initial_threshold`，而 `c2ws` 的 `:180` 赋值、`:1297` append 和 `:1249,:1263,:1265` 消费本身不能单独证明缺陷，因为 `initialize()` `:149-180` 会重建 `c2ws`。因此 HIT 依据是 `initial_threshold` 的真实消费，不是 c2ws 不对称。 |
| **GEN3C**；`nv-tlabs/GEN3C@db2ffe12ced12ddafcec5e0422ee46ce8520746b` | **HIT → HIT** | 外层 `model_seeded` 在 `gui/api/server_base.py:59-60` 初始化，`server_cosmos_base.py:62-71` 只有成功 seed 后才写真。新 seed 先清理内部状态 `:46-55`，`gen3c_persistent.py:551-553` 把 `cache=None, model_was_seeded=False`；无 depth 的公开 seed 在 `:206-210` 抛错，外层真值因此保留。随后 `/request-inference` 在 `server_base.py:121-129` 仍读到旧的 `model_seeded=True`，路径 `gen3c_persistent.py:292-312` 消费已被清掉的 `self.cache.render_cache`。这是跨层 admission flag 到资源 consumer 的真实 stale read。 |
| **CausVid**；`tianweiy/CausVid@adb6a5ecd07666b4d0290042915c8406e6d5ce22` | **HIT → CLEAN** | `causvid/models/wan/causal_inference.py:48-60` 的 cache 字典只有 `k,v`；仓库中没有 `global_end_index`/`local_end_index`。每次 `inference()` 在 `:121-143` 重算 `block_index,current_start,current_end`；`causal_model.py:140-143` 先写 `[:,current_start:current_end]`，只读 `[:, :current_end]`。长视频公开循环是 `README.md:42-46`、`minimal_inference/longvideo_autoregressive_inference.py:61-71`。因此位置每次从 0 重算，前端被覆盖，`current_end` 以外也不读；`:112-115` 只复位 cross-attention `is_init` 不构成 stale KV read。旧结论把“reset 分支不对称”误当成消费证据。 |
| **MagicWorld v1**；`vivoCameraResearch/Magic-World@a378d67d1b803db4268340fcc130c98a243ad9a8` | **NEAR → NEAR** | `videox_fun/pipeline/pipeline_magicworld_v1.py:291-295` 建立 `history_cache`，` :841-857` 在 `current_step != 0` 且有 `start_image` 时读，生成成功后 `:1015-1027` append/trim；公开循环 `inference/inference_magicworld.py:367-425` 传递 step 和上一帧。这里确有跨调用读取，但 README `:20-27,:68` 将其作为历史场景延续；没有独立新会话/错误 reset 的公开契约，不能把有意 history 判成 HIT。fast demo 还在 `inference_magicworld_fast.py:543-547,674-676` 清 cache。 |
| **PlayGen**；`GreatX3/Playable-Game-Generation@c3e541987f1d99a3e263db3f6f0b77d74a41b602` | **NEAR → NEAR** | `app.py:27-33` 是 module-level per-user 字典；`model_inference()` 在 `:120-126` 写 `user_zeta`，动作路径 `:136-149` 读/更新它，属于预期 recurrent action state。`disconnect()` `:194-207` 不删旧 `user_zeta`，但 `connect()` `:174-191` 生成新 SID 且没有旧 SID 映射；README `:39-50` 要求先 Start Game。没有证明旧 key 在重连后的公开路径被消费，因此不能升级 HIT；若严格要求 `self.x` 实例字段，该行甚至应为 OUT，而不是 HIT。 |
| **Self-Forcing**；`guandeh17/Self-Forcing@33593df3e81fa3ec10239271dd2c100facac6de1` | **CLEAN → CLEAN** | `pipeline/causal_inference.py:111-132` 每次 inference 初始化或重置 KV 的 `global_end_index/local_end_index` 及 cross-attention `is_init`；consumer `wan/modules/causal_model.py:201-235` 先写当前 slice 后读当前窗口，cross-attention `wan/modules/model.py:174-183` 在 `is_init=False` 重算。VAE cache 的 `wan/modules/vae.py:545-569`、`utils/wan_wrapper.py:89-108` 也有清理/禁用路径；未发现外层 gate 漏清。 |
| **LongLive v1**；`NVlabs/LongLive@e52d9ef6865d843282a6b5e9d46d03b35f88929` | **CLEAN → CLEAN** | `pipeline/causal_inference.py:109-132` 每次 inference 重建 cache，`:245-283` 建 cache；模型字段在 `:134-137,:285-317` 重置。interactive prompt switch 在 `pipeline/interactive_causal_inference.py:34-50,92-96,145-173` 重新 cache；consumer `causal_model.py:228-315` 使用当前 cache。未发现跨层 admission/session marker。 |
| **LongLive 2.0**；`NVlabs/LongLive@6b36d20ec6f7958d29d11a704dfa64611a9f2572` | **CLEAN → CLEAN** | `pipeline/causal_diffusion_inference.py:229-261` 重置 logical state，`:267-287,342-364` 覆盖并恢复模型 runtime 字段，`:881-890` 提供 clear_cache；consumer `causal_model.py:457-781,1481-1483` 使用本次重建的索引/窗口，wrapper `utils/wan_5b_wrapper.py:343-370` 每次发布当前 metadata，未发现遗漏的外层读字段。 |
| **Matrix-Game 1**；`SkyworkAI/Matrix-Game@71c3cd7f741311f8100f6cf9cde942b6c1378d11` | **CLEAN → SUSPECT-UNTRACED（主规则）**；**公开 API 配置敏感性：→ HIT** | `Matrix-Game-1/inference_bench.py:88-97` 写的是 class-level TeaCache（`cnt,num_steps,previous_modulated_input,previous_residual`），不是每次调用的实例 reset。consumer `Matrix-Game-1/teacache_forward.py:101-121` 在非起点/终点先读旧 input/residual，计算分支在 `:123-233` 才写 residual。`matrixgame/sample/pipeline_matrixgame.py:585-600,826-837,900-910` 的 `num_inference_steps` 是公开参数，CLI `inference_bench.py:267-276` 独立暴露 `--inference_steps` 与 `--num_steps`。因此 call A=40、call B=50 时，B 确实先读 A 的 class-level 值；这是扩展 C1（纳入 class-level、允许公开配置不匹配）下的 HIT。原固定 benchmark 的 50/50 包络会使 `cnt` 完整回绕，不能据此宣称稳定 HIT；所以主表保守标为 SUSPECT-UNTRACED，并把 HIT 作为明确敏感性，而非主 M/N。 |
| **Matrix-Game 2.0**；同上 commit | **CLEAN → CLEAN** | `Matrix-Game-2/pipeline/causal_inference.py:216-234`，streaming `inference_streaming.py:517-535` 在每次调用先把 KV/cross cache 置空再重建；consumer `wan/modules/causal_model.py:165-193`、`action_module.py:288-319,414-447,495-521` 写当前 slice 后消费，cross-attention `wan/modules/model.py:230-255` 重算。未发现另一层未清 gate。 |
| **FramePack**；`lllyasviel/FramePack@97fe5dbe06ac1f337ece08935b1076a35eefeeb9` | **CLEAN → CLEAN（顺序单 worker 包络）** | `demo_gradio.py:196-221` 每个 latent section 调 TeaCache 初始化；`pipeline/hunyuan_video_packed.py:822-830` 重置 `cnt,num_steps,threshold,accumulated distance,previous_modulated_input,previous_residual,rescale`，forward 的读取在 `:950-995` 受 cnt 分支约束并在计算分支写回。`demo_gradio.py:183-196,318-326` 使用 worker-local history/新 AsyncStream。并发 session 的 module-global `stream`（`:96,:318-326`）是另一个未在原顺序包络中审计的风险，不足以改写本行 CLEAN。 |
| **MemFlow**；`KlingTeam/MemFlow@7ed514771f5add2af7cc60889e8310ce2b70ab1e` | **CLEAN → CLEAN** | `pipeline/interactive_causal_inference.py:149-176` 每次重建 KV、cross-attention、KV-bank；consumer `wan/modules/causal_model.py:307-404,1313-1356` 随后只读本次对象。基类清理 `pipeline/causal_inference.py:331-360` 对 `kv_bank` 某个 logical index 的清理不完整，但下一次 inference 在读前先重建 bank，故没有真实跨调用 stale read，也没有外层 gate 漏清。 |
| **Pyramid Flow**；`jy0205/Pyramid-Flow@a012faa1dc4d71301a7a153c7f9554c081947ea2` | **CLEAN → CLEAN** | `app.py:13-17,127-146` 只缓存模型；每次 callback `:165-265` 建立调用状态。`pyramid_dit/pyramid_dit_for_video_gen_pipeline.py:1081-1082` 无条件写 guidance，读取 `:774-779`；生成列表 `:1123-1203` 与 scheduler `:705-727` 每次重建。 |
| **HunyuanVideo**；`Tencent-Hunyuan/HunyuanVideo@e748c73ac064728bf6bd15b1cdb8161e55a4f331` | **CLEAN → CLEAN** | 常驻 Gradio 模型/重复 callback 在 `gradio_server.py:14-21,67-130`；sampler 每次建 scheduler `hyvideo/inference.py:529-566,608-616`，pipeline `pipeline_hunyuan_video.py:810-828` 重置调用字段，读取 `:646-660,840-860,955-963`，`_num_timesteps` 也重算。未发现外层 session flag。 |
| **DIAMOND**；`eloialonso/diamond@5bcd1599755b4f2fae8e5e079e02f0728e174965` | **CLEAN → CLEAN** | `src/envs/world_model_env.py:45-53` reset observation/action/recurrent state/episode length，consumer `:65-105` 只推进当前 episode；dead reset `:56-62,78-89`，游戏层 reset `src/game/game.py:64-74,122-150`，PlayEnv `src/game/play_env.py:99-110` 覆盖相关状态。 |
| **CogVideoX / SAT**；`zai-org/CogVideo@7a1af7154511e0ce4e4be8d62faa8c5e5a3532d2` | **CLEAN → CLEAN** | `sat/vae_modules/cp_enc_dec.py:365-373` 先读 cache 后删除/置空，`:374-401` 仅在当前 clear 条件下写；sample/decode 调用在 `sat/diffusion_video.py:197-223`、`sat/sample_video.py:146-160,243-275`，最终 chunk 清理。未发现跨调用未覆盖的读字段；异常中断未完成清理不等于已证明的后续 stale read。 |
| **AlayaWorld**；`AlayaLab/AlayaWorld@ea03cfbb2e4c4e9102ed8ea8562e0b5370ca9b79` | **CLEAN → CLEAN** | session start/end `reactor/alayaworld.py:284-316` 清 `_cache,_camera,_ar_index,_active_prompt`；reset event `:567-602` 与 `_reset_rollout` `:772-815` 清理/重建；consumer `_generate_chunk` `:858-920` 读的是当前 rollout 的有意历史，没有遗漏的外层 gate。 |
| **ViewCrafter**；`Drexubery/ViewCrafter@97cdb8634b28708cbd50912d57c52f23c5ffbf09` | **CLEAN → CLEAN** | singleton callback `gradio_app.py:19-22,59-78`；`viewcrafter.py:436-457` 每次覆盖 opts、trajectory、seed、images/img_ori，consumer `:108-169` 使用本次输入；diffusion locals `utils/diffusion_utils.py:117-201`。未发现 later read 未被覆盖。 |
| **SEVA / Stable Virtual Camera**；`Stability-AI/stable-virtual-camera@fe19948e9b7bea261ab2db780a59656131404a83` | **CLEAN → CLEAN** | `demo_gr.py:107-122,462-651` 的输入/options 是调用局部；session setup/cleanup `:740-789,1239-1244` 创建/停止 renderer 并移除 abort event，`SevaRenderer.visualize_scene:245-249` 重置 viewer。未发现遗漏的跨层读字段。 |
| **Zing-0.5**；`seedleap/zing-world-model@11212da06f63290f4d354cdc0324241ba6eac356` | **CLEAN → CLEAN** | `src/zing_v0_5/pipeline.py:77-93` 每个 generate 建新 cache；读写 `:107-140` 对同一调用对象，model lazy positional state `src/zing_v0_5/model/modeling.py:228-264` 不跨请求消费。 |
| **Open-Sora**；`hpcaitech/Open-Sora@7ad6a96a135feb81f755c84fb391818718f6beb2` | **OUT → OUT** | `gradio/app.py:92-141` 每次 `build_models()` 重建，`run_inference()` `:247-250` 取得新组件；scheduler `:411-435` 在同一调用使用，Generate `:701-754` 没有跨调用 stale consumer。 corrected rule 不会把无跨调用读的系统变成 HIT。 |
| **Yume**；`stdstu12/YUME@111c3fab7fb020d1e261a68be6ec78a3fecc8d5b` | **OUT → OUT** | module-level `LAST` 在 `webapp_single_gpu.py:161-168`，读 `:611-615`、写 `:872-876`；调用者显式选择 continuation `:1164-1166,1203-1205,1328,1415-1444`。这是用户选择的延续状态，不是未声明的 stale reset path。 |
| **Hunyuan-GameCraft**；`Tencent-Hunyuan/Hunyuan-GameCraft-1.0@9a35ecf495a1b97b4929524fff442481069ecdc2` | **OUT → OUT** | `hymm_sp/gradio/app_gamecraft.py:44-47,350-369` 的 module globals 在输入改变时清理；`hymm_sp/sample_inference.py:446-500` 通过显式 `last_latents/ref_latents` 参数传 continuation。没有固定谓词所需的隐藏实例 stale read。 |
| **HunyuanWorld 1.0**；`Tencent-Hunyuan/HunyuanWorld-1.0@57fa9f3a79eae1079c279968cdb9d82c75fa7c86` | **OUT → OUT** | `demo_panogen.py:33-77,235-264`、`demo_scenegen.py:26-50,98-134` 是 CLI，输入和 pipeline 状态为调用局部，无公开重复交互 session。 |
| **Wan 2.1**；`Wan-Video/Wan2.1@9737cba9c1c3c4d04b33fcad41c111989865d315` | **OUT → OUT** | `gradio/t2v_14B_singleGPU.py:20-23,35-50` 的全局对象在启动时建立，callback `:134-146` 没有 guarded 跨调用生成字段；只有常驻模型。 |
| **Wan 2.2**；`Wan-Video/Wan2.2@42bf4cfaa384bc21833865abc2f9e6c0e67233dc` | **OUT → OUT** | 公开树是 `generate.py` 批处理；VAE `wan/modules/vae2_2.py:784-860` 有显式 `clear_cache()`，没有可审计的交互跨调用 API。 corrected rule 不会推翻 OUT。 |
| **WorldMem**；`xizaoqu/WorldMem@c1cc91bdfb2dda52fe309280e5ed046b1faba448` | **OUT → OUT** | Gradio State 显式传 memory `app.py:200-217,524-529,556-561`；`reset()` `:305-325` 清 memory/actions/poses/c2w/frame index，`generate()` `:244-289` 消费传入 state。没有隐藏 model-instance stale read。 |
| **Cosmos-Predict2**；`nvidia-cosmos/cosmos-predict2@661da4774b0ca41d082a0ecbeb47550bcf07e03f` | **OUT → OUT** | `examples/video2world.py:353-403` 是 CLI；`pipeline.py:917-920` 每次调用设置 scheduler，无公开长驻交互 session 或跨调用未重算字段。 |
| **Oasis**；`etched-ai/open-oasis@f59deef2c019c212bd0c5a3a5b986a51f3701847` | **OUT → OUT** | rotary cache `rotary_embedding_torch.py:242-260,288-301` 是同一次 autoregressive loop 的 cache；公开 `generate.py:23-45,86-123` 是一次性 CLI，README `:31-42` 没有用户跨调用 API。 |
| **ForgeWM**；`asdfo123/ForgeWM@a922c6b42d2e1dcfdc367a27a07c0148cb8ed6d8` | **OUT → OUT** | lazy cache/consumer 在 `pipeline/causal_inference.py:87-90,166-200,308-320`；公开 `inference.py:270-296,397-421` 是 one-shot CLI，README `:353-366` 明确 interactive demo 尚未完成。 |
| **Voyager**；`MineDojo/Voyager@55e45a880755d0c8c66ca7fb5fe7962ac8974f89` | **modality exclusion → modality exclusion** | `voyager/agents/action.py:40-74` 的 chest memory 可能是 agent state，`voyager/voyager.py:165-198,287-293` 有 rollout reset/step；但它是 LLM Minecraft agent，不是本审计目标的视频 world model，不能计入 M/N。 |
| **NVIDIA GR00T**；R15-F 记录的固定 commit | **modality exclusion → modality exclusion** | 机器人/VLA 模态，未把其 agent state 当作视频 world-model stale-read 样本；保持排除，不进入 N=20。 |

## Priority 2 的“跨层是否还有漏读字段”结论

- **Self-Forcing、LongLive v1/v2、Matrix-Game 2.0、FramePack（顺序 worker）、MemFlow、AlayaWorld、ViewCrafter、Pyramid Flow、HunyuanVideo、DIAMOND、CogVideoX：** 已检查 later-path consumer、重建/清理点和 wrapper/server 层，未找到 reset 不覆盖的 later-read 字段。以上各行已给出具体 reset、consumer 和 commit。
- **Matrix-Game 1：** 有。class-level TeaCache 在 `inference_bench.py:88-97` 建立，`teacache_forward.py:101-121` 可在下一公开调用先读；固定 50/50 benchmark 不足以建立跨调用 stale 序列，但公开 API 的 40→50 配置序列可以。因此 CLEAN 不能继续作为无条件结论，主表保守标为 `SUSPECT-UNTRACED`，扩展谓词下为 HIT。
- **FramePack 并发边界：** module-global `stream` 在 `demo_gradio.py:96,318-326`，若把并发跨 session 纳入 C4，需要另行审计 worker 是否读取了别的 job 的 stream；本轮固定顺序 worker 包络没有把这个并发风险升级成 HIT。

## Priority 3：OUT verdict 是否会被新规则推翻

没有。Open-Sora、Yume、Hunyuan-GameCraft、HunyuanWorld、Wan 2.1、Wan 2.2、WorldMem、Cosmos-Predict2、Oasis、ForgeWM 的上表证据都缺少“先写、后读、未重算/未覆盖”的隐藏 stale consumer，或缺少公开交互调用边界；修正规则只会防止误报，不会把这些变成 HIT。R14-D 另列的 Matrix-Game 2/3、Cosmos-Predict2.5、StreamingT2V、FantasyWorld 也没有被修正规则推翻：其先前固定 commit 与排除理由见 `work/agents/CODEX_R14D_SECOND_CONSUMER_FEASIBILITY_20260919.md` 对应条目；它们不进入本轮 N=20。

## Q2：正确的 M/N

主分母是 **N=20**：R15-F 已完成 commit 锁定、公开调用边界和条件 1–4 审计的 video/world-model 候选，去掉 10 个 OUT-OF-PREDICATE 和 2 个 modality exclusion。按本轮严格的消费点规则：

- **M=2/20 静态 HIT：VMem、GEN3C。**
- **2/20 NEAR：MagicWorld v1、PlayGen。**
- **15/20 CLEAN。**
- **1/20 SUSPECT-UNTRACED：Matrix-Game 1。**

若把公开 API 的 class-level 状态和配置不匹配纳入 C1–C3，Matrix-Game 1 变成第三个 HIT，即 **3/20**；这只是谓词边界敏感性，不能与主结果混写。若把所有 32 行机械相加，静态 HIT 是 **2/32**，但那个分母混合了 OUT 和 modality，不是 prevalence 估计。由于 C5 没有运行，冻结权重下已测行为 HIT 的诚实计数是 **0/20 measured**；静态 HIT 不能写成用户可见质量退化的实证结果。

## Q3：条件 1–3 是否是问题

是。旧版条件把“有字段”“某分支没 reset”“同一对象可再次调用”近似当成 stale read，正是 CausVid 假阳性的来源；GEN3C 又证明单层 reset 不能推出 CLEAN。替换文本就是本文开头的三条：识别跨层所有权；跟到后续实际 consumer 并证明没有先重算/覆盖；再检查所有外层 gate、别名和失败路径是否覆盖。条件 3 的结论应允许 `SUSPECT-UNTRACED`，不能在“未找到 reset”与“HIT”之间跳跃。

建议把每个候选的最小证据强制写成四元组：

`(writer on call A, public sequence A→B, exact consumer on B, dominance check showing no recompute/overwrite/reset covers it)`。

缺少其中任何一个，最多是 `SUSPECT-UNTRACED`；有意 history/AR 状态另标 `INTENDED-CONTINUATION`，不能用来填补缺口。

## Q4：对跨系统 prevalence claim 的评审结论

**This methodology cannot support a prevalence claim.** 这轮把 CausVid 从 HIT 改成 CLEAN，说明一个结构上很像缺陷的 reset 不对称可以在消费点追踪后完全消失；GEN3C 的相反方向说明“存在显式 reset”也不能推出 CLEAN，因为外层 `model_seeded` 仍控制 later admission。两种错误都能通过一次代码复核，且都受以下因素放大：候选集是启发式/方便取源的样本，不是抽样框；不同项目的公开 API、配置包络和 intended continuation 不同；C5 行为结果没有测量；单个 reviewer 很容易把结构信号写成结论。

因此 2/20 只能叫“这个便利审计框中，静态代码路径满足新规则的计数”，不能叫“world models 中 stale-state defect 的发生率”。若要支持 prevalence，至少需要预注册总体和纳入规则、独立双人逐 consumer 复核、把 OUT/未检查明确分层，并对每个 HIT 做冻结权重的失败/干净 reset 对照。即使做到这些，也只能支持一个定义清楚的审计框 prevalence，不能外推到所有公开或闭源系统。

## 可复核性记录

本轮没有改动任何既有文件；唯一应新增的是本报告。项目要求的外部 Codex/Astra 复核命令已尝试，但当前环境对 Responses WebSocket 返回 `401 Unauthorized`，没有可引用的外部裁定；本文件只采用仓库固定 commit、项目 pinned copy 和独立源码复核结果，不把失败的外部调用当作证据。
