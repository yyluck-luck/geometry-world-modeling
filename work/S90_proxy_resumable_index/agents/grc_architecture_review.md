# GRC-Memory 最小可部署架构审查

<!-- EXPERIMENT_NAME_LEGEND_20260912_BEGIN -->
> **S编号与具体试验名称说明（2026-09-12更新）**  
> 文档中的 `S86`–`S90` 是项目内部阶段编号，保留它们是为了让结果、日志和回执可以追溯；括号内是给新读者看的具体名称。编号不是论文术语、结果等级或“实验成功”的标志。S88–S90主要是数据资格/传输与协议审查，不能误读成模型性能实验。
>
> - **S86（单场景四目标几何条件注入基线实验）**：在一个已见静态场景、四个相关目标上，比较历史几何注入方式的真实生成链和RGB误差。
> - **S87（末端引导强度控制与多步引导必要性反例实验）**：复用S86缓存，比较末端处理强度与持续多步引导；它只检验该已见场景的有限反例，不验证GRC或长期几何收益。
> - **S88（RTMV相机JSON元数据与静态投影数据资格检查）**：核对归档身份、相机元数据和可访问的静态文件头；不是RGB-D配对性能实验。
> - **S89（RTMV配对数据TLS接续失败审查）**：记录两种TLS/传输接续尝试及其失败边界；失败本身不等于数据缺失或科学负结果。
> - **S90（RTMV归档配对数据恢复与索引协议审查）**：检查受限Range传输、归档成员身份、断点恢复和索引安全条件；已恢复的512B文件头不等于取得可用深度正文。
>
> 后续报告首次出现编号时应同时写成“**S86（单场景四目标几何条件注入基线实验）**”这类形式；后文可使用编号，但不要只写编号来替代试验名称。
<!-- EXPERIMENT_NAME_LEGEND_20260912_END -->


**审查时间：** 2026-09-11（Asia/Shanghai）  
**身份：** 架构与接口审查；不是方法验证，也不授予 novelty authorization。  
**目标：** 在当前 M3 Max 64 GB、无远程 GPU、VMem/CUT3R 现有缓存和未闭合 RGB–depth–camera 配对的限制下，给出一个不会读取未来答案的最小 GRC 选择器。

## 0. 一句话边界

GRC 只能在决策时看到**历史前缀、当前已知动作/目标相机查询和固定预算**；未来 RGB、未来深度、未来真值位姿、未来生成结果只能在训练标签、校准损失或最终 test 评分阶段出现，不能进入部署时的特征、排序或阈值。下文是一个待实现的接口合同，不是“GRC 有效”的结果。

当前最重要的工程事实是：S82 已真实得到四张历史照片的 CUT3R 预测点图、置信度和相机缓存，但它们不是传感器真值；S86/S87 已有 VMem 消费者的单场景生成和 MSE 反证；S90 只取回了 RTMV 一个 512B depth tar header，尚未取得可配对的 RGB–depth–camera–future 三件套。因此架构先从**选择器重放和几何评价**开始，暂不启动大规模生成。

## 1. 已核的现有代码接点

### 1.1 历史几何和缓存

现有 `src/s6_memory_bridge.py` 已给出一个可复用但需明确证据身份的适配层：

- `normalize_predictions`（约第 52–85 行）只从 CUT3R 的 `frame{i}_pts3d_in_self_view` 和 `frame{i}_camera_c2w` 得到归一化深度与相对相机；它明确不读取 measured depth 或 reference trajectory。
- `make_surfels`/`build_memory`（约第 88–176 行）把预测深度、置信度、RGB 和相机变成 surfel 与 `mapping[source_frame_id]`；最多接收 20 个历史帧。
- `make_selector`（约第 190–224 行）包装未修改的 VMem `ObservedKernel`，保留 source ID、camera、intrinsic、surfel 映射和 `context_num_frames=4`。

这条路径适合生成**候选特征**，但其中的深度和置信度属于 `predicted`，不能在报告中标成传感器真值。

### 1.2 当前 VMem 选择器和消费者

- `src/rgbd_retrieval.py:21–55` 的 `make_selector`/`select` 调用原始 `get_context_info`，返回 `context_time_indices`、候选、可见 source、权重、NMS 阈值和覆盖率。
- `src/vmem_retrieval_kernel.py:244–328` 的原路径先把查询相机变成平均 pose，在 surfel 上渲染、按可见 surfel 分配历史权重，再按 pose 距离和 NMS 选最多四个 context ID，最后从原 `latents`、`encoder_embeddings`、`c2ws`、`Ks` 按 ID 打包。
- `src/rgbd_dataset.py:8–33` 当前 `block0 development; blocks1,2 fixed test` 是同一环境的时间块，不应在论文中叫独立跨场景 test；若沿用，必须标作 temporal holdout。

**架构决定：** 不改动 `vmem_retrieval_kernel.py` 的原始 AST，不把 GRC 插入 denoiser 或 VAE。GRC 作为旁路 selector adapter，输出一组合法 source IDs；另写一个与原 `prepare_context_data` 等价的只读打包函数，把同一组 IDs 的 latent/embedding/camera/K 交给原消费者。

## 2. 最小数据合同

### 2.1 决策时可见的 `HistoryPrefix`

每一个 decision record 对应一个 episode 和截止时刻 `t`：

```text
HistoryPrefix {
  episode_id: str
  cutoff_time: float
  frame_ids: int[]                 # 每个 <= cutoff_time
  rgb_paths/hash: str[]            # 仅历史图
  c2w_optical: float64[n,4,4]
  K_pixels: float64[n,3,3]
  cut3r_pts_self/cross: float32[n,224,224,3] | absent
  cut3r_conf_self/cross: float32[n,224,224] | absent
  predicted_or_observed: enum      # 每个字段单独标 provenance
  vmem_surfels + surfel_to_timestep
  latent_ref/encoder_embedding_ref: opaque IDs into verified cache
  memory_digest: sha256
}
```

`HistoryPrefix` 构建时必须拒绝 `future_*`、`target_rgb`、`target_depth`、`gt_pose`、`posthoc_score` 等字段；文件名和 JSON key 也要做白名单检查。历史图若曾用于看答案或选规则，记录 `exposure_status=seen/development`，不能再作为确认 test。

### 2.2 当前查询 `QueryState`

```text
QueryState {
  query_source: {planned_action, observed_current_pose}
  query_pose_or_action: float64[...]  # 决策时已知
  query_K: float64[3,3] | absent
  budget_k: int                        # 目前 VMem 默认 k=4
  cost_budget: float
  consumer_id: str                    # 固定 VMem adapter/model version
}
```

只有 planned action 或已知当前相机可以进入 selector。由未来真值图像反解出的 pose、由未来深度优化出的 pose、或从目标 RGB 计算的 query embedding 都是泄漏，必须拒绝。若生成设置没有已知 query pose，则使用动作/轨迹预测值，并把不确定性作为输入；不能悄悄换成 GT pose。

### 2.3 选择前的候选特征 `CandidateFeatures`

对每个历史 ID `i` 只计算过去可得量：

```text
phi_i = {
  pose_distance_to_query,
  projected_surfel_coverage,
  visibility_fraction,
  history_pairwise_reprojection_residual,
  depth_consistency_residual,
  cut3r_self_cross_disagreement,
  cut3r_confidence_summary,
  source_age / timestamp,
  latent_bytes / estimated_consumer_cost,
  provenance_flags
}
pair_phi_ij = {
  overlap, redundancy, conflict, shared_surfel_fraction
}
```

重投影和深度一致性只能使用历史观测之间的配准；`future_position_error`、目标深度和目标生成图不得参与这些值。对缺失深度不填零冒充低风险，使用 `missing` mask 和预先规定的惩罚/拒绝规则。所有尺度（像素、米、归一化深度）由 train split 估计，不能用全数据统计量。

## 3. 最小选择器，不训练大模型

### 3.1 选择策略

先实现一个冻结参数的 set scorer，而不是端到端训练 VMem：

```text
u_theta(S | phi, pair_phi, QueryState)
rho_theta(S | phi, pair_phi, QueryState)
cost(S)
J_lambda(S) = u_theta(S) - beta * rho_theta(S) - lambda * cost(S)
pi_lambda(X) = argmax_{S subset candidates, |S| <= k} J_lambda(S)
```

`u_theta` 和 `rho_theta` 可从历史前缀训练出的线性/小型树模型开始；set 聚合至少包含 mean/max/coverage、pairwise overlap/conflict 和缺失 mask，不能默认 `sum_i rho_i`，因为历史之间可能冗余或协同。初版不宣称互信息，使用可解释的 past-only utility surrogate。`lambda`、`beta`、特征归一化和模型权重全部冻结在 train/calibration 结束后。

### 3.2 Exact enumeration baseline

当前最大历史候选数为 20，VMem context budget 为 4。对 `n=20,k=4`，所有不超过 k 的非空集合数为

```text
C(20,1)+C(20,2)+C(20,3)+C(20,4) = 6,195
```

另加空集为 6,196。CPU 上对这个小问题可先完整枚举 `J_lambda`，把结果作为 selector 的 reference；不得在没有测量的情况下写 `1-1/e`。若候选数更大，再使用 beam/greedy，但必须报告它相对 exact enumeration 的 regret；没有次模证明时只叫近似实现。

Exact enumeration 有两个不同用途，不能混淆：

1. **可部署的 exact surrogate enumeration：** 只用 `phi`、`pair_phi`、query 和冻结 `theta`，可以在 test 选择。
2. **不可部署的 oracle enumeration：** 用未来真值计算真实 `L_set(S)`，只能在离线 test 评价中给上界/诊断，不能把 oracle 结果当 selector 成绩。

完整 VMem 生成不能对 6,196 个集合各跑一次；在本机 CPU 上这是不可接受且会改变预算。先用几何 surrogate 枚举，再只对预先登记的 GRC、VMem、最近相机、随机和 oracle subset 做真实消费者实验。

## 4. Train / calibration / test 分离

### 4.1 Train split

按 episode/scene 切分，而不是按相邻帧随机切分。每个 train decision `t` 只用 `H_{<=t}` 和当时可用的 query/action 计算 `phi`；标签可在训练阶段由后续窗口 `Y_{t+1:t+K}` 计算：

```text
L_set(j,S) = clip(
  mean_{h=1..K} normalized_future_geometry_error(j,S,h),
  0, 1)
```

标签可以用于训练 `u_theta/rho_theta`，但绝不能写入 `HistoryPrefix` 或 feature cache。若同一场景既出现在 train 又出现在 test，只能称 temporal extrapolation，不能称 cross-scene。

### 4.2 Calibration split

使用完全未参与 `theta` 拟合的 calibration episodes。对每个候选 `lambda`，运行**完整的 policy** `pi_lambda`，得到一个最终集合 `S_j(lambda)`，然后计算 bounded set loss `L_set(j, S_j(lambda))`。校准对象是 policy/集合，不是单个 item 的三维 residual。

如果 loss columns 能按预先定义的风险预算保持单调，才调用官方 Conformal Risk Control 的全局 `lambda_hat` 接口；该接口（固定代码 `conformal-risk/core/get_lhat.py:8–12`）接收校准损失表并返回一个 lambda，不提供 post-selection conditional guarantee。若单调性或 exchangeability 不成立，停止使用“conformal guarantee”措辞，改称 calibration heuristic，并报告 bootstrap/置信区间。

可选的事件版本是 `L_event=1{L_set>epsilon}`；CRC 这时至多控制边际事件概率的期望，不是每个场景、每个记忆或每个集合的条件上界。校准文件必须保存 alpha、loss bound、lambda grid、scene IDs、policy hash、feature normalizer hash 和数据 manifest hash。

### 4.3 Test split

在 test 选择时只加载：

```text
HistoryPrefix(t), QueryState(t), frozen theta, frozen normalizer, calibrated lambda
```

在把 `selected_ids` 封存后，才允许另一个评分进程读取未来 RGB/depth/camera，计算 `L_set`、coverage、重投影误差、位置误差、RGB/感知质量和成本。选择器进程应在读取答案目录前退出或由文件系统权限隔离；test 日志先写 `SELECTION_TRACE.json`，后写 `EVALUATION.json`。这样能证明 test 选择没有偷看答案，而不是仅靠代码作者口头保证。

## 5. Set-level risk 的定义和报告

推荐的第一版几何损失是一个有界、可解释的集合损失：

```text
L_geo(S) = clip(
  w_r * mean future reprojection error / tau_r
  + w_p * mean future position error / tau_p
  + w_v * visibility-conflict rate,
  0, 1)
```

`w`、`tau` 只在 train 开发并冻结；若没有物理真值，不能把观察器内部 residual 叫 position error。RGB MSE、LPIPS/FVD、几何误差和成本分别报告，不合并成一个“清晰度”数。每个 episode 先算一个 `L_geo`，再跨 episode 汇总均值、分位数和置信区间；不能把像素、连续帧或检查次数当独立样本。

对每个 test scene 至少保存：

```text
selected_ids, candidate_ids, L_geo, L_event, coverage,
reprojection/position distributions, RGB/perceptual metrics,
latency/FLOPs/token or context count, failure/invalid masks
```

不写 `q_i = quantile(vector)`。若确实需要单项风险，只能把它作为 feature 或诊断；论文中的正式保证应针对 `S` 或 `pi_lambda`。

## 6. VMem 接口适配，不改原代码

### 6.1 推荐的旁路接口

```python
def build_grc_features(history_cache, query_state) -> CandidateTable:
    """Past-only; reject future/gt keys and return immutable feature hashes."""

def select_grc(candidate_table, policy) -> SelectionTrace:
    """Exact surrogate enumeration for n<=20,k<=4; no future arrays."""

def pack_vmem_context(vmem_obj, selected_ids) -> ContextBatch:
    """Read-only equivalent of prepare_context_data for exact source IDs."""

def consume_with_fixed_budget(context_batch, original_model, rng_contract) -> Output:
    """Same sampler/VAE/steps/RNG as a named baseline; selector is the only change."""
```

`pack_vmem_context` 必须逐项读取原 `obj.c2ws[i]`、`obj.latents[i]`、`obj.encoder_embeddings[i]`、`obj.Ks[i]`，保留 source ID 顺序和 dtype/device；它不能重新编码 RGB、翻转相机、重估 K 或偷偷增加 context。返回的 `ContextBatch` 应有 `selected_ids`、body SHA、shape/dtype 和 consumer version。

原消费者的 context 数和 target 槽位也必须固定。若 `|selected_ids|<4`，适配器只能按事前冻结的 padding/空 context 合同补齐，或直接把该决策标为 invalid；不能因为 GRC 选得少就改变 token 数、采样预算或给 GRC 一个隐含的计算优势。所有 selector 的有效 context 数、padding 字节和成本都要写入 trace。

### 6.2 与当前 VMem 的公平对照

每个 test decision 记录同一个 `eligible_history`、同一 `QueryState`、同一 `k=4`、同一模型/采样步数/随机合同和同一成本预算，分别运行：

1. 原始 VMem `get_context_info`（当前 retrieval baseline）；
2. 最近相机/pose distance；
3. random（固定 seed，多次）；
4. coverage/geometry-only；
5. confidence-only；
6. Fisher/EIG-style utility（若能用相同信息实现）；
7. utility-only learned selector；
8. GRC risk-aware selector；
9. oracle subset（只作离线上界，不作部署方法）。

GRC 若使用 CUT3R self/cross disagreement、预测 visibility 或历史 depth，就给所有允许使用这些字段的基线相同输入；若某 baseline 只能使用 pose，须明确是弱基线而不是公平结论。MemLearner 等端到端 context-query 方法属于高层近邻，不能把 GRC 的分数与其在不同模型/训练数据上的结果直接横比；应在可获得实现时说明模型和训练信息边界。

### 6.3 与 CUT3R 的接点

`CUT3RHistoryAdapter` 只消费 S82 `execution_geometry_03` 中的历史 RGB、self/cross pointmaps、confidence 和预测相机，输出上述 `HistoryPrefix`。它不能读取目标照片、目标深度或 S81/S72 的评分数组。`VMemContextAdapter` 再把 source IDs 映射到已经核验的 VMem latent/embedding cache。

两种几何来源必须带 provenance：

```text
predicted_geometry  # CUT3R/DPT output; useful selector feature, not GT
observed_geometry   # registered RGB-D/depth/camera; evaluation/calibration answer
```

不能用 observed geometry 计算 test selector 的 `r_i`，再声称是在线预测；也不能把 S82 预测点图贴合自身 warp 当作真实几何改善。

## 7. 真实资源下的分阶段实施顺序

### Level 0：接口和泄漏单元测试（不算科学样本）

- 构造含 `future_*`/`gt_*` key 的恶意 fixture，确保 `build_grc_features` 拒绝；
- 同一 prefix 改变未来文件，选择 trace 必须字节不变；
- 检查 `selected_ids` 全属于 `eligible_history`，`k` 和 context 数不超预算；
- 对 n=20,k=4 核对 exact enumeration 返回 6,196 个集合（含空集）；
- 对 `pack_vmem_context` 做 body SHA/shape/dtype/顺序比对，不跑 denoiser。

### Level 1：保存缓存上的选择器重放

使用 S82/S85 已保存的预测几何、surfel provenance 和历史 latent 元数据，只运行候选特征、set scorer、exact enumeration 和 selection trace。这个阶段只能回答“接口和选择逻辑是否正确”，不能回答未来几何收益。

### Level 2：一小批未见 RGB-D 几何评价

先获得合法的 RGB–depth–camera–future tuple，再冻结 train/calibration/test manifest。选择器输出先封存，随后独立 scorer 读答案计算 set-level loss。若没有跨场景数据，明确降级为 single-scene temporal pilot，不宣称泛化。

### Level 3：少量 VMem 消费者对照

只有 Level 1/2 通过，才把 GRC、原 VMem、最近/随机和 oracle 少量集合接入原生成消费者。沿 S70/S86 的 RNG、50 step、VAE、context 预算和保存量合同；不要为 6,196 个集合跑完整 CPU 生成。S86/S87 已显示一条链需要很长 CPU 时间，故先做 selector-only 和几组预登记 subset。

## 8. 失败即停止的架构门

- 任何 test selector 读取未来 key、未来 pose 或评分数组：该运行作废，不能修后覆盖；
- 没有合法未来真值时：只能做接口/预测几何诊断，停止 GRC 收益结论；
- set-level risk 在 calibration/test 不稳定，或 selection-induced shift 破坏 coverage：删除 conformal 保证，保留启发式结果；
- exact enumeration 显示 greedy/surrogate 明显选错，且没有次模证明：删除 `1-1/e`，报告 exact regret；
- utility-only、pose distance 或原 VMem 在相同预算下解释全部提升：停止新 selector 主张；
- 只在 S86/S87 已见静态场景的 RGB MSE 下降：只能更新 baseline 记录，不能写 GRC 方法有效。

## 9. 架构裁决

该设计把 GRC 限定为一个可审计的 policy adapter：**历史前缀 → past-only 特征 → set-level surrogate → exact 小预算枚举 → source-ID-preserving VMem packer**。它解决的是接口和泄漏风险，尚未证明 risk-aware 选择比原 VMem 或普通强基线好，也没有给予任何理论保证。下一步应先完成 Level 0 的泄漏/枚举/缓存单元测试，再等待真实 RGB–depth–camera–future 数据门；在此之前不实现大模型训练、不改原 VMem 源码、不报告创新收益。
