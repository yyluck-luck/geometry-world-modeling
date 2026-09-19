# S42 统计预注册：VMem 真实 baseline 后的消费者因果审计

## 文档身份与当前裁决

- 文档类型：**分阶段统计预注册与审稿风险审计**。它补充现有科学协议，不覆盖现有协议，也不是结果报告。
- 唯一科学阶段与臂定义来自：
  - `work/S41_gemini_adversarial_review/primary_retrieval_and_root_review.md`
  - SHA-256：`fd07dfc743f9a0c3f350f5d719936b74d5d902f3f10910c1a0b30b8ecda4059a`
- 标签协调来自：
  - `work/S42_causal_memory_gap_search/RECONCILIATION.md`
  - SHA-256：`2cda8410dcc32fe1bfde9de249c78b9f45bf75bc77c3730f6843f45220219958`
- 覆盖范围：真实 S40 baseline 成功后，依次审计 `A0@rep=n`、`A1`、`A2`–`A5`，以及满足进入条件时的 `F00/F10/F01/F11`。
- 不覆盖：`E-*`、`S_*`、`C(type,q,policy)`；它们需要各自的新预注册。
- 当前证据边界：本文没有运行模型、没有生成视频、没有观察新分数、没有确定样本量，也不证明任何机制或创新成立。
- **裁决：校准阶段 PASS；确认性执行前 REVISION_REQUIRED。** 原因是最小有意义效应、独立场景数、每场景重访事件数、配对 seed 数、重放容差和守门阈值必须在看确认性臂输出前写入并哈希冻结。本文禁止用猜测数字补齐它们。

## 技能应用边界

本文严格应用三个本地技能的实质要求：

1. `sci-hypothesis-generation`：列出互斥或可区分的解释、定量预测、反证结果和最便宜的判别实验。
2. `sci-statistical-analysis`：事前确定统计单位、配对结构、效应量、置信区间、假设检查、样本量依据、多重比较和完整报告规则。
3. `sci-peer-review`：用 CRITICAL/MAJOR 缺陷检查伪重复、双重使用数据、遗漏对照、可重复性和过度结论。

本文不是该 hypothesis-generation 技能规定的“正式 LaTeX hypothesis report”，而是对已冻结根问题的执行与统计补充，所以不采用其 LaTeX 模板，也不触发该正式报告的 1–2 幅 AI 图要求。peer-review 技能建议考虑图示；本协议已有可机器检查的阶段表和决策表，且任务禁止运行模型，故不生成装饰性示意图。这一取舍不改变三个技能的实验设计、统计和反证要求。

## 给新手的一句话解释

我们不是先问“哪个新方法赢了”，而是依次问四个更便宜的问题：原结果能否重放；CLIP 条件是否真的改变回访失败；四个普通替代是否已经解释或解决问题；只有前三步通过，才问某一来源的改变是否主要落在它几何支持的区域。任何一步失败都应停止相应故事，而不是继续调参找好看的例子。

## 1. 预注册对象、版本与冻结顺序

### 1.1 三个不可混用的数据阶段

| 阶段 | 允许用途 | 禁止用途 |
|---|---|---|
| `CAL` 校准/发现集 | 检查 S40 接线、发现自然失败、估计 replay 噪声和方差、选择单一主指标、给 SESOI/容差提供独立依据、估算所需样本量 | 不能贡献确认性 p 值或 CI；不能把挑中的最差案例当总体证据 |
| `CONF` 确认性留出集 | 按冻结 manifest 运行全部合格事件、计算主要效应和置信区间、执行预先定义的 gate | 不能改 ROI、指标、seed、臂、编辑、阈值或样本量；不能因中间结果好坏提前停 |
| `EXP` 探索集 | 记录未预注册指标、可视化和后续假说 | 不能与确认性结果混合，也不能补救失败的主要检验 |

优先在**场景级**划分 `CAL` 与 `CONF`。若只能在同一场景内留出轨迹/重访事件，必须写作“同场景留出”；它不能支持跨场景外推。若只有一个场景，全部统计只描述该场景内的条件效应或 seed Monte Carlo 变异，不能声称群体显著性、普适机制或跨场景稳定。

### 1.2 冻结的时间顺序

1. S40 真实 baseline、组件 hash、`samples_z`→第二批 cache readback 和自然失败候选通过根协议 G0。
2. 只用 `CAL`：冻结一个主要回访失败指标、ROI 生成规则、两个 guardrail 指标、输出差异表示、数值容差、SESOI、方差/聚类结构估计和反事实编辑族。
3. 运行样本量/精度计算，得到整数 `n_scene_confirmatory`、各场景 `n_episode_per_scene`、`n_seed_pair`、`n_a0_replay`。这些是输出，不在本文编造。
4. 生成符合 `manifest.schema.json` 的 execution manifest；把所有文件、代码、权重、数据清单和分析脚本 SHA-256 一并冻结。
5. 冻结后才允许查看 `CONF` 上的 A1/A2–A5/F 输出。

确认性 manifest 任一 required 字段为空、`null`、`TBD` 或未哈希，确认性执行自动判 `NOT_PREREGISTERED`；仍可作为探索运行，但不能事后升级。

## 2. 可区分的竞争解释与反证预测

| 代号 | 解释 | 必要预测 | 最快反证 |
|---|---|---|---|
| `H-R` | 原 baseline 可确定性重放 | `A0@rep=n` 的实际条件张量、noise 与输出均在冻结 replay 容差内 | 任一科学分析前出现无法解释的 A0 超差、cache/ID/noise 不同 |
| `H-NOCLIP` | 当前失败与 CLIP 消费路径无关 | A1−A0 的输出效应不超过 replay；或只改变不可归因于失败的全局外观 | A1 在留出事件上产生超过 replay 且与冻结回访指标有关的配对效应 |
| `H-GLOBAL` | 只是全局 CLIP 存在/内容起作用，未证明 mean 有害 | A1 有相关作用，但 A2–A5 没有一个在守门指标上稳定胜过 A0，或变化只在全局风格 | 普通 A2–A5 中有臂跨留出场景稳定改善且无 guardrail 代价 |
| `H-AGG` | 算术 mean 是可由普通聚合替代暴露的问题 | 至少一个 A2–A5 相对 A0 达到预注册有意义改善；A2 与 A3 的关系区分目标方向与任意向量扰动 | 所有 A2–A5 的确认性 CI 均排除有意义改善，且结果不是低功效造成 |
| `H-ADDR` | 固定 retrieval 后，某来源的条件变化对其几何支持区有可复现的局部响应 | F11 coherent 反事实超过 replay 且响应在 `M_i` 富集；F10/F01 若解释为分支响应，还须跨至少两种预注册编辑方向/定位一致并与 F11 一致 | F11 无超过 replay 的局部响应；定位不超过面积基线；只剩全局色调；或 F10/F01 只在 cross-path conflict 中出现 |
| `H-CONFOUND` | 表面效应来自 norm、noise、相机、cache、执行顺序、编辑破坏几何或指标循环 | 修正这些混杂后效应消失 | 任一 material invariant 不匹配，或结果依赖 GT/输出后选择 |

这些假说只用于区分机制解释。`H-AGG` 或 `H-ADDR` 得到支持仍不等于新方法，也不等于 PhD/CCF A 级创新。

## 3. 实验单位、重复和配对

### 3.1 唯一统计层级

- **干预实验单位**：预注册的 `scene × target/revisit episode`。一个 episode 包含冻结的历史候选、目标窗口、ROI、相机轨迹和全部臂的配对生成。
- **总体外推的独立聚类单位**：scene。一个 scene 内的多个 episode 共享外观、几何和历史，必须作为嵌套观测，不能当成相互独立的场景。
- **配对技术重复**：同一 episode 上的 noise tensor/seed。所有臂必须使用逐值相同的实际 noise tensor；seed 只估计生成随机性，不增加独立场景 `n`。
- **A0 replay 重复**：写作 `A0@rep=n_replay`。它是工程重复，不是新臂，也不增加科学样本量。
- **F 阶段单位**：`scene × episode × observed source i`；预注册编辑和 seed 嵌套其中。至少两个低强度编辑是复现条件，不是两个独立 scene。
- pixel、patch、frame、扩散 step、候选 memory ID、同一视频的重叠窗口均是测量或子样本，绝不作为独立 `n`。

论文和表格必须同时报告：独立 scene 数、scene 内 episode 数、每个 episode 的有效配对 seed 数、A0 replay 次数、F 的 source 数与 edit 数。只报总帧数或总像素数属于伪重复。

### 3.2 配对聚合

令 `Y_{s,e,r,a}` 为场景 `s`、事件 `e`、配对 seed `r`、臂 `a` 的冻结结果。先在同一事件内按冻结规则聚合技术重复：

\[
\bar Y_{s,e,a}=\operatorname{mean}_{r\in R_{s,e}}Y_{s,e,r,a}.
\]

主要 A 臂配对效应定义为：

\[
d_{s,e,a}=\bar L_{s,e,A0}-\bar L_{s,e,a},\quad a\in\{A1,A2,A3,A4,A5\},
\]

其中主要失败损失 `L` 越低越好，因此 `d>0` 表示替代臂改善。每个 scene 先对其 episode 等权平均，再对 scene 等权汇总；不得让某个场景因窗口更多而占更大权重。均值是主要估计量，因为研究问题关心期望损失且 factorial interaction 需要线性 contrast；scene 级中位数与胜率是稳健性报告，不替换主要估计量。

## 4. 结果、效应量和置信区间

### 4.1 运行前必须冻结的指标

每个指标须写清：输入文件、预处理、方向、聚合维度、有效范围、缺失规则、软件版本和代码 hash。

1. `L_revisit`：唯一主要回访失败损失，越低越好；只在输出前冻结的 ROI 上计算。
2. `D_output`：A1/A0 或 F/F00 的固定输出/特征距离；表示和层必须在看臂输出前冻结。
3. `G_camera`：相机服从 guardrail，方向和非劣 margin 预注册。
4. `G_quality`：整体质量 guardrail，方向和非劣 margin 预注册。
5. `G_global_style`：用于识别“只改变全局色调/风格”的诊断指标；不能在看到结果后挑选。

若主要指标使用与 CLIP 相同或高度重叠的特征编码器，必须另报一个独立感知/几何指标和人工盲评敏感性，避免“改变 CLIP 条件后用 CLIP 给自己打分”的循环。人工盲评若加入确认性结论，须另冻结受试者数、盲法、随机顺序和一致性分析；否则只作探索。

### 4.2 必报效应量

对每个预注册 contrast 均报告：

- 主要：原始指标单位的 scene 等权配对均值差及双侧 95% CI。
- 稳健性：scene 级配对中位数差、scene/episode 胜率及其 95% CI。
- 可选描述：配对标准化效应 `d_z = mean(d_s)/sd(d_s)`；独立 scene 太少时不解释该不稳定量。
- guardrail：原始单位差和单侧非劣 CI，相对事前 margin 判断。
- 完整分布：每个 scene/episode 的配对点，而非只给总体柱形图。

不允许只报告 p 值或“提升百分比”。CI 跨越零表示方向不确定；CI 未覆盖预注册 SESOI 才能讨论实践意义。未显著不能写作“无效”，除非等效检验的完整 CI 落在预注册等效区间内。

### 4.3 主要区间估计

确认性主要 CI 使用**保持配对的层级 cluster bootstrap**：先有放回抽 scene，再在抽中的 scene 内有放回抽 episode；同一 episode 的所有臂、seed 和 edit 必须成组移动。bootstrap 随机种子和重复次数在 execution manifest 中冻结。

确认性 p 值使用与主要估计量一致的**零假设中心化 scene-cluster bootstrap**，而不是把像素或 seed 打散：先形成每个 scene 的等权配对效应，再在所检验的零假设边界上中心化，重抽 scene，并在 scene 内保持全部 episode/臂配对。改善检验以 `theta=delta_revisit` 为零假设边界，等效检验对 `-delta_direction` 与 `+delta_direction` 做两个单侧检验，等效 claim 的 p 值取两者较大值。F 复合 claim 的必要子检验同理。bootstrap 重复次数、随机种子、尾部定义和有限重复修正必须在 manifest/analysis script 中冻结。主要结论须由 CI 与 SESOI 同时支持；p 值只承担预注册错误率决策。

若独立 scene 数不足以支持预注册的 cluster 估计与精度目标，不切换成把 episode 或 seed 当独立样本的普通 bootstrap；应降级为场景条件下的描述性/Monte Carlo 结果。正态性检验不会被用作“看到数据后换检验”的开关。Q-Q 图、残差、离群点和 scene 异质性只作为诊断；主要稳健分析始终按预注册层级完成。

可将 `metric ~ arm + (1|scene) + (1|scene:episode)` 的混合效应模型作为敏感性分析，但不能在 bootstrap 和混合模型中事后挑更显著者。若模型奇异、收敛失败或 scene 太少，原样报告失败，不用删除 scene 修复结论。

## 5. 校准、SESOI 与样本量

### 5.1 禁止编造样本量

本文不写虚构的 scene、episode 或 seed 数。确认性样本量由以下流程生成并写入 manifest：

1. 从 `CAL` 的 A0 replay 和 baseline 获取 scene 间、scene 内 episode 间、配对 seed 间的方差与 intraclass correlation；报告估计不确定性。
2. 每个主要结果设定 **SESOI**（smallest effect size of interest）：
   - `delta_revisit`：值得改变结论的最小回访损失差；
   - `delta_direction`：A2/A3 可视为等效的最大容许差；
   - `delta_localization`：Localization 相对 mask 面积基线的最小富集；
   - `delta_interaction`：值得解释的最小 signed factorial interaction；
   - camera/quality 非劣 margins。
3. SESOI 必须来自任务意义、已独立冻结的测量误差或外部先验；不能设为刚好小于已观察效应。
4. 用保守方差（优先使用方差上限）模拟完整层级、配对结构和 Holm gatekeeping，求满足目标功效与 CI 精度的最小整数设计。默认目标是双侧 familywise `alpha=0.05`、主要科学主张功效至少 0.80；最终数值和模拟脚本 hash 必须冻结。
5. 同时检查精度：主要 95% CI 的预期半宽不大于对应 SESOI。功效和精度取更大的样本设计。

配对高斯近似可作 sanity check：

\[
n_{pair}\approx\left(\frac{(z_{1-\alpha^*/2}+z_{1-\beta})\sigma_d}{\delta_*}\right)^2,
\]

但正式设计必须用层级模拟，因为 episode 嵌套在 scene，且存在多臂和 gate。这里的 `n_pair` 不能被解释为 seed 数。

若校准样本不足以稳定估计方差，增加 `CAL`，或把项目声明为 pilot/估计研究。若可用计算预算小于所需确认性设计，冻结预算并降级研究目标；禁止运行到“显著”为止。研究结束后不报告 post-hoc power，改报实际 CI、可检测效应和未排除的效应范围。

### 5.2 replay 容差

`A0@rep=n_replay` 只用 `CAL` 冻结：

- `tau_numeric`：由 dtype、设备、算子和确定性设置给出的工程数值容差；
- `tau_replay`：由 A0 technical replay 分布的事前固定上尾规则给出的统计容差；规则、分位点、置信上界算法和 `n_replay` 均写入 manifest；
- 最终 `tau_output=max(tau_numeric,tau_replay)`。

在 `CONF` 上，任一 material invariant 不同或 A0 replay 超过 `tau_output` 都是接线失败。不得把 A0 超差样本按“离群点”删除后继续科学检验。

## 6. 执行、随机化、盲法与无效运行

### 6.1 每个配对块必须逐值相同

除被指定干预的 CLIP/replace 条件外，下列对象必须由 hash 或逐值比较核验：历史 IDs 与顺序、`replace`、`concat`、`dense_vector`、两份 Plücker、mask、实际 noise tensor、RNG state、sampler、CFG、steps、模型、权重、VAE、解码器、评价代码和硬件/软件版本。A2–A5 还要记录实际送入 denoiser 的向量及 L2 norm；F 阶段保存两条条件空间的实际 delta。

### 6.2 执行顺序与盲法

- 先物化并保存每个 episode 的实际 noise tensor，再运行任何臂。
- 在每个 episode/seed block 内，用冻结随机化表平衡臂的执行顺序；每臂使用新进程或经验证的完整 state reset。
- A0 在预注册的 block 位置重复，用于检测时间漂移；这些仍叫 `A0@rep=n`。
- metric 计算脚本接收匿名 arm code；ROI、mask 和 edit 不能看输出后调整。
- 解盲只在全部输出、运行失败记录、metric 原始表和 hash 冻结后进行。

### 6.3 无效运行与缺失

只允许基于输出前可判定的工程条件宣布 invalid：hash/shape/dtype 不符、OOM/进程崩溃、cache readback 失败、实际 noise 不同、文件损坏或执行协议未完成。低分、伪影、方向不符、极端值均不是删除理由。

- 工程失败按同一 unit/arm/实际 noise 重试，保存每次 attempt 和原因。
- 无法恢复的配对块从该 contrast 的主要 paired analysis 中缺失，同时报告各臂失败率与原因。
- 若失败率与 arm 有系统关联，主要质量比较判不可解释；另做保守 worst-case sensitivity，不能只分析成功生成。
- 不插补生成输出，不把另一 seed 顶替成原配对 seed。
- 所有排除在解盲前锁定并留下审计表。

## 7. 分阶段统计决策

### 7.1 G0 与 A0 replay

G0 不是显著性筛选。`CAL` 可用于发现并冻结自然失败；`CONF` 必须按轨迹/重访资格连续纳入全部合格 episode，而不能只留 baseline 最差者。须提供从全部候选到纳入/排除的 flow table。

`H-R` PASS 需要：

1. 原 S40 baseline provenance 和第二批 cache 消费真实核验；
2. A0 与原 baseline 的 material invariants 一致；
3. 所有计划的确认性 A0 replay 都不超过冻结 `tau_output`；
4. 无 arm 相关状态污染证据。

任一项失败：**ENGINEERING STOP**。修复后生成新版本协议和新 manifest；旧失败保留，不能在原预注册下继续。

### 7.2 G1：A1 的 influence 与 failure relevance

G1 是两个都必须通过的交集检验：

**Influence**

\[
q_{s,e}=D_{output}(A1,A0)-\tau_{output}.
\]

scene 等权汇总的 `q` 单侧 95% CI 下界必须大于 0。它只证明 CLIP 条件路径影响输出。

**Failure relevance**

\[
d_{s,e,A1}=L_{revisit}(A0)-L_{revisit}(A1).
\]

双侧 95% CI 必须完全高于 `+delta_revisit`（A1 有意义改善）或完全低于 `-delta_revisit`（A1 有意义恶化）。若 CI 位于 `[-delta_revisit,+delta_revisit]` 内，可支持“实践等效”；若横跨边界，只能写“不确定”。

进入 G2 还要求：相机和整体质量满足冻结非劣 margins，且变化不是 `G_global_style` 显示的纯全局风格变化。G1 两个必要判断构成交集，所以每个按 `alpha=0.05` 检验不会因“两个都要过”增加 I 类错误；不得把其中一个通过写成 Gate 1 通过。

G1 kill rules：

- influence 不通过：停止 mean/CLIP 消费路线；
- influence 通过但 failure relevance 不通过：只保留“CLIP 会改变像素/特征”，停止失败机制叙事；
- 只有全局风格或以相机/质量代价换回访分数：停止局部身份分支；
- A1 改善：只说明全局 CLIP 的存在/内容可能有害，不能归因于 mean。

### 7.3 G2：A2–A5 普通强基线

G1 通过后必须完成 A2–A5，不得看到 A2 后提前停。每个臂的主要效应为 `d_{s,e,a}`；确认性成功同时要求：

1. multiplicity-adjusted 95% CI 下界大于 `delta_revisit`；
2. camera 与 quality 同时满足冻结非劣 margin；
3. 改善在 scene 图上不是由单一 scene 驱动；
4. 实际信息、norm、计算量和失败率完整披露。

任何普通臂满足这些条件，就成为更强 baseline，**直接否决“需要新 router/gate 才能解决”的方法新颖性**。它不自动证明 mean 是唯一原因。

对“A2≈A3”必须做等效检验，比较 `L(A2)-L(A3)` 的 simultaneous CI 是否完整落在 `[-delta_direction,+delta_direction]`。仅因 p>0.05 不能写“相近”。即使等效成立，也必须继续 A4/A5。

若 A2–A5 均未成功：

- CI 仍包含有意义改善：结论是低精度/不确定，不能说 mean 不是原因；
- 四臂 CI 均排除 `delta_revisit` 以上改善：可拒绝“这些普通替代有足够改善”，仍不能拒绝所有可能消费者机制；
- A1 改善而四臂不改善：只保留全局 CLIP 有害/粒度/整条路径混淆；
- A1 恶化而四臂不改善：当前 CLIP 条件有用，拒绝“有害 mean”故事。

### 7.4 D：F00/F10/F01/F11 source-to-region factorial

D 仅在根协议四项进入条件全部满足且 G2 普通审计完整后运行。F00 必须逐值等于对应 A0；否则工程停止。

其中“至少一个预注册来源相关 contrast”必须在 execution manifest 中用定义文件和 SHA 明确绑定；不能跑完 A2–A5 后从多个来源、指标或区域里挑一个最有利的 contrast 作为 D 入口。

每个真实观测来源 `i` 至少有两个在输出前冻结的低强度、geometry-preserving image edits。每个 edit 保存原图、反事实、mask、参数、相机/几何/可见支持检查与 SHA。生成来源、decode/re-encode latent 或改变几何的 edit 不进入首个干净测试。

对 `c∈{10,01,11}`，先相对 F00 计算非负输出距离图 `D_c(p)`，并原样报告：

\[
T_c=\frac{1}{|\Omega|}\sum_{p\in\Omega}D_c(p),\quad
T_c^{in}=\frac{1}{|M_i|}\sum_{p\in M_i}D_c(p),\quad
T_c^{out}=\frac{1}{|\Omega\setminus M_i|}\sum_{p\notin M_i}D_c(p),
\]

\[
Localization_c=\frac{\sum_{p\in M_i}D_c(p)}{\sum_{p\in\Omega}D_c(p)+\epsilon}.
\]

`M_i` 和 `epsilon` 在看输出前冻结。主要定位判据使用原始 `Localization_c` 相对 mask 面积比例 `pi_i=|M_i|/|Omega|` 的事前 margin；`T_in/T_out/T_total` 必报，防止总效应接近零时比例虚高。pixel 不进入统计 n；这些量先聚合成 source/episode 级观测。

四个确认性 F claim：

1. `F-COHERENT`：F11−F00 总响应超过 replay，且 `Localization_11` 的 CI 下界超过 `pi_i+delta_localization`。
2. `F-CLIP-BRANCH`：F10−F00 满足同样的总响应与定位门；至少两个预注册 edit 的有符号方向和定位各自一致，并与 F11 一致。
3. `F-REPLACE-BRANCH`：F01−F00 满足同样条件，并与 F11 一致。
4. `F-INTERACTION`：对事前冻结的有符号标量 `Y`，

\[
I_Y=Y_{11}-Y_{10}-Y_{01}+Y_{00}.
\]

其 simultaneous CI 必须完全位于 `[-delta_interaction,+delta_interaction]` 外才叫有意义交互。CI 在区间内只能支持分辨率范围内近似可加；横跨边界是不确定。交互正负按 `Y` 的预注册方向解释，不得只由符号命名“协同/冗余”。

有符号 `Y`/特征轴必须由任务和 source edit 在看输出前定义。例如 photometric edit 可用其事前方向定义投影轴。若没有可辩护的有符号预测，`F-INTERACTION` 降为探索，不能先看 F11 再选择投影方向。空间交互图先在固定有符号表示逐位置计算 `F11-F10-F01+F00`，再取范数；禁止对三个非负 `D_c` 图相减。

F10/F01 是 cross-path-inconsistent branch response，绝不作为性能 baseline。即使显著，也不能说明该路径在自然一致输入下“主导”；若它们只在冲突条件产生大伪影、跨 edit 不一致或与 F11 不一致，相应分支解释被 kill。只有 F11 可代表 coherent image counterfactual。

## 8. 多重比较与确认性检验族

1. G1 为预先排序的 gate；Influence 与 Failure relevance 都通过后，后续 claim 才可开启。
2. G1 之后建立一个固定的九项主张族：
   - A2、A3、A4、A5 相对 A0 的有意义改善（4 项）；
   - A2 与 A3 的等效主张（1 项）；
   - `F-COHERENT`、`F-CLIP-BRANCH`、`F-REPLACE-BRANCH`、`F-INTERACTION`（4 项）。
3. 对九项使用 Holm familywise correction，整体 `alpha=0.05`。若 D 未进入或某个 F claim 因无有符号预测而未运行，该项按未拒绝处理，不从检验族删除以换取更宽松阈值。
4. 复合 F claim 用其必要子检验的最大 p 值作为 claim-level p 值（intersection-union），再进入 Holm；任何一致性前提失败时该 claim 直接不成立。
5. 主要论文表同时报告未调整 95% CI、Holm-adjusted p 值，并优先提供可实现时的 simultaneous 95% cluster-bootstrap CI。只用未调整 CI 作探索性可视化时必须标清。
6. camera/quality guardrails 是每个成功主张必须共同满足的非劣条件；使用同时置信界或在 guardrail 家族内 Holm 校正。
7. 未预注册的其他指标、ROI、层、时间步和来源分析统一为 exploratory；可用 Benjamini–Hochberg `q=0.05` 控制 FDR，但不能替换主检验。

不得在看到哪个 metric 显著后把它升为主要结果，也不得把九项拆成多个“各自 alpha=0.05”的家族。

## 9. 停止规则

### 9.1 科学 gate stop

- G0 无稳定自然失败：停止消费者失败方向。
- A0 replay 失败：工程停止，修接线后新建协议版本。
- G1 influence 失败：停止 CLIP/mean 路线。
- G1 relevance 失败或只有全局风格：停止局部身份/mean 路线。
- G1 通过：完整运行 A2–A5；不得因早期臂结果跳过剩余臂。
- D 进入条件未全满足：不运行确认性 F factorial。
- F11 不产生超过 replay 且定位的 coherent 响应：kill source-to-region 主假说。
- F10/F01 跨编辑或与 F11 不一致：kill 对应分支解释。

### 9.2 样本与中途查看

- `CONF` 的 scene、episode、seed 和 replay 数固定后，不做 efficacy peeking，不按 p 值、趋势或好看视频提前停止或扩充。
- 可在不解盲 arm 的情况下检查文件完整性、OOM、运行时和预注册工程失败。
- 若预注册 compute/RSS/wall-time 上限触发，停止并报告已完成比例；结果降为不完整/探索，不能用“接近显著”补结论。
- 若确需设计修改，先封存旧结果，再生成带新 SHA 的修订协议；修改后的新数据不能与旧确认性数据无标记合并。
- 不采用 post-hoc power 或“收集到显著为止”的 sequential stopping。若未来采用组序贯设计，必须在任何确认性输出前另行冻结 alpha-spending、look 次数和边界。

## 10. 假设、诊断与敏感性分析

| 假设/风险 | 事前保护 | 失败后的合法处理 |
|---|---|---|
| scene 之间可近似独立 | 场景级划分、记录采集来源/轨迹重叠 | 重复场景合并为同一 cluster；无法独立则限定为 case study |
| 臂内配对完整 | 保存同一实际 noise tensor 和所有 material hashes | 只分析完整配对并报告失败；做 worst-case 敏感性 |
| 无 cache/carryover | fresh process 或验证过的 reset；平衡执行顺序 | 存在污染则工程失败，不作因果解释 |
| ROI/M_i 与输出独立 | 从冻结预测几何和 baseline 前信息生成 | 输出后修改的 ROI 只作探索 |
| edit 只改 appearance | 保存几何/可见支持稳定证据 | 破坏几何则移到 OOD stress，不沿用原 M_i |
| metric 与干预不循环 | 主损失和独立 guardrail 预注册 | CLIP-only 评分须加独立指标并降级解释 |
| cluster bootstrap 足够 | 样本量模拟和精度检查 | 不把 pixels/seeds 提升为 n；改为估计/案例报告 |
| 极端值是真实观测 | 不按结果删点；报告 scene 图 | 仅预注册工程 invalid 可排除 |

敏感性分析的结果无论支持或反对主要结论都报告。若不同合理分析产生相反方向，结论写“分析依赖”，不能挑选一项。

## 11. 预注册失败判据与允许的结论

| 观察结果 | 允许结论 | 禁止结论 |
|---|---|---|
| A0 超 replay | 接线/确定性未过 | CLIP、mean 或 source 机制 |
| A1 无 influence | 未检测到当前条件下 CLIP 输出影响 | CLIP 永远无用；统计不显著即等效 |
| A1 influence 有、relevance 无 | CLIP 改变输出但未关联冻结失败 | mean 导致回访失败 |
| A1 relevance 有 | 当前全局 CLIP 条件与失败有关，方向已知 | 算术 mean 是原因 |
| A2–A5 普通臂成功 | 得到更强普通 baseline；router/gate 新颖性受否决 | 已得到创新方法 |
| A2–A5 均不成功且 CI 宽 | 证据不足 | mean 不是原因 |
| F11 局部响应成功 | coherent 来源反事实在该 consumer 中可局部测量 | 神经元归因、真实世界因果贡献 |
| F10/F01 单次大效应 | cross-path conflict 下的 branch response | 自然一致输入下该分支主导 |
| signed interaction 有意义 | 固定表示和干预范围内存在非加性响应 | 直接命名为协同、冗余或新架构需求 |
| 单一 scene 成功 | 该 scene 的配对案例证据 | 跨场景稳定、普适机制、CCF A 水平 |

确认性 kill 不是项目失败，而是排除一条解释。只有跨独立场景、跨配对 seed，并通过普通强基线、近邻排重和外部 consumer 复现后，才可讨论新问题/benchmark；方法贡献还需另立协议比较等信息、等参数/计算的 router/gate/PoE。本文不提供该创新结论。

## 12. 审稿人致命缺陷清单

### CRITICAL：任一项存在就不能作确认性因果/机制结论

| 编号 | 致命缺陷 | 为什么致命 | 本协议要求的修复 |
|---|---|---|---|
| C1 | 把 pixels、frames、patches、seeds 或同场景窗口当独立 n | 标准误被人为缩小，形成伪重复 | scene 为外推 cluster；episode 嵌套；seed 只作技术配对 |
| C2 | 用同一批 baseline 选最差失败、调 ROI/指标，又在同批上确认 | winner's curse、回归均值和 double dipping | CAL/CONF 分离；CONF 连续纳入全部合格事件 |
| C3 | 没有 SESOI、方差依据、样本量/精度计算 | “无显著”无法区分无效与低功效 | 先校准并模拟；预算不足则降为 pilot |
| C4 | 中途查看效果后停、增 seed/scene 或改主指标 | I 类错误和选择偏差失控 | 固定 n，无 efficacy peeking；修改须新版本 |
| C5 | A0 不能 exact replay 或 noise/cache/ID/Plücker 未逐值相同 | 干预与状态变化混杂，因果 contrast 无效 | material invariant hash/值检查；失败即工程停止 |
| C6 | ROI、source、edit、mask、投影轴看输出或 GT 后选择 | 结论由结果反向定义 | 所有对象在输出前冻结并哈希；GT 只用于冻结评价 |
| C7 | F10/F01 当自然性能 baseline | 两条 appearance path 输入互相冲突 | 只作 branch response；F11 才是 coherent CF |
| C8 | 对非负距离图直接算 F11−F10−F01+F00 | 符号和交互含义不存在 | 先在固定有符号表示作 contrast，再取 norm |
| C9 | 九项主张不校正或事后删除未运行/失败项 | 多重检验制造偶然阳性 | 固定九项 Holm family；未运行项不拒绝 |
| C10 | 用 p>0.05 宣称 A2≈A3、无影响或等效 | 未拒绝零假设不证明等效 | 事前 margin + 等效 CI/TOST |
| C11 | 只保留成功生成，且失败率依赖 arm | survivor bias 可伪造质量增益 | 报全部 attempts/失败率并作 worst-case 敏感性 |
| C12 | 单一 scene 或同场景切片声称跨场景机制 | 外推单位不足 | 限定为 case study；场景级独立留出后再确认 |
| C13 | ordinary A2–A5 已解决仍宣称新 router/gate | 强基线直接覆盖方法必要性 | 普通臂升级为 baseline，方法新颖性 kill |
| C14 | 用 CLIP 派生指标单独评价 CLIP 干预 | 评价器与干预共用表征，存在循环 | 加入独立几何/感知指标和盲评敏感性 |

### MAJOR：不一定使数据无效，但会显著削弱论文

| 编号 | 主要缺陷 | 修复 |
|---|---|---|
| M1 | 只给均值和最好视频 | 给每个 scene/episode 配对点、全部负结果和 selection flow |
| M2 | 未报告原始单位效应、CI 和 guardrail | 完整报告效应量、95% CI、相机/质量非劣结果 |
| M3 | F 编辑强度、几何稳定或实际条件 delta 不透明 | 保存 edit provenance、参数、SHA 与两路径 delta |
| M4 | 某一 scene 驱动总体效应 | scene 等权、leave-one-scene-out 敏感性并降低外推 |
| M5 | 混合模型不收敛后无记录地换分析 | 保留失败并以预注册 cluster estimator 为主 |
| M6 | A2–A5 信息/计算差异未披露 | 逐臂列输入、norm、K/V 长度、参数和运行预算 |
| M7 | 交互的符号方向事后定义 | 由 source edit 和任务预先冻结 signed axis；否则探索 |
| M8 | “未找到近邻”被写成“确认新颖” | 把排重范围和未覆盖边界写清，另做正式 novelty review |

审稿推荐规则：任何 C1–C14 未解决为 `REJECT/NOT INTERPRETABLE`；CRITICAL 全部解决但样本量/留出仍未冻结为 `REVISION_REQUIRED`；协议冻结且执行审计通过才可进入结果审查，仍不预判方法或创新。

## 13. 最小结果表与完整报告规范

每个阶段必须保存一行式 machine-readable event table，至少含：

`protocol_sha, manifest_sha, split, scene_id, episode_id, source_id, edit_id, paired_noise_sha, arm, attempt, valid, invalid_reason, material_hash_pass, metric_version, L_revisit, D_output, G_camera, G_quality, G_global_style, T_in, T_out, Localization, runtime, peak_rss, output_sha`。

最终报告按固定顺序给出：

1. 纳入/排除 flow、实际独立 scene 数、episode/seed/replay/edit 数和缺失；
2. A0 replay 与所有 material checks；
3. G1 Influence 与 Failure relevance 的原始效应、95% CI 和 gate；
4. A2–A5 全部臂及 A2/A3 等效，不论显著与否；
5. 若进入 D，F00–F11 全部 scalar、inside/outside、Localization、signed interaction 和跨 edit 一致性；
6. Holm 调整、guardrail、敏感性、失败率、runtime/RSS；
7. 与本节允许结论逐句对齐的 evidence statement；
8. exploratory 结果另表，不能混入 confirmatory 摘要。

统计结果至少报告：估计量、95% CI、检验统计量或 bootstrap/permutation procedure、有效独立 scene 数、自由度（若适用）、精确 p 值、效应量、校正方法、缺失和假设诊断。p 值不写成 `p=0.000`；极小值用 `p<...` 或软件可可靠表达的精确值。

## 14. 执行前硬门清单

只有下列全部为 PASS 才能把运行叫“确认性执行”：

- [ ] S40 真实 baseline 和 cache readback 已实际通过；
- [ ] 根协议与 reconciliation SHA 未漂移；
- [ ] CAL/CONF 划分和全部合格 episode 清单已冻结；
- [ ] 唯一主指标、ROI/M_i、guardrail 和方向已冻结；
- [ ] replay 规则、全部 SESOI 和非劣 margins 有独立依据；
- [ ] 层级功效/精度模拟已输出整数 scene/episode/seed/replay 数；
- [ ] arm、配对 noise、随机执行顺序和 fresh-state 规则已冻结；
- [ ] A2–A5 的实际信息与 norm 审计脚本已冻结；
- [ ] 若计划 D，真实 source、至少两个 edit、mask、signed axis、几何稳定规则已冻结；
- [ ] 九项检验族、Holm、CI 和缺失规则已写入 analysis config；
- [ ] manifest 符合 `manifest.schema.json` 且所有绑定文件有 SHA-256；
- [ ] 另一作者/agent 在不看结果的情况下完成 pre-run 审核。

未全部通过时，合法下一步只有校准、工程修复或协议修订；不能声称 confirmatory、机制成立或创新成立。
