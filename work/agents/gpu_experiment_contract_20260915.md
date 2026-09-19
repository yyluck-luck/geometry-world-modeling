# 学校 GPU 迁移实验合同与执行清单（S101，2026-09-15）

**文档性质：** 这是把原 proposal 的“长时程几何一致性”研究主线迁移到学校 GPU 前的实验合同。它是执行前的约束，不是实验结果，也不代表已经获得学校服务器权限。

**当前科学边界：** `new_method_validated=false`，`novelty_authorization=NONE`。S99 和 S100 都是已见 S15B 缓存输出上的几何消费者重渲染：它们能帮助定位问题，但不是完整 VMem 视频生成、不是未见场景确认，也不是 GRC-Memory 有效性证明。S97/S98 中的 TUM `fr1`、`fr2` 已参与开发，不能冒充 held-out；目前正式 S91 仍被合格未见 RGB-D/相机配对 Gate0 阻断。

## 1. 这份合同要回答什么

原 proposal 关注动态 3D/4D world modeling 中的长期几何一致性：历史观测经过一段时间、遮挡和视角变化后，模型能否在未来视角继续保持正确的物体位置、深度和相机几何。当前候选研究问题是：

> 在相同的历史候选池和相同计算预算下，历史观测的**校准几何风险**能否预测并改善独立未来 RGB-D/pose 误差？

这里的“能否”必须通过未来真值、强基线、跨场景和完整消费者路径来回答。只有风险分数在选择前固定、选择后不读取未来答案，并且在未见数据上稳定超过简单基线，才有资格继续讨论方法贡献。

## 2. 数据与身份合同

### 2.1 必须保存的每帧字段

每个历史或未来样本都要有一个不可变的 `sample_id`，并在 manifest 中记录：

| 字段 | 要求 | 失败时的处理 |
|---|---|---|
| RGB 文件与 SHA-256 | 真实 8-bit RGB，路径和字节数可回读 | 缺失或哈希不一致，样本不得进入主评测 |
| Depth 文件与 SHA-256 | 真实深度图；记录位深、单位、无效值编码和有效像素率 | 不能把 RGB 或伪深度当 depth；缺失样本只进入数据诊断 |
| RGB/depth 时间戳 | 来自数据集原始 timestamp 文件或元数据，不用文件名猜测 | 无可追溯时间戳，不能建立 RGB-D 配对 |
| 相机内参 `K` | `fx, fy, cx, cy`、分辨率、畸变/已校正状态和来源 | 分辨率或内参不一致，停止该序列的几何评分 |
| 相机外参/pose | 坐标系名称、SE(3) 方向、单位、时间戳与来源 | 方向或单位未验证，不能计算重投影或 pose 误差 |
| 目标/历史关系 | exact frame id、时间差、未来间隔、可见性标签（若有） | 只凭相邻文件序号推断时间，标记为不合格 |
| 数据划分标签 | `DEVELOPMENT_SEEN`、`CALIBRATION_ONLY`、`HELD_OUT_TEST` | 标签缺失时按已见处理，不得升级为测试 |

### 2.2 RGB-D 配对与几何真值门

1. 使用原始时间戳做一对一匹配；记录阈值、匹配算法、未匹配数和重复候选数。项目已有 TUM 开发规则 `|Δt|<0.020s`，迁移时必须把规则写入 manifest，不得事后调阈值以增加样本。
2. 明确深度单位和有效范围；至少保存有效像素数、零值/无穷值/越界值计数。无效 GT 不能从分母中静默删除。
3. 由内参和 pose 把历史深度点投影到未来相机，检查投影边界、遮挡 z-buffer 和坐标系方向。保存少量人工可读投影样例用于边界 QA。
4. 未来 RGB、depth、pose 文件在**预测封存前不可被 selector、调参脚本和人工选择流程读取**。允许读取的是公共相机轨迹元数据；未来深度和未来 pose 是评分答案。
5. 连续性和重访要分开标注。3RScan 的 reference/rescan 可用于变化/重访研究，但当前元数据没有证明连续 next-frame 语义，不能自动当作连续视频。

### 2.3 当前数据状态

- TUM `fr1`：792 个严格 RGB-D 配对，其中 788 个落在同一 GT 支持区间；已参与开发，且固定窗口审计只有 2 个合格窗口，不能作未见确认。
- TUM `fr2`：2893 个严格 RGB-D 配对，其中 2212 个落在同一 GT 支持区间；已参与开发，固定窗口可形成 6 个，但同样属于 `DEVELOPMENT_SEEN`。
- 3RScan：官方元数据和样例归档显示有 RGB、depth、pose、内参和 reference/rescan 组织，但完整帧级许可、同步、单位、有效率和 pose 正文尚未通过 Gate0；样例访问权限保持 `AMBIGUOUS_NOT_VERIFIED`。

因此 GPU 服务器上的第一批正式评测必须使用一个新的、此前未用于阈值/方法选择的 held-out scene/sequence。若只能使用已见 TUM，结果只能叫 development diagnostic，不能叫跨场景确认。

## 3. 冻结后的公平比较

### 3.1 候选池和记忆预算

- 候选池在预测开始前由历史观测构成，保存排序、source ID、时间戳、几何特征和 selector 输入哈希。
- 主预算是 `k=4` 个记忆槽位；敏感性为 `k=2` 和 `k=8`。这里的 `k` 是真实记忆槽位/输入 token 或等价容量，不能用 S99 的“每源 39/196 个 16×16 source-block rewrite”替代。
- 所有方法接收相同候选池、相同目标查询、相同输出数量、相同模型权重和相同随机种子集合。若某基线需要额外输入（例如未来答案），该条件只能标为 oracle 上界，不得放入主比较。
- 选择器输出必须在读取未来 RGB/depth/pose 之前封存；预测输出封存后才开始 GT 评分。

### 3.2 必须包含的基线

1. `recent-k`：最近时间的 k 条历史；
2. `random-k`：固定 seeds 的随机 k 条，多次重复并保存每次选择；
3. `pose-k`：按相机位姿距离选择；
4. `coverage-k`：按历史几何支持覆盖选择；
5. `confidence-k`：现有模型置信度或 confidence gain；
6. `persistent-memory-k`：已有长期记忆/缓存策略的同容量版本；
7. `utility-only-k`：只按视觉/预测 utility，不用几何风险；
8. `GRC-candidate-k`：仅在风险校准合同通过后运行，包含历史几何风险、校准规则和固定预算。

不能因为某个基线在本机表现差就删除；缺失或不兼容必须列出原因和输入差异。

## 4. 指标、主要预测与 kill criteria

### 4.1 主要指标

- 深度：全 GT 有效域 `AbsRel`、RMSE、`δ1`；记录 missing prediction 数，不通过丢掉困难像素降低损失。
- 长尾：worst-5% 有界误差和 `CVaR95`，同时报告固定分母和 coverage。
- 几何：重投影误差、有效投影覆盖率、遮挡/边界错误率。
- 位姿（若数据有可信 pose）：ATE/RPE 或预先指定的 SE(3) 误差；在协议中固定单位和对齐规则。
- 系统：读取字节、selector 时间、GPU 显存峰值、host memory、前向次数、wall time 和失败样本。

主指标和聚合方式先写入 `PROTOCOL.md`；不得在看到结果后只挑改善最大的指标。

### 4.2 可证伪预测

若“低风险历史更能支持未来几何”成立，应在未见场景中看到：

1. `GRC-candidate` 在相同 k 和相同候选池下，相对 `recent/random/pose/coverage/confidence/utility-only` 的未来 AbsRel 和长尾指标有一致方向的改善；
2. 该改善在至少两个未见场景/轨迹中复现，而不是由单个 target 或 source 身份驱动；
3. 风险分数在 calibration split 固定后仍有 risk–coverage 关系，且不依赖未来深度调阈值；
4. 真实消费者路径中的 source-level 干预效应超过 exact replay 噪声，并落在干预前几何支持区；
5. 结果不会只表现为 RGB MSE 下降而几何误差和重影恶化。

### 4.3 停止条件

出现以下任一情况，应停止 GRC 方法主张并保留结果：

- held-out RGB-D/pose Gate0 失败；
- selector 读取了未来答案，或预测未封存就读取 GT；
- GRC 只在已见开发数据或单一场景有效；
- 相对 confidence/random 的主指标没有稳定正收益，或符号随 cap/聚合规则反转；
- replay 噪声与干预效应同量级；
- 几何支持定位不超过面积/置换基线；
- 与已有公开工作在问题定义、输入、预算和完整消费者路径上实质相同；
- GPU 运行只能得到模型加载/下载成功，没有实际 forward、预测封存和未来 GT 评分。

## 5. 哪些工作本机可完成，哪些必须 GPU

### 5.1 本机（M3 Max 64 GB）可先完成

这些步骤不需要远程 GPU，应在申请服务器前尽量做完：

- RGB-D 时间戳一对一配对、内外参/坐标系/单位检查和深度有效率统计；
- held-out 场景 manifest、SHA-256、分割标签和未来答案隔离测试；
- selector 的离线实现、`k=2/4/8` 合同、固定 seeds 和预算账本；
- cached geometry consumer rerender、重投影/z-buffer 数值复核和 S99/S100 的负结果整理；
- 指标脚本、missing 计入分母、worst-5%/CVaR95 和 pose 单位单元测试；
- 小规模真实模型 smoke test（只确认依赖、输入输出 schema 和单次 forward，不宣称性能）；
- LaTeX/Markdown 报告、实验图表生成、manifest 和迁移包 QA；
- 代码静态审查、冻结文件、独立复算脚本和网络/数据下载的有界探针。

### 5.2 需要学校 GPU（或必须在 GPU 上重新跑）

- 完整 VMem/CUT3R/相关 world model 的多帧神经推理和视频生成；
- held-out 多场景、多查询、多 seed 的同候选池比较；
- 真实 `k=2/4/8` 记忆选择后重新运行生成消费者的主实验；
- GRC 与 recent/random/pose/coverage/confidence/persistent/utility-only 的全套消融；
- 长序列、遮挡后重访、视角大变化和动态物体压力测试；
- 需要多次 forward 的 source-level 反事实干预，以及端到端 RGB、depth、pose 评分；
- 记录 GPU 显存、吞吐、wall time 和多 seed 不确定性；
- 若单卡放不下模型，才考虑梯度/推理切分、量化或多卡；改变精度或并行方式必须作为实验条件记录。

GPU 不能替代数据 Gate0。没有合法 paired RGB-D、K、pose 和时间戳时，服务器上跑出的图片仍不能成为几何验证。

## 6. SSH/服务器准备（不含凭据）

学校服务器主机名、用户名、端口、分区和调度器目前未知，不能编造可直接连接的命令。拿到正式主机信息后按下面顺序执行：

1. **本机打包：** 生成代码 commit、环境版本、协议、数据 manifest、权重身份和 SHA-256 清单；不打包账号密钥、OpenRouter key 或个人信息。
2. **传输前 dry-run：** 先仅传代码/协议/小型 manifest；大型数据和权重使用服务器已有副本并做哈希核对，避免重复下载。
3. **远端环境：** 固定 Python、PyTorch、CUDA、驱动、编译器和依赖版本；执行一个不读 GT 的单样本 forward smoke test，并保存 `ENV_RECEIPT.json`。
4. **作业隔离：** 每次实验使用独立 job 目录和不可变 `FREEZE.json`；用 `tmux`/作业调度器保留 stdout、stderr、退出码、GPU 型号和显存峰值。
5. **断点与重跑：** 长作业按 scene/query/seed 分片；失败分片保留原目录和失败原因，修复后使用新版本目录，不覆盖原日志。
6. **结果回传：** 先回传 manifest、JSON/CSV、日志和低分辨率预览，再回传大体积视频；本机执行 SHA 回读和独立评分。

建议的远端目录结构（主机确定后再替换占位符）：

```text
<remote_project>/
  source/<git-commit>/
  data_manifest/<heldout-manifest-sha>/
  weights/<weight-id>/
  protocols/S101_gpu_freeze.json
  runs/<scene>/<method>/<seed>/
    ENV_RECEIPT.json
    RUN.json
    stdout.log
    stderr.log
    predictions_sealed/
    scores_after_gt/
```

SSH 只用于访问项目所需服务器；服务器权限、队列和数据许可是外部依赖，尚未验证时在账本中标为 `UNKNOWN`。

## 7. GPU 正式实验顺序

为避免只用“S 数字”让新手无法判断工作内容，GPU 阶段使用下面的**实验名称（括号内为 S 编号）**。编号只是账本索引，括号前的名称才是实验要回答的问题：

| 实验名称 | 账本编号 | 目的与进入条件 |
|---|---:|---|
| 未见场景 RGB-D/相机配对资格审计（held-out data qualification） | S102 | 在不运行方法前验证 RGB、depth、K、pose、timestamp、单位和许可；Gate0失败即停止主实验 |
| 跨场景 VMem 长时程几何基线复现（真实神经推理） | S103 | 在新序列跑 proposal 所需的历史到未来预测，确认完整 forward、生成输出和可回读日志 |
| 固定记忆槽位选择对照（same-candidate same-budget memory selection） | S104 | `k=2/4/8` 下比较 recent、random、pose、coverage、confidence、persistent、utility-only；先于 GRC |
| GRC-Memory 风险校准选择实验（geometry-risk-calibrated selection） | S105 | 使用 calibration split 固定风险分数，在 held-out 场景测试未来 RGB-D/pose；结果只按预注册指标解释 |
| 遮挡后重访与视角变化压力测试（occlusion/revisit stress test） | S106 | 检验候选机制是否只在静态近邻有效；要求统一相机轨迹定义和跨场景重复 |
| 源级反事实记忆干预（source-level counterfactual intervention） | S107 | 固定干预前外生条件，替换/删除一条历史来源并自然重算所有下游路径；须先确认 replay 噪声可控 |
| 误差尾部与几何定位分析（tail-risk and support localization） | S108 | 报告 worst-5%、CVaR95、coverage、重投影和干预支持区，防止 RGB MSE 掩盖少数严重几何错误 |
| 多 seed 与效率复核（multi-seed and resource audit） | S109 | 在主结论候选出现后测量不确定性、显存、读取字节、前向次数和 wall time；不以效率单独宣称算法创新 |

1. 本机完成数据 Gate0 和合同静态测试；若失败，先修数据，不提交 GPU 主实验。
2. 远端跑单场景、单 query、单 seed 的真实 baseline smoke test；确认有神经 forward 和可回读预测。
3. 服务器上冻结 calibration/development/held-out 身份、候选池、k、seeds、随机数和预算。
4. 先跑 `recent/random/pose/coverage/confidence/utility-only`，再跑 persistent-memory，最后才跑 GRC candidate；不得用 GRC 结果调回基线。
5. 预测全部封存后读取未来 depth/pose，统一评分并保留每场景、每 query、每 seed 原始行。
6. 对主结果做一次不同实现的独立评分和抽样投影复核；若 reviewer 发现分母、身份或预算不一致，整批降级为诊断。
7. 只有主指标、长尾、几何定位和跨场景都达到预设门槛，才建立方法论文草案；否则把失败转成边界分析或 benchmark/measurement 结果。

## 8. 交付物与记录要求

每个 GPU job 至少保存：

- `PROTOCOL.md`、`FREEZE.json`、`RUN.json`、`ENV_RECEIPT.json`；
- 输入/权重/源码/数据 manifest 及 SHA-256；
- selector 选择、候选池和预算账本；
- prediction seal（含封存时间和 GT 未读取证明）；
- 评分 JSON/CSV、完整分母、missing/invalid 计数、失败列表；
- GPU 型号、显存峰值、读取字节、前向次数、wall time；
- 独立复核报告和所有纠错追踪；
- `RESEARCH_LOG.md`、`RESEARCH_MEMORY.md`、`workflow_checks.jsonl` 的对应条目。

本文件后续若修改，必须建立新版本（例如 S101.1），记录修改时间、修改原因及是否看过旧结果；不能改写已冻结实验。

## 9. 当前决策

当前最重要的不是立即把 S100 重新跑大，而是先获得**合法未见数据 + 完整 RGB-D/K/pose/时间戳**。本机可以把合同、脚本和迁移包准备到可提交状态；完整 VMem 多场景生成和真实记忆槽位预算比较留到学校 GPU。即使 GPU 运行成功，如果数据或预测封存门失败，也只能报告工程运行，不可报告 GRC-Memory 或 proposal 的几何一致性已验证。
