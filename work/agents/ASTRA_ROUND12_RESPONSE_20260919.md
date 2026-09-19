# Round 12：约束放宽审查

## 证据边界

我先核对了仓库，而不是把 brief 当作事实。三份 pinned VMem `pipeline.py` 的 SHA-256 均为
`90a45f452a4f734b3371fb526c566162026e5d900e0c8204709dd57f44ef1d7e`，逐字节一致：

- `work/S17C_interface_preparation/isolated_vmem_source/modeling/pipeline.py`
- `work/S17_cpu_preflight/original/modeling/pipeline.py`
- `work/S102_gate0_3dmatch/adapter_v1/sources/vmem_pipeline.py`

核对到的事实是：line 180 创建 `self.c2ws = [c2w]`，line 1297 追加生成帧的相机，line 1360 只在
`undo_latest_move()` 中与 `latents`、`encoder_embeddings`、`Ks`、`pil_frames` 成组 `pop()`。
没有 setter 或对保留帧重标相机的方法。line 1249 调用
`get_context_info(target_c2ws, ...)`，line 1263 拼接 `context_c2ws` 与 `target_c2ws`，line 1265
对拼接结果做 `get_translation_scaling_factor`。因此 target 改动同时改变检索和相机归一化。
这与 [RESEARCH_MEMORY.md:940-952] 和技术报告 [TECHNICAL_REPORT_20260918.md:98-109]
一致。技术报告也确认当前对象是一组 exposed development windows、一个 dependency group、一个
frozen consumer，而不是 held-out 的普遍结果 [TECHNICAL_REPORT_20260918.md:59-67,364-369]。

我用 arXiv API 逐篇读取摘要；下面的占用判断只表示“本项目能到达的机制已经有直接近邻”，不把有限检索夸大成“全领域定理”。尤其是一个 exact sub-region 没有被查到，仍然只是 `UNVERIFIED`，不是已经证明的开放缺口。

## Q1 — 逐项放宽实际上到哪里

### C1：只放宽“no training”

单独放宽 C1 后，C2 仍禁止 fine-tuning，C3 仍禁止 new weights。因此既不能更新 VMem 的已有参数，也不能保存一个新训练的 adapter、selector 或 branch。没有新的可持久化干预，因而没有可达 axis；代数退化测试不适用，因为没有新方法。

### C2：只放宽“no fine-tuning”

fine-tuning 本身仍是 training，而 C1 继续禁止 training；C3 也继续禁止 new weights。故单独放宽 C2 仍然是空操作，没有可达 axis，也没有代数对象可测。

### C3：只放宽“no new weights”

最多可以接入一个已经训练好的、但在本项目不再训练的外部 checkpoint，例如在 wrapper 中给候选帧做深度/覆盖重排，或给相机条件计算固定特征。若新 checkpoint 还需要新 dependency group，则 C5 也必须放宽；在 C4 不变时不能把它改进成原生 VMem 的 camera-label 机制。

这落在 axis (a) evidence read、(b) conditioning representation 或 (f) geometry–generation coupling。它们已有直接占用：

- **arXiv:2606.02479 — “Retrieve What's Missing: Coverage-Maximizing Retrieval for Consistent Long Video Generation”**：预训练 3D prior、target-view coverage map 和 residual-coverage selection。
- **arXiv:2504.06672 — “RAGME: Retrieval Augmented Video Generation for Enhanced Motion Realism”**：外接检索增强并面向广泛视频生成器。
- **arXiv:2406.10126 — “Training-free Camera Control for Video Generation”**：冻结视频模型的 plug-and-play camera control。
- **arXiv:2503.03751 — “GEN3C: 3D-Informed World-Consistent Video Generation with Precise Camera Control”** 和 **arXiv:2506.04225 — “Voyager: Long-Range and World-Consistent Video Diffusion for Explorable 3D Scene Generation”**：3D cache / camera-conditioned generation。

若固定模块只对同一 target 做 common-target squared-error fusion，则仍被项目已建立的代数退化杀死；若它改变跨调用传播，A1/A2 的两步范数反例说明它不被单步谱完全约化，但这只解除代数障碍，不能解除占用问题。因此 C3 单独不产生 admissible method。

### C1+C2：允许 fine-tune 现有权重，但仍不允许 new weights

这是第一个真正能运行的训练分支：可以改已有 `model_wrapper` / `denoiser` 的参数（现有对象在
`pipeline.py:62,72`，采样在 `pipeline.py:1270-1278`），目标可以是有限视界的跨调用误差衰减，落在 axis (e)/(h)，也可能牵涉 (f)。

该区域已有直接占用：

- **arXiv:2506.08009 — “Self Forcing: Bridging the Train-Test Gap in Autoregressive Video Diffusion”**：把 self-rollout 纳入训练。
- **arXiv:2512.12080 — “BAgger: Backwards Aggregation for Mitigating Drift in Autoregressive Video Diffusion Models”**：从 rollout 构造纠正轨迹。
- **arXiv:2606.14732 — “Steady-Forcing: Balancing Spatial Persistence and Motion Continuity in Long-Horizon Nature Video Diffusion”**：训练式长期稳定/运动保持。
- **arXiv:2510.09212 — “Stable Video Infinity: Infinite-Length Video Generation with Error Recycling”**：自身生成误差回收。
- **arXiv:2602.04608 — “Jacobian Regularization Stabilizes Long-Term Integration of Neural Differential Equations”**：长期积分的方向导数稳定化。

如果把干预写成调用内 denoising / score / attention 动力学，它也落在已占的 axis (h)：**arXiv:2407.01392 — “Diffusion Forcing: Next-token Prediction Meets Full-Sequence Diffusion”**、**arXiv:2502.06764 — “History-Guided Video Diffusion”** 和 **arXiv:2608.14706 — “Equilibrium Forcing: Adaptive Video Generation Without Noise Conditioning”**。

因此它能实现一个研究程序，却没有由现有证据证明的未占 sub-region。A1/A2 只说明跨调用目标不必退化成单步风险；不构成新颖性。

### C1+C3：训练外挂新模块，冻结 VMem 主干

可以在 `cond = self.get_cond(...)`（`pipeline.py:1267`）之前/外部 wrapper 处训练 selector、conditioning adapter 或 geometry branch；若 owner 把训练 adapter 也定义为 fine-tuning，则 C2 也必须一起放宽。它到达 (a)/(b)/(f)/(h)，但已有：

- **arXiv:2509.21657 — “FantasyWorld: Geometry-Consistent World Modeling via Unified Video and 3D Prediction”**：冻结视频基础模型、可训练几何 branch、跨 branch supervision。
- **arXiv:2606.02553 — “LongLive-RAG: A General Retrieval-Augmented Framework for Long Video Generation”**：可搜索历史 latent、训练检索表示，并跨多个 AR backbone。
- **arXiv:2504.06672 — “RAGME: Retrieval Augmented Video Generation for Enhanced Motion Realism”**：外接 retrieval / grounding 路线。

所以这是可实施的 adapter 路径，但仍是已占的 evidence/conditioning/geometry 组合。仅声称“固定 consumer 上的 finite-horizon state-space slice”不能填补缺口：该 slice 尚未测量，是 `UNVERIFIED`，而不是可据此宣称未占。

### C1+C2+C3：完整训练/新权重/微调 bundle

这是自由度最大的可训练方向：可训练新的 adapter/selector/geometry branch，也可调整已有生成器，研究“固定证据读取图下的选择性跨调用误差增益”。它仍然落在 (e)/(h)/(b)/(f)，被上列 self-forcing、纠错、稳定性、检索和 geometry–generation 工作覆盖。它绕过了 common-target fusion 的单步代数陷阱，但没有绕过 occupancy。

这里唯一剩下的窄区是“非频谱、非梯度的 state-space 方向 + 固定相机证据边界 + 场景判别性保持”。Round 11 已核实：这只是一个未做过的 frozen probe；而 probe 本身属于 owner 排除的 measurement/evaluation 贡献，且本 consumer 的 query 与 normalization 尚未可独立封存。因此不能把它升级为 admissible method。

### C4：允许修改 upstream source

这是最便宜、也最容易误判的一项。真正可实现的 T1-5 需要在 source fork 中增加 retained-frame camera relabel setter，并在替换 `c2ws` 后用同一批保留图像/内参重建或同步 surfel geometry，同时保持 `latents` 等配对状态一致；只改 `self.c2ws` 列表会留下 stale geometry。也可以在同一 fork 中显式清理 `initial_threshold` 状态泄漏。它进入 axis (b) conditioning representation 和 (f) geometry–generation coupling。

它不被 A1/A2 单步谱反例直接杀死，但仍没有新颖性：

- **arXiv:2402.03908 — “EscherNet: A Generative Model for Scalable View Synthesis”**：相机 positional encoding 与多参考/目标视图。
- **arXiv:2507.10496 — “Cameras as Relative Positional Encoding”**：relative pose / full camera-frustum conditioning。
- **arXiv:2605.15182 — “Warp-as-History: Generalizable Camera-Controlled Video Generation from One Training Video”**：camera-warped pseudo-history 与 target-frame alignment。
- **arXiv:2603.16871 — “WorldCam: Interactive Autoregressive 3D Gaming Worlds with Camera Pose as a Unifying Geometric Representation”**：用 global camera pose 索引和检索历史。
- **arXiv:2503.03751 — “GEN3C: 3D-Informed World-Consistent Video Generation with Precise Camera Control”**、**arXiv:2506.04225 — “Voyager: Long-Range and World-Consistent Video Diffusion for Explorable 3D Scene Generation”**、**arXiv:2509.21657 — “FantasyWorld: Geometry-Consistent World Modeling via Unified Video and 3D Prediction”**：几何缓存与生成耦合。

这些论文占据的是 camera-pose-aligned history / conditioning / geometry-coupling 的机制语义，不声称每篇逐字实现同一个 `self.c2ws` setter；若坚持 metadata-only 的 exact slice，它仍是 `UNVERIFIED`，不能被称作开放缺口。因此 C4 买到的是“接口可用”，不是 admissible direction。并且任何 query-side 结论仍须同时控制
`get_context_info(target_c2ws, ...)` 与拼接后 `get_translation_scaling_factor` 的双重混淆。

### C5：允许多个 dependency groups / consumers

单独放宽 C5，在 C1–C4 仍固定时，能做的主要是：把同一个 frozen intervention 复制到多个 consumer、多个环境或独立场景，或者接入另一个已经存在的 frozen consumer。前者是跨场景/跨消费者泛化，后者需要额外 checkpoint 与接口。

这首先落在 axis (g) measurement/evaluation，而 owner 已明确排除该贡献类型。若把它包装成 consumer-agnostic method，已有：

- **arXiv:2406.10126 — “Training-free Camera Control for Video Generation”**：跨预训练视频生成器的 camera control。
- **arXiv:2606.02553 — “LongLive-RAG: A General Retrieval-Augmented Framework for Long Video Generation”**：跨多个 AR backbone。
- **arXiv:2606.02479 — “Retrieve What's Missing: Coverage-Maximizing Retrieval for Consistent Long Video Generation”**：几何证据与 coverage retrieval。

C5 不改变 common-target 代数，也不让一个被排除的测量贡献变成方法贡献。若同时放宽 C1+C3 做跨 consumer adapter，仍回到 LongLive-RAG/RAGME/FantasyWorld 所占的轴。

### 最小 bundle 的结论

C1、C2、C3 不是逻辑同一项，但方法能力只有以下几种：C1+C2（微调已有权重）、C1+C3（训练外挂模块；若定义为 fine-tune 则并入 C2）、C1+C2+C3（完全训练）。C2+C3 而保留 C1 时仍不能在项目内训练；C3+C5 只是在允许外部 checkpoint 和新 dependency 时接入一个固定模块。没有一个 bundle 给出已证实的未占、非退化、非 measurement 子区域。

## Q2 — 成本账

下表是**事前规划估计**，不是已经发生的 GPU 消耗；“decisive”按能完成公平对照、独立检查和占用审计计算，不把 model-load smoke 当科学结果。

| 放宽 | 到 decisive 结果的 GPU-hours（约，最近 50） | 新数据访问 | supervisor scope approval | 本学期可行性 |
|---|---:|---|---|---|
| C1 alone | 0 | 否 | 无方法 scope；只需记录 no-op | 立即可判定，但没有工作对象 |
| C2 alone | 0 | 否 | 无方法 scope；只需记录 no-op | 立即可判定，但没有工作对象 |
| C3 alone | 0–50 | 固定模块接口可不需；方法证据需 held-out | 新 checkpoint/license/dependency | 约一周可做接口核对，但不产生 admissible 方法 |
| C1+C2 | 800 起步；约 3,000 才足以做原型级稳健结论 | 训练数据与独立 held-out 都需要；只用 exposed panel 不足 | 必须批准 fine-tuning 与新研究 scope | 至少 6 周；本学期不可稳妥完成 |
| C1+C3 | 800 起步；约 3,000 才足以做原型级稳健结论 | 需要训练/校准数据和独立 held-out | 必须批准新 adapter/weights 与数据用途 | 至少 6 周；本学期不可稳妥完成 |
| C1+C2+C3 | 约 800 的最小 pilot；约 3,000 的 prototype；完整方法远高于此 | 是；ScanNet++ v2 申请还需 owner + supervisor 签名，lead time 2–6 周 | 必须批准 training、weights、数据和 scope | 800 tranche 已撤回，term 已过大半，不可行 |
| C4 | 0 GPU 做 source fork/CPU 不变量；若坚持生成验证约 50 | CPU feasibility 不需；贡献验证需独立数据 | 必须批准 upstream fork、camera-label estimand 与 provenance | 1–3 天能做工程门，但只得到可行性 |
| C5 | 0–50 做跨 consumer 接口/账本；真正跨 consumer 方法至少 800 | 新场景/held-out 必需；若只复用 exposed panel 不具泛化证据 | 必须批准 dependency/consumer/license scope | 2–6 周数据 lead time 加实验，不可稳妥完成 |
| C3+C5 | 约 100 做外部 checkpoint/interface smoke；方法级需至少 800 | 新 weights/dependency 与 held-out | 必须批准两者 | 本学期不可稳妥完成 |

因此成本最低的 C4 也只买到一次可行性修复；最可能产生方法容量的 C1–C3 bundle 同时最贵、最慢、且占用已关闭。成本不能把 occupancy 或 owner 排除的 axis(g) 变成 admissible。

审批内容不能用仓库 receipt 代替：C1+C2 必须逐项写明可训练参数、objective、checkpoint、数据 split、seed 和 compute ceiling，并批准 held-out 隔离与独立复核；C1+C3 还要批准新 adapter/branch 的权重来源、license、训练数据和冻结 backbone 边界；C4 要批准 fork 的 patch/hash、camera-label estimand、surfel 重建语义以及 retrieval/normalization 双路径控制；C5 要批准每个新增 consumer/dependency、license、跨场景 split 和匹配的 compute budget。

## Q3 — 按 admissible-contribution-per-cost 排名

没有任何 relaxation 到达“已建立为未占、非退化且允许作为方法贡献”的方向。因此**不排名**。C4 虽然最便宜，但它的预期 admissible contribution 是零；把它排第一会把 feasibility 错写成 novelty。

## Q4 — 预声明 kill criterion

Q3 没有 top choice，所以 Q4 对“top choice”的条件不适用。我不伪造一个训练门槛来给已经被占用的方向制造授权。

如果 owner 另行要求只做 C4 的工程核对，唯一合理的非方法门应是：对每一个 retained slot，`c2ws`、`pil_frames`、`latents`、`Ks` 与重建后的 surfel state 必须一一对应；任意一个 slot 不对应即 fail。即使该 CPU 门 100% 通过，它仍只证明 source patch 可执行，不能通过 occupancy 门，也不授权生成、训练或论文方法主张。

## Q5 — Ruling

**END-LINE-STANDS**

`new_method_validated=false`；`novelty_authorization=NONE`。本文件不是 human owner authorization；800 GPU-hour tranche 仍撤回。
