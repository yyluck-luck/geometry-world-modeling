# Round 26-R：B-side 合同筛选与解冻价格表（2026-09-20）

## 先给裁定

本轮没有 Part B 路径能在本学期完成一个可辩护的决定性结果，即使 owner 今天解除 consumer freeze。原因不是把候选判成“没价值”，而是每条仍活着的路线都需要尚不存在的独立 held-out 证据；若使用 ScanNet++ v2，还要先取得 owner 与 supervisor 签字并等待 2–6 周，而账本已记录至少六周、term mostly consumed。800 H800 GPU-hour tranche 仍撤回。下面的 GPU-hour 和周数都是**未验证的规划区间**，包括训练/微调、多 seed、消融、held-out、失败重跑和独立复算；不是首图预算，更不是已测吞吐。

本轮只按用户指定的 **B1–B35** 工作。R24-P 在此后另列 B36 及补充分支；它们不在本表，也没有被本轮顺带判定。

“LIVE”表示 claim、estimand、stakeholder、最小证据合同和 kill condition 已经能写清，因而值得在约束真的解除后再决定；它不是授权、创新成立或占据结论。每个 LIVE 都标为 TERM-IMPOSSIBLE。UNPRICED 表示关键任务/数据/接口合同仍未定义，不能诚实给出到决定性结果的价格。全表不做 occupancy 判断。

## 核验到的边界

- R24-P 把 B1–B35 列在 work/agents/CODEX_R24P_GENERATION_20260920.md:225-433，并把 Part B 的原始 S/M/L/XL 只定义为相对预算（同文件 :221-223），不能直接当“过审成本”。
- 三份 pinned pipeline 副本逐字节一致。以 work/S17C_interface_preparation/isolated_vmem_source/modeling/pipeline.py 为例，get_context_info(...) 在 :1249，torch.cat([context_c2ws, target_c2ws]) 在 :1263，get_translation_scaling_factor(all_c2ws) 在 :1265。self.c2ws 的直接初始化绑定在 :180，生成追加在 :1297；但 undo 在 :1360 以 pop() 原位修改列表。因此“只有两处写入”只有在指“直接绑定/追加建立状态”时才准确，不能抹掉 pop 这个删除 mutation，也没有 setter/property。
- 技术报告明确 scene_13/14 是暴露的 development sequences、14-window panel、one dependency group、one frozen consumer，不能充当独立 held-out（docs/report/TECHNICAL_REPORT_20260918.md:57-67,84-99,364-369）。
- 当前账本记录 C6 只放宽“贡献不必是 method”，没有放宽训练/微调/权重/上游/算力；800 GPU-hours 撤回，new_method_validated=false、novelty_authorization=NONE 保持不变（RESEARCH_MEMORY.md:2274-2289）。
- ScanNet++ v2 的 application critical path 是 2–6 个日历周，需 researcher/owner 与 supervisor signatures，尚未启动；提案的 17,000–37,000 H800-h、12–15 months 是完整 envelope，Phase 0–1 也写成 six weeks / ≤800 H800-h（docs/proposal_v2/NEW_PROPOSAL_DRAFT_20260919.md:82-97,112-147）。本表不把这些 proposal allocation 当已验证资源。

### 价格记号

H = 需要项目目前没有的独立 held-out RGB-D/pose/trajectory；scene_13/14 不合格。若用 ScanNet++，H+SN = 另加 2–6 周申请/签字等待，且申请尚未开始。
T = 从头训练，F = fine-tuning/LoRA/adapter，W = 新 head/adapter/模型权重，U = 上游或消费者接入/状态写回修改，MC = 多消费者或真实 action interface，C = 恢复可用 GPU-hours。若只写 F+W，不表示只放一个就够；它们在实践上是成对门。

保守规划带（每个都含决定性多 seed/held-out/独立复算）：
- S：200–800 H800-h，约 6–14 周；
- M：500–2,000 H800-h，约 10–20 周；
- L：2,000–6,000 H800-h，约 16–30 周；
- XL：6,000–20,000+ H800-h，约 26–46 周；
- 混合档取相邻区间并向上覆盖不确定性。主要 spread 是场景/长轨迹数、反事实生成次数、训练稳定性、seed、独立审查、数据许可和 ScanNet++ lead。没有本项目训练吞吐实测，所以价格只写成条件 planning range。

## Q1：B-side 表（claim · estimand · stakeholder · minimal evidence contract · registry · kill · verdict · price）

| 候选 | claim | estimand | stakeholder | 最小证据合同（含负控制） | registry position：object × time × claim type × stakeholder | kill condition | verdict | 价格到决定性结果 |
|---|---|---|---|---|---|---|---|---|
| B1 下游效用学习检索器 | 学到的 top-k 在相同候选池和预算下比静态排序更常选到真正降低下游误差的帧。 | held-out scene/window/seed 上 learned − static 的 paired RGB、LPIPS、depth、pose 与 risk–coverage；按 scene 聚合并报告候选延迟。 | VMem 作者、部署者 | train/dev/test 场景；冻结主生成器；recent/uniform/coverage/hard-negative 与 oracle 控制；三 seed；独立 scorer。 | selector；训练→部署；能力/可靠性；作者/部署者 | Δ≤0，或跨 scene 只靠 scene-ID shortcut，或只改善 selector 分数而不改善 consumer 输出。 | LIVE · TERM-IMPOSSIBLE | S：200–800 H800-h，6–14周；H+SN；T+W+C。若只接外部 wrapper 可不放 U；candidate-pair 生成与 held-out 场景决定 spread。 |
| B2 可微 surfel 渲染检索 | 软可见性/遮挡概率比 hard z-buffer 更能选到遮挡区域有用的历史证据。 | matched candidate pool 上遮挡区域误差/coverage 及 end-to-end Δ，按 scene 聚合，另报 renderer latency。 | 模型作者 | 多场景 held-out RGB-D/pose；hard z-buffer、随机/近 pose 控制；渲染器偏差控制；真实 consumer 前向。 | differentiable renderer + selector；训练/部署；能力/效率；作者/部署者 | 遮挡区和下游均无增益，或只在 synthetic render 增益。 | LIVE · TERM-IMPOSSIBLE | M：500–2,000 H800-h，10–20周；H+SN；T+W+U+C。U 取决于是否有 renderer hook；软渲染显存与 hard-negative 数量主导 spread。 |
| B3 增量 neural field / tri-plane 记忆 | 在同等更新预算下，连续 3D 记忆比离散 surfel memory 降低 novel-view 误差和长程漂移。 | 每场景 held-out multi-view 长轨迹的 RGB/depth/normal/drift 差、更新延迟和 memory bytes，在匹配预算下比较。 | 模型作者、部署者 | 多场景静/动态 held-out；离散 surfel、同内存/同延迟控制；回访与非回访分桶；独立复算。 | 3D memory representation；训练→在线部署；能力/效率；作者/部署者 | 没有几何或长程增益，或 update/latency 超预算。 | LIVE · TERM-IMPOSSIBLE | L：2,000–6,000 H800-h，16–30周；H+SN，另需多场景/动态 3D 数据；T+W+U+C（若主张通用性还需 MC）。 |
| B4 可写、可删、可修订的记忆控制器 | write/merge/decay/rollback gate 在不损失召回的情况下减少错误状态污染。 | 长轨迹每步 contamination rate、error-vs-step、recovery time、capacity–quality Pareto，相同 memory budget 对比 no-gate/oracle/fault injection。 | 模型作者、部署者 | held-out natural-failure 长轨迹；no-gate、oracle、假阳/假阴 detector 控制；完整状态版本与独立重放。 | state lifecycle；训练→部署闭环；可靠性；作者/部署者 | 污染或恢复没有改善，或 equal-capacity recall 明显下降。 | LIVE · TERM-IMPOSSIBLE | S–M：500–2,000 H800-h，10–20周；H+SN；T+W+U+C。自然失败数量和长 trace 是 spread；只做固定 wrapper 原型不能算决定性方法结果。 |
| B5 长程 recurrent world-state token | 跨调用 scene token 比每次四帧 reset context 更能保持长程/回访一致性。 | held-out 闭环轨迹的 revisit RGB/depth/pose drift、失败率和 token bytes，相对 no-token、long-context controls。 | 模型作者、部署者 | 长闭环 held-out；TBPTT truncation、四帧 reset、长 context 和容量匹配 controls；至少三 seed。 | recurrent state；训练→跨调用部署；能力；作者/部署者 | 回访无增益或 drift 随 horizon 爆炸。 | LIVE · TERM-IMPOSSIBLE | L：2,000–6,000 H800-h，16–30周；H+SN+长轨迹；T+W+U+C。序列长度和反复回访次数决定 spread。 |
| B6 来源/几何绑定 cross-attention | source ID、3D位置、可见性、时间 token 让来源效应可定位，并在 matched generic attention 之外降低局部误差。 | source ablation/swap 的局部 support effect、matched-mask localization、global RGB/depth Δ，且重算目标 source 的全部下游后代。 | 模型作者、评测者 | held-out source counterfactual；generic attention 参数匹配、dropout、matched-mask 与 negative-control localization；独立 scorer。 | source-conditioned representation；训练→单次消费；能力/可解释可靠性；作者/评测者 | tags 被忽略/变成 scene shortcut，或 localization 不超过 matched null，或无 end-to-end benefit。 | LIVE · TERM-IMPOSSIBLE | M–L：1,500–6,000 H800-h，12–24周；H+SN；T+W+U+C。反事实生成数量和 source 消费路径最影响 spread。 |
| B7 Geometry-Control 分支 | depth/normal/visibility/flow 分支在同等预算下改善 RGB、几何和 camera obedience。 | held-out paired RGB/depth/normal/trajectory Δ，按遮挡/噪声分桶，和 pixel-only/geometry-ablation 比较。 | 模型作者 | 校准 geometry 与 noisy-depth controls；pixel-only UNet、branch ablation、多 seed、多指标；独立复算。 | conditioning branch；训练→部署；能力/可靠性；作者 | 几何无增益，或错误深度放大 RGB/轨迹错误。 | LIVE · TERM-IMPOSSIBLE | L：2,000–6,000 H800-h，16–30周；H+SN+几何标签；T+W+U+C。深度质量、分支预训练稳定性和噪声桶决定 spread。 |
| B8 世界坐标扩散与可微渲染器 | 共享 3D latent 加 renderer 比 2D latent 在多视重投影和 3D 一致性上更好。 | held-out multi-camera trajectory 的 reprojection、depth/normal consistency、RGB 质量和资源/延迟，在匹配采样预算下比较。 | 模型作者、部署者 | 多相机/动作 held-out；2D baseline、camera/action controls、renderer ablation、显存/吞吐记录；独立复算。 | world representation + renderer；预训练/训练→部署；能力；作者/部署者 | 3D 指标无增益，或质量收益依赖不可接受资源。 | LIVE · TERM-IMPOSSIBLE | UNPRICED（仅量级 XL：6,000–20,000+ H800-h，26–46周）；主干/renderer、3D 动态数据和接口尚未定义，故不能把此区间当诚实 decisive price。必需 H+SN+T+W+U+C。 |
| B9 静态/动态 slot 分解 | 分开 static background、moving entity、camera motion 能降低动态区误差与 pose confusion。 | 动态 held-out 中 static/dynamic 区域 PSNR/depth/track/occlusion error 与静态区保真度，控制 slot permutation。 | 模型作者、部署者 | 动态多视/跟踪 held-out；static-only、no-decomposition、slot-permutation 与遮挡控制；独立复核。 | scene decomposition；训练→部署；能力；作者/部署者 | 动态区无改善，或静态 RGB/几何退化。 | LIVE · TERM-IMPOSSIBLE | UNPRICED（仅量级 L：2,000–6,000 H800-h，16–30周）；动态标注/跟踪和 slot contract 未定。须 H+SN+T+W+U+C。 |
| B10 闭环轨迹规划器 | 在固定 camera/action budget 下，规划获取的视角比被动逐窗 retrieval 带来更低未来重建风险。 | 可执行 held-out trajectory 上每次 observation 的未来 RGB/depth/pose utility、failure rate、latency，固定动作预算对比 no-plan/random/greedy/oracle。 | 部署者、agent/robot policy 作者 | 真实可执行 camera/action contract；长轨迹 held-out；无规划/随机/贪心/oracle；失败完整计分。 | active trajectory policy；用户闭环；能力/决策；部署者/agent | 轨迹不可执行，或 utility/risk 没有改善。 | LIVE · TERM-IMPOSSIBLE | UNPRICED（仅量级 L：2,000–6,000 H800-h，16–30周）；可执行动作空间、采集协议和任务尚未定义，须 H+SN+T+W+U+MC+C。 |
| B11 回访/循环一致性训练 | A→B→A cycle loss 降低回访 drift，且不只是 blur/过度平滑。 | held-out loop 的 RGB/depth/pose cycle error、每步 drift 与 LPIPS，和 no-cycle/identity/over-smoothing controls 比较。 | 模型作者、部署者 | 多事件闭环 held-out；no-cycle、identity、matched compute、多 seed；独立复算。 | training objective；训练→跨调用部署；能力；作者/部署者 | cycle metric 不降，或 blur/pose obedience 变差。 | LIVE · TERM-IMPOSSIBLE | M–L：1,500–6,000 H800-h，12–24周；H+SN+闭环；T+W+U+C。长序列和 cycle rollout 数量主导 spread。 |
| B12 不确定度感知多假设生成 | K 个带 calibrated confidence 的候选能在相同预算下降低 tail risk，而不依赖 oracle 选最好样本。 | fixed compute 下 risk–coverage、ECE、worst-region error、自动 selector 与 oracle gap，相对单样本/锐度控制。 | 部署者、评测者 | held-out K-way candidates；single-sample、random、oracle、sharpness controls；预注册 coverage；独立复算。 | uncertainty/decision head；训练→部署；可靠性；部署者/评测者 | 固定预算下 risk 不降，或 calibration/ECE 失败。 | LIVE · TERM-IMPOSSIBLE | M：500–2,000 H800-h，10–20周；H+SN；T+W+C（若接入生成器则 U）。K 倍 sampling 和选择器训练主导 spread。 |
| B13 可学习 denoising 时机/剂量 | 按几何覆盖与 source uncertainty 自适应 CFG/schedule/注入剂量，在相同步数和算力下改善结果。 | equal-step/equal-FLOP 的 RGB/depth/ghosting Δ，按 conflict bucket 和步数曲线比较 fixed schedule。 | 模型作者 | held-out conflict buckets；fixed schedule、dose ablation、reward-hacking 与 equal-compute controls；多 seed。 | denoising policy；训练→单次部署；能力/效率；作者 | equal-compute 无增益，或策略只 reward-hack 某 proxy。 | LIVE · TERM-IMPOSSIBLE | M–L：1,500–6,000 H800-h，12–24周；H+SN；T/F+W+U+C。步数、策略稳定性和 conflict 采样决定 spread。 |
| B14 多尺度层级记忆 | keyframe→local chunk→per-pixel evidence 路由在长会话中给出更好的 memory–quality–latency Pareto。 | held-out 长会话在相同 memory bytes/latency 下的 recall、RGB/depth、drift 和吞吐，含 level ablation。 | 部署者 | flat-list、level ablation、memory/latency matched、长程 held-out；独立复算。 | hierarchical memory/index；训练→部署；效率/能力；部署者 | Pareto 无改善，或路由错误放大失败。 | LIVE · TERM-IMPOSSIBLE | M–L：1,500–6,000 H800-h，12–24周；H+SN；T/F+W+U+C。层级规模和长会话长度决定 spread。 |
| B15 在线场景 adapter | 对未见场景只用 1/5/10 帧无标签 adapter，就能提升质量且有界遗忘。 | held-out scene 的 0/1/5/10-frame adaptation curve、forgetting、future-leak control 和 end-to-end Δ。 | 部署者 | 未见场景 held-out；zero-shot、shuffled/future-leak、标准 fine-tune、forgetting 与 compute controls；三 seed。 | scene adaptation；部署前/在线微调；能力/适应；部署者 | 无改善、使用未来帧、或旧区域遗忘超阈值。 | LIVE · TERM-IMPOSSIBLE | S：200–800 H800-h，6–14周；H+SN；F+W+C；没有 adapter hook 时再加 U。适配步数、每场景重放和 held-out 数量决定 spread。 |
| B16 相机内参/畸变/rolling-shutter 联合编码 | 联合编码在跨 calibration regime 下减少投影与轨迹错误，而非把 extrinsics 变化当收益。 | held-out calibrated camera buckets 的 projection residual、Rdist/Tdist、RGB/depth 与 c2w-only Δ。 | 模型作者 | 多相机标定 held-out；camera randomization、c2w-only、intrinsics-only 与 extrinsics controls；独立复算。 | camera conditioning；训练→部署；能力；作者 | 无 calibrated gain，或收益由 extrinsics confound 解释。 | LIVE · TERM-IMPOSSIBLE | M：500–2,000 H800-h，10–20周；H+SN+标定数据；T+W+U+C。相机 regime 覆盖和标注质量决定 spread。 |
| B17 神经对应场 | learned 3D correspondence/track 比离散 surfel_to_timestep 更能处理遮挡并改善下游几何。 | held-out correspondence accuracy、occlusion recovery、localization 与 downstream geometry Δ，另报动态/反光桶。 | 模型作者 | 动态/反光 held-out；GT/强 tracker、discrete baseline、no-correspondence controls；独立 scorer。 | correspondence representation；训练→检索/消费；能力；作者 | correspondence 或下游都无增益。 | LIVE · TERM-IMPOSSIBLE | M–L：1,500–6,000 H800-h，12–24周；H+SN+动态数据；T+W+U+C。对应标签和困难区域数量决定 spread。 |
| B18 检索—生成联合对比学习 | 与下游 utility 对齐的 embedding 在 hard negative 和 end-to-end 消费上优于当前分数。 | held-out candidate pools 的 recall@k、hard-negative 胜率、utility ranking 与 end-to-end Δ。 | 模型作者、部署者 | 生成 utility labels；static/near-pose/random controls；scene-ID test；同 K、同 seed、同 denoising budget。 | retrieval embedding；训练→部署；能力；作者/部署者 | hard-negative 和下游都无增益，或 scene-ID shortcut。 | LIVE · TERM-IMPOSSIBLE | M：500–2,000 H800-h，10–20周；H+SN；T+W+C；若替换上游检索接口则 U。utility label 生成次数决定 spread。 |
| B19 来源因果归因辅助训练 | source mask/dropout/swap 能把影响定位到来源 support，并带来 matched benefit。 | held-out source counterfactual 的 influence、matched-mask localization、B_local/B_matched 与 negative control；目标 source 后代全部重算。 | 评测者、模型作者 | source ablation、support-matched mask、negative controls、replay variance、generic-attention control；独立复算。 | provenance/causal training target；训练→消费；可解释可靠性；评测者/作者 | localization 不超过 matched null，或 benefit 不存在/符号不稳。 | LIVE · TERM-IMPOSSIBLE | L：2,000–6,000 H800-h，16–30周；H+SN；T+W+U+C。反事实次数和局部标签/审查成本主导 spread。 |
| B20 可逆状态检查点/分支世界 | versioned commit/rollback 在相同输出质量与延迟下减少永久失败并提高恢复率。 | held-out 长轨迹中 permanent-failure rate、recovery time、false rollback/false accept 和 latency，no-checkpoint 对照。 | 部署者 | fault injection + natural-failure held-out；no-checkpoint、detector 假阳/假阴、版本 hash 与独立 replay。 | runtime/state transaction；部署推理/跨调用；可靠性；部署者 | 无 recovery gain，或 detector 假阳导致不可接受的 rollback/coverage loss。 | LIVE · TERM-IMPOSSIBLE | S：200–800 H800-h，6–14周；H+SN；U+C；若 detector 要学习则 F/T+W。固定 detector 的零 GPU 原型不等于决定性方法结果。 |
| B21 质量—新颖性双门控写入 | gate 在相同 memory capacity 下增加每 slot 的新 support，同时不丢失困难证据。 | held-out 长轨迹的 new-support/slot、冗余率、quality–capacity Pareto 与 difficult-evidence recall，对比 all-write/random/oracle。 | 部署者 | fixed all-write、random、oracle 与 calibration controls；长轨迹；失败写回完整记录；独立复算。 | memory admission/write policy；部署推理/跨调用；可靠性/效率；部署者 | Pareto 无改善，或 gate 锁死难例/提高污染。 | LIVE · TERM-IMPOSSIBLE | S：200–800 H800-h，6–14周；H+SN；F/T+W+U+C。长轨迹与误拒控制决定 spread。 |
| B22 可学习重排与 slot assignment | 在候选 multiset 不变时，角色化 slot assignment 能改善局部几何/外观，而不是靠换候选。 | fixed candidate multiset 的 paired region RGB/depth/pose Δ、slot permutation stability 和 latency。 | 模型作者、部署者 | same-candidate permutation、fixed-order、random、oracle controls；held-out scene；参数/候选数/算力匹配。 | slot assignment；训练→部署；能力/效率；作者/部署者 | same multiset 无增益，或 role 在场景间不稳定。 | LIVE · TERM-IMPOSSIBLE | M：500–2,000 H800-h，10–20周；H+SN；F/T+W+C；若无 slot-role hook 则加 U。 |
| B23 目标视图分解与局部专家 | 目标可见区/深度层/遮挡边界的分解和局部专家减少新区域、support、boundary error。 | held-out 区域/边界 mask 上 RGB/depth/ghosting 与 seam rate，在相同 FLOP 下对比 monolithic baseline。 | 部署者 | depth/occlusion mask held-out；monolithic、full-repair、sham-mask、seam/compute controls。 | target decomposition/expert routing；训练→部署；能力；部署者 | regional gain 不存在，或 seam/compute 超预算。 | UNPRICED · TERM-IMPOSSIBLE | 仅量级 L：2,000–6,000 H800-h，16–30周；专家数、分解标签和 FLOP budget 未定义，不能给诚实 decisive price。至少 H+SN+T+W+U+C。 |
| B24 几何一致神经压缩记忆 | 在相同 memory bytes 下，3D-aware quantization 保留局部几何/RGB 并改善检索延迟。 | matched memory/latency 的 held-out local RGB/depth/normal error、retrieval throughput 和 quantization error。 | 部署者 | uncompressed、2D quantizer、memory/latency matched controls；长会话 held-out；独立复算。 | memory compression/codebook；训练→部署；效率/能力；部署者 | 质量损失超预登记预算，或没有 Pareto gain。 | LIVE · TERM-IMPOSSIBLE | M：500–2,000 H800-h，10–20周；H+SN；T/F+W+U+C。码本规模和长会话决定 spread。 |
| B25 RGB–depth–normal–semantic 多任务生成 | 辅助几何/语义任务在 held-out 域上提高几何与 RGB，而不以任务冲突换来表面分数。 | paired RGB/depth/normal/semantic/reprojection Δ，按任务和域聚合，含 RGB-only 与任务消融。 | 模型作者 | 有语义/深度标签的 held-out；RGB-only、各任务 ablation、task-conflict controls；独立复算。 | multi-task decoder/objective；训练→部署；能力；作者 | 几何无改善或 RGB 明显退化。 | UNPRICED · TERM-IMPOSSIBLE | 仅量级 L：2,000–6,000 H800-h，16–30周；跨任务标签、decoder 和损失权重合同未定，不能给决定性价。须 H+SN+T+W+U+C。 |
| B26 不变/可变外观分解 | content/geometry 与 appearance 双流能跨曝光/光照保持几何，并实现可控 appearance swap。 | paired illumination/exposure held-out 的 geometry/RGB Δ、swap controllability 和 identity preservation。 | 模型作者 | 多条件同场景 held-out；no-disentangle、identity、shuffle、swap 可辨识性与 leakage controls。 | representation factorization；训练→部署；能力/可控性；作者 | 跨光照无增益，或 swap 不可辨识/身份泄漏。 | UNPRICED · TERM-IMPOSSIBLE | 仅量级 L：2,000–6,000 H800-h，16–30周；paired illumination 数据合同和可辨识判据未定。须 H+SN+T+W+U+C。 |
| B27 可微遮挡/epipolar/flow/碰撞约束 | 几何约束在同等 RGB 质量/算力下减少穿透、遮挡排序和边界错误。 | held-out calibrated scenes 的 3D violation、boundary/depth/flow error 与 RGB Δ，相对 pixel-only 及逐约束消融。 | 模型作者 | static/dynamic calibrated held-out；pixel-only、constraint ablation、dynamic false-penalty controls；独立复算。 | geometric training objective；训练→部署；能力/可靠性；作者 | 3D 无增益或动态真值被错误惩罚。 | LIVE · TERM-IMPOSSIBLE | M–L：1,500–6,000 H800-h，12–24周；H+SN；T/F+W+U+C。约束权重、动态覆盖和多 seed 决定 spread。 |
| B28 长程难例课程与在线挖掘 | 按真实失败桶做 curriculum/mining 能降低 tail-risk 或达到同质量所需的训练样本。 | held-out error buckets 的 tail quantile、样本效率和固定 compute/data 下的 paired Δ，相对 random curriculum。 | 模型作者 | 先封存失败分类规则；random/no-mining、同数据量、无 future-label leakage、独立 held-out。 | data curriculum/mining；训练/微调；可靠性/效率；作者 | tail/sample efficiency 无增益，或 mining 使用未来答案/暴露 panel。 | LIVE · TERM-IMPOSSIBLE | S–M：500–2,000 H800-h，10–20周；H+SN；T/F+W+C；若改训练接口再 U。失败标注和采样偏差主导 spread。 |
| B29 教师集成到单模型的不确定度蒸馏 | 单模型在较低推理成本下保留教师质量/校准和拒答收益。 | teacher-independent held-out 上 quality、ECE、tail risk、latency/energy；与 direct model、teacher 和 compute-matched controls 比较。 | 部署者 | 教师/学生、独立场景、直接 baseline、等质量/等算力控制；独立复算。 | uncertainty distillation；训练→部署；效率/可靠性；部署者 | 质量/ECE 损失超预算，或没有实际成本节省。 | LIVE · TERM-IMPOSSIBLE | L：2,000–6,000 H800-h，16–30周；H+SN；T/F+W+U+C。teacher rollout 数和蒸馏覆盖决定 spread。 |
| B30 长程时序 Transformer + 扩散混合 | temporal backbone + diffusion 在固定 memory/latency 下减少长视频 temporal error 和回访 drift。 | held-out long-video 的 temporal LPIPS/FVD、revisit drift、memory/latency，与 local-window baseline 比较。 | 模型作者、部署者 | 长视频 held-out；local-window、cache/offline、context-length 和 compute-matched controls；独立复算。 | temporal architecture/cache；预训练/训练→部署；能力/效率；作者/部署者 | 长程无增益或资源预算失败。 | UNPRICED · TERM-IMPOSSIBLE | 仅量级 XL：6,000–20,000+ H800-h，26–46周；视频长度、FVD contract、主干接口未定义，不能给诚实 decisive price。须 H+SN+T+W+U+C。 |
| B31 主动视角/传感器协同策略 | 在真实可执行平台上，每次 observation/time 能获得更多未来几何/RGB utility。 | held-out environment 的 gain per observation/time、failure rate、信息增益，相对 random/greedy/oracle policy。 | 部署者、agent/robot 作者 | 真实 action/sensor interface、held-out environments、真实 trajectory；sim-to-real、random/greedy/oracle controls。 | active sensing policy；用户闭环；能力/决策；部署者/agent | 平台不可执行、sim-to-real 失败或 utility 无增益。 | UNPRICED · TERM-IMPOSSIBLE | 仅量级 L–XL：3,000–20,000 H800-h，20–40周；传感器、平台、动作数据和许可未定义，不能给决定性价格。须 H+SN+T+W+U+MC+C。 |
| B32 生成后局部修复扩散 | 只在 conflict mask 内低步数修复，能提升支持区且保持 mask 外 bytes/指标不变。 | held-out conflict-mask 的 local quality、boundary seam、outside-mask pixel/hash preservation 与 fixed-budget Δ。 | 部署者、评测者 | no-repair/full-repair/sham-mask；mask 外 byte/latent 守卫；matched steps/compute；独立复算。 | post-generation repair；部署后处理；可靠性/质量；部署者/评测者 | support 无改善，或 mask 外漂移/接缝超过阈值。 | LIVE · TERM-IMPOSSIBLE | M：500–2,000 H800-h，10–20周；H+SN；F/T+W+U+C。mask 质量、修复步数和 boundary controls 决定 spread。 |
| B33 跨场景元学习与快速适配 | 1/5/10 帧无标签适配提升未见 scene，且 forgetting 有界。 | held-out domain episodes 的 0/1/5/10-frame curve、forgetting、adaptation time，与 zero-shot/standard fine-tune 比较。 | 部署者 | meta-train/dev/test scene split；zero-shot、standard fine-tune、future-leak、forgetting controls；三 seed。 | meta-learning/adaptation；预训练→在线部署；能力；部署者 | 早期适配无增益或 forgetting 超阈值。 | LIVE · TERM-IMPOSSIBLE | L：2,000–6,000 H800-h，16–30周；H+SN；T/F+W+U+C。episode 数、二阶训练和域跨度决定 spread。 |
| B34 安全/拒答式世界模型 | calibrated abstention 在固定 coverage 下降低 risk，并且额外观测后的重试有净收益。 | held-out coverage–risk/ECE、abstention risk、re-observe utility，相对 always-answer/random/oracle。 | 部署者、评测者 | risk bucket、coverage 预注册；always-answer/random/oracle；post-abstention reobserve；独立复算。 | decision/assurance head；部署推理；安全/可靠性；部署者/评测者 | 固定 coverage risk 不降，或拒答后重新观测无净收益。 | LIVE · TERM-IMPOSSIBLE | S：200–800 H800-h，6–14周；H+SN；F/T+W+C，若拒答必须进入主调用则加 U。 |
| B35 统一 action/observation 接口的可学习控制器 | 学习的 action/state protocol 能在固定 action budget 下改善任务结果、组合动作和回退恢复。 | held-out tasks/long trajectories 的 success、quality、recovery 和 compositionality，相对 hand-coded API/random policy。 | 部署者、agent/任务作者 | 先冻结 user task、action/observation schema、可执行平台、长轨迹与 failure labels；hand-coded/random/oracle controls；独立复算。 | action/observation contract + controller；训练→用户闭环；能力/决策；部署者/agent | task contract 未定义，或 compositionality/recovery 无改善。 | UNPRICED · TERM-IMPOSSIBLE | UNPRICED；任务、action space、真实数据和多消费者边界尚未定义。补齐后仅能给 L–XL：3,000–20,000+ H800-h，20–40周 的量级参考；须 H+SN+T+W+U+MC+C。 |

## Q2：最便宜的可信方法路径

**本学期没有 Part B 路径能完成。**

如果 owner 明确解除 F/T + W + C，并立即启动 held-out 申请，单条最便宜、仍直接改变生成系统而不是只做安全决策的条件路径，我会选 **B21 质量—新颖性双门控写入**：

- 目标不是“写入更少”本身，而是固定 memory capacity 下提高 new-support-per-slot，同时保住困难证据；
- decisive contract 是 held-out 长轨迹、all-write/random/oracle、困难证据 recall、污染率、capacity–quality Pareto、独立复算；
- 条件价格约 **200–800 H800 GPU-hours、6–14 周实验/审查，再加 ScanNet++ 的 2–6 周申请关键路径**；若写回需要上游 hook，再增加接口工作；
- 必须解除 F/T + W + U + C（若已有可用写回 hook，U 可缩小）。这只是成本上最小的直接生成方法候选；本轮没有做 occupancy，也没有给 novelty authorization。B34 可能更便宜，但它是 risk/abstention 决策方法；B20 的固定 rollback wrapper 可能几乎不耗 GPU，但没有 held-out end-to-end 结果就不能称为 owner 原来要的决定性方法结果。

## Q3：按“每单位授权成本带来的可执行候选/决策价值”排序

这不是绝对科学价值排名；单项授权彼此不替代。排序如下：

1. **Fine-tuning（实际需与 new weights 成对）**：最便宜地打开 B15、B18、B20–B22、B28、B32、B34 等 head/adapter/controller 路线；代价是仍需 held-out 和 C。
2. **New weights**：让 adapter/head/controller 成为可部署 artifact，授权面小；单独没有训练行为，不能替代 F/T。
3. **Upstream modification**：技术上最便宜（账本曾估接口层 0 GPU、1–3 天），能打开 state write-back、slot-role、repair、abstention 等 hook；但单独主要买到“能接入”，不买到 method evidence。
4. **Training（从头或更广泛联合训练）**：覆盖面最大，可打开 B3/B5/B7–B11/B13/B19/B23–B33，但 data、稳定性和 compute 令 grant cost 高；若只给 T 而不给 W/F 或 U，很多路线仍不可部署。
5. **Compute**：必要但不是充分条件；800 h 只可能支持 premise screen，买不到 held-out、训练权重或上游权限，单独边际解锁最低。
6. **Multiple consumers**：主要购买跨消费者外部效度和泛化，不是让任一单消费者候选先跑起来；协调和评测成本最高，作为第二阶段授权。

若 owner 只问“哪一个单项最便宜能改变最多代码路径”，答案是 U；若问“哪一个单项最便宜能买到一个可能的学习型方法”，答案是 F，但必须同时给 W 和 C。把两种口径混为一个排名会误导解冻决定。

## Q4：诚实建议

**现在不要解除 freeze。**

先需要 owner 明确四件事：
1. 是不是愿意把目标从本学期交付改成至少 8–14 周的后续工作；
2. 是否愿意签 ScanNet++ v2 申请，并接受 2–6 周 lead 和 held-out 未必获批；
3. 是一次性给 F/T + W + U + C 的完整 bundle，还是只给某一个空授权（空授权会把候选停在接口或首图）；
4. 是否愿意把第二 consumer、任务/action contract 和独立复核者写进验收条件。

在这四点没有答案前，解除 freeze 只会买到 wrapper、首轮图或开发面板，买不到能经受审查的 method result。new_method_validated=false、novelty_authorization=NONE 继续保持。

## 复核执行披露

本轮实际只读核查了仓库、三份 pinned source 和账本，并由并行只读复核核对候选、约束和价格带。项目要求的外部 codex exec -m gpt-6-astra ... model_reasoning_effort=ultra 调用在本机尝试两次，均在模型启动前因 “failed to initialize in-process app-server client: Operation not permitted” 失败；因此这里没有虚构一个外部模型裁定。该工具失败不改变上述仓库事实，也不构成 owner 授权。
