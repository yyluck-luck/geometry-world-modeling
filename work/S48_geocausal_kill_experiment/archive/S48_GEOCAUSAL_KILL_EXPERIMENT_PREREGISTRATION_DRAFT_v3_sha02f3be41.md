# S48 GeoCausal 最小否证实验预注册草案 V3

- 草案时间：2026-09-08（Asia/Shanghai）
- V3修订时间：2026-09-08T14:16:45+08:00
- 状态：`REVISED_DRAFT_PENDING_FRESH_INDEPENDENT_REVIEW_NOT_EXECUTION_AUTHORIZATION`
- 本版范围：**只设计CAL/pilot否证，不授权confirmation，不进行总体显著性或方法主张**
- V1原件：`archive/S48_GEOCAUSAL_KILL_EXPERIMENT_PREREGISTRATION_DRAFT_v1_sha69ad32b9.md`，SHA-256 `69ad32b932369e6c5cc9b1fde65d20d2caca1892fd47e2a5e94c3d15b5c8ef32`
- V1独立统计审查：`INDEPENDENT_STATISTICAL_REVIEW.md`，SHA-256 `414f0119fbe901298063ff0d3eb24c0faa0f2551455f12ec27bdfad511c122c4`，裁决`BLOCKED`
- V2原件：`archive/S48_GEOCAUSAL_KILL_EXPERIMENT_PREREGISTRATION_DRAFT_v2_shaef92be76.md`，SHA-256 `ef92be76a8f8f2d6cd6fe70e629f77114751d9ed2a05228618038087e6fda92d`
- V2独立统计审查：`INDEPENDENT_STATISTICAL_REVIEW_V2.md`，SHA-256 `3470ae9a421bc3b8ce916b8e6959d36d49e1ccc9f12e7002e841fdd22ff1b372`，裁决`BLOCKED`
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

- **H0-localize：** 影响落入干预前geometry support的比例不高于面积基线，或没有进入预先冻结matched-placebo library的前5%尾部。
- **H1-localize：** 每个预定edit-family/seed效应图的真support都同时超过面积SESOI，并进入同一预冻结matched-placebo library的前5%尾部。
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
| G3 source eligibility | 普通运行的 Store、Select、Address、稳定slot→source ID映射、target-pixel→source支持映射及所有appearance consumer path清单均有证据 | 更换来源；无合格来源或support归因不唯一则停止 |
| G4 intervention validity | 外观变化低强度，source ID、shape、dtype、pose、K/Plücker、几何支持和检索身份不变 | 调整干预；不读取结果做阈值优化 |
| G5 path completeness | 同一处理进入全部真实 appearance consumer paths；目标来源后代全部重算 | F11 无效；只可作工程诊断 |
| G6 independent reference | Benefit使用从未进入memory/conditioning、在任何arm输出读取前封存的真实目标视角照片；相机/时间/身份、双向common-visible support、配准残差和warping-hole门均可复核 | 不做Benefit；若只用ID0，仅称return-to-ID0 consistency |
| G7 frozen pilot manifest | 唯一DAG、精确hook/张量、support归因、source、edit/dose与唯一聚合、matched-placebo generator、fresh-process状态、arm顺序、逐指标守卫、reference配准、metric代码、SESOI、invalid规则及全部SHA经新鲜独立前审 | 不启动任何S48 arm |

## 4. 因果对象与冻结边界

### 4.1 处理变量

本pilot只估计下列DAG中的粗体箭头以后部分：

`Stored source → ordinary Select → ordinary Address → **appearance-bundle intervention → all consumer inputs → denoising/output → optional writeback**`

唯一处理时点必须绑定VMem精确源码行与张量：普通`get_context_info`完成选择后、`get_cond`构造任何appearance consumer input之前。当前审查对象 `vendor/vmem_snapshot/modeling/pipeline.py` SHA-256 为 `90a45f452a4f734b3371fb526c566162026e5d900e0c8204709dd57f44ef1d7e`；其第759–765行只返回context tensors和`context_time_indices`，**没有返回target support**。因此当前源码不满足执行条件，不能把文本中的support当作已存在接口。

V3要求在任何arm运行前冻结并双审一个只读的`post_selection_bundle` hook。它必须在同一次普通选择调用中物化：

1. 每个slot的`context_time_index`、稳定source ID、原始position和是否重复；
2. 产生选择的surfel索引及每个surfel对应的全部source timesteps；一个surfel映射多个source时，不得事后任选其一；
3. 在固定target camera/K、深度可见性和z-buffer规则下，把每个被选source可归属的surfels投影为target-pixel support；同一像素被多个source支持时保存完整稀疏权重并使用预冻结的归一化规则；
4. `context_latents`、`context_encoder_embeddings`以及静态审计发现的所有其他appearance后代的slot/source轴映射；
5. 选择返回后到`get_cond`调用前的单一注入点，以及证明F11覆盖全部appearance路径、F10/F01只覆盖指定路径的trace字段。

hook必须只增加观察字段和一个受控替换点，不得改变普通选择顺序、tensor shape/dtype/device、pose、K、geometry或非目标slot。若无法由同一次调用得到稳定source ID和support，或多值surfel归因不能按冻结规则解析，本实验在G3停止。若源码版本、行号或consumer清单改变，必须重冻SHA并重新前审。

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

每族的`+δ/-δ`剂量只可用source输入的固定LPIPS/CLIP/edge约束校准，不能查看任何生成输出。还必须包含：identity/no-op re-encode sham；以相同剂量编辑一个未选source的negative control；对一个在源码和合成测试中已确认会进入`get_cond`的目标slot appearance tensor施加预先固定positive control。positive control的精确tensor、轴、符号无关的绝对响应门和预期trace必须写入G7，不能在看输出后换路径。

唯一聚合规则如下。对每个edit family `f`、paired seed `s`，先把对称剂量形成一个family map：

`d_{f,s}(p)=0.5×[mean_c|Y_{f,s,+δ}(p,c)-Y_{s,F00}(p,c)| + mean_c|Y_{f,s,-δ}(p,c)-Y_{s,F00}(p,c)|]/255`。

两个family × 两个paired seed形成四张预定主图；它们分别通过Influence、Localization和arm guard，主继续规则是**四者全部通过**。unit级保守摘要为四个对应统计量的最小值，只用于列表排序，不替代逐图报告。sham与未选source negative control的每张图必须`D <= tau_output + delta_I`；positive control的每张图必须`D > tau_output + delta_I`。控制失败即停止或降级，不能挑选最有利family/seed/dose。

### 5.4 运行随机化、重置与arm级守卫

- 所有arm物化同一只读state snapshot、实际initial noise和RNG state；**当前源码每个arm一律使用fresh process**，并从同一snapshot重建。`pipeline.py:135–146`的`reset()`没有清空实际使用的`latents`、`encoder_embeddings`、`c2ws`和`pil_frames`，本版本禁止任何in-process reset分支。只有另一个reset补丁SHA通过逐字段测试和独立源码双审后，未来版本才可重开该分支。
- arm顺序由pilot manifest中预先冻结的随机种子产生，并在每个seed block中随机；A0 replay按冻结位置穿插检测漂移。
- 每个fresh process的PID/process-group、启动/退出UTC、return code、峰值资源、snapshot SHA和终态receipt都进入manifest；退出后仍有子进程、终态不完整或state SHA不一致均为工程失败。每次attempt均保存；只有读取生成输出前可判定的工程错误允许标invalid。不得删除arm-related crash后只重跑失败臂；失败率依赖arm时主比较不可解释。
- F11及每个Benefit placebo都与同seed F00比较arm级相机/画质守卫。每个指标使用自己单位的A0 paired-replay最大值：`tau_h_med_px`、`tau_h_p95_px`、`tau_brightness_rgb`、`tau_sharpness_ratio`、`tau_saturation_pp`。通过条件分别为median displacement `<=max(1 px,tau_h_med_px)`、P95 `<=max(3 px,tau_h_p95_px)`、support外平均亮度差`<=max(2/255,tau_brightness_rgb)`、锐度比相对1的绝对偏差`<=max(0.10,tau_sharpness_ratio)`、饱和像素比例增加`<=max(1 percentage point,tau_saturation_pp)`。
- 所有图像守卫固定在原生576×576保存PNG、uint8 sRGB域计算，不resize、不crop、不插值。matcher、descriptor、ratio test、RANSAC阈值、固定seed和failure code进入G7；少于50个双向一致匹配、NaN、全黑、非有限统计或可复算的行/列不连续撕裂指标超出A0最大值，均判该arm守卫失败。
- 上述代码、resize、颜色域和阈值在arm输出前冻结。盲态人工视觉检查只作次要诊断；任何arm级相机/整体画质守卫失败时，Influence最多称“模型有响应”，Localization和Benefit不得通过。

### 5.5 分阶段节省计算

1. **Pilot-A：** A0 + F00/F11，一个开发来源和一个seed；若`D_intervention`不超过`tau_output+delta_I`，停止。
2. **Pilot-B：** 加F10/F01、sham、未选source negative control、positive control、第二个paired seed及第二edit family；若只有单路径、单family或单seed响应，停止。
3. **Pilot-C：** 检验预先冻结support的面积与matched-placebo描述性局部性；若任一主门失败，停止。
4. **Benefit pilot：** 只有独立真实reference和公平替代均通过G6/G7才执行；否则S48最多形成Influence/Localization诊断，不能发展acceptance head。
5. **Confirmation不属于S48授权范围。** 若pilot存活，另建S49 confirmation preregistration，并在其运行前冻结精确scene数、样本量、SESOI、检验、多重性与代码SHA；C1/C2/CAL scene永久排除。

## 6. 指标

### 6.1 Influence

对相同target frame的同一像素`p`，主效应图使用无需学习的归一化RGB绝对差。唯一主数值域为模型保存后的原生576×576 PNG、8-bit uint8、sRGB、三通道RGB；读取后转float64再除以255，不做resize、crop、颜色线性化或额外clipping。shape、mode或有效像素域不同即invalid：

`d_i(p) = mean_c |Y_i,F11(p,c) − Y_i,F00(p,c)| / 255`。

其中单个`F11`由§5.3唯一指定的`d_{f,s}`替代。令`D_{f,s}=mean_{p∈Ω_i} d_{f,s}(p)`；四个`(f,s)`分别过门。单位级净Influence只作描述：

`I_{f,s} = D_{f,s} − tau_output,s`。

Pilot继续门不是`I>0`，而是四个预定`D_{f,s} > tau_output,s + delta_I`全部成立；报告每个replay、edit family、dose、seed的完整距离与倍率，不计算总体CI或p值。

LPIPS/spatial feature difference 只能作为冻结后的次要稳健性指标，不能在看结果后替换主指标。

### 6.2 Localization

令`S_i`为任何arm启动前由§4.1 `post_selection_bundle`的source-weighted geometry投影得到并冻结的support，`Ω_i`为有效评价区域。固定`ε=1e-12`：

`mass_{f,s}(S_i) = sum_{p∈S_i} w_i(p)d_{f,s}(p) / (sum_{p∈Ω_i} d_{f,s}(p) + ε)`

`area_i = sum_{p∈Ω_i}w_i(p) / |Ω_i|`

`L_{f,s} = mass_{f,s}(S_i) − area_i`。

同时报告 enrichment ratio：

`ER_{f,s} = mass_{f,s}(S_i) / area_i`。

若`S_i`为空、覆盖全部`Ω_i`、`area_i`不在`(0,1)`、source权重非有限，或某张效应图总mass不超过`ε`，Localization记`NOT_IDENTIFIABLE`并停止，不输出任意ER/rank。

面积基线只是第一关。在任何A0/F00/F11/Benefit arm启动前，先做**无生成输出的matched-placebo feasibility audit**。唯一generator使用固定seed产生`K=199`个唯一假support：候选来自未选source的干预前几何投影、保持拓扑的刚性平移/旋转和预注册camera-geometry placebo。每个候选须与`S_i`满足面积±2%、连通分量数相同、周长/√面积±10%、质心位于同一4×4位置格、IoU≤0.10，并在只由干预前source/geometry计算的可见深度、深度梯度、投影置信度和边界密度四分位上落入同一冻结stratum。禁止使用当前unit的F00、replay、F11、reference error或Benefit输出做matching。

feasibility report必须在生成前保存每个proposal family的提议数、去重数、各caliper拒绝数、acceptance rate、最终199个mask及其SHA。不能得到199个时直接停止；不得换mixture、seed、family或放宽caliper。该library只是在观测到的图像结构上构造困难placebo，**没有随机分配真support**。

定义`mass_{f,s}(M)`同上，主局部量为：

`L^matched_{f,s} = mass_{f,s}(S_i) − median_b mass_{f,s}(M_{i,b})`。

描述性上尾排名定义为`r_mask,f,s=(1 + #{b: mass_{f,s}(M_{i,b}) >= mass_{f,s}(S_i)})/(K+1)`。它不是p值，199个mask也不是199个科学样本。Pilot通过必须让四个预定`(f,s)`全部满足：`ER_{f,s}>1`、`L_{f,s}>=0.02`、`L^matched_{f,s}>0`、`r_mask,f,s<=0.05`；且未选source投影与camera-geometry placebo均不能通过同一四条件门。另固定support erosion/dilation与occlusion-aware sensitivity为次要稳健性检查，主support和library保持唯一。

### 6.3 Natural revisit loss

沿用冻结的重访ROI，ID0与回到同一请求视角ID8之间RGB MSE只叫`return-to-ID0 consistency loss`；同时保留全帧和固定四区诊断。它可筛查RQ0，但ID0若进入memory/conditioning就不是独立答案，不能用于“correctness/quality/Benefit”主张。只有数值相机/K守卫和视觉相机服从检查通过时才解释为重访差异。

### 6.4 Benefit

定义损失越小越好。`F11−F00`不参与收益定号。`R_i`必须是从未进入memory、selection、conditioning或任何arm的真实目标视角照片，并在任何Benefit arm启动前封存相机、K、时间、文件SHA和资格结果；否则RQ3不执行。

reference与source replacement的可比区域只由reference/source图像、干预前camera/K/depth/geometry和冻结代码计算，不能读取任何Benefit arm输出。固定3D双向配准：正反投影都在图像边界内、forward-backward reprojection error `<=1.0 px`、相对深度差`<=0.02`，并通过双向z-buffer可见性。`C_i`是原`S_i`、reference和replacement三者的双向common-visible support；要求`|C_i|/|S_i|>=0.70`且warping-hole比例`<=0.10`。reference相对target的相机转角`<=2°`、平移baseline相对差`<=10%`、FoV差`<=1°`；任一资格、配准或深度输入缺失即RQ3 invalid-stop，不得放宽门或换reference。

主损失`ℓ_C`是在`C_i`上的归一化uint8 sRGB MSE，`ℓ_out`是在`Ω_i\S_i`上的同域MSE；原`S_i`全区结果作为覆盖敏感性，LPIPS只作次要稳健性。主分析不做曝光归一化；预冻结的每通道稳健仿射校正可作次要敏感性，但不能替换主结果。pilot Benefit的SESOI固定为`delta_B=0.001`，即自然严重阈值0.01的10%，不从arm输出估计。

第一种局部收益使用同一来源、同一slot/address的对称appearance treatment`T_{+δ}`与`T_{−δ}`：

`B_i^local(δ) = 0.5 × [ℓ_C(Y(T_{+δ}(x_i)), R_i) + ℓ_C(Y(T_{−δ}(x_i)), R_i)] − ℓ_C(Y(x_i), R_i)`。

- `B_i^local > 0`：原外观在这个局部邻域内优于同幅度的两侧变化；
- `B_i^local < 0`：原外观在这个局部邻域内不是 loss-optimal；
- 这不是“该 item 存在相对不存在”的绝对收益。

第二种增量收益使用任何Benefit输出读取前冻结的匹配未选帧集合`P_i`：同scene、同对象identity，并保持相同tensor/token shape、slot、位置编码、source-ID接口、token数、顺序、mask、geometry和context长度。候选须同时满足：相对target的相机转角差不超过2°；平移baseline相对差不超过10%；FoV差不超过1°；投影support IoU至少0.80且面积比位于`[0.90,1.10]`；blur/exposure/saturation各落入同一CAL四分位；recency相差不超过2个source插入事件；并通过上述双向common-visible与warping-hole门。使用满足条件的全部未选帧，若为空则`B_matched` invalid，不得放宽caliper：

`B_i^matched = mean_{P∈P_i}[ℓ_{C(P)}(Y(P), R_i) − ℓ_{C(P)}(Y(x_i), R_i)]`。

对一般原来源 `O` 和公平替代条件 `P`，可统一记作：

`B_i = Loss(Y_i,P) − Loss(Y_i,O)`。

- `B_i > 0`：原来源相对替代条件有益；
- `B_i < 0`：原来源有害；
- 接近 0：该来源对该质量结局无可分辨收益。

`B_matched`是未来confirmation的主Benefit，`B_local`是必要稳健性门；若只存在其中一个，只能写对应alternative下的相对效用。Pilot继续要求两个paired seed中`B_local>delta_B`与`B_matched>delta_B`且符号一致。每个量同时报告`ℓ_out`和原`S_i`结果，并要求support外损失恶化不超过`delta_out=0.0005`；再报告common-support相对matched-placebo的difference-in-differences。zero token或缩短context的OOD条件不能承担主placebo。两种Benefit符号不一致、common support覆盖不足或配准门失败即停止一般Benefit主张。

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
8. I²AM式双向attribution与random-region/overall区域比较；attribution map和mask内外一致性不视为本项目单独创新；
9. AGRA式task-relevant/irrelevant空间干预敏感性；空间token干预和用空间语义对齐表示不视为本项目单独创新；
10. TetherCache 式 attention + diversity 选择与 trusted-alignment 修复的可比实现或最接近公开结果；
11. CUE-R式REMOVE/REPLACE/DUPLICATE逐项干预、paired signed utility与保持长度/接口的公平版本；
12. identity re-encode sham、未选source同剂量negative control及已知consumer positive control；
13. 普通轻量gate、单一pose/retrieval/source-quality阈值；
14. source-agnostic全模块ablation与更长上下文/不使用外部item的强架构对照；
15. 若进入接受阶段，报告AURC、risk–coverage、clean false rejection与所有样本的总体paired loss。

## 9. Kill conditions

以下任一项成立，就停止或降级当前主张：

1. C1/C2 没有稳定自然严重差异事件；
2. 相机/K 或视觉相机服从失败；
3. A0 本底与 F11 效应同量级且无法解释；
4. 没有普通运行实际选中、可寻址、全路径可审计的来源；
5. F11 无响应而 F10/F01 响应，说明路径冲突或遗漏；
6. influence 不超过 replay；
7. localization 不超过support面积基线，或任一预定family/seed没有进入matched-placebo描述性前5%尾部；
8. benefit 对 placebo 构造敏感，符号不稳定；
9. 独立真实reference、双向common-visible support、199个合格matched-placebo masks或匹配未选来源不可获得；
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

> S48 V1和V2均经独立统计审查BLOCKED。V3删除了无可交换依据的“随机化p值”，把matched masks降为描述性placebo尾部排名；当前源码强制每arm fresh process，并加入可执行的source-support hook、逐指标守卫、唯一edit/seed聚合和双向common-visible Benefit。V3仍待新鲜独立复审，尚不授权运行。

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
