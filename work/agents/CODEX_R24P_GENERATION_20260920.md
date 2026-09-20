# Round 24-P — 生成档案（不做占据评估）

日期：2026-09-20。本文的任务是先扩大候选空间，随后由 owner 另行做近邻、可行性和证据门审查。文中的“弱”只表示我预期机制或论文叙事较弱；它不是占据、拒绝或授权结论。`new_method_validated=false` 与 `novelty_authorization=NONE` 保持不变。

## 先做的事实核对

我逐字检查了三份 pinned VMem 副本：

- `work/S17C_interface_preparation/isolated_vmem_source/modeling/pipeline.py`
- `work/S17_cpu_preflight/original/modeling/pipeline.py`
- `work/S102_gate0_3dmatch/adapter_v1/sources/vmem_pipeline.py`

三份文件在目标路径都先调用 `get_context_info(target_c2ws, use_non_maximum_suppression)`，随后执行 `torch.cat([context_c2ws, target_c2ws])`，再调用 `get_translation_scaling_factor(all_c2ws)`。`self.c2ws` 的直接建立点是初始化处约 180 行，生成后的追加点是约 1297 行；代码还在 undo 路径成组 `pop`，但没有把保留帧的相机位姿改写成另一位姿的 setter。这意味着下面凡是涉及“改检索 query”“改 camera normalization”“重放/回滚状态”的候选，都必须把这几个对象作为同一个干预包记录，不能把它们默认为独立因素。

我还核对了公开原文的以下标题，引用只用来说明技术例子，不表示本轮对其新颖性、优劣或占据作判断：

- arXiv:2506.18903, *VMem: Consistent Interactive Video Scene Generation with Surfel-Indexed View Memory*。
- arXiv:2503.03751, *GEN3C: 3D-Informed World-Consistent Video Generation with Precise Camera Control*。
- arXiv:2506.04225, *Voyager: Long-Range and World-Consistent Video Diffusion for Explorable 3D Scene Generation*。
- arXiv:2402.03908, *EscherNet: A Generative Model for Scalable View Synthesis*。
- arXiv:2507.10496, *Cameras as Relative Positional Encoding*。
- arXiv:2503.14489, *Stable Virtual Camera: Generative View Synthesis with Diffusion Models*。

本轮没有 GPU、训练、微调、权重下载或安装包。涉及真实视频质量的项只能先做源码/协议/合成 trace/已有封存数据的准备，不能提前写成效果结论。

## Part A — 冻结消费者、零 GPU 条件下的生成

这里的“冻结”指不改 VMem 上游、不训练、不微调、不添权重；外部 wrapper、sidecar、输入准备器、状态账本、CPU 分析器和后处理器仍可作为候选对象。每项都写出四件事：改动对象、干预、测量、可能机制。需要真实前向的测量明确标为后续依赖，不假装已完成。

### A1. 可提交的状态事务 wrapper

- **对象：** `pil_frames`、latents、encoder embeddings、`c2ws`、`Ks` 以及调用前后的状态版本。
- **干预：** 每次 `generate_trajectory_frames` 前复制不可变快照，调用成功后先写临时版本；只有通过输入长度、位姿、帧数、NaN 和重投影守卫才 commit，否则恢复快照。
- **测量：** CPU 合成 trace 的 commit/rollback 完整性、异常后状态字节差、重复调用的确定性；未来前向再量失败传播率与恢复后的质量。
- **机制：** 把“一次坏生成永久污染后续记忆”改成可撤销事务。它利用现有接口外部包裹，不需要修改消费者内部。

### A2. 分支式状态 shadow 与可重放调用

- **对象：** 单一 `self.c2ws` 列表及其配套 frame/latent/embedding/K 状态。
- **干预：** 不在主对象上试探候选；为每个候选建立 sidecar 状态记录，按同一输入重放，选定后才一次提交。sidecar 保存源帧 ID、调用序号、随机种子和 hash。
- **测量：** 多分支是否能逐字节重放、分支间状态差异是否只来自预声明干预、状态树的内存/时间成本。
- **机制：** 将不可逆的“试一次就写入”变为 copy-on-write。当前可用合成状态和封存输出做验证。

### A3. 来源—状态—输出 provenance ledger

- **对象：** 被选 context 的索引、位姿、原始帧 hash、padding 重数、目标位姿、输出帧和下一次写回关系。
- **干预：** 在消费者外侧建立 typed record；每个输出带可追溯的 parent source 集合和可见性 mask，不改变像素输入。
- **测量：** provenance 完整率、来源重放一致率、随机删除一个来源后是否能定位受影响区域；未来用 source swap 做影响图。
- **机制：** 让“检索到”与“生成实际消费”分开可审计，支持后续任何算法的因果排查。
- **弱：** 可能更像可复现实验工具，不一定改变生成行为。

### A4. 目标 query 的多假设共识检索

- **对象：** `get_context_info` 使用的目标 `c2ws` 查询。
- **干预：** 外侧对同一目标生成小范围 SE(3) 扰动、目标末端/全轨迹两种摘要和尺度扰动，分别读出候选列表；只保留在多数查询中稳定出现且顺序稳定的 frame，再按原接口送入。
- **测量：** 候选集合 Jaccard、排序 Kendall tau、query 扰动下输出的方差；后续比较共识候选与单 query 的 RGB/深度/轨迹误差。
- **机制：** 把单个末端位姿的脆弱选择变成对小 query 误差鲁棒的选择。
- **弱：** 多次读回不等于更准确；可能只增加 CPU/调用次数。

### A5. 覆盖率—距离—新颖性三项重排

- **对象：** 已返回的候选帧排序和四个 context slots。
- **干预：** 对每个候选计算目标视锥的 surfel 覆盖、与已选帧的重叠、相机距离和时间年龄；用固定权重或预声明 lexicographic 规则重排，仍只传真实历史帧。
- **测量：** 选中集合的可见 surfel 覆盖、重复率、深度空洞率、slot 分配；后续生成质量按区域报告。
- **机制：** 让“相关”包含互补视域和新信息，减少四个槽位重复描述同一表面。

### A6. 遮挡/深度风险优先的候选选择

- **对象：** 每个候选 frame 到目标视图的几何投影。
- **干预：** 用已有深度、法线或可见性信息估计重投影的遮挡冲突、空洞和 z-buffer 不确定度；对高风险但近距离的候选降权，对能补空洞者升权。
- **测量：** 目标视域的可见面积、冲突像素比例、遮挡边界误差；无 GPU 时先在保存的深度/pose 上做 CPU 重投影。
- **机制：** 近相机距离不保证能解释被遮挡区域；风险项可把候选选择从距离代理移向可消费证据。

### A7. 时间新鲜度与几何新颖性解耦

- **对象：** frame 的时间索引与 surfel 观测记录。
- **干预：** 用二元分数分别表示“最新状态”和“覆盖新表面”，固定至少一个 slot 给最新状态、其余 slots 给几何互补；不能满足时显式标记缺口。
- **测量：** 不同 slot 配额下的覆盖、最新状态一致性、重复率和后续错误传播。
- **机制：** 把动态变化与静态布局两个需求分开，避免所有 slot 都被同一时间或同一表面占满。

### A8. 外侧相机标定/坐标合同适配器

- **对象：** 进入 pipeline 的 `c2w`、`K`、尺度、深度单位和坐标手性。
- **干预：** 在调用前验证并转换单位、轴序、camera-to-world/world-to-camera、主点与畸变；在输出旁保存转换矩阵，不改模型权重。
- **测量：** round-trip 位姿误差、投影像素误差、不同来源 pose 的合同一致性；用合成立方体和已有保存 pose 做 CPU 守卫。
- **机制：** 消除“检索本身没错，但 query 与 normalization 在不同坐标合同下”的系统性错误。

### A9. 双路径相机归一化的外侧隔离

- **对象：** 目标位姿改变同时影响检索和 `get_translation_scaling_factor` 的耦合。
- **干预：** 对每个候选先固定一份参考 `all_c2ws`/scale，再单独改变 retrieval query；或在 wrapper 中计算并记录两条包，比较固定 scale 与随 query 更新的结果。
- **测量：** query-only、normalization-only、联合路径的输入张量 hash 和输出差；先做零扩散/条件包比对，未来再做质量。
- **机制：** 把双重混杂拆成可复现实验臂，避免把检索变化误读成几何归一化变化。
- **弱：** 主要是诊断/识别方法，单独的生成收益尚未定义。

### A10. 深度重投影产生 virtual context

- **对象：** 输入 context frame，而不是模型本身。
- **干预：** 用真实历史 RGB-D/pose 做 CPU z-buffer 重投影，在目标相机生成带空洞 mask 的虚拟 RGB/深度；将其作为外部可接受的 context 图像或只用于候选排序，明确标记“虚拟来源”。
- **测量：** 重投影误差、空洞比例、虚拟与真实 context 的差异；若接口不接受虚拟帧，则只测排序/拒答收益。
- **机制：** 对已观察表面提供目标视角的证据，减少模型自己从远视角猜测。
- **弱点：** 空洞和遮挡边界可能反而误导；需要严格区分合成/真实来源。

### A11. 候选去重与 slot 角色匹配

- **对象：** `(a,a,b,c)` 之类含重复 frame 的 context 列表及其 slot 顺序。
- **干预：** 外侧先按 frame ID 去重，再按预声明角色（锚点、近景、补洞、最新）做稳定匹配；缺槽时输出明确的“缺候选”状态而不是偷偷复制。
- **测量：** 输入包是否达到预定的重复数、slot permutation 的输入 hash、未来的区域质量和 no-op 保护。
- **机制：** 让 context 预算花在独立证据上，同时保留重复臂作为可解释对照。
- **弱：** 可能只是一个小修补，必须用预先固定阈值检验。

### A12. 可拒答的几何风险门

- **对象：** “无论证据是否冲突都生成并写回”的调用策略。
- **干预：** 在调用前计算候选间 pose/depth/visibility 分歧；超过阈值时返回 `needs_more_evidence`，选择固定历史 fallback 或暂停写回。
- **测量：** risk–coverage 曲线、拒答后重试收益、错误写回率和延迟；零 GPU 先在已有封存候选上离线计算。
- **机制：** 对不可辨识视图宁可延迟决定，避免把猜测变成持久记忆。
- **弱：** 可能降低可用 coverage，不能只报告保留样本。

### A13. 调用顺序的安全调度器

- **对象：** navigation action 的调用顺序和 pipeline 内继承状态。
- **干预：** 每次动作从干净状态启动，显式传递 NMS/threshold 参数；若 public API 不支持，就用 snapshot→reset→priming→调用→校验的 wrapper 协议。
- **测量：** 顺序交换后的 threshold、候选 ID、padding multiplicity 和 context packet 是否逐字节相同；记录异常序列。
- **机制：** 把跨调用状态泄漏从隐藏副作用变成显式协议。
- **弱：** 是可靠性方法，不能单凭顺序不变就宣称质量提升。

### A14. 自适应 context budget（无新增权重）

- **对象：** 每次调用的 `context_num_frames`/候选请求长度。
- **干预：** 用查询熵、可见性缺口和候选分歧决定请求 1…K 个候选；低风险少取，高风险保留更多并在固定 slot 数内重排。
- **测量：** 在相同输出槽预算下的候选池大小、CPU/显存/延迟、覆盖和风险；用 trace 验证不读未来答案。
- **机制：** 把固定预算分配给真正不确定的窗口，而不是每个 query 使用同样的候选开销。

### A15. 轨迹微规划与历史重访

- **对象：** 用户请求的短轨迹及每个窗口的 target pose。
- **干预：** 在不改变最终用户目标的前提下，对中间查询插入少量可逆探针视角，选择能最大化新表面覆盖或降低不确定度的路径；若路径不可改，则把规划只用于候选检索排序。
- **测量：** 每一步新增覆盖、探针开销、目标终点误差和长程失败率；静态阶段先做几何模拟。
- **机制：** 通过主动获取“缺少的证据”减少被动外推。
- **弱：** 如果应用不允许改变轨迹，它退化为分析工具。

### A16. 多随机种子的一致性接受器

- **对象：** 同一 context/target 的采样 seed 和写回决策。
- **干预：** 生成若干 CPU 可排队的 seed 记录（实际采样仍需未来 GPU），用几何/来源一致性指标选一个或拒答；不把最低单次 RGB 指标当真值。
- **测量：** seed 间方差、几何一致性、选择器与 oracle 的差、额外成本；先用已有封存输出重算。
- **机制：** 让偶然的漂亮样本不自动进入持久状态。
- **弱：** 多样本会放大成本，而且自洽不保证真实。

### A17. 生成后几何冲突局部修复

- **对象：** 已生成的 RGB 帧和目标 pose。
- **干预：** 用历史深度/pose 做 CPU 投影，定位重影、穿透和明显冲突区域；用光流/颜色守恒做局部后处理或把帧标记为不可写回，区域外像素保持不变。
- **测量：** conflict mask precision/recall（有独立 reference 时）、边界接缝、全图像素守恒和写回率。
- **机制：** 将几何失败限制在局部，避免整个帧污染下一次检索。
- **弱：** 更像后处理/守门器，必须避免把像素变好误称为世界模型变好。

### A18. 生成帧的质量—新覆盖准入

- **对象：** 生成后自动追加到 `self.c2ws`/frame bank 的动作。
- **干预：** 只有同时满足重投影一致、与已有帧非冗余、目标区域有新覆盖的帧才进入主状态；否则保存为旁支档案。
- **测量：** 单位 memory slot 的新覆盖、冗余率、失败传播率、拒写后的状态长度；当前先在 saved-data 上重算。
- **机制：** 让记忆容量成为受控资源，而不是所有输出都永久写入。

### A19. 读取—消费的双 hash 审计包

- **对象：** context RGB、latent、encoder embedding、pose、K 及 mask。
- **干预：** 对读回列表和真正传入 `get_cond` 的张量分别 hash；比较 source IDs、顺序、padding 和归一化前后 hash。
- **测量：** 逐字段差异矩阵、重复执行字节一致率、输入包能否重放；不宣称质量结果。
- **机制：** 识别“候选列表看起来改了，但消费者实际收到另一包”的接口错位。
- **弱：** 主要是审计基础设施。

### A20. 选择器的保守分数校准

- **对象：** 几何距离、surfel 计数、时间等启发式分数的数值尺度。
- **干预：** 在不训练的情况下，用固定开发集做 rank-preserving monotone calibration（例如分位数或温度），输出概率式“可消费性”而不是任意线性加权。
- **测量：** 校准曲线、Brier/ECE、top-k 选择稳定性、跨序列迁移；不读取 future target 作为调参答案。
- **机制：** 让分数可比较并暴露不确定度，而不是把不同量纲相加。
- **弱：** 仍属于启发式选择，效果很可能依赖开发面板。

### A21. 物理与颜色的外侧标准化

- **对象：** 输入 RGB 的曝光、白平衡、量化和深度单位。
- **干预：** 记录并做固定、可逆的 photometric/depth normalization；保留原始 bytes 与变换参数，避免模型把曝光变化当几何变化。
- **测量：** normalization round-trip、颜色直方图漂移、投影误差、不同序列合同一致性。
- **机制：** 减少跨来源帧的非几何差异干扰 context 消费。
- **弱：** 更像数据合同修复；不应直接称作 world-model 方法。

### A22. 受限来源反事实回放器

- **对象：** 已封存的 context 包及其生成输出，不读新的 GT。
- **干预：** 在同一 state/seed 下逐个删、换、重排一个 source，重放所有下游输入，形成 leave-one-source-out 与 matched replacement 对照。
- **测量：** 来源影响、空间支持、输出差异、replay variance；只报告 post-selection influence，不把它叫 total causal benefit。
- **机制：** 先找出“哪类证据真的到达生成器”，为未来方法选择具体失败对象。
- **弱：** 这是诊断候选而非直接收益方法。

### A23. 时间窗口的有限状态机

- **对象：** 多次调用的 `initialize / move / turn / undo / reset` 协议。
- **干预：** 在 wrapper 层把动作建成 typed FSM，禁止非法状态转移；每一步声明预期 bank 长度、可用 frame IDs 和阈值来源。
- **测量：** 状态机覆盖、非法转移检测、实际与预期 state trace 的差；可用合成动作序列穷举。
- **机制：** 让跨调用转换动态可验证，而不是靠隐式列表长度推断。

### A24. 延迟—质量预算的选择器

- **对象：** retrieval 候选数、几何投影次数、调用重试次数。
- **干预：** 预声明 Pareto 策略：每一单位 CPU/显存预算换取最大覆盖下降或风险下降；输出质量与成本曲线。
- **测量：** latency、峰值内存、候选数、覆盖/风险、每次调用成本；零 GPU 先只测输入处理。
- **机制：** 在真实部署中把“更好”定义为可用的质量—成本组合。
- **弱：** 可能是系统设计/分析，不是生成机制。

### A25. 失败类型驱动的 fallback 集合

- **对象：** retrieval 失败、候选不足、几何冲突、采样异常四类错误路径。
- **干预：** 每类错误绑定一个不同的固定 fallback：最近合法历史、固定 offset、虚拟重投影、拒答；禁止一个万能 fallback 掩盖原因。
- **测量：** 每类触发率、恢复率、状态是否污染、额外延迟；先用合成异常注入验证。
- **机制：** 失败处理与失败原因对齐，降低错误恢复的二次污染。
- **弱：** 若没有真实失败分布，策略权重只是暂定。

## Part B — 假设解除冻结后的生成

以下假设允许训练、微调、新权重、上游改动和算力。成本是到一个“能作出决定性首轮结果”的相对预算，而非承诺；S 约 1 张 40–80 GB GPU 数小时至数日，M 约 4–8 张 H800/A100 数日至一周，L 约 8–32 张卡一至两周，XL 约 32–128 张卡数周。每项都需另行决定数据、权重、消费者和评测合同。

### B1. 下游效用学习的检索器

- **对象/干预：** surfel→frame 计数和固定排序；训练可微 top-k/Gumbel selector，输入目标 pose、可见 surfels、候选外观与不确定度，预测“该帧被消费后目标重建损失下降”，以生成损失和 slot 预算正则替换静态分数。
- **测量/机制：** 固定候选集的 RGB/LPIPS/深度/pose、risk–coverage、跨场景选择校准；把“相关/近”变成下游效用。
- **成本/弱点：** M（检索头+冻结主干，4–8 卡）；候选标签需许多配对生成，可能学到场景 ID。

### B2. 可微 surfel 渲染检索

- **对象/干预：** 当前硬 z-buffer 与 timestep 计数；训练软可见性、遮挡概率和 3D 特征聚合，让 selector 使用覆盖、法线、深度和空洞风险。
- **测量/机制：** 遮挡区域误差、覆盖、检索—消费影响；避免单个最近 surfel 代表整片视域。
- **成本/弱点：** M；软光栅化偏差和显存可能掩盖收益。

### B3. 可增量 neural field / tri-plane 记忆

- **对象/干预：** surfel list 与 `surfel_to_timestep`；将历史帧编码为可在线更新的 3D feature grid/tri-plane/NeRF-like field，目标相机读取颜色、几何和置信度 tokens。
- **测量/机制：** novel-view RGB/depth/normal、长程漂移、更新成本；连续空间共享比重复离散 surfel 更适合回访。
- **成本/弱点：** L–XL（8–32 卡起，需多场景 3D 数据）；在线更新慢、动态物体污染。

### B4. 可写、可删、可修订的记忆控制器

- **对象/干预：** `c2ws`、latents、embeddings、Ks 和 scene map 生命周期；训练 write gate 决定写入、合并、衰减和回滚，保存时间、来源、置信度和版本。
- **测量/机制：** 记忆污染率、误差随步数、回滚恢复、容量—质量；阻止错误生成永久进入上下文。
- **成本/弱点：** M；门控可能删掉难例，需要带自然失败的长序列。

### B5. 长程 recurrent world-state token

- **对象/干预：** 每次只交给扩散器的 context frames；加入跨调用 GRU/Transformer scene token，以 3D/相机/重建辅助损失做 TBPTT。
- **测量/机制：** 长轨迹一致性、回访重建、token 容量、误差传播；保存不可从四帧恢复的全局状态。
- **成本/弱点：** L（8–16 卡）；状态漂移和截断训练是风险。

### B6. 来源/几何绑定的 cross-attention

- **对象/干预：** 普通 context latent 拼接进入 UNet cross-attention；每 token 加 source ID、3D 位置、可见性和时间，分离 source attention 与 target query，并做来源 dropout。
- **测量/机制：** source ablation 的局部支持效应、attention entropy、局部深度/纹理；让网络消费可定位来源。
- **成本/弱点：** M–L；tag 可能被忽略或变成捷径。

### B7. Geometry-Control 分支

- **对象/干预：** 扩散 UNet 条件接口；新增 depth/normal/visibility/flow ControlNet 或 FiLM 分支，几何分支先预训练再联合微调。
- **测量/机制：** RGB、深度、法向、遮挡边界和轨迹服从；让几何证据在每个去噪阶段起作用。
- **成本/弱点：** L（8–32 卡）；错误深度会被硬放大。

### B8. 世界坐标扩散与可微渲染器

- **对象/干预：** 2D latent 中直接生成目标视图；改成生成稠密/稀疏 3D latent，再渲染任意 camera，并把渲染残差回流扩散。
- **测量/机制：** 多视重投影、跨轨迹一致性、3D 几何和 RGB；共享 3D latent 绑定多相机。
- **成本/弱点：** XL（32–128 卡，重训主干+renderer）；显存和动态场景是主要成本。

### B9. 静态/动态 slot 分解

- **对象/干预：** 单一 surfel/map 与视频 latent；分为静态背景、可动实体、相机运动，学习每 slot 的 SE(3)/deformation 与遮挡排序。
- **测量/机制：** 静/动态区域分别的 PSNR、物体轨迹、遮挡恢复、回访一致；不把物体运动写成错误相机/几何。
- **成本/弱点：** L–XL；需要动态标注或可靠多视跟踪，slot permutation 不稳定。

### B10. 闭环轨迹规划器

- **对象/干预：** 给定 camera trajectory 的逐窗 retrieval；训练 model-predictive controller 预测选帧/下一视点的多步结果，最大化未来重建与不确定度下降。
- **测量/机制：** 固定相机预算下的长程质量、覆盖、失败率和规划成本；提前获取关键视角。
- **成本/弱点：** L（8–32 卡）；规划误差会累积，若轨迹不可改只剩 retrieval 策略。

### B11. 回访/循环一致性训练

- **对象/干预：** 多次调用生成链；对 A→B→A 或闭环轨迹加 latent/feature/render cycle loss，训练相机条件和状态更新。
- **测量/机制：** cycle RGB/depth/pose、每步 drift、方向变化；把长期一致性从单步目标变成训练信号。
- **成本/弱点：** M–L（4–16 卡）；循环可能学成过平滑。

### B12. 不确定度感知多假设生成

- **对象/干预：** 单一扩散样本；输出 K 个带几何/来源置信度候选，学习 calibrated selector 或融合器。
- **测量/机制：** oracle 与自动选择差、ECE、tail risk、最差区域、样本成本；显式表示新视角的多模态性。
- **成本/弱点：** M–L；推理成本 K 倍，选择器可能偏好锐度。

### B13. 可学习 denoising 时机和剂量

- **对象/干预：** 固定 CFG、步数和 schedule；策略/FiLM 根据几何覆盖与 source uncertainty 决定每步的 CFG、noise schedule、context 注入强度。
- **测量/机制：** 同算力下 PSNR/LPIPS/深度、重影率、步数曲线；可靠几何强注入、冲突证据延迟或减弱。
- **成本/弱点：** M–L；RL 不稳定、容易 reward hacking。

### B14. 多尺度层级记忆

- **对象/干预：** 单一 frame list；建立 scene keyframes→local chunks→per-pixel evidence 三级索引和路由。
- **测量/机制：** 容量—质量、长序列召回、延迟/显存和层级消融；全局布局与局部细节分开服务。
- **成本/弱点：** M–L；层级路由错了会放大错误。

### B15. 在线场景 adapter

- **对象/干预：** 冻结主干；首帧用无标签重投影/多视一致只更新 LoRA/scene adapter，后续固定或慢更新。
- **测量/机制：** 每场景 1/5/10 帧适配曲线、零样本差、遗忘、时间和显存；适应材质、尺度和相机分布。
- **成本/弱点：** S–M（LoRA）；易过拟合首帧并造成答案泄露。

### B16. 相机内参、畸变、rolling-shutter 联合编码

- **对象/干预：** 当前只用 c2w/平均 K 的条件；新增 SE(3)+intrinsics/distortion/shutter encoder，并训练相机随机化。
- **测量/机制：** 跨焦距、主点、畸变和 rolling-shutter 的投影与轨迹误差；不把内参变化误当场景变化。
- **成本/弱点：** M；需要多相机标定数据。

### B17. 神经对应场替代离散时间索引

- **对象/干预：** `surfel_to_timestep` 离散反查；学习跨帧 3D correspondence/feature tracks，将同一表面聚合到稳定 memory slot。
- **测量/机制：** correspondence 精度、遮挡恢复、检索局部性和生成几何；反射、动态物体单独报告。
- **成本/弱点：** M–L；动态与反光区域对应不确定。

### B18. 检索—生成联合对比学习

- **对象/干预：** 独立 retrieval 分数和生成器；正样本是实际降低目标重建/几何误差的历史帧，hard negative 是近位姿但遮挡或过时的帧。
- **测量/机制：** recall@k、下游 utility、hard-negative 胜率和跨场景泛化；embedding 直接对齐消费效果。
- **成本/弱点：** M；正样本要许多候选生成。

### B19. 来源因果归因辅助训练

- **对象/干预：** 无法区分 context 贡献的 UNet；训练 source-mask/dropout、counterfactual latent swap 和局部几何损失，使输出变化落在被选来源的支持区。
- **测量/机制：** 影响、localization、matched benefit、negative control；让来源消费可定位而非全局平均。
- **成本/弱点：** L；局部损失容易被纹理捷径满足。

### B20. 可逆状态检查点与分支世界

- **对象/干预：** 生成后立即写回同一 map；维护版本树，先用重投影/不确定度/几何检查提交，异常则回滚并从多假设重生成。
- **测量/机制：** 长程失败率、恢复率、延迟和树大小；阻断一次错误的永久传播。
- **成本/弱点：** M；检测器假阳和树爆炸。

### B21. 质量—新颖性双门控写入

- **对象/干预：** 所有生成帧默认写入；训练门控同时考虑质量、几何新覆盖和与已有帧的冗余。
- **测量/机制：** 单位 slot 新覆盖、冗余、容量—质量 Pareto 和门控校准；让内存预算可解释。
- **成本/弱点：** S–M；早期 gate 偏差可能锁死错误状态。

### B22. 可学习重排与 slot assignment

- **对象/干预：** 候选排序后直接填 context slots；给 slot 定义锚点、近景、补洞、最新等角色，用 Sinkhorn 匹配候选到角色。
- **测量/机制：** slot permutation、区域几何/RGB、同候选不同分配；避免 slot 位置语义被浪费。
- **成本/弱点：** M；slot 角色可能随场景改变。

### B23. 目标视图分解与局部专家

- **对象/干预：** 单一全图扩散；先预测目标可见区、深度层、遮挡边界，再由背景/前景/新区域专家或 adapter 生成并合成。
- **测量/机制：** 区域误差、边界重影、分解准确率和专家调用成本；新颖区域不被历史背景平均。
- **成本/弱点：** L；分解错会产生接缝。

### B24. 几何一致的神经压缩记忆

- **对象/干预：** latents/embeddings 与 c2w 列表；训练 3D-aware VQ/quantizer，码字带位置、法向、时间，误差预算优先可见支持。
- **测量/机制：** 同内存质量、检索速度、量化误差和局部几何；让长会话记忆可扩展。
- **成本/弱点：** M；码本跨场景外推不稳。

### B25. RGB—depth—normal—semantic 多任务生成

- **对象/干预：** 只有 RGB/VAE latent 的消费者；联合 decoder 预测 RGB、depth、normal、semantic occupancy，生成时互相条件。
- **测量/机制：** 多任务、重投影、遮挡和跨域鲁棒性；辅助几何任务约束外观歧义。
- **成本/弱点：** L；任务冲突和伪深度偏差。

### B26. 不变/可变外观分解

- **对象/干预：** memory embedding 混合几何、光照和材质；分为 content/geometry 与 appearance 双流，做跨时同几何对比和光照增强。
- **测量/机制：** 跨曝光/光照的几何与 RGB、appearance swap 可控性；回访不把外观变化写成结构变化。
- **成本/弱点：** L；解耦不可辨识，需多条件数据。

### B27. 可微遮挡、epipolar、flow 与碰撞约束

- **对象/干预：** 训练只用像素扩散 loss；加入 z-buffer、遮挡顺序、epipolar/flow、碰撞/穿透损失和随机相机轨迹。
- **测量/机制：** 遮挡边界、穿透、深度排序和长轨迹质量；排除像素相似但 3D 错的解。
- **成本/弱点：** M–L；近似物理可能惩罚真实动态。

### B28. 长程难例课程与在线挖掘

- **对象/干预：** 训练数据混合比例与轨迹采样；从短静态→多视→长闭环→动态遮挡/大位移，按错误类型挖 hard windows。
- **测量/机制：** 按场景、轨迹、遮挡分桶的 tail-risk、收敛样本效率；把自然失败转为针对性监督。
- **成本/弱点：** S–M（数据处理+微调）；课程顺序和挖掘偏差会影响结论。

### B29. 教师集成到单模型的不确定度蒸馏

- **对象/干预：** 多采样、多视几何教师和单一大消费者；蒸馏均值、分位数和拒答信号到单模型。
- **测量/机制：** 同算力质量、ECE、拒答后的重试收益和延迟；把昂贵搜索变成可部署路由。
- **成本/弱点：** L；教师偏差可能被蒸馏成过平滑。

### B30. 长程时序 Transformer + 扩散混合

- **对象/干预：** 每次独立局部时序窗口；用时序主干预测低频 camera/scene state，再由扩散补高频外观，跨窗口用 KV/scene cache。
- **测量/机制：** 长视频 FVD/temporal LPIPS、回访误差、显存与延迟；结构由时序主干维持，细节由扩散补齐。
- **成本/弱点：** XL；长上下文训练昂贵，两个主干的接口可能错配。

### B31. 主动视角/传感器协同策略

- **对象/干预：** 固定历史帧来源；训练 policy 选择下一观测，使地图不确定度最大下降或目标区域补齐。
- **测量/机制：** 单位观测/时间的几何与 RGB 收益、信息增益和策略鲁棒性；获取被动历史永远看不到的表面。
- **成本/弱点：** L–XL；需要真实可执行相机和额外采集。

### B32. 生成后局部修复扩散

- **对象/干预：** 一次性全图输出；检测重投影/深度冲突区域，只对 mask 内进行低步数 image-to-image refinement，mask 外 latent 锁定。
- **测量/机制：** 支持区质量、边界接缝、全图守恒和额外步数；把算力放在几何失败位置。
- **成本/弱点：** M；mask 错误会制造边界伪影。

### B33. 跨场景元学习与快速适配

- **对象/干预：** 固定通用参数；meta-train scene episodes，使少量首帧无标签梯度适配 camera scale、材质和写入 gate。
- **测量/机制：** 1/5/10 帧适配曲线、未见域和遗忘；提升新场景早期表现。
- **成本/弱点：** L；元训练分布限制和二阶成本。

### B34. 安全/拒答式世界模型

- **对象/干预：** 任何低置信目标都强行输出并写回；训练 calibrated abstention head，在不可见/冲突视图输出“需要额外观测/多假设”，阻止写回。
- **测量/机制：** coverage–risk、拒答后补观测收益、长程失败率；把不确定性变成决策合同。
- **成本/弱点：** S–M（只训 head）或 L（联合训练）；用户必须接受空输出或额外观测。

### B35. 统一 action/observation 接口的可学习控制器

- **对象/干预：** VMem 的移动、转向、回退 API 与生成器状态之间的手工协议；训练 action encoder 和 state transition，使动作、相机轨迹、记忆写回共同优化。
- **测量/机制：** 同一目标在不同 action 分解下的结果、动作可组合性、回退恢复和跨任务泛化；把调用序列作为可学习对象。
- **成本/弱点：** L–XL；需要带动作的长轨迹和用户任务定义。

### B36. 资源感知稀疏注意力/编译路径

- **对象/干预：** 长 context 的 attention kernel 和显存访问，而不是生成函数；按几何邻接做 block-sparse attention，采用 IO-aware kernel。
- **测量/机制：** 相同输出的吞吐、峰值显存、能耗、延迟和数值误差；让更长的历史成为可运行选项。
- **成本/弱点：** M–L（kernel 原型+少量微调可 M）；主要是系统贡献。技术例子可参照 arXiv:2205.14135, *FlashAttention: Fast and Memory-Efficient Exact Attention with IO-Awareness*，但本候选的具体实现尚未定义。

## Part C — 八个槽位的结构性盲点

八槽把搜索空间建成一个**单一运行时管线的 intervention topology**：证据读、条件表示、持久状态、目标分解、跨调用转移、几何耦合、调用内采样、测量。这个视角适合回答“在现有消费者的哪个节点动手”，但不是完整的论文贡献本体。更完整的坐标至少还要有：

1. **改变的对象：** task、data、training objective、model、runtime、system、evidence contract。
2. **发生时间：** 预训练、微调、部署推理、用户闭环、事后审计。
3. **主张类型：** 能力、效率、可靠性/安全、可校准性、任务定义、理论性质、可复现性。
4. **受益者/做决定的人：** 模型作者、部署者、评测者、agent/player、最终用户或政策制定者。

因此，增加“第九个内部轴”还不够；不少贡献改变的是边界、数据、任务或判定规则，无法定位到一个运行时节点。

### C1. 问题/能力定义和 action-observation contract

有些工作首先改变“什么是可查询、可行动的世界”，而非 VMem 内部如何读 frame。例：arXiv:2402.15391, *Genie: Generative Interactive Environments*，把无监督视频、latent action 和逐帧交互环境定义成核心对象。硬塞进“条件表示”会丢掉 action contract 和可交互能力本身。

### C2. 数据引擎、监督与数据课程

训练视频的筛选、配对、合成、相机标注、难例课程和伪标签是数据生产对象，不是运行时 evidence read。它们可以改变学习到的能力，却没有一个对应的八槽节点。一个可查的技术例子是 arXiv:2406.17711, *Data curation via joint example selection further accelerates multimodal learning*；把它归入 retrieval 会混淆“训练数据选择”和“在线 context 选择”。

### C3. 学习目标与训练—推理契约

loss、噪声日程、teacher/student、rollout supervision、梯度截断和 train-test gap 发生在参数学习阶段。arXiv:2407.01392, *Diffusion Forcing: Next-token Prediction Meets Full-Sequence Diffusion* 的中心是独立 token 噪声和序列训练范式；arXiv:2506.08009, *Self Forcing: Bridging the Train-Test Gap in Autoregressive Video Diffusion* 的中心是用模型自己的 rollout、rolling KV cache 和 holistic loss 训练。把它们叫“within-call inference dynamics”会漏掉训练契约。

### C4. 系统、编译器、硬件和资源合同

保持生成函数不变，只改变 kernel、IO、并行度、显存流量、能耗或延迟，也可能是有价值的系统工作。arXiv:2205.14135, *FlashAttention: Fast and Memory-Efficient Exact Attention with IO-Awareness*，把 HBM/SRAM 读写作为主要对象；八槽没有“执行介质/资源合同”这一维。

### C5. benchmark、数据集和验证协议作为对象

“measurement”这个槽位把已有系统的测量压成一个位置，但新 benchmark 往往同时改变 task suite、标签、judge、validity 和 claim-target contract。例：arXiv:2311.17982, *VBench: Comprehensive Benchmark Suite for Video Generative Models*；以及 arXiv:2502.20694, *WorldModelBench: Judging Video Generation Models As World Models*。它们的对象是可复用的评测边界和判定工具，不只是给 VMem 加一个指标。

### C6. 交互闭环、策略和用户协议

生成器内部不一定改变，agent/player 的 action policy、目标、可供性、人工反馈和何时重访仍可改变系统能力。Genie 同时是这一类的例子；另一个可搜的例子是 arXiv:2309.17080, *GAIA-1: A Generative World Model for Autonomous Driving*，其输入输出包含 video/text/action 与 ego/scene 控制。八槽会把应用/交互协议错误地压到“跨调用 transition”。

### C7. 不确定性、风险、拒答和 assurance

“何时行动、何时重访、何时拒答、风险上限是多少”是 decision contract，不等于 state 或 retrieval 的内部改动。可作技术对照的例子是 arXiv:2512.05927, *World Models That Know When They Don't Know - Controllable Video Generation with Calibrated Uncertainty*；其对象包括校准不确定度、proper scoring、OOD 和拒答边界。八槽若只写 measurement，会漏掉风险策略本身。

### C8. 理论性质和因果可辨识性

稳定性、可组合性、可辨识性、泛化界、因果效应和可证明的安全性质可能横跨所有节点，不能指向单一 slot。一个 runtime intervention 可能只是理论问题的实现载体；反过来，一个理论结果也可能完全不改 runtime。

### C9. 表征学习范式

arXiv:2404.08471, *Revisiting Feature Prediction for Learning Visual Representations from Video*，中心是 feature-prediction 的自监督目标和冻结下游评估；将它归到“conditioning representation”会把训练 regime 与部署条件混为一谈。

### C10. 跨层共同设计和可复现 artifact

模型、数据、硬件、API、隔离、hash、状态账本和发布 artifact 的组合可以构成一个可复用系统合同，单个内部槽位无法表达。它还可能贡献负结果或边界条件：某个 claim 在明确的 consumer/data/evidence contract 下不成立。八槽会把这种科学结论错误缩成“measurement”。

### C11. 应改用多层地图

比单轴表更能表达候选的方法是一个三维或四维 registry：`object of change × time of intervention × claim/stakeholder`，再为每项链接 evidence contract。一个候选可同时落在 data+training+runtime；不要强迫它选择唯一 slot。这样“生成→筛选”顺序才不会再被自己的八轴地图提前截断。

## Part D — 我本来应该先问的一个问题

**主问题：**“我们真正要交付的贡献对象和 estimand（要估计的量）是什么，谁会据此改变决定；在不预设内部干预轴的情况下，哪个最小证据合同足以让这个决定可复核？”

更口语地说，是先问“我要改变的是系统、任务、证据合同，还是读者对 world model 这个词的判断？谁会因为这项工作采取不同动作？”，而不是先问“哪个内部槽位还空着？”

### 对这个问题的回答

过去的流程默认：固定一个消费者，找一个尚未被占的内部干预，就可能得到方法论文。这个默认把四个层次压扁了：

- 如果 estimand 是“一个冻结消费者在暴露的 14-window panel 上的 RGB PSNR”，现有资产最多支持条件性诊断，不能把有限 panel 外推成普适方法。
- 如果 estimand 是“未来若干次调用的几何一致性、风险校准或成本—质量 Pareto”，需要预先定义长程状态、独立 held-out 场景、消费者输入、输出 provenance 和失败处理；方法可能要跨训练、状态和决策层。
- 如果目标是可复用的 validity/diagnostic artifact，使用者是评测者或系统作者，交付物应是 typed input/state/consumer/output contract、负控制、反事实回放、独立 verifier 和跨系统复核，而不是把工具改名成方法。
- 如果 owner 要求方法论文，必须先写出外部使用者真正要解决的能力，再决定是否解除训练、权重、数据和算力约束。Part B 提供的是“解除约束后会出现的候选空间”，不是授权也不是验证。

所以我现在的答案不是选择某一个候选，而是先固定 `claim + estimand + stakeholder + minimal evidence contract`，再从 Part A/B 里选一个可证伪机制。这个顺序仍然允许零 GPU 的诊断/合同工作，也保留未来方法路线；它避免把“没有找到第九个槽位”误当成“没有研究问题”。

## 引用核对清单（仅作技术例子）

- arXiv:2506.18903 — *VMem: Consistent Interactive Video Scene Generation with Surfel-Indexed View Memory*。
- arXiv:2503.03751 — *GEN3C: 3D-Informed World-Consistent Video Generation with Precise Camera Control*。
- arXiv:2506.04225 — *Voyager: Long-Range and World-Consistent Video Diffusion for Explorable 3D Scene Generation*。
- arXiv:2402.03908 — *EscherNet: A Generative Model for Scalable View Synthesis*。
- arXiv:2507.10496 — *Cameras as Relative Positional Encoding*。
- arXiv:2503.14489 — *Stable Virtual Camera: Generative View Synthesis with Diffusion Models*。
- arXiv:2402.15391 — *Genie: Generative Interactive Environments*。
- arXiv:2406.17711 — *Data curation via joint example selection further accelerates multimodal learning*。
- arXiv:2407.01392 — *Diffusion Forcing: Next-token Prediction Meets Full-Sequence Diffusion*。
- arXiv:2506.08009 — *Self Forcing: Bridging the Train-Test Gap in Autoregressive Video Diffusion*。
- arXiv:2205.14135 — *FlashAttention: Fast and Memory-Efficient Exact Attention with IO-Awareness*。
- arXiv:2311.17982 — *VBench: Comprehensive Benchmark Suite for Video Generative Models*。
- arXiv:2502.20694 — *WorldModelBench: Judging Video Generation Models As World Models*。
- arXiv:2309.17080 — *GAIA-1: A Generative World Model for Autonomous Driving*。
- arXiv:2404.08471 — *Revisiting Feature Prediction for Learning Visual Representations from Video*。
- arXiv:2512.05927 — *World Models That Know When They Don't Know - Controllable Video Generation with Calibrated Uncertainty*。

这些引用用于说明“八槽可能漏掉的对象”或启发机制，不是本轮的占据审查；所有候选仍需后续原文近邻、实现可行性、独立证据和 owner 决策。

## 补充生成分支：wrapper 与数据/训练层

下面这些是并行生成阶段另外提出的候选，保留它们是为了不让第一轮分组过早压缩空间。

### A45. epoch token 防陈旧阈值

- **对象：** `initial_threshold`、候选缓存和 reset/branch 生命周期。
- **干预：** 每次 initialize/reset/branch 递增 epoch，把 threshold 与候选列表绑定到 epoch；读取时若 epoch 不同就拒绝缓存并重新计算。
- **测量：** move/turn/reset 顺序下的 threshold provenance、selection identity、stale-read 次数；先用合成状态序列。
- **机制/边界：** 把继承字段的隐式读取变成显式 miss；更偏可靠性机制，不能假设生成质量会改善。

### A46. shadow selector

- **对象：** released selector 与候选策略。
- **干预：** 实际调用仍使用 released IDs，sidecar 同时计算去重/MMR/coverage/trajectory-union IDs；只有在预声明切换点才允许采用新策略。
- **测量：** 策略一致率、Jaccard、覆盖和已有输出的 counterfactual 差异；不把 shadow 日志当作真实生成结果。
- **机制/边界：** 先观察候选政策的行为而不污染主状态；shadow 与真实 surfel 状态错位是风险。

### A47. capability/contract negotiation

- **对象：** 消费者固定 K、mask、dtype、pose shape、NMS 和 target padding 合同。
- **干预：** wrapper 启动时读取 capability manifest；不满足合同就拒绝请求而不是返回“成功”状态。
- **测量：** 提前拒绝率、runtime exception、invalid-condition 计数和重放 hash。
- **机制/边界：** 把接口不兼容变成可解释拒绝；拒绝本身不是输出改善。

### A48. dry-run/full-run 分离

- **对象：** 请求调度。
- **干预：** CPU dry-run 先验证 shape、状态、候选可用性、normalization stats、来源 hash，通过后才放行真实 call。
- **测量：** false positive/negative、被省掉的非法调用、dry-run wall time。
- **机制/边界：** 零 GPU 能先筛控制流错误；不覆盖模型数值。

### A49. sidecar provenance chain

- **对象：** RGB/depth/pose/K 配对及其 crop/resize/latent encode 链。
- **干预：** 每次变换保留 parent hash 和 immutable metadata，直到真正 `get_cond` 输入。
- **测量：** pairing break、duplicate source、late GT read、hash-chain 完整率。
- **机制/边界：** 保护来源身份与数据合同；不能仅凭 metadata 证明像素正确。

### A50. admission queue 与 commit barrier

- **对象：** 连续交互请求、并发 UI 和半写入 bank。
- **干预：** retrieve→condition→generate→append 作为不可打断事务；下一个 turn 只能读取已 commit epoch。
- **测量：** 并发/中断下 list length、epoch、state hash、额外延迟。
- **机制/边界：** 消除异步读写竞态；吞吐可能下降。

### A51. camera convention guard

- **对象：** 输入/输出 `c2w` 坐标轴、手性和 `get_cond` 的轴变换。
- **干预：** 检查右手性、det≈1、最后一行和 y/z 约定，映射到唯一 canonical convention；保存逆变换。
- **测量：** invalid pose 计数、round-trip inversion error、选择 ID 稳定性。
- **机制/边界：** 防止数据已经翻转而消费者再次翻转；自动修正可能掩盖上游错误。

### A52. intrinsic-aware resize/crop

- **对象：** RGB resize/crop 与 `K`。
- **干预：** 每次 resize/crop 显式更新 fx/fy/cx/cy，保留 source→model 坐标变换。
- **测量：** projected-pixel residual、边缘 coverage、depth reprojection；先 CPU 合成验证。
- **机制/边界：** 把相机内参错位与 geometry/generation error 分开；只修输入坐标合同。

### A53. action debounce/turn barrier

- **对象：** 短时间连续 UI 动作和 move/turn 三入口。
- **干预：** 合并时间窗内同向小 move，turn 前强制 commit；动作 regime 绑定策略版本并记录。
- **测量：** 有效调用数、pose deviation、selection duplicate、状态 race。
- **机制/边界：** 减少半成品状态和过密 query；可能改变用户真实轨迹。

### A54. source-hash deterministic seed schedule

- **对象：** 生成调用的随机种子。
- **干预：** 令 seed 由 scene、target pose、selected-source hash、branch epoch 的 hash 派生，同时保存用户 seed 映射。
- **测量：** exact replay bytes、cross-order invariance、seed collision、跨分支差异。
- **机制/边界：** 稳定可追溯；固定 seed 可能减少多样性，需要真实生成检验。

### A55. pose trajectory smoothing

- **对象：** 输入 `c2ws` 序列。
- **干预：** 在 SE(3) log-space 用预登记的 Savitzky–Golay/Bezier 只平滑超过阈值的高频抖动，K 同步更新。
- **测量：** 角速度/加速度、pose reprojection、temporal drift。
- **机制/边界：** 试图减少目标轨迹抖动传播；可能抹掉真实急转，需独立轨迹真值。

### A56. lookahead retrieval cache

- **对象：** 已知未来 camera trajectory 与下一 epoch 候选。
- **干预：** 当前 commit 后用 CPU 预计算下一批 support/候选，真正 call 只读取同 epoch cache；路径变更即失效。
- **测量：** cache hit、CPU latency、候选一致性和失效率。
- **机制/边界：** 降低交互延迟且不在生成期间改变状态；只是调度机制。

### A57. periodic state compaction

- **对象：** 长会话 surfels/lists 与索引。
- **干预：** 每 N 次 commit 合并近重复 source、重建 `surfel_to_timestep` 和候选 index，保留旧 snapshot/hash。
- **测量：** state bytes、render speed、ID preservation、selection drift。
- **机制/边界：** 控制长期 append 的重复和索引膨胀；重建可能改变 provenance。

### A58. historical quality gate

- **对象：** 写入 memory 的历史或生成 RGB。
- **干预：** CPU 计算 Laplacian variance、饱和/裁剪、压缩伪影和 depth support；低分帧转 tentative，不做 anchor。
- **测量：** 拒绝率、quality score 与后续 residual 的相关性、source survival。
- **机制/边界：** 低质帧不污染后续检索；清晰度不等于几何正确。

### A59. latent/embedding cross-check

- **对象：** 存储的 VAE latent 与 encoder embedding 的配对。
- **干预：** append/读取前做 hash、范数和可用的 RGB↔latent 重编码一致性检查，不一致则回退 source。
- **测量：** pairing mismatch、过滤后的重复率和输出差异。
- **机制/边界：** 防止相机/帧正确但 latent 与 embedding 错配；CPU 编解码误差需要单独校准。

### A60. static CPU all-history upper-bound probe（弱）

- **对象：** 候选集合截断。
- **干预：** 不截断候选，用 CPU 全库覆盖计算后取 K；只作为选择层上界和压力测试。
- **测量：** 候选数、CPU 时间、coverage、与固定 K 选择差异。
- **机制/边界：** 显示候选池截断本身的代价；计算不公平，不能当 end-to-end winner。

### B37. 可微/可回放合成轨迹引擎

- **对象：** 训练样本与候选效用标签。
- **干预：** 用有 mesh/NeRF 真值的场景随机生成相机、内参、遮挡、动态、光照轨迹，并保存每条历史候选对未来目标的 visibility/depth/reprojection 监督。
- **测量/机制：** 合成→真实迁移、几何支持、长轨迹误差；给 selector/state 明确监督而不依赖“最近帧”代理。
- **成本/弱点：** M–L（渲染+8–32 卡训练）；渲染域差距可能主导结果。

### B38. 反事实消费数据集

- **对象：** source utility label。
- **干预：** 固定 scene/target/noise，逐条替换、删除、交换 context，保存 F00/F10/F01/F11、support mask、replay variance。
- **测量/机制：** utility predictor calibration、跨场景排序、真实闭环收益；直接监督“被消费后有用”。
- **成本/弱点：** L–XL（8–32 卡离线生成，存储大）；每例要多次扩散。

### B39. 自然失败挖掘器

- **对象：** 训练分布与采样轨迹。
- **干预：** 先按重影、漂移、遮挡、pose 不服从、状态污染聚类失败，再主动采样对应轨迹和 hard negatives。
- **测量/机制：** tail-risk、错误桶召回、课程样本效率；让训练针对真实瓶颈。
- **成本/弱点：** S–M；失败分类器可能过拟合暴露 panel。

### B40. RGB-D/IMU/pose 同步数据引擎

- **对象：** RGB 帧和几何标签配对。
- **干预：** 构建严格时间同步的 RGB-D/IMU/pose，注入传感器缺失和曝光变化，并把缺失作为训练 mask。
- **测量/机制：** 缺失/噪声鲁棒性、内参外推、动态/静态分桶；训练真实传感器误差而非理想配对。
- **成本/弱点：** M–L（采集、许可、标注）；同步合同成本高。

### B41. 状态污染合成器

- **对象：** 长序列训练状态。
- **干预：** 故意注入错误 frame、pose 偏移、重复 slot、错误 surfel merge、低置信输出，并提供恢复/回滚目标。
- **测量/机制：** 污染检测 AUROC、恢复成功率、污染长度下的质量；训练系统在坏状态中自愈。
- **成本/弱点：** M；合成故障可能不覆盖真实故障。

### B42. 动态物体/交互数据引擎

- **对象：** 静态地图假设。
- **干预：** 采集或合成可动物体、遮挡、接触和相机运动长轨迹，附 object track、SE(3)、deformation 标签。
- **测量/机制：** 动态区几何、遮挡后回访、物体身份；将世界建模目标从静态 NVS 扩展到交互场景。
- **成本/弱点：** L–XL；真实动态 GT 昂贵。

### B43. 效用排序与双重分数损失

- **对象：** selector logits 与生成器 loss。
- **干预：** 候选按反事实下游损失差做 pairwise/listwise ranking；生成 loss 分开 RGB、depth、normal、reprojection 和 pose obedience，并学习置信度权重。
- **测量/机制：** 排序 Spearman、top-k utility、质量—计算 Pareto 和各 loss 分量；防止单一 PSNR 掩盖几何损失。
- **成本/弱点：** M–L；标签贵，权重学习可能 reward-hack。

### B44. 路径级 diffusion consistency

- **对象：** 逐窗训练样本和 rollout。
- **干预：** 将连续相机轨迹展开，联合计算每步输出和末端误差，以 teacher forcing→free running curriculum 训练长程 loss。
- **测量/机制：** 误差随步数、闭环与单步差、长轨迹 tail；直接惩罚误差传播。
- **成本/弱点：** L–XL；显存和梯度爆炸。

### B45. 几何因果干预目标

- **对象：** UNet 对 context 的使用路径。
- **干预：** 训练时 source drop/swap、geometry-preserving appearance edit、source-coherent mask，要求变化局限在可见支持且目标几何保持。
- **测量/机制：** source influence、localization、placebo、replay variance；抑制全局纹理捷径。
- **成本/弱点：** L；局部 mask/编辑器误差会污染监督。

### B46. 分位数校准与 conformal 拒答

- **对象：** 输出与 selector 的不确定度头。
- **干预：** 预测 RGB/depth 分位数和候选风险，用 proper scoring、conformal calibration 和 abstention loss 训练。
- **测量/机制：** ECE/NLL/coverage–risk、置信驱动重试收益；显式表示何时证据不足。
- **成本/弱点：** M–L；校准可能跨域漂移。

### B47. 可纠错冗余记忆

- **对象：** 单 frame 作为唯一证据。
- **干预：** 为关键表面存多源低维码/冗余视图，训练 decoder 在随机删帧或污染时恢复几何/外观。
- **测量/机制：** 删除/污染下恢复率、容量归一质量；把 memory 当纠错码。
- **成本/弱点：** M；冗余占容量并可能平均化细节。

### B48. 空间哈希/八叉树神经缓存

- **对象：** 线性 surfel 数组和全局扫描。
- **干预：** 分层空间哈希，每格保存局部 feature/不确定度/来源；query 只读目标 frustum，局部更新。
- **测量/机制：** 检索延迟、覆盖召回、内存和长场景质量；使地图规模与视域而不是总帧数绑定。
- **成本/弱点：** M–L；尺度边界和 hash collision。

### B49. pose-graph/地图联合优化

- **对象：** 生成使用的 c2w 与地图。
- **干预：** 跨帧匹配构造 pose graph，异步优化相机与 map 后再条件生成，学习权重拒绝错误闭环。
- **测量/机制：** ATE/RPE、重投影、生成稳定性和优化延迟；降低累积位姿漂移。
- **成本/弱点：** M–L；没有闭环时退化，优化开销大。

### B50. 离线 RL 检索策略

- **对象：** 固定排序 policy。
- **干预：** state=target frustum/candidates/memory confidence，action=选/删/重排 context，reward=多步几何+RGB收益−算力；以反事实数据做 conservative Q-learning。
- **测量/机制：** offline policy value、长程闭环、OOD 安全；从序列级收益而非单窗距离学习。
- **成本/弱点：** L；离线分布和价值外推风险。

### B51. bandit 式在线候选探索

- **对象：** 每次只取 top-k 的 selector。
- **干预：** 保留少量探索 slot，依据不确定度尝试非近邻 frame，并用后续残差更新 bandit。
- **测量/机制：** 累计收益、探索开销、收敛和失败尾部；发现距离排序漏掉的互补证据。
- **成本/弱点：** M；探索结果可能直接污染输出。

### B52. 主动记忆压缩/遗忘策略

- **对象：** 会话中无限增长的 frame/map。
- **干预：** policy 估计未来访问价值与重建成本，合并、量化或淘汰并保留不可逆摘要，训练长期回放 reward。
- **测量/机制：** 容量—质量、删除后回访、检索延迟；在有限内存保留可消费证据。
- **成本/弱点：** M；未来访问不可知。

### B53. 多模型专家路由

- **对象：** 单一消费者面对所有视图。
- **干预：** 为静态/动态/近景/大位移/低光训练专家 UNet 或 LoRA，由 geometry/scene router 选择或 ensemble。
- **测量/机制：** 每桶质量、路由准确、参数/延迟；减少单模型在冲突分布上的折中。
- **成本/弱点：** L；专家负载和 router 崩溃。

### B54. 教师搜索蒸馏到单步策略

- **对象：** 昂贵的多候选、多采样、局部修复组合。
- **干预：** 教师离线枚举 retrieval/generation/repair 组合，学生直接预测动作、初始 latent 和不确定度。
- **测量/机制：** 固定部署预算下接近教师程度、跨域和失败尾部；把算力密集决策压缩到部署。
- **成本/弱点：** L；教师偏差会被蒸馏。

### B55. 几何稀疏注意力与带宽调度

- **对象：** context×target attention、显存访问和长上下文上限。
- **干预：** 用可见 frustum/epipolar 邻域形成 learned block-sparse mask 和 IO-aware kernel，并以质量守恒约束微调。
- **测量/机制：** 同质量下显存、吞吐、能耗、长上下文上限和几何指标；把更多历史/多假设预算放进可运行系统。
- **成本/弱点：** M（mask+kernel 原型）到 L（重写 attention）；mask 错会漏证据，工程复杂。

## 最后边界

本文件故意同时保留强、弱、诊断型、系统型、数据型和方法型候选。它没有运行真实生成，没有做 occupancy gate，没有恢复 GPU/训练授权，也没有把任何候选写成创新成立。下一轮若要筛选，建议对每一项先补四个字段：明确的使用者与决定、唯一 estimand、最小独立证据合同、以及一个看到负结果就停止的条件。

## Part A 的资源层标记与实现特化补充

为避免“冻结、零 GPU”被误读成所有候选都能在本轮测完，给 Part A 加四级标签：

- **G0（CPU-only）**：state/schema/sidecar/调用调度、候选重排、hash、几何合同和后处理协议可直接执行。
- **G1（CPU+封存 artifacts）**：候选重排、intermediate diff、反事实输入包和已有输出的后处理可执行，但不能写成 fresh model effect。
- **G2（改 conditioning/latent、权重不变）**：可写 wrapper 和输入包设计；新的像素结果需要未来 GPU。
- **G3（冻结权重的 test-time 多采样/采样 schedule）**：模型仍冻结，但 fresh effect 仍需要 GPU；当前只可利用已有输出设计协议。

以下是实现特化的附加候选；同样不作占据或收益判断。

### A87. functional conditioning / 禁止 in-place mutation（G0）

- **对象：** `all_c2ws`、Plücker/conditioning tensors 与调用方缓存。
- **干预：** 在 `get_cond` 前 clone，禁止对传入张量直接做轴翻转、平移或缩放；每次从 immutable copy 计算 conditioning。
- **测量：** 重复调用、跨 branch 的 tensor hash、二次选择和 state fingerprint。
- **机制/弱点：** 防止一次调用的 in-place sign/scale 污染下一调用；主要是状态可靠性，不预期自动改善单次画质。

### A88. anchor-normalized robust scale（G2）

- **对象：** `get_translation_scaling_factor` 的第 0 相机范数和固定偏置规则。
- **干预：** 预登记用首 context/medoid 做零点，以 robust radius/MAD 计算 global scale，并在 trace 中写 anchor ID。
- **测量：** 对整体平移/旋转/缩放的 metamorphic invariance、Plücker norm 与 camera residual；fresh pixel 另行授权。
- **机制/弱点：** 偶然的 slot-0 anchor 可能放大尺度差；替代 scale 也可能改变训练分布。

### A89. per-frame mass cap（G0/G1）

- **对象：** `process_retrieved_spatial_information` 的 frame count/fractional remainder。
- **干预：** 对单 frame 的 mass 设上限，余量按 next-best unique frame 分配，保持总 K。
- **测量：** frame mass entropy、重复率、visible support、候选耗尽率和已存输出的尾部指标。
- **机制/弱点：** 防止一个 timestep 因一对多 surfel 映射吸走全部槽；质量集中可能本来就是正确证据。

### A90. per-surfel contribution normalization（G0/G1）

- **对象：** `cos_value/(1+depth)` 对一个 surfel 的多 timestep 累加。
- **干预：** 先把一个 surfel 对多个 timestep 的贡献归一为总权重 1，再分摊给 frame。
- **测量：** source mass、候选稳定性、不同 renderer resolution 下的敏感性。
- **机制/弱点：** 防止同一表面被一对多映射重复计权；会改变原 selector semantics，可能降低召回。

### A91. calibrated renderer focal scale（G0/G1）

- **对象：** retrieval probe 的固定 focal scale 和 principal point。
- **干预：** 使用场景/分辨率一致的 K，或在预登记小网格中选择最小视锥重投影误差的 focal scale；不得读取 future answer 调参。
- **测量：** visible surfel count、depth/occlusion residual、candidate ID churn。
- **机制/弱点：** 固定缩放可能使候选可见性与真实目标不匹配；若用 future depth 选择会产生泄漏。

### A92. min/softmin trajectory distance（G0/G1）

- **对象：** 先对多 target 取 average pose 再排序的距离。
- **干预：** 用 `min_t d(frame,target_t)`、softmin 或 weighted quantile，保留 target-level provenance。
- **测量：** 每目标的 min/max distance、coverage、候选稳定性。
- **机制/弱点：** 平均位姿可能落在无真实观测的中间位置；softmin 温度会改变任务偏好。

### A93. nearest-gap threshold rule（G0/G1）

- **对象：** NMS threshold 的静态百分位与实际 bank density。
- **干预：** 根据排序候选 nearest-gap 和预定 desired-K 计算 threshold，固定在 protocol 中。
- **测量：** threshold provenance、distinct K、NULL/PERMUTATION/CONTENT 分层。
- **机制/弱点：** 随 bank density 调整候选间隔；仍是手工 selector，必须与 state isolation 分开测。

### A94. duplicate source-ID attenuation（G0/G1）

- **对象：** 候选列表可重复出现同一 frame。
- **干预：** 先合并 unique frame 的 timestep weight，再对 score 施加预登记 concave transform，最后排序。
- **测量：** weighted unique coverage、pool exhaustion、selection IDs。
- **机制/弱点：** 区分“支持量高”和“同一 frame 重复”；可能把真实强支持压低。

### A95. deterministic tie-break schema（G0）

- **对象：** 相同/近相同距离的 sort key。
- **干预：** 显式 `(distance, -support, frame_id, insertion_epoch)`，记录 float tolerance 和线程数。
- **测量：** 跨 Python/PyTorch/线程的 byte identity、tie frequency、重放一致率。
- **机制/弱点：** 消除隐性 order drift；只保证确定性，不保证语义质量。

### A96. endpoint-aware trajectory weighting（G0/G1）

- **对象：** target batch 的平均支持目标。
- **干预：** 预先声明末端或用户关注目标的权重，例如末端 2×、中间 1×，对 union score 做 quota。
- **测量：** 每 target support、末端 RGB/depth tail、weight sensitivity。
- **机制/弱点：** 反映终点更重要的使用场景；可能牺牲中间帧，任务效用需明确。

### A97. five-list state-schema validator（G0）

- **对象：** `c2ws`、`Ks`、latents、encoder embeddings、`pil_frames` 五个配套列表。
- **干预：** 每次 write/pop 检查长度、dtype/shape、source index 和 epoch；不通过即拒绝 commit。
- **测量：** schema violation、undo/redo 后 hash、异常恢复率。
- **机制/弱点：** 保护成组写入/撤销的一致性；属于 guard/diagnostic。

### A98. saved denoising trace step selector（G1/G3，弱）

- **对象：** 已封存 `samples_z` 或 step trace。
- **干预：** 从预登记的末步截断/混合候选解码，用几何 score 选择，不重新训练。
- **测量：** step 与 consistency/quality 的关系、runtime；只适用于 trace 实际保存的样本。
- **机制/弱点：** 试探冻结 sampler 的终点选择；事后挑选不能冒充在线新方法。

### A99. source-consensus latent decode（G1/G2，弱）

- **对象：** 同一 source 的多次 latent/embedding。
- **干预：** coordinate-wise median/trimmed mean 后再 decode 或后处理，保留原 latent fallback。
- **测量：** latent variance、decoded residual、source identity 和独立 reference。
- **机制/弱点：** 可能压低采样噪声；latent median 可能不是自然图像，需 fresh model 验证。

### A100. static/dynamic memory split（G0/G1）

- **对象：** surfel memory 的长期/短期写入。
- **干预：** 用 frame difference/optical flow 将 static 与 moving region 分开；静态 source 进入 persistent bank，动态只短期缓存。
- **测量：** dynamic leakage、static coverage、revisit consistency、误分率。
- **机制/弱点：** 避免动态内容污染静态 world model；静态开发 panel 可能不足以支持动态结论。

这些 G0–G3 标签只描述当前执行边界；它们不会把零 GPU 的协议证据升级成真实生成效果。
