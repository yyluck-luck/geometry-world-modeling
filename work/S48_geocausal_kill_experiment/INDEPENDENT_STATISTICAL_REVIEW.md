# S48 GeoCausal 最小否证实验：独立统计与因果审查

- 审查角色：独立统计／因果审查者；未参与 S48 草案撰写
- 审查对象：`S48_GEOCAUSAL_KILL_EXPERIMENT_PREREGISTRATION_DRAFT.md`
- 被审版本 SHA-256：`69ad32b932369e6c5cc9b1fde65d20d2caca1892fd47e2a5e94c3d15b5c8ef32`
- 审查范围：项目文字与 VMem 只读源码结构
- 严格边界：未运行模型，未读取 C1/C2 tensor、image 或 pixel body，未修改被审草案
- 总裁决：**BLOCKED**
- 适用含义：当前版本不能授权 S48 运行，也不能支持 confirmatory causal、geometry-localized benefit 或 method claim；C1/C2 baseline 收尾可继续。

## 1. 审稿人摘要

草案做对了五件重要的事：先要求自然失败；把 F10/F01 降为路径冲突诊断；只允许 F11−F00 作为一致干预；禁止冻结目标来源的下游中介；把 pilot 与 confirmation 在概念上分开。这些选择使路线具备可证伪性。

但当前版本仍有四项阻断：处理节点与“total effect”称谓没有唯一化；Localization 只有面积基线而没有匹配空间零假设；Benefit 缺独立 reference 及 `B_local/B_matched` 的可计算定义；确认阶段没有冻结 SESOI、样本量、独立 scene 数、精确检验和多重性。任何一项都足以使漂亮结果无法识别草案声称的目标。

| 等级 | 数量 | 最先修复的三项 |
|---|---:|---|
| CRITICAL | 4 | ①冻结处理发生时点和 estimand；②补 matched-mask null；③定义独立 reference、`B_local`、`B_matched` |
| MAJOR | 8 | replay/SESOI、发现与确认分离、scene 独立性、camera/quality guardrail、干预稳健性、多重性、近邻公平对照、执行随机化 |
| MINOR | 4 | 数值域与 epsilon、退化 support、术语、完整 flow reporting |

## 2. 处理节点与因果对象

### CRITICAL C1：`total effect` 与实际 post-selection 干预尚未对齐

**草案原文。** 第 83–87 行把 `G_i` 定义为冻结的 pose、K/Plücker、深度／点图和 target support，并称目标为“给定 `Z_i,G_i` 的 source-appearance total effect”；第 94–96 行又固定 retrieval IDs、slot 顺序和 `Z_i,G_i`。

**源码事实。** VMem 的实际顺序是：

1. `pipeline.py:957–1039` 从输入／已生成图像构造 point cloud、depth 与 surfel；
2. `pipeline.py:639–764` 用 surfel 投影、source timestep 与 pose 选择 context source；
3. `pipeline.py:1123–1185` 将所选来源送入 global-CLIP、replace latent 及 Plücker 条件；
4. `pipeline.py:1270–1309` 生成输出并继续写回 embedding、latent 与 scene memory。

因此，geometry 与 selection 相对“源图像被修改”是后代；相对“选完来源后，在缓存 appearance 表示入口注入修改”才是处理前条件。草案没有唯一指定干预发生在哪一行／哪一个张量边界，导致两个不同 estimand 被混写：

- 若先编辑源图像再存储，固定 surfel、geometry、retrieval 和 source ID 会冻结中介；结果是受控直接效应，不能称 source total effect。
- 若先由普通运行完成 Store→Select→Address，再只替换被选来源的 cached appearance representations，固定 `Z_i,G_i` 合法；但结果只能称 **baseline-selected、addressable source 的 post-selection downstream representation effect**。它不包括 Store、Select 或 Address 的因果效应。

**可执行修复。** 在协议开头画出并哈希冻结唯一 DAG 和注入边界。推荐本次最便宜版本采用第二种定义：

> treatment 在 `get_context_info` 已返回普通运行选择结果后、`get_cond` 构造全部 consumer inputs 前发生；固定 source ID、slot、geometry/retrieval 与其他干预前状态；对目标来源所有 appearance representations 作同一编辑，并重算 `get_cond`、attention、denoising、输出与后续写回。主 estimand 命名为 `post-selection downstream appearance effect`。

若以后要主张完整 source-item total effect，必须另立实验：在 Store 前干预源图像，并允许 geometry、retrieval、selection、consumer 与写回全部重算。两个 estimand 不得共用标题或结论。

### 判断

在上述时点冻结之前，不能判断 geometry 是条件还是被冻结的中介，故为 **CRITICAL**。

## 3. 指标是否识别目标

### MAJOR M1：Influence 的 replay 扣减不是完整零假设

**草案原文。** 第 144–150 行定义 `I_i = mean_p d_i(p) − mean_p d_i,replay(p)`；第 115–117 行允许 bitwise replay 时把 floor 记为 0。

非负距离在 bitwise replay 为 0 时，任何数值极小的 F11 响应都会满足“超过 replay”；这不能区分科学上可忽略的敏感度。单次 replay 均值也没有给出上尾不确定性。

**可执行修复。** 事前冻结：

- `D_intervention = mean_p d(F11,F00)`；
- `D_replay` 来自规定数量的 F00–F00 重放对，报告中位数、上分位与其置信上界；
- `tau_output = max(tau_numeric, tau_replay)`；
- 独立于 pilot 观测效应的最小有意义影响 `delta_I > 0`；
- 确认判据为 scene 等权估计的单侧置信下界超过 `tau_output + delta_I`，而不是只做均值相减。

Pilot-A 只有一个单位时只能报告 `D_intervention`、全部 replay 距离和倍率，不能使用“显著”或总体 CI。

### CRITICAL C2：Localization 的面积基线不能识别 geometry-specific localization

**草案原文。** 第 156–164 行只定义 `L_i = mass_i − area_i`，并要求 scene-cluster CI 下界大于 0。

面积基线隐含“若没有几何关系，影响在 Ω 内均匀交换”的假设。扩散输出的敏感度会随画面中心、边缘、高纹理、运动、遮挡、baseline error 和 replay variance 改变；真实 support 往往也集中在这些位置。因此 `L_i>0` 可能只是空间结构重合，并不识别来源几何。

这也是对 S43 当前合同的回退：`LIVE_NOVELTY_REFRESH_2026-09-08.md:81–84,112–114` 已明确要求 matched-mask null 和 `B_local/B_matched`，S48 草案没有把它们操作化。

**可执行修复。** 在读取任何 F 输出前冻结 matched-mask 生成器：

1. 每个 source-support 产生固定数量 `K` 个假 support；只使用干预前／CAL 信息。
2. 匹配面积、连通分量数、形状／周长、图像位置或相机射线分布、可见深度范围、baseline edge density、baseline replay variance 和 baseline error strata。
3. 固定候选不足、support 重叠、边界截断和无法匹配时的 invalid 规则。
4. 定义 `L_area = mass(S)-area(S)`；再定义主量 `L_matched = mass(S)-median_b mass(M_b)` 或相应 enrichment contrast。
5. `K` 个 mask 是单个 unit 内的随机化参考，不能被当成 `n=K` 个独立样本。先形成 unit 级 statistic，再按 scene 聚类。
6. 加入两个 placebo：非选中来源的投影 support，以及保持面积／形状的相机平移 support。两者必须在 F 输出前冻结。
7. 对 geometry 不确定性预注册 erosion／dilation 与 occlusion-aware sensitivity；主 mask 仍保持唯一。

确认性局部结论至少要求总 Influence 先过门、`L_area` 过 SESOI、`L_matched` 超过冻结零假设，并且 camera/quality guardrails 通过。

### CRITICAL C3：Benefit、`B_local` 与 `B_matched` 尚未被识别

**草案原文。** 第 168 行把 ID0–ID8 RGB MSE 作为 natural revisit loss；第 172–180 行只定义一般 `B_i = Loss(Y_P) − Loss(Y_O)`，替代条件仍“尚未冻结”。草案没有定义 `B_local` 或 `B_matched`。

ID0–ID8 RGB MSE 首先是“回到 ID0 外观的一致性”，不是外部正确性或一般视频质量。若 ID0 本身进入 memory，尤其当目标 source 就是 ID0，使用 ID0 同时作来源和答案会结构性偏爱 original source。即使 source 不是 ID0，该指标仍可能奖励复制旧外观而非生成正确的新视图。

**可执行修复。** 先定义唯一、与 O/P 均独立的 return reference `R_i`：优先使用从未进入 memory、在解盲前封存的真实目标视角照片；若只能使用 ID0，结论必须改名为 `return-to-ID0 consistency`，不得称 correctness、quality 或真实 benefit。

随后把两种相对收益分开：

\[
B_{local,i}=\tfrac12\{\ell_{S_i}(Y_{i,P^-},R_i)+\ell_{S_i}(Y_{i,P^+},R_i)\}-\ell_{S_i}(Y_{i,O},R_i),
\]

其中 `P−/P+` 是同一来源、事前冻结的对称低强度 photometric alternatives。它只测 original appearance 相对局部扰动的稳定性／局部相对收益。

\[
B_{matched,i}=\operatorname{mean}_{P\in\mathcal P_i}\{\ell_{S_i}(Y_{i,P},R_i)-\ell_{S_i}(Y_{i,O},R_i)\},
\]

其中 `P` 是按同 scene、identity、pose/FoV、support、recency、source quality 与 tensor/token interface 匹配的未选来源。匹配算法、caliper、候选不足规则、placebo 主次关系和 `|\mathcal P_i|` 必须冻结。

两者都应同时报告 support 外差异；可再定义 support 对 matched-mask 的 difference-in-differences 作为局部特异性诊断。两个量都只是“original 相对指定 alternatives”的收益，不等于“有记忆相对无记忆”的绝对效用。后者需要另一个 in-distribution、保持 context 长度和接口的 drop/null policy；zero token 不能承担该角色。

## 4. 样本、独立性与确认阶段

### CRITICAL C4：确认性设计缺少可执行的样本量与错误率冻结

**草案原文。** 第 138 行只说“用 pilot 方差冻结样本量”；第 186–190 行把 scene-cluster bootstrap 或 paired permutation 留作二选一，没有给出 SESOI、alpha、power、scene 数、每 scene 的 episode 数、seed/replay 数或具体算法。

这不足以叫 preregistration。它也比已经存在的 S42 `PROTOCOL.md:131–166,295–308,323–329` 与 `manifest.schema.json` 更弱。当前版本无法判断阴性是等效还是低功效，也无法控制多重检验和可选停止。

**可执行修复。** S48 应复用或扩展 S42 manifest，并在 confirmation 前冻结：

- CAL/CONF 的 scene-level 划分、资格规则和完整 unit list；
- `delta_I`、`delta_L_area`、`delta_L_matched`、`delta_B_local`、`delta_B_matched`、`tau_output`、camera/quality 非劣 margins；
- familywise alpha、目标 power 和 CI 半宽目标；
- 基于保守 CAL 方差上限的层级配对模拟脚本与输出 SHA；
- 整数 `n_scene`、每 scene 的 episode/source 数、paired seed 数、replay 数、edit 数和 placebo 数；
- 唯一主 estimator、cluster 层级、bootstrap/permutation 细节、重复次数、随机种子和有限重复修正；
- invalid、missing、arm-related failure、worst-case sensitivity 和 no optional extension 规则；
- 冻结 analysis code、metric code、arm code 和数据 manifest 的 SHA。

预算达不到所需独立 scene 数时，合法结论是 case study／pilot，不得把 seed、frame、pixel、source 或 matched mask 升格成科学样本量。

### MAJOR M2：发现失败与确认效应的分离仍不完整

第 56、117、138、185 行正确地说开发单位不进入 confirmation，但没有定义 confirmation 如何纳入 target/source。如果在同一 baseline realization 中先挑 `MSE>0.01` 的极端失败，再只在这些失败上估计或预测 benefit，会产生 winner's curse、回归均值和 outcome-conditioned selection。

**修复。**

- C1/C2 只属于 CAL／开发，不进入确认统计。
- CONF 以 scene 为最高层留出；按与干预输出无关的资格规则连续纳入全部合格 episode。
- 若研究目标明确是“失败条件下的效应”，用独立 screening seed 判定 failure，再用未参与筛选的 paired seeds 做干预，并把 estimand 明确写成 `effect among screen-positive episodes`。
- 若要训练或检验自然失败预测器，确认集必须同时包含 success 与 failure，按 scene 划分 train/validation/test；不能只从失败事件学习。
- source 的 ordinary-run selection 可以作 post-selection estimand 的资格条件，但必须报告全部候选 source 到纳入 source 的 flow，不能在多个 selected sources 中按 F11 效果挑最好者。

### MAJOR M3：scene、episode、source、seed 和空间像素的相关性还未完全落地

第 51 行把 `(scene,target,source,seed)` 称为一个单位，而第 186 行又说 source-target 对是独立单位、按 scene 聚类。这会让 seed 看似扩充 `n`。同一 scene 的 target、source、frames、seeds 与重叠轨迹高度相关；scene cluster bootstrap 在只有 C1/C2 两个候选轨迹时也没有可靠的总体覆盖率。

**修复。** 把层级固定为：scene 是外推 cluster；scene×episode×selected-source 是观测单位；seed/edit/placebo/mask 是嵌套技术重复。先在 source/episode 内按冻结方式聚合，再让每个 scene 等权。样本量模拟须确定最小独立 scene 数；达不到时不计算总体显著性，只给完整配对点和描述性区间。

## 5. 混杂、控制与执行有效性

### MAJOR M4：camera 与 overall quality 只被口头要求，未成为每个 arm 的非劣门

第 27、70–75、168 行要求 baseline 相机守卫和视觉排查，但 F11/P placebo 自身可能改变感知相机、画面锐度、曝光、撕裂或全局风格。请求 pose/K 相同只证明输入相同，不证明生成画面服从相同相机。RGB output difference 与 revisit MSE 都会被这些变化放大。

**修复。** 对 F00/F11 及每个 Benefit placebo 预注册：独立 image-based camera adherence proxy、整体质量指标、global style 指标及单侧非劣 margin；评价代码与阈值在输出前冻结。arm code 匿名后评分。任一 guardrail 失败时，Influence 最多解释为“模型对该干预有响应”，Localization 与 Benefit 均不得通过。视觉相机检查若参与 gate，须冻结判据、随机顺序、盲法和评审一致性；否则只作探索。

### MAJOR M5：单一“低强度编辑”不足以排除 activation-patching 式 corruption artifact

第 74、87、128、190 行没有定义编辑族、剂量、语义／几何稳定检验和 sham。已有 activation-patching 研究说明，corruption 与 metric 的选择会改变归因结论；一次 F11 响应也可能是异常表示激活休眠路径，而非自然记忆消费。

**修复。** 在 CAL 上、看 F 输出前固定至少：

1. 两个机制不同但都 geometry-preserving 的对称低强度 edit families；
2. 每个 edit 的 dose、mask、色域、encoder delta 和几何稳定容差；
3. identity／no-op re-encode sham；
4. 同剂量编辑一个未选 source 的 negative control；
5. 能触发已知 consumer 的 positive control；
6. 编辑强度与输出效应的预注册 dose-response 或跨 edit 方向一致性规则。

只有对合理 corruption 选择稳健的 post-selection effect 才可进入论文主张；否则写作 intervention-specific sensitivity。

### MAJOR M6：arm 顺序、cache 污染、无效运行和缺失规则没有冻结

VMem 会把输出继续写回 memory；不同 arm 顺序若复用 state，会造成 carryover。当前草案没有要求 blocked random order、fresh process／validated full reset、A0 插入位置、匿名 arm code、失败重试和 arm-related crash 处理。

**修复。** 物化同一实际 noise；在 episode×seed block 内冻结随机执行顺序；每 arm 使用 fresh process 或逐项验证过的 reset；将 A0 放在预注册 block 位置检查漂移；只允许输出前工程条件判 invalid；保存每次 attempt。若失败率依赖 arm，主要比较判不可解释并报告 worst-case sensitivity。

## 6. 多重检验与预测主张

### MAJOR M7：固定层级方向正确，但检验族和复合主张未定义

第 188 行的 Influence→Localization→Benefit 顺序可形成 fixed-sequence gate，但仍缺 alpha 和每一层内部的规则。多个 edit、两个以上 placebo、ROI／四区诊断、LPIPS、两种 benefit、多个预测 baseline 和正负收益样本都会产生额外尝试。第 43 行把“平均正收益”与“存在可预测负收益样本”放进同一个 H1，它们是两个不同问题。

**修复。**

- 选一个主 Influence、一个主 Localization、一个主 Benefit；固定 sequence 中每个使用同一 familywise alpha。
- 若要求两个 edit／placebo 都通过，把它们定义为 intersection-union，claim-level p 值取必要子检验最大值；若任一通过即可，则用 Holm 调整。
- camera/quality guardrail 使用同时非劣区间或单独 Holm 家族。
- `B_local`、`B_matched` 明确主次，另一个作必要稳健性或经调整的共同主张。
- 将“平均 benefit”与“负收益预测”拆成两项。预测主张使用预冻结 features、scene-level held-out split、单一主指标及与普通 proxies 的 nested comparison；训练／阈值选择不能接触 test scenes。
- 未计划的 ROI、layer、time step、source 或指标统一标为 exploratory，不能补救主 gate 失败。

## 7. 与最近工作的重叠边界

### MAJOR M8：当前方法差异只能依赖联合证据，不能依赖单个组件

1. **CUE-R。** per-item REMOVE/REPLACE/DUPLICATE、paired delta、bootstrap 和 signed utility 已经覆盖“逐项干预→效用”的抽象结构；其自身还提醒长度、上下文分布和 attention 变化使结果更接近 interventional sensitivity。S48 只有在保持接口／长度、验证分布匹配、覆盖所有 VMem appearance paths、加入 geometry matched null 并连接独立自然重访 reference 后，才保留视频世界模型特有差异。
2. **Activation patching / causal tracing。** corruption choice、metric choice 与 dormant-path activation 已是直接威胁。多 edit、sham、negative control、positive control 和 dose robustness 是必要识别条件，不是附加美化。
3. **TetherCache。** attention+diversity selection、recalled K/V trusted alignment 与系统收益已经占据 generic selection/repair/gate 空间。未来 GeoCausal Acceptance Head 只有在同一模型、数据、输入信息、context budget 和计算预算下，证明 causal labels 对样本外 risk–coverage／total paired loss 有增量收益，才可能形成方法差异；引用公开表格中不可比数字不能替代实现级对照。
4. **I²AM／AGRA。** reference-to-region map、随机区域基线、空间 mask、因果干预和区域敏感度已有直接近邻。matched-mask 或热图本身不能称新；候选只能是“ordinary selected source + all-path post-selection intervention + pre-treatment 3D support + independent signed revisit benefit + out-of-sample prediction”的联合。

因此，S48 即使通过也首先是 architecture-scoped measurement evidence。方法新颖性仍需跨 scene、跨 source、跨 edit、跨至少第二个 consumer architecture 的确认，以及对 TetherCache/普通 gate 的公平增量比较。

## 8. MINOR 修订

| 编号 | 问题 | 可执行修复 |
|---|---|---|
| N1 | 第 146 行除以 255，未固定模型输出是 uint8 还是 float、色彩空间、resize/crop 和对齐 | 冻结输入数值域、颜色空间、量化时点、插值算法和有效范围；优先在解码前统一 float 域计算 |
| N2 | 第 158 行 `epsilon` 未给值；support 为空、覆盖全部 Ω、总效应为 0 时没有规则 | 冻结 epsilon 来源；对 empty/full support 和零总质量预先判 `NOT_IDENTIFIABLE`，不输出任意比例 |
| N3 | “显著”“稳定”“方向一致”“分布匹配”均未操作化 | 为每个词给出统计判据、容差、最小重复和失败动作，或改为描述性语言 |
| N4 | 未要求报告全部 target/source 候选与 support coverage | 输出 selection flow、每 scene/episode/source 的纳入排除、support area/visibility、所有负结果和全部 denominator |

## 9. 修订后的最小可执行顺序

1. 完成 C1 数值相机守卫与盲评分、C2 独立生成和同级评分；不把 S48 审查阻断解释成 baseline 阻断。
2. 只用 C1/C2 作 CAL，冻结一个自然失败开发单位；不作总体显著性或新颖性结论。
3. 冻结 treatment 注入点、DAG 与 `post-selection downstream effect` 称谓；枚举实际 CLIP、replace/latent 及任何新增 appearance path。
4. 冻结两类 edit、sham、未选-source control、A0 replay、`delta_I`、camera/quality guardrails 和 fresh-state 随机执行表。
5. 冻结主 support、matched-mask generator、两个 geometry placebo、`L_area/L_matched` 与退化 mask 规则。
6. 冻结独立 return reference，以及 `B_local/B_matched` 的公式、placebo 主次和 matching algorithm。
7. Pilot-A/B/C 仅作开发与 kill；无响应、无 matched localization、guardrail 失败或 benefit 符号对 placebo 不稳即停止。
8. 只有 pilot 通过后，使用 CAL 方差上限和独立 SESOI 生成完整 CONF manifest；新 scene 连续纳入，固定样本量、检验族与 analysis SHA 后再请求独立前审。

## 10. 最终裁决

**BLOCKED。** 当前草案不能授权 S48 pilot 或 confirmation，因为连 pilot 的处理入口、matched spatial null 和 benefit reference 都尚未唯一冻结；直接运行会让结果反过来塑造 estimand、mask 和 placebo。允许继续的工作仅限 baseline 收尾、源码路径枚举、指标／mask／placebo 构造的无结果开发，以及修订版预注册。

解除阻断的最低条件是：

- 明确选择 post-selection downstream effect，并冻结实际注入点和所有后代重算边界；
- 加入 matched-mask null、geometry placebos 和退化 support 规则；
- 给出独立 `R_i`、`B_local`、`B_matched` 与 matching/placebo 公式；
- 冻结 replay/SESOI、camera/quality margins、编辑族和执行随机化；
- 对 confirmation 冻结 scene-level CAL/CONF、样本量模拟、multiplicity、analysis code 和独立前审。

这些修复完成后，可对修订版重新做独立审查；本文件不授权复用旧版本的任何 PASS。
