# S48 GeoCausal 最小否证实验预注册草案

- 草案时间：2026-09-08（Asia/Shanghai）
- 状态：`DRAFT_NOT_EXECUTION_AUTHORIZATION`
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

- **H0-influence：** 全路径一致改变目标来源后，输出差异不超过 exact-replay 本底。
- **H1-influence：** `F11−F00` 的配对输出效应稳定超过 exact replay。

### RQ2：作用是否发生在正确空间位置

- **H0-localize：** 影响落入干预前 geometry support 的比例，不高于该 support 的面积占比。
- **H1-localize：** 影响在 support 内显著富集，并跨种子/来源保持方向。

### RQ3：该来源是有益还是有害

- **H0-benefit：** 原来源相对同形状、同位置、同几何、分布匹配的替代条件，不改善自然重访损失。
- **H1-benefit：** 原来源带来可重复的正收益，或存在可预测的负收益样本。

RQ1/RQ2 的外观干预只能识别影响和位置，**不能单独给出收益符号**。RQ3 必须使用独立的质量结局和公平替代条件。

## 2. 分析单位与范围

### 2.1 分析单位

一个单位是 `(scene, revisit target, selected source, seed)`：

- target 必须来自普通、未干预运行；
- source 必须在普通运行中实际被选中，具有稳定 ID，并在当前时刻可寻址；
- source 的存储、选择和进入真实消费者的证据必须先独立复核；
- 第一轮只从 C1/C2 选择一个开发单位，用于 kill experiment，不进入后续确认集。

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

## 4. 因果对象与冻结边界

### 4.1 处理变量

把目标来源拆为：

- `Z_i`：来源身份、时间、slot 和检索身份；
- `G_i`：在干预前冻结的 pose、K/Plücker、深度/点图与 target support；
- `A_i`：来源的外观内容及由它产生的 CLIP、VAE/latent 等 appearance 表示。

RQ1/RQ2 估计的是 **给定 `Z_i,G_i` 的 source-appearance total effect**：对 `A_i` 做低强度干预，重算 `A_i` 的所有下游后代。它不是原始像素对几何估计器的无条件总效应。

### 4.2 可以冻结的量

- prompt；
- 请求 camera、pose、K/Plücker；
- 实际初始 noise 与 RNG state；
- retrieval source IDs 和 slot 顺序；
- 非目标记忆的干预前初态；
- 目标来源干预前、被定义为处理条件的 `Z_i,G_i`；
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

在同一冻结状态、实际 noise、RNG 和全部记忆下重放 F00 **至少 3 次**。先检查可达到的确定性：

- 若 bitwise 相同，replay floor 记为 0；
- 若不相同，保留差异，不事后挑选容差；用多个完全相同的重放估计 `D_replay`，并先查明非确定来源；
- pilot 方差只用于冻结确认阶段样本量，pilot 单位不进入确认统计。

### 5.2 来源外观四格

| Cell | CLIP/semantic path | replace/VAE/latent path | 用途 |
|---|---|---|---|
| F00 | 原来源 | 原来源 | 主基准 |
| F10 | 编辑来源 | 原来源 | 路径冲突诊断 |
| F01 | 原来源 | 编辑来源 | 路径冲突诊断 |
| F11 | 同一个编辑来源 | 同一个编辑来源 | 唯一主处理 |

若发现更多真实 appearance consumer path，必须全部加入 F11；上表的两列只是当前已知路径，不得被写成完整性的先验保证。

主比较仅为 `F11−F00`。F10/F01 不估计 total effect，只检验单路径注入是否制造冲突或休眠旁路。

### 5.3 分阶段节省计算

1. **Pilot-A：** A0 + F00/F11，一个开发来源和一个 seed；若无超过 replay 的效应，停止。
2. **Pilot-B：** 加 F10/F01 与第二个 paired seed；若只有单路径响应或方向不稳定，停止。
3. **Pilot-C：** 检验预先冻结 support 的局部性；若不超过面积基线，停止。
4. **Benefit pilot：** 只在前三步通过后构造公平替代条件；若收益符号不可识别，候选保持诊断工具，不发展 gate。
5. **Confirmation：** 用 pilot 方差冻结样本量和新场景/来源/seed，开发单位不得重复进入。

## 6. 指标

### 6.1 Influence

对相同 target frame 的同一像素 `p`，主效应图先使用无需学习的归一化 RGB 绝对差：

`d_i(p) = mean_c |Y_i,F11(p,c) − Y_i,F00(p,c)| / 255`。

单位级 influence：

`I_i = mean_p d_i(p) − mean_p d_i,replay(p)`。

LPIPS/spatial feature difference 只能作为冻结后的次要稳健性指标，不能在看结果后替换主指标。

### 6.2 Localization

令 `S_i` 为输出前从原来源几何投影得到并冻结的 support，`Ω_i` 为有效评价区域：

`mass_i = sum_{p∈S_i} d_i(p) / (sum_{p∈Ω_i} d_i(p) + ε)`

`area_i = |S_i| / |Ω_i|`

`L_i = mass_i − area_i`。

同时报告 enrichment ratio：

`ER_i = mass_i / area_i`。

面积基线只是第一关。主零分布由平移/置换 masks 构成，并与 `S_i` 在面积、形状、edge density 和 F00 baseline error 上尽量匹配。Pilot 要求 `ER_i > 1` 且超过该 matched-mask 分布的 95% 分位；确认阶段还要求 `L_i` 的场景聚类置信下界大于 0。不得把 support 内像素更多或本来误差更大导致的差异误写成局部性。

### 6.3 Natural revisit loss

沿用冻结的重访 ROI，主自然损失为 ID0 与回到同一请求视角的 ID8 之间 RGB MSE；同时保留全帧和固定四区诊断。只有数值相机/K 守卫和视觉相机服从检查通过时才解释为重访差异。

### 6.4 Benefit

定义损失越小越好。`F11−F00` 不参与收益定号。第一种局部收益使用同一来源、同一 slot/address 的对称 photometric treatment `T_{+δ}` 与 `T_{−δ}`：

`B_i^local(δ) = 0.5 × [Loss(Y(T_{+δ}(x_i)), Y*) + Loss(Y(T_{−δ}(x_i)), Y*)] − Loss(Y(x_i), Y*)`。

- `B_i^local > 0`：原外观在这个局部邻域内优于同幅度的两侧变化；
- `B_i^local < 0`：原外观在这个局部邻域内不是 loss-optimal；
- 这不是“该 item 存在相对不存在”的绝对收益。

第二种增量收益使用看结果前冻结的同场景、同对象 identity、相邻时刻、pose/FoV/support 匹配未选帧 `M_i`：

`B_i^matched = Loss(Y(M_i), Y*) − Loss(Y(x_i), Y*)`。

对一般原来源 `O` 和公平替代条件 `P`，可统一记作：

`B_i = Loss(Y_i,P) − Loss(Y_i,O)`。

- `B_i > 0`：原来源相对替代条件有益；
- `B_i < 0`：原来源有害；
- 接近 0：该来源对该质量结局无可分辨收益。

`Y*` 必须是真实 GT return 或在 treatment 输出读取前冻结的真实 revisit observation。替代条件尚未冻结，必须在读取任何 S48 输出前由独立审查确定。最低要求：相同 tensor/token shape、slot、位置编码、source-ID 接口、token 数、顺序、mask、`G_i` 和 context 长度；内容来自训练分布内的匹配来源或经验证的分布匹配 null。至少使用 `B_local` 与 `B_matched` 两种构造检验结论是否依赖 placebo，不能把 zero token 的 OOD 反应当作收益。

## 7. 统计规则

- 所有生成比较按相同 seed/noise 成对；不比较不成对的随机输出均值。
- pilot 只用于否证、发现工程问题和估计方差；不得与 confirmation 混合报显著性。
- confirmation 的独立单位是 source-target 对，按 scene 聚类；像素不能当独立样本。
- 主区间使用 scene-cluster bootstrap 或配对置换，方法和重复次数在样本量冻结时一并固定。
- 多指标层级固定为 Influence → Localization → Benefit；前门不通过，不检验后门，避免多重尝试挑结果。
- 同时报效应量、区间、样本数、失败/排除数量；不只报 p 值。
- 任何阈值、ROI、support、编辑强度与 source 选择都在输出读取前冻结。

## 8. 必须比较的强基线

1. exact replay；
2. attention mass；
3. retrieval similarity / score；
4. pose overlap 与 geometry support area；
5. source 被保留/选中的二元变量；
6. WorldTrace 式 addressability 修复或等价地址诊断；
7. TetherCache 式 attention + diversity 选择与 trusted-alignment 修复的可比实现或最接近公开结果；
8. 普通轻量 gate；
9. source-agnostic 全模块 ablation；
10. 若进入接受阶段，报告 AURC、risk–coverage、clean false rejection 与所有样本的总体 paired loss。

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
9. attention、pose overlap、retrieval score 或简单 gate 达到相同样本外预测；
10. 只能在一个场景、来源、编辑或消费者中成立；
11. 新公开工作完成同一联合协议。

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

> 已形成一个分阶段、可否证的 S48 预注册草案，明确区分 influence、localization 与 benefit，并把真实 C1/C2 自然失败作为启动硬门。

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
- [WorldTrace](https://arxiv.org/abs/2608.07408)
- [WorldKV](https://arxiv.org/abs/2605.22718)
- [Echo-Memory](https://arxiv.org/abs/2606.09803)
- [TetherCache](https://arxiv.org/abs/2606.13035)
- [CUE-R](https://arxiv.org/abs/2604.05467)
- [Utility-Oriented Visual Evidence Selection](https://arxiv.org/abs/2605.13277)
- [Is This the Subspace You Are Looking for? / ICLR 2024](https://openreview.net/forum?id=Ebt7JgMHv1)
- [SelectiveNet / ICML 2019](https://proceedings.mlr.press/v97/geifman19a)
