# Round 25-Q：Part A 合同过滤结果（不评估 occupancy）

日期：2026-09-20。本轮只过滤 R24-P 的 Part A：A1–A25、补充 A45–A60、实现特化 A87–A100，共 55 项。候选原文位置分别为 work/agents/CODEX_R24P_GENERATION_20260920.md:30-219、:538-648、:798-894。Part B 不在本轮范围内。

本轮的“LIVE”只表示：能在冻结消费者、零 GPU 的限制下，用 CPU 或已有封存量裁定一个狭义、可证伪的研究 claim。它不表示方法成立、创新成立、生成质量改善或 occupancy 结论。NEEDS-RESOURCES 表示 claim 可证伪，但最小合同需要 fresh frozen-consumer forward、独立 RGB-D/pose reference、合资格 held-out 数据或尚未保存的中间量。NO-CLAIM 表示原候选只有工程动作、proxy 或诊断日志，无法在不改写成空泛句子的情况下形成 reviewer 必须接受为新的研究 claim。NO-STAKEHOLDER 表示没有已指定的决策者会因结果改变动作。本轮不使用 prior-art 或 occupancy 作为死因。

## 先核实的运行边界和源码事实

- 当前 handoff 明确：已有 fixed-context forward 只是暴露 development scene 上、绕过 VMem retrieval 的结果；Gate0 仍为 BLOCKED_INDEPENDENT_REVIEWS_ONLY，不能启动正式 forward、评分或未来答案访问（docs/RESEARCH_HANDOFF_CURRENT.md:1-9,1148-1158）。
- 报告范围是两个暴露 development sequence、一个 frozen consumer，不是独立 held-out 评价；消费者约束为不训练、不微调、不加权重、不改 upstream source（docs/report/TECHNICAL_REPORT_20260918.md:57-72,96-104）。治理旗标仍为 new_method_validated=false、novelty_authorization=NONE（:400-404,542-547）。
- 三份 pinned pipeline 完全相同，SHA-256 均为 90a45f452a4f734b3371fb526c566162026e5d900e0c8204709dd57f44ef1d7e：
  - work/S17C_interface_preparation/isolated_vmem_source/modeling/pipeline.py
  - work/S17_cpu_preflight/original/modeling/pipeline.py
  - work/S102_gate0_3dmatch/adapter_v1/sources/vmem_pipeline.py
- 三份文件均在 line 1249 调用 get_context_info(target_c2ws, use_non_maximum_suppression)，line 1263 做 torch.cat([context_c2ws, target_c2ws])，line 1265 调用 get_translation_scaling_factor(all_c2ws)。
- self.c2ws 的直接初始化/追加只有 line 180 的 self.c2ws = [c2w] 和 line 1297 的 self.c2ws.append(...)；未发现 setter 或重新赋值。但 line 1360 还有 undo 路径的 self.c2ws.pop()。因此只能说“两处 direct create/append，另有 pop 删除”，不能说“所有 mutation 只有两处”。scale 函数改的是由 torch.cat 得到的局部 all_c2ws，不是 self.c2ws 列表。
- Astra 外部复核命令按项目要求尝试两次，均在本机初始化 app-server 时以 Operation not permitted 退出，没有输出文件或仓库改动；本文不把失败进程当科学意见。

## Q1 — Survivor table

registry 的格式为 object × time × claim type × stakeholder。表格中 NC 是 negative control。状态计数：LIVE 10、NEEDS-RESOURCES 16、NO-CLAIM 27、NO-STAKEHOLDER 2；因此 45/55 项本轮不存活。

| ID | Claim | Estimand | Stakeholder | 最小证据合同、NC、零 GPU | Registry | Kill | Status |
|---|---|---|---|---|---|---|---|
| A1 | — | 事务正确性可测，但这是 wrapper 工程控制；没有 reviewer-new 的非工程句子。 | 模型作者/部署者可用，但不改变研究 claim。 | CPU fault matrix 可做；success/no-op/partial-append NC 不能补足 claim 类型。 | state × pre-call × reliability × author/deployer | 仅能 kill 实现，不能救活研究 claim。 | NO-CLAIM |
| A2 | — | copy-on-write 与 replay 是控制机制；byte identity 不是 world-model estimand。 | 作者/评估者可用，但没有独立研究决定。 | CPU branch trace、顺序置换 NC；仍是工程验收。 | state × pre-commit × reliability × author/evaluator | 只能否定实现，不能形成 reviewer-new claim。 | NO-CLAIM |
| A3 | — | provenance completeness 的真值边界和语义消费 oracle 未定义。 | 未指定一个改变动作的 stakeholder。 | hash-chain/删源可记录，但无可判定分母；随机删源 NC 不足。 | provenance × through-call × measurement × evaluator | 无法定义“所有真正消费边”的真值集合。 | NO-CLAIM |
| A4 | 小范围 SE(3)/尺度 query 共识能降低候选选择对 query 扰动的脆弱性。 | 固定目标、扰动集、K 下，consensus 与 single 的 mean Jaccard/Kendall instability 差；按窗口先聚合。 | 部署者、评估者。 | CPU candidate trace；zero-perturb、random-list、single-query NC；零 GPU可裁定选择层 claim。 | retrieval × pre-call × robustness × deployer/evaluator | 稳定性不降，或 coverage/可用候选下降超预设阈。 | LIVE |
| A5 | 覆盖–距离–新颖性规则在固定 K 下提高 union support 且不增重复。 | coverage@K、duplicate-rate@K、hole-rate@K 相对 released IDs 的差；固定窗口聚合。 | 部署者。 | CPU 几何/深度重投影；distance-only、shuffle-score、no-op NC；只裁定选择层。 | retrieval × pre-call × selection × deployer | coverage 不增且重复不降，或增益只来自改分母/近邻代理。 | LIVE |
| A6 | 遮挡/深度风险优先选择在固定 K 下减少冲突和空洞。 | conflict-pixel-ratio@K 与 hole-ratio@K 相对 distance selector 的差；分 clean/occluded。 | 部署者、下游 agent。 | CPU saved depth/pose z-buffer；clean geometry、distance-only、shuffle-risk NC；不写生成质量。 | retrieval × pre-call × risk × deployer/agent | 冲突/空洞不降，或收益完全由更近造成。 | LIVE |
| A7 | 分离 freshness 与 novel-surface 配额可在固定 K 下同时提高两者，或明确不可兼得的缺口。 | freshness 与 novel coverage 的 trade-off 没有预登记任务权重和可接受下降。 | 未指定动态/静态任务 owner。 | CPU 可算双目标，但不能决定采用哪个 Pareto 点。 | retrieval × pre-call × multi-criterion × deployer | 只能列曲线，没有 stakeholder decision。 | NO-STAKEHOLDER |
| A8 | — | 合同适配器的 round-trip residual 可精确测，但它是接口工程 guard；按项目原则不构成独立 reviewer-new claim。 | Gate0/部署者/评估者可用。 | CPU 立方体、pose、单位/轴序/handedness 与 invalid NC；可完成但属于 guard。 | input-contract × pre-call × reliability × evaluator/deployer | 合法 residual 超阈或非法输入静默接受，只能否定 guard。 | NO-CLAIM |
| A9 | — | query-only、normalization-only、joint hash matrix 是诊断拆分，不是可接受的研究 claim。 | 作者/评估者可观察。 | CPU 条件包/hash；fixed-all-c2ws、joint-only NC；缺少会改变的下游决策。 | normalization × pre-conditioning × diagnostic × evaluator/author | 三臂不可区分只能 kill 诊断实现。 | NO-CLAIM |
| A10 | virtual context 若被消费者接受，应降低目标视角空洞/重投影误差。 | reprojection residual、hole-ratio 与最终 geometric error，相对 real-context/distance-only。 | 部署者、下游 agent。 | CPU z-buffer 只覆盖前半段；interface acceptance、synthetic occlusion NC；消费/生成 effect 需 fresh forward。 | conditioning × pre-call × geometry × deployer/agent | 接口拒绝 virtual frame，或 hole/conflict 不降。 | NEEDS-RESOURCES |
| A11 | — | unique IDs/slot role 只是规则输出，没有绑定 downstream utility 或可接受 trade-off。 | 未指定。 | CPU candidate list 可数；intentional duplicate NC 不能定义采用门槛。 | retrieval × pre-call × selection × deployer | unique count 上升不等于决策改善。 | NO-CLAIM |
| A12 | risk gate 在相同 coverage 下减少 geometry error 和 writeback contamination。 | 固定 coverage c 下 error rate 与 contamination rate，相对 always-generate。 | 部署者、下游 agent。 | 封存输出加 independent RGB-D/pose；risk-permutation、no-abstain、all-reject NC；当前缺件。 | admission × pre-call × risk/abstention × deployer/agent | 同 coverage error 不降、拒答全覆盖或 risk 反向。 | NEEDS-RESOURCES |
| A13 | — | clean-state scheduler 的顺序不变性是工程控制，非独立 reviewer-new claim。 | 作者/部署者。 | CPU action permutation、no-op、非法序列 NC 可做；只能验收实现。 | state × between-call × reliability × author/deployer | 合法顺序仍 divergence 只是否定实现。 | NO-CLAIM |
| A14 | 自适应候选预算能在固定 K 下不增风险而降低平均候选/CPU 成本。 | 等 K 下的 coverage/risk/latency/candidate-count Pareto frontier，相对 fixed-budget。 | 部署者。 | CPU query-entropy/visibility trace；fixed-budget、all-history、random-budget NC；quality/risk 外推需独立 reference。 | retrieval × pre-call × resource-quality × deployer | 无 cost saving，或 coverage/risk 严格变差。 | LIVE |
| A15 | 少量可逆探针/重访能提高终点新覆盖并降低长程失败。 | 等 probe budget 下 terminal error 与 long-horizon failure，相对 no-probe/random-probe。 | 部署者、下游 agent。 | 真实交互轨迹和独立终点/失败 reference；零 GPU不可完成。 | trajectory × between-call × utility × deployer/agent | terminal 偏差超阈或 coverage 不超过 random probe。 | NEEDS-RESOURCES |
| A16 | 多 seed 接受器能降低固定接受预算下的几何/来源尾部错误。 | tail geometric error/consistency，相对 single-seed/no-filter，接受预算固定。 | 部署者、下游 agent。 | fresh multi-sampling 与 independent reference；random-seed/no-filter NC。 | sampling × pre-commit × risk/acceptance × deployer/agent | tail error 不降，或成本超预设且无收益。 | NEEDS-RESOURCES |
| A17 | 局部修复/拒写能减少冲突且保持 mask 外像素不变。 | mask precision/recall、outside-mask pixel-change、contamination，相对 no-repair。 | 部署者、评估者。 | 生成帧与 independent reference；identity/no-op mask、面积匹配 NC。 | postprocess × post-generation × quality/risk × deployer/evaluator | 冲突不降、mask 外改动超阈或不优于面积 NC。 | NEEDS-RESOURCES |
| A18 | 质量–新覆盖准入能降低 slot 冗余和后续污染。 | unique coverage/slot 与 downstream contamination，相对 unconditional append。 | 部署者、下游 agent。 | 多步生成、封存输出、independent reference；always-append/no-write NC。 | admission × post-generation × utility/risk × deployer/agent | coverage 不增或 contamination 不降。 | NEEDS-RESOURCES |
| A19 | — | read→consume dual hash 能检错，但它是接口审计工程，不是独立 reviewer-new claim。 | 作者/评估者可用。 | CPU stub/saved packet；permutation、padding、source-swap、no-op NC；只能形成 guard receipt。 | provenance × through-call × measurement × author/evaluator | 注入错位漏检或合法误报，只否定 guard。 | NO-CLAIM |
| A20 | 单调校准能保持 rank 并改善 selector probability calibration。 | ECE/Brier 与 rank-stability，相对 uncalibrated，固定 dev panel。 | 部署者、评估者。 | outcome labels、跨序列 independent reference；temperature-only/shuffled-label NC。 | selection × pre-call × calibration × deployer/evaluator | ECE/Brier 不降或跨序列恶化。 | NEEDS-RESOURCES |
| A21 | — | photometric/depth normalization 只有漂移与 round-trip proxy，没有指定下游决策。 | 未指定。 | CPU paired transform 可做；identity/geometry-only NC 不能补足 stakeholder。 | input-contract × pre-call × reliability × deployer/data engineer | 指标改变却不能决定是否采用。 | NO-CLAIM |
| A22 | 固定 post-selection 下，删除/替换 source 能测出其对已封存几何消费者的受限 influence，并检验空间支持。 | 只对当前封存的 depth_m 与 source_pixel_identity 做 source-level delta/identity-support overlap，按 replay variance 标准化；当前没有 RGB output，因此不写 F11−F00，也不是 total causal benefit。 | 评估者、下游 agent。 | 现有 exact replay 包（predict_01/：model_calls=0，只有 depth_m 与 source_pixel_identity）；LOO、matched replacement、replay-noise、matched-mask NC；只限 CPU source/depth geometry artifact。 | provenance × post-selection × measurement/causal-diagnostic × evaluator/agent | effect 不超过 replay variance、localization 不超面积匹配，或不能 exact replay。 | LIVE |
| A23 | — | typed FSM 是工程调度/复核控制，项目原则明确不把它作为算法创新。 | 作者/部署者可用。 | CPU 穷举 action sequence、合法/随机 FSM NC；只能验收实现。 | state × between-call × reliability × author/deployer | 非法漏放或合法误拒，只否定实现。 | NO-CLAIM |
| A24 | Pareto selector 能在声明预算下达到低风险/高 coverage 前沿。 | 固定 CPU/显存/latency budget 下 quality/risk/coverage，相对 baseline frontier。 | 部署者、产品决策者。 | quality 需真实 output/reference；CPU proxy 仅前筛；fixed-budget/no-op NC。 | resource policy × pre-call × utility × deployer/product | frontier 不支配 baseline，或 proxy 与真实 quality 不相关。 | NEEDS-RESOURCES |
| A25 | — | failure-type fallback 是工程恢复策略；没有超出实现正确性的 reviewer-new claim。 | 部署者/作者可用。 | CPU exception injection、no-fault/universal-fallback/wrong-label NC；只能验收恢复。 | failure handling × post-failure × reliability × deployer/author | contamination 不降或原因被改写，只否定策略。 | NO-CLAIM |
| A45 | — | epoch token 是 stale-cache guard；stale-read count 不是独立研究 claim。 | 作者/部署者可用。 | CPU lifecycle permutation、same-epoch/no-op/expired-cache NC；属于 guard。 | state × between-call × reliability × author/deployer | 跨 epoch 被接受或同 epoch 被误拒，只否定 guard。 | NO-CLAIM |
| A46 | — | shadow selector 只记录 policy difference，没有预登记的采用决策或 downstream estimand。 | 未指定。 | CPU sidecar log、released-policy/no-op NC；观察日志不能单独成为 claim。 | retrieval × pre-call × measurement × evaluator/author | 无 decision threshold。 | NO-CLAIM |
| A47 | — | capability negotiation 是接口拒绝机制，按项目原则属于工程调度/合同 guard。 | 作者/部署者可用。 | CPU manifest matrix；valid/invalid/replay NC；只能形成 guard receipt。 | input-contract × pre-call × reliability × deployer/author | 漏拒或误拒，只否定 guard。 | NO-CLAIM |
| A48 | — | dry-run/full-run 是控制流检查，不是 world-model 或 selection claim。 | 作者/部署者可用。 | CPU stub/fault matrix、valid/no-op/late-failure NC；只能验收。 | request-gating × pre-call × reliability × deployer/author | 非法漏过或合法误拒，只否定实现。 | NO-CLAIM |
| A49 | — | sidecar provenance chain 是数据血缘工程，没有独立语义 oracle。 | 评估者/数据工程师可用。 | CPU transform fixture；swap/duplicate/late-GT NC；不能推出像素正确。 | provenance × through-call × measurement × evaluator/data engineer | 丢 parent 或错配漏检，只否定工具。 | NO-CLAIM |
| A50 | — | admission queue/commit barrier 是并发工程控制，不是独立方法 claim。 | 部署者/作者可用。 | CPU concurrent/interrupted simulator；serial/abort/overload NC；只能验收。 | state × between-call × reliability × deployer/author | uncommitted epoch 可见或 deadlock，只否定实现。 | NO-CLAIM |
| A51 | — | camera convention guard 是 A8 的具体子例，R24-P 没给独立研究 claim。 | A8 的 stakeholder，但未独立指定。 | 可并入 A8 的 axis/handedness NC。 | input-contract × pre-call × reliability × deployer/data engineer | 只能重复 A8 的 round-trip。 | NO-CLAIM |
| A52 | — | resize/crop 更新 K 是数据合同修复，没有独立 reviewer-new claim。 | 数据工程师/部署者可用。 | CPU checkerboard/known-K、identity/wrong-K NC；只能验收。 | input-contract × pre-call × geometry × data engineer/deployer | residual 不优于 naive 只否定修复。 | NO-CLAIM |
| A53 | debounce 可减少半成品调用/重复选择，同时把终点 pose 偏差控制在预算内。 | debounce 改变用户轨迹；没有动作语义、pose 偏差和 latency 的产品 owner。 | 未指定。 | event-log replay 可做，但不能定义采用门槛。 | interaction × between-call × reliability/utility × product | 缺 predeclared trajectory trade-off。 | NO-STAKEHOLDER |
| A54 | — | deterministic seed schedule 只有可追溯性 claim；完整 output replay/quality 需要 forward，seed map 本身不构成研究 claim。 | 未指定。 | CPU seed property/collision NC；不能推出 output claim。 | sampling × pre-call × reproducibility × author/evaluator | seed-only 结果不改变决策。 | NO-CLAIM |
| A55 | SE(3) smoothing 若有效应减少高频抖动且不超过终点/投影预算。 | high-frequency angular/linear acceleration 变化与 terminal reprojection error，相对 raw trajectory。 | 部署者、下游 agent。 | CPU 轨迹加独立 reference、identity/sharp-turn NC；视频 temporal claim 需 fresh forward。 | trajectory × pre-call × quality/utility × deployer/agent | 抖动不降或 sharp-turn/terminal error 超阈。 | NEEDS-RESOURCES |
| A56 | — | lookahead cache 只有 latency/stale-use 工程指标，没有采用阈值或科学决策。 | 未指定。 | CPU cache simulator、path-change invalidation NC；不能形成独立 claim。 | retrieval × between-call × resource/reliability × deployer/author | 只能报告更快/更慢。 | NO-CLAIM |
| A57 | — | periodic compaction 的 N、合并规则和容量–质量 estimand 未冻结，只是索引工程。 | 未指定。 | CPU bytes/index time 可测；no-compaction NC 不能固定质量合同。 | state × between-call × resource/reliability × deployer/author | 参数一换结论即变，缺预注册 decision。 | NO-CLAIM |
| A58 | quality gate 应阻止低质帧成为 anchor 并降低后续 residual，而非只提高清晰度。 | matched-retention 下 downstream residual/contamination 与 quality–residual correlation，相对 unconditional anchor。 | 部署者、下游 agent。 | 历史帧与 independent geometry/reference；sharp-but-wrong、blurry-but-correct、multi-threshold NC。 | admission × pre-commit × quality/risk × deployer/agent | quality 与 residual 无关、residual 不降，或拒绝清晰正确帧超预算。 | NEEDS-RESOURCES |
| A59 | latent/embedding cross-check 若有效应发现配对错位并降低其下游错误。 | mismatch recall 与过滤后的 output-error/duplicate-rate reduction，相对 no check。 | 模型作者、部署者。 | CPU swapped/valid-pair detector NC 可测；完整 output effect 需 forward/reference。 | provenance × pre-call × reliability × author/deployer | 错配漏检、合法误拒，或 output error 不降。 | NEEDS-RESOURCES |
| A60 | — | all-history probe 是选择层压力测试，没有公平消费合同或采用门槛，不能称 upper-bound claim。 | 未指定。 | CPU exhaustive history、fixed-K/random/no-op NC；不能决定部署。 | retrieval × pre-call × measurement/resource × evaluator/deployer | 结果不能作为公平上界或没有 adoption threshold。 | NO-CLAIM |
| A87 | — | immutable functional conditioning 是 in-place mutation guard，不是独立 reviewer-new claim。 | 作者/部署者可用。 | CPU clone/hash property、intentional in-place/no-op NC；只能验收。 | state × pre-conditioning × reliability × author/deployer | 合法重复调用 hash 漂移，只否定 guard。 | NO-CLAIM |
| A88 | robust anchor/MAD scale 能在整体平移/旋转/缩放 metamorphic test 下减少 camera residual。 | Plücker norm/camera residual 与 metamorphic invariance，相对 slot-0 scale；pixel effect 分开。 | 模型作者、部署者。 | CPU pose/tensor metamorphic、slot-0/medoid/no-scale NC；consumer validity/fresh pixels 需 GPU。 | normalization × pre-conditioning × geometry × author/deployer | invariance 不改善、residual 增大或越出合同。 | NEEDS-RESOURCES |
| A89 | per-frame mass cap 能在固定 K 下减少单 frame 吸走全部质量并提高 weighted unique support。 | frame-mass entropy、duplicate fraction、unique visible support@K，相对 uncapped selector。 | 部署者、评估者。 | CPU saved surfel/timestep records；cap=∞、uniform、one-frame-dominant NC；选择层可裁定。 | retrieval × pre-call × selection × deployer/evaluator | unique support 不增、pool exhausted，或 coverage/recall proxy 降超阈。 | LIVE |
| A90 | per-surfel contribution normalization 能减少重复计权并提高跨 renderer resolution 的选择稳定性。 | source-mass concentration 与 ID churn across resolutions，相对 raw accumulation。 | 评估者、部署者。 | CPU renderer traces；single-hit/no-dup、resolution-shuffle NC；选择层可裁定。 | retrieval × pre-call × robustness × evaluator/deployer | 重复敏感性不降，或 coverage proxy 降超阈。 | LIVE |
| A91 | calibrated focal scale/principal point 能使 retrieval probe 更符合声明的 camera contract。 | visible-surfels/occlusion residual 与 candidate-ID churn，相对 fixed-scale probe。 | 部署者、评估者。 | CPU known-K 与预登记 focal grid；wrong-K、future-depth-tuned、fixed-scale NC；只裁定 probe contract。 | input-contract × pre-call × geometry × deployer/evaluator | residual/churn 不降，或使用 future depth 调参。 | LIVE |
| A92 | min/softmin trajectory distance 能避免平均 pose 落在无观测中间点并提高 target-level support。 | per-target minimum distance/coverage 与 candidate stability，相对 average-pose ranking；按 target 先聚合。 | 部署者。 | CPU multi-target pose；single-target、average-pose、random-target NC；选择层可裁定。 | retrieval × pre-call × selection × deployer | 任一 target coverage 下降且无预登记权重解释，或单点变好而其余 targets 崩溃。 | LIVE |
| A93 | — | nearest-gap threshold 只是 NMS 参数规则；distinct-K 不是质量 estimand，也没有缺槽代价合同。 | 未指定。 | CPU density sweep/fixed-threshold/no-NMS NC 只能验收参数。 | retrieval × pre-call × selection × deployer/author | threshold 改变却不改变任何已声明决策。 | NO-CLAIM |
| A94 | duplicate source-ID attenuation 能在保持总支持量时降低重复造成的 weighted-coverage 偏斜。 | weighted unique coverage 与 duplicate fraction，相对 raw score，固定 K。 | 部署者、评估者。 | CPU candidate weights；concave/no-transform、truly-strong-source NC；选择层可裁定。 | retrieval × pre-call × selection × deployer/evaluator | 偏斜不降，或强来源被压低导致 coverage proxy 超阈下降。 | LIVE |
| A95 | — | deterministic tie-break 是可复现工程规范；tie byte identity 不是独立 reviewer-new claim。 | 作者/评估者可用。 | CPU cross-version/thread/property 与 non-tie NC；只能验收。 | retrieval × pre-call × reproducibility × author/evaluator | tie 漂移或 non-tie 被改，只否定规范。 | NO-CLAIM |
| A96 | endpoint-aware weighting 能在明确 endpoint-priority 任务固定 K 下增加 endpoint support，并显式报告中间代价。 | endpoint coverage 增量与 intermediate-support loss，相对 uniform/reversed weights。 | 部署者、产品决策者。 | CPU trajectory 加 endpoint task contract、uniform/reversed NC；终点生成质量/真实 utility 需资源。 | retrieval × pre-call × utility × deployer/product | endpoint 不增、中间损失超预算，或任务没有 endpoint stakeholder。 | NEEDS-RESOURCES |
| A97 | — | five-list schema validator 是成组状态的工程 guard，不是独立研究 claim。 | 作者/部署者可用。 | CPU write/pop/undo、single-field corruption/valid-sequence/epoch NC；只能验收。 | state × pre-commit × reliability × author/deployer | 漏检/误拒或 undo hash 不一致，只否定 guard。 | NO-CLAIM |
| A98 | saved denoising trace selector 若有效应在固定 trace 集减少 residual。 | consistency/quality per compute，相对 terminal-step/no-selection，禁止 post-hoc oracle。 | 评估者、部署者。 | 需真实 samples_z/trace 和 independent reference；terminal/no-selection/post-hoc NC。 | sampling × post-generation × quality × evaluator/deployer | trace 不存在、效果不超 replay variance，或依赖事后 GT。 | NEEDS-RESOURCES |
| A99 | 同源多 latent consensus decode 若有效应减少 latent variance 并改善 decoded geometry。 | latent variance 与 decoded residual，相对 single latent，固定 source/decoder/reference。 | 模型作者、部署者。 | 同源 multi-latent、decoder/forward、independent reference；median/trimmed/single NC。 | representation × post-generation × quality × author/deployer | median 非有效样本、residual 不降，或需事后挑样本。 | NEEDS-RESOURCES |
| A100 | static/dynamic memory split 若有效应降低动态泄漏且保持静态 revisit consistency。 | dynamic leakage 与 static revisit error/coverage，相对 unsplit memory，分误分类桶。 | 部署者、下游 agent。 | 多步运动数据与 independent reference；CPU flow 仅前筛；all-static/misclassified-motion/unsplit NC。 | state × between-call × risk/utility × deployer/agent | leakage 不降，或 static coverage/consistency 降超阈，或误分类不可界定。 | NEEDS-RESOURCES |

## Q2 — 按决策价值 / 单位成本的前五名

这里的“价值”是结果能否改变一个真实选择，不是工程便利或论文叙事；“成本”是获得决定性 CPU/封存数据证据的代价。

1. **A22，受限 source counterfactual replay。** Claim 是在固定 post-selection 条件下，source 删除/替换能改变已封存几何 artifact 且影响落在其支持区。Estimand 是 depth_m/source_pixel_identity 的 source-level delta，按 replay variance 标准化并与 matched-mask overlap 比较；当前没有 RGB output，不写 F11−F00/F01−F00。Evidence contract 是 exact replay、LOO、matched replacement、replay-noise 与面积匹配 NC；若缺 exact replay，立即改为 NEEDS-RESOURCES。它直接决定是否继续 source-level 机制线，且不需要把影响图冒充 total benefit。
2. **A6，遮挡/深度风险优先选择。** Claim 是 fixed K 下减少 conflict/hole。Estimand 是 conflict-pixel-ratio@K 与 hole-ratio@K 相对 distance selector，按窗口、clean/occluded 分层。Evidence contract 是 CPU z-buffer、distance-only、shuffle-risk、clean-geometry NC。它能决定 selector 是否值得继续，而不是只报告候选 ID。
3. **A5，覆盖–距离–新颖性重排。** Claim 是 fixed K 下增加 union coverage 且不增 duplicate。Estimand 是 coverage@K、duplicate-rate@K、hole-rate@K 的预定义差分。Evidence contract 是 CPU projection、distance-only、shuffle-score、no-op NC。
4. **A14，自适应候选预算。** Claim 是固定 K 下不增风险而降低候选/CPU 成本。Estimand 是 fixed-budget 对比的 coverage/risk/latency/candidate-count Pareto frontier。Evidence contract 是 CPU entropy/visibility trace、fixed-budget、all-history、random-budget NC；主 claim 不能借 CPU proxy 写成未来 RGB 质量。
5. **A4，多假设 query 共识。** Claim 是降低 query perturbation instability。Estimand 是固定扰动集和 K 下 Jaccard/Kendall instability 的差。Evidence contract 是 CPU query trace、zero-perturb、random-list、single-query NC；若 stability 下降或可用候选减少立即停止。

A8、A19、A1、A23、A97 的单位成本更低，但经过本轮严格“reviewer-new”过滤，它们只保留为工程/验收支撑件，不列为 survivor。

## Q3 — 死亡候选的共同失败模式

1. 把 wrapper、guard、cache、日志或参数规则直接写成方法；它描述了动作，没有 reviewer 必须接受的非工程 claim。
2. proxy 没有绑定 decision。稳定性、hash、coverage、清晰度、entropy、latency 都可能是观测量，却没有写清谁因哪个阈值改变动作，也没有唯一聚合顺序。
3. 把 diagnostic 当 benefit。source influence、输入合同、候选重复、packet 差异最多先证明可观测路径，不能自动证明生成更好、几何风险更低或 world model 更可靠。
4. 零 GPU边界与质量 claim 不匹配。A10、A12、A15–A18、A20、A24、A55、A58、A59、A88、A96、A98–A100 需要 fresh consumer output、独立 reference 或合资格 held-out 数据；CPU trace 只能是前筛。
5. negative controls 和 kill condition 没有在生成时固定。很多候选只有“以后比较质量”的方向，没有 no-op、置换、matched-mask、random 或 invalid-contract NC，也没有看到一个观察就停止的条件。
6. 生成轮次仍隐含 slot-first 偏差：先问哪个内部位置能改，再补 claim。Round 24-P 要求的顺序应当反过来：先固定 claim、estimand、stakeholder、minimal evidence contract，再选择可证伪机制。本轮没有使用 occupancy 判断。

## Q4 — 本周零 GPU是否有 survivor？

有。严格 survivor 是 A4、A5、A6、A14、A22、A89、A90、A91、A92、A94；其中 A22 只有在已有 exact replay/几何 source artifact 可读时成立，其余是选择层 CPU合同。首个最有决策价值的 artifact 是 A6 的 CPU-only selector risk receipt（本轮没有创建该文件）：每个 candidate 的 projected conflict、hole、visible-area、固定 K 选择、distance-only 与 clean-geometry negative controls、预登记聚合规则和 kill threshold。它只判断选择层风险 proxy，不调用 VMem、不读 future outcome、不宣称生成质量。

本轮没有改变 new_method_validated=false、novelty_authorization=NONE、800 GPU-hour tranche withdrawn 或 outbound-message 限制。

