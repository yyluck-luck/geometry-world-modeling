# S48 GeoCausal 最小否证实验预注册草案 V2

- 草案时间：2026-09-08（Asia/Shanghai）
- V2修订时间：2026-09-08T13:33:24+08:00
- 状态：`REVISED_DRAFT_PENDING_FRESH_INDEPENDENT_REVIEW_NOT_EXECUTION_AUTHORIZATION`
- 本版范围：**只设计CAL/pilot否证，不授权confirmation，不进行总体显著性或方法主张**
- V1原件：`archive/S48_GEOCAUSAL_KILL_EXPERIMENT_PREREGISTRATION_DRAFT_v1_sha69ad32b9.md`，SHA-256 `69ad32b932369e6c5cc9b1fde65d20d2caca1892fd47e2a5e94c3d15b5c8ef32`
- V1独立统计审查：`INDEPENDENT_STATISTICAL_REVIEW.md`，SHA-256 `414f0119fbe901298063ff0d3eb24c0faa0f2551455f12ec27bdfad511c122c4`，裁决`BLOCKED`
- 适用对象：具有稳定 source ID，且能够枚举全部真实消费路径的显式检索式视频世界模型
- 当前候选模型：VMem 的 C1/C2 确认运行；C1 尚未完成数值相机守卫与盲评分，C2 尚未生成
- 当前新颖性授权：`NONE`

## 0. 给新手的说明

这份实验不是为了尽快做出一张漂亮图，而是用最小成本判断创新方向是否值得继续。

它依次问四件事：

1. 真实生成是否真的出现了稳定重访错误；
2. 普通运行选中的一条历史记忆是否真的改变了后续画面；
3. 变化是否集中在几何上应由这条记忆负责的位置；
4. 保留这条记忆，相比公平替代它，究竟改善还是损害了重访质量。

前一问不通过，就不做后一问。这样可以避免先做复杂方法，再寻找能支持方法的案例。

## 1. 预注册研究问题与假设

### RQ0：自然失败是否存在

- **H0-natural：** 在已冻结的 B0/C1/C2 重访轨迹中，没有达到原协议严重差异阈值且可重复的自然失败。
- **继续条件：** C1 或 C2 至少一行在数值相机/K 守卫通过后，盲评分报告 `primary ROI MSE > 0.01`，并由独立结果复核确认；视觉检查还必须排除“相机根本没按轨迹走”的替代解释。
- 若继续条件不成立，S48 停止。B0 的 `0.005278160708699555` 已低于该严格大于阈值，只能作为无严重事件的开发行。

### RQ1：该来源是否被消费者实际使用

- **H0-influence：** 在普通运行完成Select/Address之后，全路径一致改变目标来源的appearance bundle，输出差异不超过exact-replay本底加最小有意义差异。
- **H1-influence：** `F11−F00` 的配对输出效应同时超过exact-replay本底与预先冻结的最小有意义差异。本pilot只判“继续/停止”，不称总体显著。

### RQ2：作用是否发生在正确空间位置

- **H0-localize：** 影响落入干预前geometry support的比例，既不高于面积基线，也不高于在面积、形状、位置、边缘、重放方差、baseline error和可见深度上匹配的假support零分布。
- **H1-localize：** 真support的影响富集同时超过面积SESOI与matched-mask 95%分位，并在预定edit family/seed中保持方向。本pilot只写“超过冻结零分布”，不用“显著”。

### RQ3：该来源是有益还是有害

- **H0-benefit：** 对从未进入memory或conditioning的独立真实return reference，原来源相对公平替代条件不降低冻结损失。
- **H1-benefit-local：** 原来源同时优于同一来源的对称低强度appearance alternatives。
- **H1-benefit-matched：** 原来源优于同scene、identity、pose/FoV/support/source-quality及接口预算匹配的未选来源。
- “平均收益是否为正”和“能否预测负收益样本”是两个研究问题；S48只筛查前者，不训练或评价预测器。

RQ1/RQ2 的外观干预只能识别影响和位置，**不能单独给出收益符号**。RQ3 必须使用独立的质量结局和公平替代条件。

## 2. 分析单位与范围

### 2.1 分析单位

科学外推的最高单位是`scene`；观测单位是`scene × episode × revisit target × ordinary-run selected source`。seed、edit、replay、placebo和matched mask都是嵌套技术重复，不能增加科学样本量。

- target 必须来自普通、未干预运行；
- source 必须在普通运行中实际被选中，具有稳定 ID，并在当前时刻可寻址；
- source 的存储、选择和进入真实消费者的证据必须先独立复核；
- 第一轮只从C1/C2选择一个开发观测单位；它和所属scene永久标为CAL，不进入任何后续confirmation。
- C1/C2若用同一输入scene或同一轨迹家族，只算一个scene cluster。
- 开发单位选择顺序固定为C1后C2中第一个通过RQ0的预注册行；source固定为该行普通运行slot顺序中第一个通过G3且不是return reference的来源。不得按F11、Localization或Benefit结果换source。
- 若后续研究“自然失败中的作用”，screening seed只负责判定失败，另用未参与筛选的paired seeds做干预；不得从多个source中按F11效果挑最好者。

### 2.2 明确排除

- 不推广到无法追踪来源或无法枚举消费路径的纯隐状态模型；
- 不把合成矩阵或人工制造的像素差称为自然视频失败；
- 不把 attention、retention、retrieval score 或 source 被保存当作消费证据；
- 不把一个场景、一个 seed 或一个编辑的结果写成泛化结论；
- 不在本阶段训练接受器。

## 3. 执行前硬门

| Gate | 必须看到的证据 | 失败动作 |
|---|---|---|
| G0 baseline completion | C1 数值相机守卫、盲评分、独立结果复核；C2 独立生成与同级评分证据 | 不启动 S48 |
| G1 natural failure | 至少一个自然严重差异事件，视觉上不是相机失从或明显生成崩溃 | 停止或改写为 baseline negative result |
| G2 reproducibility | 相同冻结输入/实际 noise/RNG 的 exact replay 本底可测且稳定 | 调试确定性；不做因果结论 |
| G3 source eligibility | 普通运行的 Store、Select、Address、所有 consumer path 清单均有证据 | 更换来源；无合格来源则停止 |
| G4 intervention validity | 外观变化低强度，source ID、shape、dtype、pose、K/Plücker、几何支持和检索身份不变 | 调整干预；不读取结果做阈值优化 |
| G5 path completeness | 同一处理进入全部真实 appearance consumer paths；目标来源后代全部重算 | F11 无效；只可作工程诊断 |
| G6 independent reference | Benefit使用从未进入memory/conditioning、在任何arm输出读取前封存的真实目标视角照片；其相机、时间和身份可复核 | 不做Benefit；若只用ID0，仅称return-to-ID0 consistency |
| G7 frozen pilot manifest | 唯一DAG、注入行/张量、source、edit/dose、mask generator、arm顺序、metric代码、SESOI、invalid规则及全部SHA经新鲜独立前审 | 不启动任何S48 arm |

## 4. 因果对象与冻结边界

### 4.1 处理变量

本pilot只估计下列DAG中的粗体箭头以后部分：

`Stored source → ordinary Select → ordinary Address → **appearance-bundle intervention → all consumer inputs → denoising/output → optional writeback**`

唯一处理时点必须绑定VMem精确源码行与张量：`get_context_info`已返回普通运行的selected IDs/slot/support之后、`get_cond`构造任何appearance consumer input之前。若源码版本改变或找不到一个覆盖全部路径的共同边界，本协议失效。

把普通运行已选中的目标来源拆为：

- `Z_i`：来源身份、时间、slot 和检索身份；
- `G_i`：普通Select/Address已经产生的pose、K/Plücker、深度/点图与target support；
- `A_i`：来源的外观内容及由它产生的 CLIP、VAE/latent 等 appearance 表示。

RQ1/RQ2的唯一estimand命名为 **baseline-selected、addressable source的post-selection downstream appearance effect**：给定普通运行已观察到的`Z_i,G_i`，对选中来源的RGB副本做低强度appearance edit，重新编码并替换该来源在全部appearance consumer paths中的表示，再重算全部下游。它不包含Store、Select或Address的因果效应，也不叫source total effect。

若以后要估计source item从进入Store开始的总效应，必须另立实验，在Store前干预并允许geometry、retrieval、selection、consumer和writeback全部重算；不得与本pilot共用标题、estimand或结论。

### 4.2 可以冻结的量

- prompt；
- 请求 camera、pose、K/Plücker；
- 实际初始 noise 与 RNG state；
- retrieval source IDs 和 slot 顺序；
- 非目标记忆的干预前初态；
- 处理发生前普通运行已经产生并记录的`Z_i,G_i`；
- 评价前冻结的 ROI 与 geometry support。

### 4.3 必须重算的量

- 目标来源的 CLIP/语义表示；
- 目标来源的 VAE/replace/latent 表示；
- 所有其他以 `A_i` 为祖先的 consumer 输入；
- 由这些输入产生的 attention、融合状态、denoising state、latents 和最终输出；
- 后续将该输出写回记忆后产生的所有目标来源后代。

禁止为了“控制变量”冻结上述中介；冻结它们会切断真正作用路径。

## 5. 条件与执行顺序

### 5.1 A0：exact replay

在同一冻结状态、实际noise、RNG和全部记忆下重放F00 **至少3次**。原F00与每次replay形成所有成对差异，先检查可达到的确定性：

- 若bitwise相同，经验replay floor记为0，但科学门仍保留最小有意义差异；
- 若不相同，保留全部差异，不事后挑选容差；`tau_replay`取所有F00–F00配对主距离的最大值，不能只扣均值；
- `tau_numeric=1e-6`，`delta_I=0.5/255≈0.0019607843`（在有效区域上的平均归一化RGB绝对差）；pilot Influence门固定为`D_intervention > tau_output + delta_I`，其中`tau_output=max(tau_numeric,tau_replay)`；
- pilot 方差只用于冻结确认阶段样本量，pilot 单位不进入确认统计。

### 5.2 来源外观四格

| Cell | CLIP/semantic path | replace/VAE/latent path | 用途 |
|---|---|---|---|
| F00 | 原来源 | 原来源 | 主基准 |
| F10 | 编辑来源 | 原来源 | 路径冲突诊断 |
| F01 | 原来源 | 编辑来源 | 路径冲突诊断 |
| F11 | 同一个编辑来源 | 同一个编辑来源 | 唯一主处理 |

若发现更多真实 appearance consumer path，必须全部加入 F11；上表的两列只是当前已知路径，不得被写成完整性的先验保证。

主比较仅为`F11−F00`。F10/F01不估计总效应，只检验单路径注入是否制造冲突或休眠旁路。

### 5.3 编辑族、sham与正负控制

读取任何F输出前，在source-only信息上冻结两个机制不同且geometry-preserving的对称低强度edit family：

1. 全局曝光/白平衡仿射族；
2. 不移动边缘位置的低幅高频纹理族。

每族的`+δ/-δ`剂量只可用source输入的固定LPIPS/CLIP/edge约束校准，不能查看任何生成输出。还必须包含：identity/no-op re-encode sham；以相同剂量编辑一个未选source的negative control；对已知真实consumer施加的预先固定positive control。两个edit family都须通过source identity、shape/dtype、边缘位移及接口检查；任一只能触发单路径或仅一个family有反应，主结论降为`intervention-specific sensitivity`。

### 5.4 运行随机化、重置与arm级守卫

- 所有arm物化同一实际initial noise/RNG/state；每个arm用fresh process或逐字段验证的full reset，禁止沿用前一arm写回后的memory。
- arm顺序由pilot manifest中预先冻结的随机种子产生，并在每个seed block中随机；A0 replay按冻结位置穿插检测漂移。
- 每次attempt均保存；只有读取生成输出前可判定的工程错误允许标invalid。不得删除arm-related crash后只重跑失败臂；失败率依赖arm时主比较不可解释。
- F11及每个Benefit placebo都与同seed F00比较arm级相机/画质守卫：稳健单应性相对identity的median displacement不超过`max(1 px, replay最大值)`且P95不超过`max(3 px, replay最大值)`；support外平均亮度差不超过`max(2/255, replay最大值)`；锐度比须在`[0.90,1.10]`内；饱和像素比例增加不超过`max(1 pp, replay最大值)`；不得有NaN、全黑、撕裂或少于50个可用匹配点。
- 上述代码、resize、颜色域和阈值在arm输出前冻结。盲态人工视觉检查只作次要诊断；任何arm级相机/整体画质守卫失败时，Influence最多称“模型有响应”，Localization和Benefit不得通过。

### 5.5 分阶段节省计算

1. **Pilot-A：** A0 + F00/F11，一个开发来源和一个seed；若`D_intervention`不超过`tau_output+delta_I`，停止。
2. **Pilot-B：** 加F10/F01、sham、未选source negative control、positive control、第二个paired seed及第二edit family；若只有单路径、单family或单seed响应，停止。
3. **Pilot-C：** 检验预先冻结support的面积与matched-mask局部性；若任一主门失败，停止。
4. **Benefit pilot：** 只有独立真实reference和公平替代均通过G6/G7才执行；否则S48最多形成Influence/Localization诊断，不能发展acceptance head。
5. **Confirmation不属于S48授权范围。** 若pilot存活，另建S49 confirmation preregistration，并在其运行前冻结精确scene数、样本量、SESOI、检验、多重性与代码SHA；C1/C2/CAL scene永久排除。

## 6. 指标

### 6.1 Influence

对相同 target frame 的同一像素 `p`，主效应图先使用无需学习的归一化 RGB 绝对差：

`d_i(p) = mean_c |Y_i,F11(p,c) − Y_i,F00(p,c)| / 255`。

令`D_intervention=mean_{p∈Ω_i} d_i(p)`。单位级净Influence只作描述：

`I_i = D_intervention − tau_output`。

Pilot继续门不是`I_i>0`，而是`D_intervention > tau_output + delta_I`；报告每个replay、edit family、seed的完整距离与倍率，不计算总体CI或p值。

LPIPS/spatial feature difference 只能作为冻结后的次要稳健性指标，不能在看结果后替换主指标。

### 6.2 Localization

令 `S_i` 为输出前从原来源几何投影得到并冻结的 support，`Ω_i` 为有效评价区域：

`mass_i = sum_{p∈S_i} d_i(p) / (sum_{p∈Ω_i} d_i(p) + ε)`

`area_i = |S_i| / |Ω_i|`

`L_i = mass_i − area_i`。

同时报告 enrichment ratio：

`ER_i = mass_i / area_i`。

面积基线只是第一关。读取F11前，唯一冻结generator为每个`S_i`产生`K=199`个唯一假support：候选来自未选source的投影、保持拓扑的刚性平移/旋转和预注册相机平移placebo；每个候选须与`S_i`满足面积±2%、连通分量数相同、周长/√面积±10%、质心位于同一4×4位置格、IoU≤0.10，并在F00 edge density、replay variance、independent-reference baseline error和可见深度四分位上落入同一预先定义stratum。generator只可读取干预前/CAL量，不能读取F11或任何Benefit输出。

定义`mass(S)`同上，主局部量为：

`L_matched_i = mass(S_i) − median_b mass(M_{i,b})`。

有限随机化p值为`p_mask=(1 + #{b: mass(M_{i,b}) >= mass(S_i)})/(K+1)`；199个mask只形成一个unit内的零分布，不能算199个样本。Pilot通过必须同时满足：`ER_i>1`、`L_i>=0.02`、`p_mask<=0.05`，且非选source投影与相机平移placebo均不通过同一门。若无法生成199个满足条件的mask，Localization记invalid并停止，不得放宽caliper。另固定support erosion/dilation与occlusion-aware sensitivity为次要稳健性检查，主mask保持唯一。

### 6.3 Natural revisit loss

沿用冻结的重访ROI，ID0与回到同一请求视角ID8之间RGB MSE只叫`return-to-ID0 consistency loss`；同时保留全帧和固定四区诊断。它可筛查RQ0，但ID0若进入memory/conditioning就不是独立答案，不能用于“correctness/quality/Benefit”主张。只有数值相机/K守卫和视觉相机服从检查通过时才解释为重访差异。

### 6.4 Benefit

定义损失越小越好。`F11−F00`不参与收益定号。`R_i`必须是从未进入memory、selection、conditioning或任何arm的真实目标视角照片，并在输出读取前封存相机/时间/文件SHA；否则RQ3不执行。主损失`ℓ_S`是support内归一化RGB MSE，`ℓ_out`是support外归一化RGB MSE；LPIPS只作次要稳健性。pilot Benefit的SESOI固定为`delta_B=0.001`，即自然严重阈值0.01的10%，不从arm输出估计。

第一种局部收益使用同一来源、同一slot/address的对称appearance treatment`T_{+δ}`与`T_{−δ}`：

`B_i^local(δ) = 0.5 × [ℓ_S(Y(T_{+δ}(x_i)), R_i) + ℓ_S(Y(T_{−δ}(x_i)), R_i)] − ℓ_S(Y(x_i), R_i)`。

- `B_i^local > 0`：原外观在这个局部邻域内优于同幅度的两侧变化；
- `B_i^local < 0`：原外观在这个局部邻域内不是 loss-optimal；
- 这不是“该 item 存在相对不存在”的绝对收益。

第二种增量收益使用看结果前冻结的匹配未选帧集合`P_i`：同scene、同对象identity，并保持相同tensor/token shape、slot、位置编码、source-ID接口、token数、顺序、mask、geometry和context长度。候选须同时满足：相对target的相机转角差不超过2°；平移baseline相对差不超过10%；FoV差不超过1°；投影support IoU至少0.80且面积比位于`[0.90,1.10]`；blur/exposure/saturation各落入同一CAL四分位；recency相差不超过2个source插入事件。使用满足条件的全部未选帧，若为空则`B_matched` invalid，不得放宽caliper：

`B_i^matched = mean_{P∈P_i}[ℓ_S(Y(P), R_i) − ℓ_S(Y(x_i), R_i)]`。

对一般原来源 `O` 和公平替代条件 `P`，可统一记作：

`B_i = Loss(Y_i,P) − Loss(Y_i,O)`。

- `B_i > 0`：原来源相对替代条件有益；
- `B_i < 0`：原来源有害；
- 接近 0：该来源对该质量结局无可分辨收益。

`B_matched`是未来confirmation的主Benefit，`B_local`是必要稳健性门；若只存在其中一个，只能写对应alternative下的相对效用。Pilot继续要求两个paired seed中`B_local>delta_B`与`B_matched>delta_B`且符号一致。每个量同时报告`ℓ_out`，并要求support外损失恶化不超过`delta_out=0.0005`；再报告support相对matched-mask的difference-in-differences。zero token或缩短context的OOD条件不能承担主placebo。两种Benefit符号不一致即停止一般Benefit主张。

## 7. 统计规则与confirmation边界

### 7.1 S48 pilot唯一允许的分析

- 所有生成比较按相同seed/noise/state成对；不比较不成对的随机输出均值。
- 报告每个scene/episode/source/seed/edit/replay/arm的完整flow、点估计、invalid和失败；不把pixel、frame、seed、mask或source当独立scene。
- S48只按冻结门做顺序性继续/停止：Influence→Localization→Benefit。除matched-mask有限随机化rank外，不给总体p值、置信区间或“显著”结论。
- 所有阈值、ROI、support、source、edit/dose、arm顺序、mask、reference、metric及代码SHA均在输出读取前冻结。

### 7.2 若pilot存活，S49必须另行冻结

S49不是本文件授权的一部分。它必须在任何CONF生成前通过独立统计审查，并精确写入：

1. CAL/CONF按scene完全分离的名单、资格规则和所有候选到纳入unit的flow；
2. 独立screening seed，以及未参与筛选的paired intervention seeds；
3. `delta_I`、`delta_L_area`、`delta_L_matched`、`delta_B_matched`、`delta_B_local`、`tau_output`与camera/quality非劣margin；
4. familywise `alpha=0.05`、目标power `>=0.90`、CI半宽目标，以及由保守CAL方差上限作出的层级配对模拟脚本/输出SHA；
5. 唯一整数`n_scene`、每scene episode/source数、paired seed/replay/edit/placebo数；预算不足则只能报告case study；
6. 唯一主estimator：先在source/episode内聚合技术重复，再让scene等权；scene-cluster bootstrap固定`10,000`次和固定seed，或exact scene-level sign/permutation test，二者在manifest中只能选一个；
7. Influence→Localization→Benefit的fixed-sequence gate。两个edit family需要同时通过时使用intersection-union；若“任一通过”则Holm校正。`B_matched`为主、`B_local`为必要稳健性；camera/quality使用同时非劣区间；
8. missing、invalid、arm-related failure、worst-case sensitivity、无可选加样/no optional stopping、冻结analysis/metric/arm代码和data manifest SHA。

预测负收益的acceptance head属于再下一阶段：预冻结features、scene-level held-out split、单一主指标和相对普通proxy的增量比较都必须另立协议；不得与S49平均Benefit检验共享测试scene。

## 8. 必须比较的强基线

1. exact replay；
2. attention mass；
3. retrieval similarity / score；
4. pose overlap 与 geometry support area；
5. source 被保留/选中的二元变量；
6. WorldTrace 式 addressability 修复或等价地址诊断；
7. TetherCache 式 attention + diversity 选择与 trusted-alignment 修复的可比实现或最接近公开结果；
8. CUE-R式REMOVE/REPLACE/DUPLICATE逐项干预、paired signed utility与保持长度/接口的公平版本；
9. identity re-encode sham、未选source同剂量negative control及已知consumer positive control；
10. 普通轻量gate、单一pose/retrieval/source-quality阈值；
11. source-agnostic全模块ablation与更长上下文/不使用外部item的强架构对照；
12. 若进入接受阶段，报告AURC、risk–coverage、clean false rejection与所有样本的总体paired loss。

## 9. Kill conditions

以下任一项成立，就停止或降级当前主张：

1. C1/C2 没有稳定自然严重差异事件；
2. 相机/K 或视觉相机服从失败；
3. A0 本底与 F11 效应同量级且无法解释；
4. 没有普通运行实际选中、可寻址、全路径可审计的来源；
5. F11 无响应而 F10/F01 响应，说明路径冲突或遗漏；
6. influence 不超过 replay；
7. localization 不超过 support 面积基线或 matched-mask 95% 分位；
8. benefit 对 placebo 构造敏感，符号不稳定；
9. 独立真实reference、199个合格matched masks或匹配未选来源不可获得；
10. 任一arm级相机/整体画质守卫失败，或sham/未选source产生同量级响应；
11. attention、pose overlap、retrieval score 或简单 gate 达到相同样本外预测；
12. 只能在一个场景、来源、编辑或消费者中成立；
13. 新公开工作完成同一联合协议。

## 10. 条件式方法路线：GeoCausal Acceptance Head

只有 confirmation 证明 `B_i` 存在稳定正负差异，而且预处理可见特征能预测它时，才进入方法阶段：

1. 用昂贵的 source-level `B_i` 产生离线因果教师标签；
2. 输入只使用生成前可见的 addressability、source-target geometry、retrieval、attention 先验和 memory-trust 特征；
3. 训练轻量学生预测 `B_i > 0` 或收益区间；
4. 在风险约束下选择 accept、reject 或 re-observe；
5. 与 TetherCache、普通 gate 和单一 pose/retrieval 阈值比较；
6. 报告所有样本的总体损失和覆盖率，不只展示被接受子集。

这一方法的潜在区别是“用来源级、几何定位、全路径因果收益作教师信号”，不是 gate 结构本身。Visual RAG 已有 utility surrogate，selective prediction 已有 risk–coverage；两者都必须作为直接近邻，而不是包装成全新思想。

## 11. 当前允许写的结论

当前只允许写：

> S48 V1经独立统计审查BLOCKED；V2已把干预时点改为明确的post-selection representation边界，操作化matched-mask与独立reference，并将范围缩为不作总体推断的CAL/pilot否证。V2仍待新鲜独立复审，尚不授权运行。

当前禁止写：

- 已发现自然失败；
- 已证明某条记忆被使用；
- 已证明空间局部因果；
- 已证明记忆有益/有害；
- 已提出有效新方法；
- 已达到 PhD、CCF A 或任何录用水平。

## 12. 近邻方法依据

- [SPMEM / NeurIPS 2025](https://proceedings.neurips.cc/paper_files/paper/2025/hash/467655d26fcc207bca08915dc91964c6-Abstract-Conference.html)
- [WorldModelBench / NeurIPS 2025](https://proceedings.neurips.cc/paper_files/paper/2025/hash/4ec03ed08a3fcb59e1c815b5598beff1-Abstract-Datasets_and_Benchmarks_Track.html)
- [Long-Context State-Space Video World Models / ICCV 2025](https://openaccess.thecvf.com/content/ICCV2025/html/Po_Long-Context_State-Space_Video_World_Models_ICCV_2025_paper.html)
- [VMem / ICCV 2025](https://openaccess.thecvf.com/content/ICCV2025/html/Li_VMem_Consistent_Interactive_Video_Scene_Generation_with_Surfel-Indexed_View_Memory_ICCV_2025_paper.html)
- [Geometry-guided Online 3D Video Synthesis / CVPR 2025](https://openaccess.thecvf.com/content/CVPR2025/html/Ha_Geometry-guided_Online_3D_Video_Synthesis_with_Multi-View_Temporal_Consistency_CVPR_2025_paper.html)
- [WorldTrace](https://arxiv.org/abs/2608.07408)
- [WorldKV](https://arxiv.org/abs/2605.22718)
- [Echo-Memory](https://arxiv.org/abs/2606.09803)
- [TetherCache](https://arxiv.org/abs/2606.13035)
- [CUE-R](https://arxiv.org/abs/2604.05467)
- [Utility-Oriented Visual Evidence Selection](https://arxiv.org/abs/2605.13277)
- [Is This the Subspace You Are Looking for? / ICLR 2024](https://openreview.net/forum?id=Ebt7JgMHv1)
- [SelectiveNet / ICML 2019](https://proceedings.mlr.press/v97/geifman19a)
