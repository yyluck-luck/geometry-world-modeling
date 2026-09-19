# S48 GeoCausal 最小否证实验预注册草案 V4

- 草案时间：2026-09-08（Asia/Shanghai）
- V4修订时间：2026-09-08T14:52:04+08:00
- 状态：`REVISED_DRAFT_V4_PENDING_FRESH_INDEPENDENT_REVIEW_NOT_EXECUTION_AUTHORIZATION`
- 本版范围：**只设计CAL/pilot否证，不授权confirmation，不进行总体显著性或方法主张**
- V1原件：`archive/S48_GEOCAUSAL_KILL_EXPERIMENT_PREREGISTRATION_DRAFT_v1_sha69ad32b9.md`，SHA-256 `69ad32b932369e6c5cc9b1fde65d20d2caca1892fd47e2a5e94c3d15b5c8ef32`
- V1独立统计审查：`INDEPENDENT_STATISTICAL_REVIEW.md`，SHA-256 `414f0119fbe901298063ff0d3eb24c0faa0f2551455f12ec27bdfad511c122c4`，裁决`BLOCKED`
- V2原件：`archive/S48_GEOCAUSAL_KILL_EXPERIMENT_PREREGISTRATION_DRAFT_v2_shaef92be76.md`，SHA-256 `ef92be76a8f8f2d6cd6fe70e629f77114751d9ed2a05228618038087e6fda92d`
- V2独立统计审查：`INDEPENDENT_STATISTICAL_REVIEW_V2.md`，SHA-256 `3470ae9a421bc3b8ce916b8e6959d36d49e1ccc9f12e7002e841fdd22ff1b372`，裁决`BLOCKED`
- V3原件：`archive/S48_GEOCAUSAL_KILL_EXPERIMENT_PREREGISTRATION_DRAFT_v3_sha02f3be41.md`，SHA-256 `02f3be4120ba4c7ee7da719313c1d430d133185cafbe56bb80eea3788b5896c1`
- V3独立统计审查：`INDEPENDENT_STATISTICAL_REVIEW_V3.md`，SHA-256 `7f0bc591aca198223cfa01792ea5eb9feb8f4f28f27cfc930085763a12c2b163`，裁决`BLOCKED`
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

- **H0-localize：** 影响落入干预前、逐实际target相机重投影的geometry-projected expected locus的比例不高于面积基线，或没有分别超过形状位置与相机几何两类预冻结placebo。
- **H1-localize：** 每个预定edit-family/seed/target效应图的真support都超过面积SESOI，并分别进入`G_shape`和`G_camera`各自预冻结library的前5%尾部；若再超过合格`G_source`，才允许selected-source-specific表述。
- matched-placebo结果只叫**描述性尾部排名**，不叫随机化p值、显著性或零分布；这些placebo没有把真support随机分配到候选集合，因而不满足可交换随机化推断。

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
| G3 source eligibility | 普通运行的 Store、Select、Address、稳定slot→source ID映射、完整多来源surfel provenance、逐实际target camera/K重投影的三种support及所有appearance consumer path清单均有证据 | 更换来源；无合格来源或support归因不唯一则停止 |
| G4 intervention validity | 外观变化低强度，source ID、shape、dtype、pose、K/Plücker、几何支持和检索身份不变 | 调整干预；不读取结果做阈值优化 |
| G5 path completeness | 同一处理进入全部真实 appearance consumer paths；目标来源后代全部重算 | F11 无效；只可作工程诊断 |
| G6 independent reference | Benefit使用从未进入memory/conditioning的同步真实目标视角照片；在任何arm输出读取前按唯一roster/排序封存，并通过`|Δt|<=0.010 s`、身份、动态排除、相机、双向common-visible、配准残差和warping-hole门 | 不做Benefit；若只用ID0，仅称return-to-ID0 consistency |
| G7 frozen pilot manifest | 唯一DAG、精确hook/张量、support归因、source、edit/dose与唯一聚合、matched-placebo generator、fresh-process状态、arm顺序、逐指标守卫、reference配准、metric代码、SESOI、invalid规则及全部SHA经新鲜独立前审 | 不启动任何S48 arm |

## 4. 因果对象与冻结边界

### 4.1 处理变量

本pilot只估计下列DAG中的粗体箭头以后部分：

`Stored source → ordinary Select → ordinary Address → **appearance-bundle intervention → all consumer inputs → denoising/output → optional writeback**`

唯一处理时点必须绑定VMem精确源码行与张量：普通`get_context_info`完成选择后、`get_cond`构造任何appearance consumer input之前。当前审查对象 `vendor/vmem_snapshot/modeling/pipeline.py` SHA-256 为 `90a45f452a4f734b3371fb526c566162026e5d900e0c8204709dd57f44ef1d7e`；其第759–765行只返回context tensors和`context_time_indices`，**没有返回target support**。因此当前源码不满足执行条件，不能把文本中的support当作已存在接口。

V4规定在任何arm运行前实现、测试、冻结并双审一个只读的`post_selection_bundle` hook。当前只有合同和静态可行性证据，**API仍缺失，hook尚不可执行**。实现后必须在同一次普通选择调用中物化：

1. 每个slot的`context_time_index`、稳定source ID、原始position和是否重复；
2. 产生选择的surfel索引及每个surfel对应的全部source timesteps；一个surfel映射多个source时，不得事后任选其一；
3. 保存普通retrieval所用平均pose/`0.65K`图仅作Select审计；另对每个实际输出target的精确`c2w_t/K_t`，使用冻结surfel、完整provenance、576×576 canvas及普通renderer完全相同的near/far、backface、disk rasterization、z-buffer和tie-break重新投影；
4. 对最前方surfel `j_t(p)`的全部来源集合`T_t(p)`，主权重固定为`w^frac_t(p)=1{s* in T_t(p)}/|T_t(p)|`，并同时封存`w^union_t(p)=1{s* in T_t(p)}`与`w^exclusive_t(p)=1{T_t(p)={s*}}`；空像素、无provenance、非有限depth和z-buffer未命中均为0；
5. `context_latents`、`context_encoder_embeddings`以及静态审计发现的所有其他appearance后代的slot/source轴映射；
6. 选择返回后到`get_cond`调用前的单一注入点，以及证明F11覆盖全部appearance路径、F10/F01只覆盖指定路径的trace字段。

hook必须只增加观察字段和一个受控替换点，不得改变普通选择顺序、tensor shape/dtype/device、pose、K、geometry或非目标slot。每个target frame单独保存`j_t`和三种support的SHA、area、exclusive purity、hole/invalid counts；先逐帧计算，再等权聚合，禁止把pixel或frame当科学样本。这里的support只叫**geometry-projected expected locus**，不能称为denoiser逐像素routing证据。若无法由同一次调用得到稳定source ID和support，或多值surfel归因不能按冻结规则解析，本实验在G3停止。若源码版本、行号或consumer清单改变，必须重冻SHA并重新前审。

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
- `tau_numeric=1e-6`，`delta_I=0.5/255≈0.0019607843`（在有效区域上的平均归一化RGB绝对差）；每个seed的`tau_output,s=max(tau_numeric,tau_replay,s)`，主门使用§6.1相对`max(replay,sham,negative)`的控制校准效应；
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

每族在输出产生前冻结严格升序候选剂量ladder、source-only最小可辨编辑门，以及LPIPS/CLIP/edge/clipping上界。对每个候选同时检查`+δ/-δ`，唯一选择函数是**两侧均通过全部source-only门的最小剂量**；无候选通过即该family停止。选定剂量对所有seed/path/Benefit-local固定，不能因生成响应弱而增大。全部数值阈值、实现和SHA进入G7，任何生成输出不得参与校准。

还必须包含：identity/no-op re-encode sham；按普通slot顺序确定、以相同family/dose编辑的第一个合格未选source negative control；对一个在源码和合成测试中已确认会进入`get_cond`的目标slot appearance tensor施加预先固定positive control。positive control的精确tensor、轴、剂量、预期trace和`delta_positive=0.5/255`必须写入G7，不能在看输出后换路径；若没有合格negative source，RQ1停止。

唯一聚合规则如下。对每个edit family `f`、paired seed `s`，先把对称剂量形成一个family map：

`d_{f,s}(p)=0.5×[mean_c|Y_{f,s,+δ}(p,c)-Y_{s,F00}(p,c)| + mean_c|Y_{f,s,-δ}(p,c)-Y_{s,F00}(p,c)|]/255`。

两个family × 两个paired seed形成四张预定主图；它们分别通过Influence、Localization和arm guard，主继续规则是**四者全部通过**。unit级保守摘要为四个对应统计量的最小值，只用于列表排序，不替代逐图报告。target的响应必须相对同seed replay、sham和同family/dose negative中的最强者仍超过`delta_I`；positive control相对replay/sham仍超过`delta_positive`且trace匹配。控制失败即停止或降级，不能挑选最有利family/seed/dose。

### 5.4 运行随机化、重置与arm级守卫

- 所有arm物化同一只读state snapshot、实际initial noise和RNG state；**当前源码每个arm一律使用fresh process**，并从同一snapshot重建。`pipeline.py:135–146`的`reset()`没有清空实际使用的`latents`、`encoder_embeddings`、`c2ws`和`pil_frames`，本版本禁止任何in-process reset分支。只有另一个reset补丁SHA通过逐字段测试和独立源码双审后，未来版本才可重开该分支。
- arm顺序由pilot manifest中预先冻结的随机种子产生，并在每个seed block中随机；A0 replay按冻结位置穿插检测漂移。
- 每个fresh process的PID/process-group、启动/退出UTC、return code、峰值资源、snapshot SHA和终态receipt都进入manifest；退出后仍有子进程、终态不完整或state SHA不一致均为工程失败。每次attempt均保存；只有读取生成输出前可判定的工程错误允许标invalid。不得删除arm-related crash后只重跑失败臂；失败率依赖arm时主比较不可解释。
- 每个进入response、path-conflict、control或Benefit判定的生成arm，包括F10/F01/F11、sham、negative、positive及全部replacement，都与同seed F00比较同一套arm级相机/画质守卫。每个指标使用自己单位的A0 paired-replay最大值：`tau_h_med_px`、`tau_h_p95_px`、`tau_brightness_rgb`、`tau_sharpness_ratio`、`tau_saturation_pp`。通过条件分别为median displacement `<=max(1 px,tau_h_med_px)`、P95 `<=max(3 px,tau_h_p95_px)`、support外平均亮度差`<=max(2/255,tau_brightness_rgb)`、锐度比相对1的绝对偏差`<=max(0.10,tau_sharpness_ratio)`、饱和像素比例增加`<=max(1 percentage point,tau_saturation_pp)`。
- 所有图像守卫固定在原生576×576保存PNG、uint8 sRGB域计算，不resize、不crop、不插值。matcher、descriptor、ratio test、RANSAC阈值、固定seed和failure code进入G7；少于50个双向一致匹配、NaN、全黑、非有限统计或可复算的行/列不连续撕裂指标超出A0最大值，均判该arm守卫失败。
- 上述代码、resize、颜色域和阈值在arm输出前冻结。盲态人工视觉检查只作次要诊断；任何arm级相机/整体画质守卫失败时，Influence最多称“模型有响应”，Localization和Benefit不得通过。

### 5.5 分阶段节省计算

1. **Pilot-A：** A0 + F00/F11 + sham + 同family/dose negative，一个开发来源和一个seed；若`D_target-max(tau_output,D_sham,D_negative)`不超过`delta_I`，停止。
2. **Pilot-B：** 加F10/F01、sham、未选source negative control、positive control、第二个paired seed及第二edit family；若只有单路径、单family或单seed响应，停止。
3. **Pilot-C：** 检验预先冻结support的面积与matched-placebo描述性局部性；若任一主门失败，停止。
4. **Benefit pilot：** 只有独立真实reference和公平替代均通过G6/G7才执行；否则S48最多形成Influence/Localization诊断，不能发展acceptance head。
5. **Confirmation不属于S48授权范围。** 若pilot存活，另建S49 confirmation preregistration，并在其运行前冻结精确scene数、样本量、SESOI、检验、多重性与代码SHA；C1/C2/CAL scene永久排除。

## 6. 指标

### 6.1 Influence

对相同target frame `t` 的同一像素`p`，主效应图使用无需学习的归一化RGB绝对差。唯一主数值域为模型保存后的原生576×576 PNG、8-bit uint8、sRGB、三通道RGB；读取后转float64再除以255，不做resize、crop、颜色线性化或额外clipping。shape、mode或有效像素域不同即invalid。对每个family `f`、paired seed `s`和符号`a∈{+,-}`：

`d^a_{f,s,t}(p)=mean_c |Y^a_{f,s,t}(p,c)-Y^0_{s,t}(p,c)|/255`，

`d_{f,s,t}(p)=0.5[d^+_{f,s,t}(p)+d^-_{f,s,t}(p)]`。

必须先对每侧取绝对差再平均，禁止先平均正负输出。令`D_{f,s}`先逐帧取全有效域均值，再对全部预注册target frames等权平均。每个seed的`tau_output,s`唯一取该seed原F00加至少3次replay共至少4个实例之间，所有实例对、所有target frame主距离的最大值，再与`tau_numeric=1e-6`取最大。

`D_sham,s`按相同逐帧再等权规则计算；`D_negative,f,s`是该family/dose对预注册唯一negative source的响应。控制校准后的主效应为：

`I_{f,s}=D_{f,s}-max(tau_output,s,D_sham,s,D_negative,f,s)`。

四个预定`(f,s)`必须各自满足`I_{f,s}>=delta_I=0.5/255`且全部arm通过§5.4守卫。positive control另满足`D_positive,s-max(tau_output,s,D_sham,s)>=delta_positive=0.5/255`并命中预注册trace；它不进入treatment effect。报告全部replay、control、edit、dose、seed和frame距离；不计算总体CI或p值。

LPIPS/spatial feature difference 只能作为冻结后的次要稳健性指标，不能在看结果后替换主指标。

### 6.2 Localization

令`W_t=S_t=w^frac_t`为任何arm前由§4.1按实际`c2w_t/K_t`重投影并冻结的主geometry-projected expected locus，`Ω_t`为该target有效域。对任意`[0,1]`权重图`W`和固定`ε=1e-12`：

`area_t(W)=sum_{p∈Ω_t}W(p)/|Ω_t|`，

`mass_{f,s,t}(W)=sum_{p∈Ω_t}W(p)d_{f,s,t}(p)/(sum_{p∈Ω_t}d_{f,s,t}(p)+ε)`，

`L^area_{f,s,t}=mass_{f,s,t}(S_t)-area_t(S_t)`，`ER_{f,s,t}=mass_{f,s,t}(S_t)/area_t(S_t)`。

若`S_t`为空或全屏、`area`不在`(0,1)`、权重非有限，或效应总mass不超过`ε`，该target记`NOT_IDENTIFIABLE`并停止。`w^union`与`w^exclusive`只作预定sensitivity，不能替换主权重。

在任何生成arm前，对每个target分别完成无输出的三族placebo feasibility；三族**分别生成、分别报告、绝不pool**：

1. `G_shape,t`：在576方形lattice上，对`S_t`按`rotation∈{0°,90°,180°,270°}`和整数`dx,dy∈[-575,575]`的词典序枚举刚性变换，排除identity；90°旋转以整张canvas中心作精确索引置换，随后平移。权重值原样携带，不插值、不wrap、不重归一化；任何正权重越界的候选整张拒绝，因此无裁切、碰撞或孔洞。
2. `G_camera,t`：使用同一冻结surfel/provenance和实际`K_t`。令实际target的`c2w_t=[R_t|c_t]`，`b_t=||c_O-c_t||_2`；`b_t<=1e-6`即该family不可识别并停止Localization。按`α,β,γ∈{-3°,-1.5°,0°,1.5°,3°}`和`u,v,w∈{-0.10,-0.05,0,0.05,0.10}b_t`的词典序枚举，排除六参数全零；固定`R'=R_t R_x(α)R_y(β)R_z(γ)`、`c'=c_t+R_t[u,v,w]^T`，intrinsics保持`K_t`。在实际576 canvas上用§4.1同一renderer重投影；伪相机只生成权重图，不改变effect map。角度为degree，平移为当前scene单位；轴手性与现有`c2w`完全相同并由G7测试向量验证。
3. `G_source,t`：对普通运行所有合格但未选来源，使用同一实际`c2w_t/K_t`、同一renderer和同一多provenance分数式重投影；使用全部合格来源，不抽样、不补齐。

三族都产生`[0,1]`权重。binary topology固定在`1{W>0}`计算；weighted area用`sum W`。候选必须同时满足：weighted area相对差`<=2%`；binary connected-component数相同；尺度归一化周长相对差`<=10%`；weighted centroid处于同一4×4闭开网格；binary IoU`<=0.10`；10个固定区间`[0,.1),...,[.9,1]`的归一化weight histogram L1距离`<=0.05`；并在全target干预前地图预先计算的可见depth中位数、depth-gradient中位数、投影confidence中位数和boundary density四分位上各自同stratum。零分母、边界等于分位点和NaN动作在G7代码中固定，禁止读取任何生成或reference loss。

`G_shape,t`和`G_camera,t`各自先按固定网格枚举并去重，再按`(weighted-area relative error, weight-histogram L1, perimeter relative error, centroid distance, parameter tuple, mask SHA)`升序取前`K=199`；不足199即停止，不换seed、网格或caliper。`G_source,t`保存完整资格flow和有序SHA清单。所有mask、proposal/rejection counts、配置与代码SHA在任何输出前封存。

对`g∈{shape,camera}`分别定义：

`L^g_{f,s,t}=mass_{f,s,t}(S_t)-median_{M∈G_g,t}mass_{f,s,t}(M)`，

`r^g_{f,s,t}=[1+sum_{M∈G_g,t}1{mass(M)>=mass(S_t)}]/200`。

`r^g`只叫finite-library descriptive tail rank。`G_source`若有`n_t>=19`个合格mask，按同式以分母`n_t+1`计算`r^source`并要求真support严格超过中位数且`r^source<=0.05`；若`n_t<19`，只报告真support对全部候选的序位，selected-source-specific localization记`NOT_IDENTIFIABLE`。

每个预注册`f×s×t`都必须满足`ER>1`、`L^area>=0.02`，并对`G_shape`与`G_camera`分别满足`L^g>0`、`r^g<=0.05`。只有`G_source`也满足时才允许source-specific表述。episode摘要是target-frame统计量的等权平均，同时报告最差target；继续门是所有target均通过。erosion/dilation、union/exclusive及occlusion-aware结果只作预冻结sensitivity。

### 6.3 Natural revisit loss

沿用冻结的重访ROI，ID0与回到同一请求视角ID8之间RGB MSE只叫`return-to-ID0 consistency loss`；同时保留全帧和固定四区诊断。它可筛查RQ0，但ID0若进入memory/conditioning就不是独立答案，不能用于“correctness/quality/Benefit”主张。只有数值相机/K守卫和视觉相机服从检查通过时才解释为重访差异。

### 6.4 Benefit

定义损失越小越好。`F11−F00`不参与收益定号。当前C1/C2没有已证明的同步、独立真实reference，因此默认不满足G6；以下合同只规定未来资格，不能把ID0或生成图补成reference。

在任何Benefit输出产生前，以数据manifest列出的全部、从未进入memory/selection/conditioning/arm的真实相机观测形成reference roster。候选必须有文件SHA、整数纳秒时间戳、同步校准receipt、camera/K/depth、dataset scene ID和support内instance identity；scene/instance标签缺失、冲突或需要看输出人工决定即不合格。时间资格固定为`|t_R-t_target|<=0.010 s`，同步残差也必须`<=0.010 s`。全部合格候选按`(|Δt| ns, camera angular difference μdeg, translation-baseline relative difference ppm, FoV difference μdeg, file SHA)`升序，唯一取第一项为`R_i`；空集即RQ3停止。

相机平移baseline相对差唯一写为`| ||c_R-c_t||_2-||c_O-c_t||_2 | / ||c_O-c_t||_2`，其中`O`为普通原来源；分母`<=1e-6`场景单位时停止。reference还必须满足转角`<=2°`、该相对差`<=0.10`、FoV差`<=1°`。

动态/遮挡排除只读取真实预处理观测和冻结几何。排除mask是以下集合的union后作半径5 px的圆盘binary dilation：数据集动态instance标签；冻结光流实现得到的forward-backward error `>1.0 px`；测得flow与冻结depth/camera刚体flow差`>1.0 px`；任一方向z-buffer判遮挡。光流代码/weights/输入相邻帧SHA必须进G7；缺相邻真实帧、标签和可复核flow中的任一必需输入，或非动态区几何warp后的每通道RGB中位差任一`>2/255`，均停止RQ3，不作输出驱动修补。

reference与source replacement的可比区域只由reference/source真实图像、干预前camera/K/depth/geometry和上述冻结代码计算。对target像素的冻结3D点正反投影，要求两向均在边界内、forward-backward reprojection error `<=1.0 px`、相对深度差`<=0.02`、双向z-buffer可见且不在排除mask。局部比较用`C^local_t=support(S_t>0)∩V_O∩V_R`；每个replacement `P`单独用`C^matched_t(P)=support(S_t>0)∩V_O∩V_P∩V_R`。要求每个集合相对`support(S_t)`覆盖`>=0.70`且warping-hole比例`<=0.10`。validity mask在RGB插值前确定，不能填洞；不同arm共用封存的同一集合。任一资格、配准、identity或深度输入缺失即RQ3停止，不得放宽门或换reference。

主损失`ℓ_C`是在`C_i`上的归一化uint8 sRGB MSE，`ℓ_out`是在`Ω_i\S_i`上的同域MSE；原`S_i`全区结果作为覆盖敏感性，LPIPS只作次要稳健性。主分析不做曝光归一化；预冻结的每通道稳健仿射校正可作次要敏感性，但不能替换主结果。pilot Benefit的SESOI固定为`delta_B=0.001`，即自然严重阈值0.01的10%，不从arm输出估计。

第一种局部收益对每个edit family `f`、seed `s`使用同一来源、同一slot/address及§5.3唯一剂量：

`B^local_{f,s}=0.5[ℓ_C(Y^+_{f,s},R_i)+ℓ_C(Y^-_{f,s},R_i)]-ℓ_C(Y^0_s,R_i)`。

- `B^local_{f,s} > 0`：原外观在这个family/seed局部邻域内优于同幅度的两侧变化；
- `B^local_{f,s} < 0`：原外观在这个family/seed局部邻域内不是 loss-optimal；
- 这不是“该 item 存在相对不存在”的绝对收益。

第二种增量收益使用任何Benefit输出读取前冻结的匹配未选帧集合`P_i`。候选来自manifest的全部未选真实帧，必须与原来源dataset scene/instance identity精确相同，并保持tensor/token shape、slot、位置编码、source-ID接口、token数、顺序、mask、geometry和context长度。候选须同时满足：相对target转角差`<=2°`；以上述同一公式计算、相对原来源target baseline差`<=0.10`且原baseline`>1e-6`；FoV差`<=1°`；逐target投影support binary IoU`>=0.80`且weighted area比位于`[0.90,1.10]`；blur/exposure/saturation各落入由全部干预前候选计算的同一CAL四分位；recency相差`<=2`个source插入事件；并通过上述时间、动态、双向common-visible与warping-hole门。候选只按文件SHA排序，使用全部合格项；空集即停止，不放宽caliper：

`B^matched_s=mean_{P∈P_i}[ℓ_{C(P)}(Y_s(P),R_i)-ℓ_{C(P)}(Y_s(O),R_i)]`。

对一般原来源 `O` 和公平替代条件 `P`，可统一记作：

`B_i = Loss(Y_i,P) − Loss(Y_i,O)`。

- `B_i > 0`：原来源相对替代条件有益；
- `B_i < 0`：原来源有害；
- 接近 0：该来源对该质量结局无可分辨收益。

`B_matched`是未来confirmation的主Benefit，`B_local`是必要稳健性门；若只存在其中一个，只能写对应alternative下的相对效用。Pilot继续要求四个`f×s`的`B^local_{f,s}>delta_B=0.001`，两个seed的`B^matched_s>delta_B`，且全部符号一致。每个target先计算后等权聚合；每个量同时报告`ℓ_out`和原`S_t`结果，并要求每个family/seed/replacement的support外损失恶化不超过`delta_out=0.0005`。common-support相对空间placebo的difference-in-differences仅作明确标记的exploratory结果，不进入任何继续门；四个cell和代码若未在G7冻结则不计算。zero token或缩短context的OOD条件不能承担主placebo。两种Benefit符号不一致、common support覆盖不足或配准门失败即停止一般Benefit主张。

### 6.5 G7不可缺字段与执行授权边界

G7不是留待执行者自由选择参数的占位符。它只能把本协议已定义的统计对象绑定到当前unit、源码和实现。以下任一字段缺失或fresh review非PASS，所有S48模型arm保持BLOCKED：

| 组 | 必须绑定的字段 |
|---|---|
| 版本 | 实际import源码、hook patch、weights/config/environment/driver/device、launcher、renderer、metric及每个SHA；准确行号和consumer inventory |
| 静态证据 | 每份回执内部记录Python版本、解释器绝对路径、完整参数数组、audit script SHA、exit code、UTC和author/reviewer role；文件名本身不算版本证明 |
| 因果对象 | 固定estimand字符串、DAG、唯一post-selection injection point、目标与非目标slot、全部appearance descendants |
| selection/support | ordinary call ID、source/slot/order/duplicate map；每target实际camera/K；surfel/provenance、`j_t`、fractional/union/exclusive support、area/purity/hole及全部SHA |
| placebo | 三family独立配置、完整枚举顺序、caliper边界/NaN规则、proposal/rejection/accept counts、有序mask IDs/SHA和family-specific gates |
| edits/controls | 两family公式、完整dose ladders、双侧source-only门与唯一最小合格dose；sham、唯一negative、positive tensor/dose/trace与阈值 |
| 随机性/进程 | paired seed IDs、实际noise tensor SHA、Python/NumPy/Torch CPU/CUDA RNG、deterministic capability；base digest、arm order、attempt ID、PID/PGID、timeout/resource/terminal规则 |
| A0/guards | replay schedule、每个seed和每种单位的floor公式与receipt；所有生成arm使用同一相机/整体质量守卫 |
| reference | 完整roster/排除flow、纳秒时间、同步/identity/dynamic证据、唯一排序、camera/depth/flow/warp/common-support artifacts及SHA |
| 统计/报告 | RGB域、epsilon、逐frame→episode聚合、全部SESOI、invalid/missing/arm failure规则、所有attempt flow、无optional stopping及claim ladder |

当前静态审计只证明源码边界存在且API缺失。必须先实现observer/replacement patch、全consumer枚举、合成trace、fresh-process launcher、placebo generator、registration/metric代码与无生成输出的feasibility，再由不同作者做fresh源码与协议审查。自然失败G0/G1仍优先；G7 PASS也不自动授权在没有自然失败时运行S48。

## 7. 统计规则与confirmation边界

### 7.1 S48 pilot唯一允许的分析

- 所有生成比较按相同seed/noise/state成对；不比较不成对的随机输出均值。
- 报告每个scene/episode/source/seed/edit/replay/arm的完整flow、点估计、invalid和失败；不把pixel、frame、seed、mask或source当独立scene。
- S48只按冻结门做顺序性继续/停止：Influence→Localization→Benefit。matched-placebo只报告描述性尾部rank；不给总体p值、置信区间或“显著”结论。
- source/ROI/support/edit/dose与聚合、arm顺序、matched-placebo library、reference/common-support、逐指标守卫、metric及代码SHA均在任何对应arm启动前冻结。控制侧A0只用于预先规定的replay floors，不能反向改source、support、mask generator、caliper或SESOI。

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
7. I3DM式3D retrieval confidence、coverage与reliable-warp region proxy；其3D support、geometry-aware retrieval/injection和可靠区域图均视为已有思想；
8. WorldStereo式global-geometric memory与3D-correspondence-constrained spatial-stereo attention；几何约束memory attention不视为本项目单独创新；
9. Spatia式point-cloud projection、reference、preceding-video多条件组合消融，以及PlenopticDreamer式3D-FoV多历史视频检索；
10. LongDiff式informative-frame selection/固定窗口，用来排除普通context dilution解释；
11. I²AM式双向attribution与random-region/overall区域比较；attribution map和mask内外一致性不视为本项目单独创新；
12. AGRA式task-relevant/irrelevant空间干预敏感性；空间token干预和用空间语义对齐表示不视为本项目单独创新；
13. TetherCache 式 attention + diversity 选择与 trusted-alignment 修复的可比实现或最接近公开结果；
14. CUE-R式REMOVE/REPLACE/DUPLICATE逐项干预、paired signed utility与保持长度/接口的公平版本；
15. identity re-encode sham、未选source同剂量negative control及已知consumer positive control；
16. 普通轻量gate、单一pose/retrieval/source-quality阈值；
17. source-agnostic全模块ablation与更长上下文/不使用外部item的强架构对照；
18. 若进入接受阶段，报告AURC、risk–coverage、clean false rejection与所有样本的总体paired loss。

## 9. Kill conditions

以下任一项成立，就停止或降级当前主张：

1. C1/C2 没有稳定自然严重差异事件；
2. 相机/K 或视觉相机服从失败；
3. A0 本底与 F11 效应同量级且无法解释；
4. 没有普通运行实际选中、可寻址、全路径可审计的来源；
5. F11 无响应而 F10/F01 响应，说明路径冲突或遗漏；
6. influence 不超过 replay；
7. localization 不超过support面积基线，或任一预定family/seed/target没有分别进入`G_shape`与`G_camera`描述性前5%尾部；
8. benefit 对 placebo 构造敏感，符号不稳定；
9. 同步独立真实reference、动态排除、双向common-visible support、`G_shape/G_camera`各199个合格placebo或匹配未选来源不可获得；
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

> S48 V1–V3均经独立统计审查BLOCKED。V4把空间placebo拆为互不混合的`G_shape/G_camera/G_source`，固定fractional权重与逐实际target相机重投影，把Influence改为超过replay/sham/negative后的净SESOI，并唯一化同步reference、动态排除及family×seed Benefit。当前只规定hook合同，真实API仍缺失；V4待新鲜独立复审，不授权运行。

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
- [Spatia / CVPR 2026](https://openaccess.thecvf.com/content/CVPR2026/papers/Zhao_Spatia_Video_Generation_with_Updatable_Spatial_Memory_CVPR_2026_paper.pdf)
- [WorldStereo / CVPR 2026](https://openaccess.thecvf.com/content/CVPR2026/html/Zhang_WorldStereo_Bridging_Camera-Guided_Video_Generation_and_Scene_Reconstruction_via_3D_CVPR_2026_paper.html)
- [PlenopticDreamer / CVPR 2026](https://openaccess.thecvf.com/content/CVPR2026/papers/Fu_Plenoptic_Video_Generation_CVPR_2026_paper.pdf)
- [LongDiff / CVPR 2025](https://www.openaccess.thecvf.com/content/CVPR2025/papers/Li_LongDiff_Training-Free_Long_Video_Generation_in_One_Go_CVPR_2025_paper.pdf)
- [WorldTrace](https://arxiv.org/abs/2608.07408)
- [I3DM](https://arxiv.org/abs/2603.23413)
- [WorldKV](https://arxiv.org/abs/2605.22718)
- [Echo-Memory](https://arxiv.org/abs/2606.09803)
- [TetherCache](https://arxiv.org/abs/2606.13035)
- [CUE-R](https://arxiv.org/abs/2604.05467)
- [Utility-Oriented Visual Evidence Selection](https://arxiv.org/abs/2605.13277)
- [Is This the Subspace You Are Looking for? / ICLR 2024](https://openreview.net/forum?id=Ebt7JgMHv1)
- [I²AM / ICLR 2025](https://openreview.net/forum?id=bBNUiErs26)
- [AGRA](https://arxiv.org/abs/2606.12217)
- [SelectiveNet / ICML 2019](https://proceedings.mlr.press/v97/geifman19a)
