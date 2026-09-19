# 顶会因果归因刷新回执（2026-09-08T08:46Z）

- 状态：`LITERATURE_SEARCH_ONLY`
- 数据源：会议官方页面/OpenReview；未把搜索摘要当作模型实验
- 目标：检查“逐 source 的实际影响与跨 consumer 竞争”是否已有直接顶会先例，并提取可用于 S48 的实验方法
- 新颖性授权：`NONE`

## 查询面

1. CVF：video generation + memory + causal intervention + source attribution；
2. NeurIPS：video generation + memory interference + retrieval + source attribution；
3. OpenReview/ICLR：causal tracing + memory retrieval + generative model；
4. PMLR/ICML：selective memory + retrieval utility + causal evaluation。

查询时间为2026-09-08T08:39Z左右。网页搜索不是系统综述，未命中不能作为“没有相关工作”的证明。

## 新增有效近邻与方法启发

### Finding NeMo（NeurIPS 2024）

官方页面：<https://proceedings.neurips.cc/paper_files/paper/2024/hash/a102dd5931da01e1b40205490513304c-Abstract-Conference.html>

该工作把 diffusion memorization 从输出现象定位到 cross-attention neuron，并用停用该 neuron 的干预检验功能作用。对本项目的启发是：从“相关”升级到“干预后功能改变”是有顶会先例的创新动作。

它处理训练数据记忆和 neuron-level memorization，不处理交互视频世界模型中 ordinary-selected external memory source 的 Store→Benefit 全链，因此只是跨问题的方法先例，不能直接证明本项目差别成立。

### Reasoning or Retrieval?（ICLR 2026）

官方 OpenReview PDF入口：<https://openreview.net/pdf/1def5a871c606ae6ba6a3acfaf2475ab3a731283.pdf>

该工作通过分别操纵 reasoning cue 与 retrieval answer，识别两个竞争机制对最终答案的相对作用。对 PC-DPM 的直接启发是：F10/F01/F11 必须按析因设计分开 semantic/latent consumer，并检验联合干预能否解释自然输出。

它属于语言推理/检索归因，并非视频 memory 或几何定位近邻。当前只保留“竞争机制可用正交干预识别”的设计启发。

## 未纳入为直接近邻的结果

- 对话 memory 的多粒度选择：覆盖 memory segmentation/retrieval，但没有视频生成、几何 support 或逐 source output intervention；
- 训练数据或事实归因：对象是训练样本/文本证据，不是运行时可枚举 appearance consumer；
- WACV workshop/style-transfer memory：可作为弱背景，不能替代 CVPR/ICCV/NeurIPS 强对照。

## 对 S48/PC-DPM 的实际修改要求

1. 保留 `F10/F01/F11` 析因结构，同时加入 `F00`、same-path dose-zero、未选 source negative 与已知 consumer positive control；
2. 禁止用 attention 或 retrieval score代替 Influence；必须看 matched intervention 的输出差；
3. 两条 consumer 单独看似有影响仍不足；核心预测是同一 source provenance 同步后，冲突效应和真实 loss 同时改善；
4. 若 F10/F01 没有竞争或 F11 不恢复，立即删除 PC-DPM 机制故事；
5. 本轮搜索未发现与完整六级合同完全等价的正式顶会工作，但这只是当前查询范围中的未命中，不能升级新颖性授权。

