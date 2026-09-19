# S43：长期世界模型记忆的颠覆式创新框架审计

- 审计状态：`PARADIGM_HYPOTHESES_ONLY / KEEP_CONDITIONAL / NOT_EXECUTED`
- 冻结时间：2026-09-07T13:43:03Z
- 审计范围：问题重构、近邻排重、可证伪实验和退出条件；不设计或运行 S40 新实验。
- 本轮边界：0 次模型运行，0 次 S40 评分，0 张生成图查看或解码，0 个 S40 tensor/array 正文读取，0 项效果或新颖性结论。
- 新手版结论：现在最值得问的不是“换哪种 attention”，而是“模型把什么当成事实、什么时候应该不相信记忆、以及一条记忆是否真的影响了它应该影响的画面区域”。这些只是待检验问题，还不是创新成果。

本报告严格按 Supervisor-Skills handbook 2.3 的四步组织：第一性原理、房间里的大象、技术周期、Hamming 式重要问题。创新候选同时接受 idea-evaluator 的 fatal-flaw 约束：若自然失败不存在、因果通路不活跃、普通基线已解决、近邻已经等价覆盖，立即停止，不靠换模块救故事。

输入身份：

| 输入 | SHA-256 | 用途 |
|---|---|---|
| `work/S23_innovation_2_geometry/sources/handbook_2_3.md` | `c4a0022cad1bfeb09301d3b78e16f2197693bd170d613e6a2be5e45c73266b59` | 四步颠覆式创新框架 |
| `../Yiyang_LIU_Proposal.pdf` | `12a7e9605511726be84d70e3b4218d0f89508bf9abf719975d41648473768afa` | 研究目标、学期工作量与“先失败、后方法”顺序 |
| `RESEARCH_MEMORY.md` | `4c4ce04f06f6032f1a8c9819ce359f84dd1c657b9070d8bbf51f28928764e454` | 当前项目事实边界 |
| `work/S41_gemini_adversarial_review/primary_retrieval_and_root_review.md` | `fd07dfc743f9a0c3f350f5d719936b74d5d902f3f10910c1a0b30b8ecda4059a` | S41 根审与执行门 |
| `work/S42_baseline_failure_preregistration/PROTOCOL.md` | `89fb44e0b77a85a66fe611cd2f885fed0288229cbb027e04da25fc0631507b3f` | B0/C1/C2 自然失败判据 |
| `work/S42_statistical_preregistration/PROTOCOL.md` | `5e194397c52fae4630e5badfd868f50335a09e0d5820d3cfe3dff07b623449e6` | 配对、校准、区间与停止规则 |
| `work/S42_causal_memory_gap_search/RECONCILIATION.md` | `2cda8410dcc32fe1bfde9de249c78b9f45bf75bc77c3730f6843f45220219958` | G0→G1→G2→D 的 canonical 顺序 |
| `work/S42_causal_memory_gap_search/REPORT.md` | `8693ace94524cafb5b5e44cf72f4011e757266a70a8025bb6839b777efdaf6ea` | 近邻、结构定理与候选因果实验 |
| `work/S41_clip_mean_innovation_audit/AUDIT.md` | `922f708a3b319e98fd5b84116a9a298df349d86700c26aded83e8ce279617475` | 普通机制黑名单与直接近邻 |
| `work/S40_result_readback/revision_v3_3_receipt.json` | `bebc80b8fccf6e8699d4768f6ffab097bcc75f6bca4a7f101ef53e827b0e2e9d` | readback v3.3 修订身份 |
| `work/S40_result_readback/source_review_v3_3.json` | `70d4c48a6940778247763c901637e18e231b926f4733ac8edb64923ef0240484` | v3.3 第一份源码 PASS |
| `work/S40_result_readback/source_review_v3_3_adversarial.json` | `8ca313e712eec18d275122c95181aff987ae1ff5ceb04a880af61bb41b5a3ec7` | v3.3 第二份攻击审 PASS |
| `work/S40_result_readback/supervisor_rebind_v2_receipt.json` | `2fc1a6aa640d39f3503605610dd88b57299632c3b88ccd6f89f6b6d99cf159cb` | attempt02 外层监督器重绑身份 |

截至本审计冻结时间，真实事实是：声明的 `VMem + stabilityai/sd-vae-ft-mse` 组件变体已在本机完成一次两批真实生成，元数据表明历史从 1→5→9，第二批选中 `[0,2,4,1]`，其中含生成帧 ID。首次保存量 readback 因 list/tensor 表示处理错误失败并保留；readback v3.3 已获得两名不同作者的源码 PASS，attempt02 外层监督器已重绑，但其独立 v2 审查在 13:43:03Z 检查时尚无回执，因此 attempt02 没有运行。尚无位级历史消费 PASS、B0/C1/C2 分数、画面相机服从门、自然失败确认、方法增益或创新证据。S42 统计预注册仅校准阶段 PASS，确认性执行仍为 `REVISION_REQUIRED`。

## 1. 第一性原理：长期记忆真正要解决什么

### 1.1 从隐藏世界状态开始，而不是从缓存结构开始

设真实但不可直接完整观察的世界状态为 \(x_t\)，相机或动作是 \(a_t\)，观测是 \(o_t\)，记忆是 \(m_t\)：

\[
m_t = U(m_{t-1}, o_t, a_t, s_t),\qquad
\hat y_{t:t+h}, u_t = R(m_t, a_{t:t+h}).
\]

其中 \(s_t\) 不是多余标签，而是证据身份：真实传感观测、模型生成、几何估计、重编码结果或外部参考。\(u_t\) 表示模型对“当前证据不足或互相冲突”的不确定性以及可采取的动作，例如拒绝写入、拒绝消费、保留多个假设、请求重新观察。

长期记忆的目标不是保存最多旧帧，也不是让返回帧单独获得更高 PSNR。它应在部分可观测、会变化、并且模型会把自身输出继续写回的环境里，维持一个对未来预测和行动**足够、可校准、可修正、可追溯**的世界信念，同时满足内存和计算预算。

这个目标至少包含五个可验收性质：

| 性质 | 操作化含义 | 失败示例 |
|---|---|---|
| 持久性 | 在没有反证时，已观察实体、几何和身份在长间隔后仍可恢复 | 回到旧视点后对象身份或布局漂移 |
| 动态正确性 | 世界允许变化；遮挡期间的状态按行动和物理过程演化 | 把已移动或消失的对象冻结为旧状态 |
| 证据校准 | 真实观测、预测和推断拥有不同证据地位；冲突时不会自动平均成一个确定答案 | 模型把自己生成的错误当成新事实继续放大 |
| 可修正性 | 新的可信观测到来后，旧错误能够撤回、降权或被替换 | 一次错误写入长期支配后续所有回访 |
| 因果可寻址性 | 一条记忆若被宣称“使用”，其干预应主要影响它支持的目标区域或状态 | 检索 ID 正确，但输出只发生全局色调变化 |

### 1.2 一个更严格的成功目标

在给定记忆预算 \(B_m\)、推理预算 \(B_c\) 和允许拒绝/重观察代价 \(C_u\) 时，可以把目标写为：

\[
\min \; \mathbb{E}[L_{future}(\hat y, y^*)]
+ \lambda_{cal} L_{calibration}(u, L_{future})
+ \lambda_{rev} L_{irreversibility}
+ \lambda_c C_u,
\quad \text{s.t. } |m_t|\le B_m,\; \mathrm{compute}\le B_c.
\]

这里最关键的变化是：

1. 目标包含未来预测或行动结果，而不是只优化记忆内部的检索分数。
2. 不知道时允许表示“不知道”，并为重观察付出显式成本。
3. 错误是否可被新证据纠正进入目标，而不是只看短期平均一致性。
4. 记忆的来源和作用需要审计，不能把 `stored`、`retrieved`、`consumed`、`helpful` 当成同一个事件。

### 1.3 哪些才算范式假设，哪些只是模块替换

| 层级 | 真正改变了什么 | 本项目例子 | 当前裁决 |
|---|---|---|---|
| 范式候选 | 改变任务目标、状态语义、允许的决策或评价单位 | cache 变为带来源和可撤销性的 evidence ledger；总要生成变为可拒绝/重观察；稳定性变为可修正性和因果承诺 | 可以提出可证伪问题，尚未成立 |
| 方法候选 | 在同一任务内改变可学习机制 | 学习何时把生成预测升级为可信证据 | 只有先证明问题和 oracle headroom 才可设计 |
| 普通强基线 | 在既有输入输出接口内换聚合或路由 | mean→最近帧、medoid、几何加权、attention、router、PoE | 必须比较，不能叫颠覆式创新 |
| 工程修复 | 使声明的原流程正确运行 | readback schema、加载、路径、梯度或尺度修复 | 必要，但不是科研创新 |

下列想法已被 S41/S42 近邻或通用做法压成普通基线：`mean→attention/router/weighted mean/top-k`、source ID/RoPE、geometry mask/camera gate、patch token、多 token memory、可更新点云/SLAM、保护 anchor、普通 confidence threshold、memory experts/PoE。把其中两三个组合进 VMem 也不会自动变成范式创新。

## 2. 房间里的大象：领域真正回避的困难

### 2.1 模型把自己写成了“事实”

VMem 固定源码会把新生成的 `samples_z` 加入后续 latent cache，并从解码图重新计算全局 CLIP embedding。S40 的元数据已经证明第二批检索包含生成 ID；位级 readback 仍未通过，所以本审计只说**闭环路径真实存在**，不说它已经造成错误。

房间里的大象是：许多长期记忆系统默认真实观测、模型预测、估计几何和重编码表示具有相同可信度。这样会产生自我确认环：一次生成错误被写回，下一次检索把它当证据，随后生成又为旧错误提供“新证据”。只看最终一致性可能把稳定的错误误认为好记忆。

最直接反证：在完全匹配的轨迹、noise、真实观测和预算下，允许生成写入与隔离生成写入没有稳定的 `write policy × rollout depth` 交互，或者差异可由 coverage/K、相机或质量失败解释。出现这种结果就杀死“闭环污染是主因”。

### 2.2 “存了和选了”并不等于“用到了”

当前 VMem 的 Surfel、source vote、相机距离与 NMS 负责选择 frame IDs；被选帧的 per-frame latent 进入 `replace`，Plücker 进入 `concat/dense_vector`，全局 CLIP 向量先求 mean 后成为一个 cross-attention token。正确选中历史 ID 只证明 store/select 层工作，不能证明：

- consumer 对这条信息敏感；
- 影响与冻结的回访失败有关；
- 某个来源影响它在几何上支持的区域；
- 影响方向是改善而不是全局风格漂移；
- 信息没有被更强的 per-frame latent 或相机路径压过。

这也是为什么当前首选路线必须先做 A0 exact replay、A1 zero-CLIP，再做 A2–A5 普通基线，最后才可能进入 source→target-region 反事实。

### 2.3 系统默认“每次都该回答、每条检索结果都该消费”

当记忆不足、过期或互相冲突时，生成一个看似合理的确定画面可能比声明未知更危险。视频世界模型通常没有显式的 null、abstain 或 re-observe 动作；即使存在一个 confidence gate，也常只优化平均质量，没有报告 risk–coverage、clean false-reject 和总体损失。

这里可能的新问题不是“再加一个 gate”，而是：在有相机/行动后果的视觉世界里，什么时候继续生成、什么时候保留多假设、什么时候请求一个新视点，才使未来风险最小。RAG 的 sufficient-context 和参考扩散的 adaptive conditioning 已覆盖抽象机制，因此只有世界模型特有的时空、行动和闭环证据语义才能留下研究空间。

### 2.4 静态回访可能奖励错误捷径

返回图相似可能来自复制旧帧、相机没有真正移动、画面整体冻结或生成器忽略 command。返回图不相似也可能只因实际画面视点错了。当前 B0 协议已正确区分请求的 c2w/K 与画面相机服从，并要求在独立画面相机 proxy 通过前不得把 RGB 差异归因给 memory。

更深一层的问题是：即使静态 ID0↔ID8 完全一致，遮挡期间世界可能已经变化。真正的长期世界模型应记住身份，同时允许状态演化。只测“回来后像不像旧图”会奖励把世界冻结在过去。

### 2.5 错误是否能被纠正，几乎没有被当作主要结果

长期系统不可避免会写错。一个实用记忆系统的关键量可能不是首次错误率，而是：新的真实证据到来后，错误多久消失、是否留下 hysteresis、是否需要手工清空 cache。平均回访质量掩盖了错误半衰期。

这个问题的最便宜形式是：预注册一次小幅错误写入，随后提供一次干净重观察，测之后两次固定回访的恢复曲线。若原系统自然恢复到 replay/SESOI 内，或 oracle retract 没有 headroom，这条路线立即停止。

### 2.6 评测容易把多个失败原因混成“memory failure”

当前项目已经暴露出至少六个必须分开的层：组件身份、读取/保存接线、请求相机、画面相机服从、视觉质量、回访一致性。真实 GT 只覆盖已观察视点；生成历史和模型预测几何不能被改名为 GT。只用一张最坏 crop、CLIP 相似度或模型自身估计器，会给出循环证据。

因此，领域最难的问题之一不是再做一个更高分模型，而是建立一个不会通过挑场景、挑帧、挑 ROI、挑 seed 或挑指标制造结论的自然失败与因果审计协议。

## 3. 当前技术周期：为什么“加一个记忆模块”已经不够

### 3.1 2024：几何进入多视图生成的 attention

SPAD 和 EpiDiff 已把 Plücker、极线或局部几何对应写入跨视图 diffusion attention。这个阶段解决“不同视图的 token 应该在哪里交互”。因此，geometry mask、epipolar attention 或 camera-conditioned attention 已经是成熟技术族，不能单独支撑新颖性。

### 3.2 2025：记忆成为显式、可检索的模型状态

VMem 用 Surfel 索引历史视图；WorldMem 把帧、pose 和 timestamp 组成 memory units，并用 state-aware attention 支持长间隔回访和动态演化。MiMo 又显示历史内部表征质量本身会限制 VideoAR。研究问题从“有没有几何条件”转向“存什么、以什么状态检索、历史表征是否可用”。

### 3.3 2026：竞争点转向可寻址读出、地址稳定、可靠历史和组合记忆

WorldStereo 使用 3D correspondence 约束 target-reference 的细节读出；Spatia 持续更新 3D point-cloud spatial memory；WorldTrace 直接处理长 rollout 中 RoPE 地址越出训练范围以及错误的 cache 压缩；ReMind 通过 protected anchors、noisy memory 和专门训练让模型使用动态历史。PoCo、ReBind、稀疏 router、memory experts 等工作继续覆盖来源绑定和多记忆组合。

由此得到一个保守推断：多 token、source tag、router、gate、PoE、点云更新和几何局部 attention 已属于本技术周期的常规设计空间。真正仍可能开放的层面是记忆的证据语义、校准、可撤销性、可观察性、因果验收和失败评测。

### 3.4 2026 中后期：从静态返回转向遮挡期间状态演化

MemoBench 明确设置“对象在不可见期间经历物理过程，再以更新后的状态出现”；ReMind 也把 out-of-sight state evolution 作为中心问题。这意味着静态回环仍是必要工程门，但不足以成为前沿级最终故事。后续若只在 changi 的一个静态返回上成立，结论必须限于 case study；若要升级，需要跨 scene、第二 consumer，以及动态隐藏状态任务。

### 3.5 当前能力变化带来的真正机会

开放模型现在暴露 cache、latent、pose、geometry memory 和 sampler 输入，使我们可以在固定内部状态、实际 noise 和检索结果后做因果干预。这让“记忆消费者审计”变得可执行。它没有自动让一个新 gate 变得新颖，而是使一个更严格的 benchmark/diagnostic 成为可能：逐层区分 stored、selected、consumed、localized、helpful 和 recoverable。

### 3.6 正式原文与访问记录

访问/复核日期统一为 **2026-09-07**。只把正式会议原页或 arXiv 原始记录用作技术事实；arXiv 项明确按预印本处理。CVF 原页在本轮网络直取返回 403 时，仅沿用 S41/S42 已冻结的正式原文记录与官方 URL，不把抓取失败改写成新证据。

| 工作 | 原始入口 | 本报告使用的最小事实 | 状态 |
|---|---|---|---|
| SPAD, CVPR 2024 | https://openaccess.thecvf.com/content/CVPR2024/html/Kant_SPAD_Spatially_Aware_Multi-View_Diffusers_CVPR_2024_paper.html | 几何约束跨视图 diffusion attention | 正式会议；本地冻结原文记录 |
| EpiDiff, CVPR 2024 | https://openaccess.thecvf.com/content/CVPR2024/html/Huang_EpiDiff_Enhancing_Multi-View_Synthesis_via_Localized_Epipolar-Constrained_Diffusion_CVPR_2024_paper.html | 局部 epipolar-constrained 多视图读出 | 正式会议；本地冻结原文记录 |
| VMem, ICCV 2025 | https://openaccess.thecvf.com/content/ICCV2025/html/Li_VMem_Consistent_Interactive_Video_Scene_Generation_with_Surfel-Indexed_View_Memory_ICCV_2025_paper.html | Surfel-indexed view memory 与长时回访 | 正式会议；本地冻结原文记录 |
| WorldMem, NeurIPS 2025 | https://proceedings.neurips.cc/paper_files/paper/2025/hash/470629a47e2d65ce0606c40055df5d26-Abstract-Conference.html | pose/time-bound memory units 与 state-aware attention | 正式会议；本轮原页复核 |
| Sufficient Context, ICLR 2025 | https://proceedings.iclr.cc/paper_files/paper/2025/hash/33dffa2e3d2ab74a783d1a8c292f66d9-Abstract-Conference.html | context sufficiency 与 guided abstention | 正式会议；本轮原页复核 |
| MiMo, ICLR 2026 | https://proceedings.iclr.cc/paper_files/paper/2026/hash/9d30c2def27b5c6a5fb21a9aa5c16f8f-Abstract-Conference.html | masked history modeling 强化 VideoAR 历史表征 | 正式会议；本轮原页复核 |
| Ada-RefSR, ICLR 2026 | https://proceedings.iclr.cc/paper_files/paper/2026/hash/9d0947107ea92d6ce369dce7749180dd-Abstract-Conference.html | 不可靠参考条件下的 adaptive conditioning | 正式会议；本轮原页复核 |
| WorldStereo, CVPR 2026 | https://openaccess.thecvf.com/content/CVPR2026/html/Zhang_WorldStereo_Bridging_Camera-Guided_Video_Generation_and_Scene_Reconstruction_via_3D_CVPR_2026_paper.html （并列 arXiv：https://arxiv.org/abs/2603.02049） | 3D geometric memories 与 correspondence-constrained readout | 正式 CVPR 原页；本轮 arXiv 原始记录复核 |
| Spatia, CVPR 2026 | https://openaccess.thecvf.com/content/CVPR2026/papers/Zhao_Spatia_Video_Generation_with_Updatable_Spatial_Memory_CVPR_2026_paper.pdf （并列 arXiv：https://arxiv.org/abs/2512.15716） | 持续更新的 point-cloud spatial memory | 正式 CVPR 原文；本轮 arXiv 原始记录复核 |
| WorldTrace | https://arxiv.org/abs/2608.07408 | 长 rollout 中的 memory addressability 与 cache compression | 预印本；本轮原页复核 |
| ReMind | https://arxiv.org/abs/2605.25333 | out-of-sight dynamics、protected anchors、noisy-memory training | 预印本；本轮原页复核 |
| MemoBench | https://arxiv.org/abs/2606.27537 | 遮挡期间动态变化的 disappear-and-reappear benchmark | 预印本；本轮原页复核 |

这些来源只能说明普通设计空间拥挤、候选需要更窄。没有找到精确组合不等于首次提出；投稿前仍需 citation-network、同义词和第二名独立检索者复核。

## 4. 重要问题清单与最便宜的判别实验

### 4.1 Top 5 范式候选

#### P1：记忆因果契约，而不是“检索到就算记住”

- **隐藏假设**：只要正确存储并检索一帧，生成器就会把它用于正确的目标区域。
- **范式版本**：每项记忆是一条带来源、适用范围和可干预验收的证据承诺；系统要分别通过 store、select、consume、localize、benefit 五层。
- **普通模块版本**：把 mean 换成 attention、source tag、geometry mask 或 router。该版本已被 WorldMem、WorldStereo、PoCo、SPAD/EpiDiff 等直接施压，只能做 baseline。
- **最便宜判别实验**：沿现有 canonical 链推进。先通过 G0 的 B0/C1/C2 自然失败与独立画面相机门；再做 A0 exact replay 和 A1 zero-CLIP。只有 influence 与 failure relevance 都过，且 A2–A5 普通臂已完整审计，才对一个真实 source 做低强度、geometry-preserving 的 coherent F11 反事实。固定 retrieval IDs、latents、pose/K、Plücker、实际 noise、RNG 和生成前支持 mask，比较总效应与 `Localization_11` 相对 mask 面积基线。
- **Kill criterion**：无稳定自然失败；A0 不能重放；A1 不超过 replay 或只改变全局风格；F11 总效应不超过 replay；定位 CI 下界不高于面积基线；定位不能增量预测自然回访误差。任一成立即停止。
- **与现有方案差异**：WorldTrace 解决 cache 的地址失效，WorldStereo 设计 correspondence readout，本候选问的是部署中的某条证据在固定其他状态后是否产生预期的局部因果作用。
- **为什么可能是新问题**：本次定向检索未找到同时冻结自然失败、检索、latent、几何、相机和实际 noise，再以生成前支持区验收单来源作用的完整协议。它目前只够称 benchmark/characterization seed；要讨论新问题，必须跨第二 consumer 复现。
- **当前优先级**：1。它复用已完成最多的 S41/S42 准备，且最容易被便宜实验杀死。

#### P2：自生成预测何时有资格升级为证据

- **隐藏假设**：真实观测、生成 latent、重编码 CLIP 和预测几何可以用同一规则写入和检索。
- **范式版本**：记忆带 epistemic type。真实观测、模型预测、几何推断和外部参考有不同的写入、确认、撤回和消费规则。
- **普通模块版本**：给生成帧乘一个置信度、保护几个 anchor、recent-only 或 reject-all。这些都只是必须击败的基线。
- **最便宜判别实验**：同一初始真实观测、轨迹、第二批 target 和配对 noise 下，比较 `generated-write` 与 `generated-quarantine`；再预注册生成来源剂量 `q∈{0, half, all}`。固定真实 ID0、总 memory budget，并逐臂报告 K、coverage 和检索 ID 差异。主检验是回访损失对 rollout depth 的 `write policy × depth` 交互。
- **Kill criterion**：append-all 不劣于 quarantine；没有随 q 或深度的单调/稳定恶化；效果被 coverage/K、pose、质量或相机失败解释；只在极端人工 corruption 出现。
- **与现有方案差异**：ReMind 已有 noisy memory 和 protected anchors，普通 robust-memory 训练并不新。本候选聚焦在线闭环里“预测何时由假设晋升为事实”的证据类型和错误传播。
- **为什么可能是新问题**：若能定义并跨模型测量 epistemic promotion 的风险、校准和错误传播，它改变的是 memory update 的语义，而非一条 gate。但与 ReMind、robust world model 和 SLAM 不确定性非常接近，新颖性风险高。
- **当前优先级**：2。先等 P1/G0 和 readback；不能越过真实失败门直接跑。

#### P3：记忆的可修正性与错误半衰期

- **隐藏假设**：降低平均写入错误就足够，系统一旦写错后能否恢复不是核心指标。
- **范式版本**：把“新可信证据到来后错误多久消失”作为一等目标，要求错误可撤回、冲突可解决并报告 hysteresis。
- **普通模块版本**：loop closure、覆盖旧条目、固定衰减或简单 rollback。它们是 baseline，不是贡献本身。
- **最便宜判别实验**：向一个固定 write 注入预注册的小幅 pose、depth 或 appearance 错误，随后给一次干净重观察；测之后两次固定 return 的误差恢复曲线。原 append-only 对比 oracle retract/rollback 和一个普通 merge。oracle 只测 headroom。
- **Kill criterion**：下一次干净证据后原系统已回到 replay/SESOI 内；oracle 撤回没有 headroom；效果只在 gross corruption 存在；恢复差异由相机或全局质量解释。
- **与现有方案差异**：SLAM loop closure 和 robust memory 关心修图/抗噪，本候选把视频世界模型的 error half-life、可撤销性和后续生成风险设为主要结果。
- **为什么可能是新问题**：它把长期一致性的方向从“不要变”改为“错了能改”。是否已经被 dynamic-memory 或 map-correction 工作等价覆盖仍需专项系统检索。
- **当前优先级**：3。适合作为 P2 成立后的确认性问题，不是当前第一实验。

#### P4：记忆不足或冲突时，拒绝与重观察也是正确答案

- **隐藏假设**：每个 query 都必须生成一幅确定图，检索到的所有记忆都应被消费。
- **范式版本**：输出动作集合包含 `generate / abstain / request-view / keep-multiple-hypotheses`，优化的是带拒绝成本的未来风险。
- **普通模块版本**：confidence gate、subset selector、best-single、null token、PoE。RAG 和参考扩散已有直接近邻，只能当 baseline。
- **最便宜判别实验**：在真实自然错误和预注册 conflict dose 下比较 original、null、nearest/best-single 与 oracle subset/null。先只测 oracle headroom；随后冻结 deployable score，在确认集报告 risk–coverage/AURC、clean false-reject、总体 paired loss 和重观察成本。
- **Kill criterion**：错误/冲突记忆不比 null 更坏；oracle subset/null 无正 headroom；不确定性不预测错误；AURC 不优于普通 confidence；收益依赖过高 clean false-reject；generic gate 达到同样结果。
- **与现有方案差异**：Sufficient Context 已研究 RAG 中上下文充分性和 abstention，Ada-RefSR 已做不可靠参考条件下的 adaptive conditioning。本候选只有在行动条件、几何覆盖、时序闭环和 re-observation 成本共同进入任务后才可能不同。
- **为什么可能是新问题**：视觉世界模型中的“拒绝”可以转成主动获取新视点，而不是只返回一句不知道；这改变了交互协议。基础思想不新，世界模型特有设置必须产生可复现的新失败和评价。
- **当前优先级**：4。必须先过错误记忆比无记忆更坏与 oracle headroom 两门。

#### P5：遮挡期间应维护多假设状态，而不是复制最后快照

- **隐藏假设**：不可见期间的世界有一个可由最近历史唯一确定的状态。
- **范式版本**：memory 保存对隐藏状态的校准分布；新证据到来前保留多个合法假设，证据到来后快速收缩。
- **普通模块版本**：增加 stochastic sampling、更多 memory token 或把 timestamp 加入 attention。这些不能单独证明 belief memory。
- **最便宜判别实验**：构造具有完全相同可见 prefix 的 ambiguity twins，遮挡期间分别“未变”和“移动/移除”。揭示前用预注册 paired samples 测合法状态覆盖与校准；揭示后测状态修订速度，并与 deterministic snapshot、普通 stochastic baseline 比较。
- **Kill criterion**：prefix 实际泄露未来；现有随机输出已经校准覆盖且能快速修正；多假设不改善未来风险；或 MemoBench/ReMind 等已完整等价覆盖任务与机制。
- **与现有方案差异**：MemoBench 和 ReMind 已把 out-of-sight state evolution 推到中心。本候选进一步要求“证据不足时保持校准多假设，证据到来后收缩”，但 POMDP/belief state 思想本身很旧。
- **为什么可能是新问题**：若现有视频生成 benchmark 只看单次最像 GT 的样本，而不测分布覆盖、校准和 revision，它可能形成新的评价问题。当前近邻压力最高，需要最严格排重。
- **当前优先级**：5。更像下一阶段或跨项目方向，不应挤占本学期的 G0→G1→D 主线。

### 4.2 Hamming 式 20 个重要问题

每个问题都绑定一个能让它失败的观察，避免把口号积累成“创新”。

| # | 重要问题 | 最小可证伪观察 | 当前状态 |
|---:|---|---|---|
| 1 | S40 的组件、两批 cache、ID、pose/K、noise 和保存链是否真实一致？ | readback 任一 material invariant 不符即工程停止 | 生成终态元数据有 PASS；位级 readback 未完成 |
| 2 | 预注册自然回访失败是否存在？ | B0/C1/C2 三行中不足两行满足固定 `MSE_M>0.01` | 未评分 |
| 3 | 返回差异能否排除相机没有正确回程？ | 独立画面相机 proxy 不过 | proxy 尚未冻结/通过 |
| 4 | 能否排除空白、撕裂、冻结、复制等整体生成崩坏？ | 九帧盲 QA 或质量门能完整解释主差异 | 未做 |
| 5 | 失败是否随 gap、camera excursion 或 chunk 数呈预注册剂量关系？ | 不随强度变化，或只由单场景/seed 驱动 | 未做 |
| 6 | A0 能否 exact replay？ | 任一 input/RNG/output 超 `tau_output` | 未运行 |
| 7 | CLIP cross-attention 支路是否真的影响输出？ | A1 zero-CLIP 的 `D_output` 不超过 replay 门 | 未运行 |
| 8 | CLIP 影响是否与冻结回访失败相关？ | A1 只改变输出但 `L_revisit` 无有意义变化 | 未运行 |
| 9 | 变化是否只属于全局色调或风格？ | 局部失败不改善，或 camera/quality guardrail 受损 | 未运行 |
| 10 | 最近来源 A2 与最远来源 A3 是否有目标方向性差异？ | 两者实践等效，表明可能只是任意向量扰动 | 未运行 |
| 11 | A4 medoid 或 A5 geometry-weighted mean 是否已足够？ | 任一普通臂达到 SESOI 且无 guardrail 代价 | 未运行；若成功则升级为强 baseline |
| 12 | coherent F11 单来源编辑是否产生超过 replay 的总响应？ | `T_total` 不超过 replay 或接近零 | G0/G1 前禁止运行 |
| 13 | 响应是否在生成前冻结的几何支持区富集？ | `Localization_11` CI 下界不高于 mask 面积基线 | 禁止运行 |
| 14 | 定位是否跨两种低强度 edit 和 paired noise 重现？ | 只在一个 edit/seed 出现或方向翻转 | 禁止运行 |
| 15 | F10 CLIP-only、F01 replace-only 是否与 coherent F11 一致？ | 分支方向或区域与 F11 冲突 | 禁止运行；冲突只能叫 branch-response |
| 16 | 两条路径是否有超过等效区间的有符号交互？ | factorial interaction CI 落在等效区间 | 禁止运行；可加性也是有效负结论 |
| 17 | 可定位性是否对自然失败有增量预测力？ | 控制 coverage、camera error、支持面积和全局相似度后无增量 | 未做；失败则 diagnostic 缺论文价值 |
| 18 | 错误写入是否真的比无记忆更坏？ | matched-budget always-write 不劣于 recent-only/reject-all | 未做；不过则 uncertainty gate 无动机 |
| 19 | oracle subset/null 是否有 headroom，预测 uncertainty 能否在留出集复现？ | oracle 无收益，或 deployable score 无 AURC/clean 非劣收益 | 未做；oracle 无收益立即停止 gate |
| 20 | 结论能否跨独立 scene、第二 consumer 和动态隐藏状态成立？ | 只在一个 changi case 或 VMem 接口成立 | 当前完全未证明 |

### 4.3 执行优先级和退出树

本学期当前唯一值得立即接续的科学链是 P1，而且必须复用已经冻结的 G0→G1→G2→D 顺序：

```text
S40 readback 是否通过？
├─ 否：只修工程链，不解释图片，不启动创新实验
└─ 是：B0/C1/C2 + 画面相机/质量门是否确认自然失败？
   ├─ 否：停止当前静态回访故事
   └─ 是：A0 exact replay 是否通过？
      ├─ 否：工程停止
      └─ 是：A1 是否同时有 influence 与 failure relevance？
         ├─ 否：杀死当前 CLIP consumer 路线
         └─ 是：A2–A5 普通臂是否已解释或解决？
            ├─ 是：将其作为强 baseline，不称创新
            └─ 否：才允许 F00/F10/F01/F11 source→region 诊断
               ├─ 无稳定总效应/定位/失败关联：杀死 P1
               └─ 有：只保留 benchmark seed；跨第二 consumer 后再做新问题排重
```

P2 和 P3 放入下一队列：它们只有在位级闭环和自然失败成立后才有科学输入。P4 必须先证明错误记忆比无记忆更坏，并存在 oracle subset/null headroom。P5 的动态隐藏状态和校准分布需要新数据或 benchmark，属于更长周期。任何确认性 A/F 实验前，还必须补齐当前 S42 统计预注册中尚未冻结的 SESOI、样本量、独立 scene/episode/seed、replay 容差和 guardrail margins；`REVISION_REQUIRED` 不能被本审计绕过。

### 4.4 最终裁决

- **当前可保留的新问题种子**：`固定内部状态后的记忆证据因果验收`，状态 `KEEP_CONDITIONAL`。
- **最有范式潜力的扩展**：`带 epistemic type、可拒绝、可撤销的 evidence ledger`。它目前只是问题框架，近邻压力高。
- **立即否决的创新包装**：mean→attention/router/weighted mean、source tag、geometry mask/gate、patch token、多 token、point-cloud update、PoE、普通 confidence gate。
- **当前论文证据级别**：真实声明变体生成的工程里程碑，加上未执行的因果与范式假设；没有自然失败、方法增益、跨场景结论或创新成立。
- **达到 PhD/CCF A 级别所需的最低新增证据**：自然失败在独立 scene 上稳定复现；完整因果链和普通强基线；预注册效应与 guardrails；跨第二 consumer 或动态状态任务；系统化近邻检索；允许负结果杀死主故事。

本报告不承诺论文级创新一定存在。它把最容易让老师失望的“换模块即创新”提前淘汰，并给每条高风险想法绑定了最便宜的判别实验和明确退出条件。
