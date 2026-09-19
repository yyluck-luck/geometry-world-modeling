# RAIMA V4 source-only 统计冻结候选

- 建立时间：`2026-09-08T10:26:18.197619+00:00`
- 作者角色：`/root/c2_generation_builder`
- 状态：`SOURCE_ONLY_CANDIDATE_PENDING_FRESH_NON_AUTHOR_REVIEW`
- 方法状态：`NO_METHOD_SELECTED`
- 新颖性授权：`NONE`
- 模型运行：`0`
- Stage C scene/data roster：`0`
- Stage C arm：`0`
- 图片或像素读取：`0`
- 执行授权：`NONE`

## 1. 这一版解决什么

V3 的独立审查保留了 AOIG、SEM、RCSU 三个谨慎的操作性量，但阻止直接进入确认实验。原因是 V3 的主分母、consumer/edit 合并、reference 缺失、scene 抽样、功效和计算预算没有形成唯一实现。

V4 把这些决定收成一个 source-only 包。它不生成数据，而是先固定：

1. 三个 estimand 各自测什么和不能说什么；
2. primary endpoint 从 typed receipts 到 scene gate 的唯一纯函数；
3. 20 个独立 scene 槽位、每 scene 两条轨迹、每轨迹一个 primary source-target 的选择规则；
4. 10-scene futility check 加最大 20-scene 的两阶段设计；
5. reference 合同当前因 S48 V6 被否决而保持 fail-closed，等待 fresh-reviewed S48 V7；
6. 唯一 confirmatory hypothesis 与有限的 descriptive registry；
7. 本机计算量和不能删控制的边界；
8. 2024 至 2026 年最直接近邻与已被占据的宽泛主张。

## 2. 被保留且不得修改的上游文件

- V3：`../INNOVATION_NORTH_STAR_V3.md`，SHA256 `f0e5893ad4892f11f36641476f8858ca9347db4075b35b32faf5beaf4ce102aa`
- V3 fresh review：`../INNOVATION_NORTH_STAR_V3_ADVERSARIAL_REVIEW.md`，SHA256 `6482266ea27dbdca110531725ec1613b1204a54a4b7e59c30cf2a46efb9a4599`
- 计算可行性：`../RAIMA_V3_COMPUTE_FEASIBILITY.md`，SHA256 `c762be650a7cd91405a8a2b04992b8ef9a2f27100dc2e0146c6b9c3d8b49eebe`
- 第一碰撞补充：`../RAIMA_V3_LIVE_COLLISION_ADDENDUM_2026-09-08T1002Z.md`，SHA256 `91c300c4365dbae1ea0715d159b1248c88cf159e2949e7aa13267a9e0ec77550`
- 第二碰撞补充：`../RAIMA_V3_LIVE_COLLISION_ADDENDUM_2026-09-08T1018Z.md`，SHA256 `7885ff52ba98ad3db3aa7430de714acb8da9da1d03bc33bcfbb1224246efafdd`

V4 是新版本，不回写 V3 或其审查。任何 V4 文件改动都使本目录后续冻结回执失效。

## 3. 冻结包文件

| 文件 | 作用 |
|---|---|
| `ESTIMAND_TABLE.json` | treatment、outcome、unit、eligibility、解释边界 |
| `primary_endpoint_reference.py` | 标准库唯一 primary 聚合和两阶段概率函数 |
| `test_primary_endpoint_reference.py` | 边界、缺失、重复、聚合和随机性质反例 |
| `SCENE_SAMPLING_MANIFEST.json` | scene/trajectory/seed 槽位与 metadata-only 选择规则 |
| `POWER_AND_SENSITIVITY.json` | V3 低功效、V4 两阶段边界、精确概率和假设 |
| `REFERENCE_CONTRACT_BINDING.json` | S48 V6 BLOCKED 证据及等待 V7 的 fail-closed 绑定 |
| `FINITE_HYPOTHESIS_REGISTRY.json` | 一个确认性主假设和有限 descriptive endpoints |
| `COMPUTE_MANIFEST.json` | arm 公式、串行天数、资源门和停止规则 |
| `NOVELTY_MATRIX.md` | 强近邻、禁止主张、未来必须胜过的对照 |
| `FROZEN_SOURCE_SET.json` | 上述源文件的 exact SHA 集；只在双解释器测试后创建 |
| `SOURCE_ONLY_TEST_RECEIPT.json` | 双解释器结果与证据边界；不授权真实执行 |

## 4. 唯一主分析

每个 scene 有固定两条轨迹：`return_short` 和 `return_long`。每条轨迹只有一个 primary source-target unit：目标 checkpoint 由路线在结果前固定；source 是 ordinary selector 的 rank-1 稳定 source ID。排序只使用运行 trace 元数据，不使用生成图像、reference loss 或 endpoint 结果。rank-1 source 若没有完整 Address 证据，保留 `FAIL/MISSING`，不换成下一个 source。

每个 access-pass unit 必须从未来合法 S48 V7 得到三个完整状态：

- `AOIG`：是否满足 operationally insensitive 的完整合取；
- `HARMFUL_SEM`：是否满足 raw matched-zero support mismatch 加独立 reference harm veto；
- `NEGATIVE_STABLE_RCSU`：是否在完整 reference roster 上得到稳定负的 comparator-relative utility。

任一个 endpoint 阳性，该 unit 的 union 只计一次。任何 technical missing、reference ineligible、access failure 或 access missing 都使整个 scene 不可评价，并使确认 gate fail closed。没有 complete-case 删除，也不能替换 scene、trajectory、source、target 或 seed。

每个 scene 的 rate 是两条轨迹 unit 指示量的等权平均，因此只可能为 `0`、`1/2`、`1`。scene-positive 阈值仍登记为 `1/5`，在这个有限 roster 中等价于“两条轨迹至少一条阳性”。这项离散含义必须在结果中直接写出，不能把 `20%` 描述成高精度连续比例。

## 5. 两阶段规则

- Stage C1：10 个确认 scene。若阳性 scene `<=2`，以 `STOP_CONFIRMATION_FOR_FUTILITY` 停止；若 `>=3`，继续收集预先登记的另外 10 个 scene。Stage C1 永不产生 efficacy success。
- Stage C2：总计 20 个 scene。只有阳性 scene `>=8`、20-scene 等权平均 rate `>=1/5`、所有 leave-one-scene-out mean `>=3/20` 且 20 个 scene 全部可评价时，才通过 composite gate。
- Stage D 不属于这 20 个 scene，不能修改阈值、endpoint、seed、sampling frame 或 continuation rule。

在当前固定的每 scene 两个二元 unit 下，8 个阳性 scene 已保证总体 mean 至少 `1/5`；由于每个 rate 不超过 1，也保证最小 leave-one-out mean 至少 `3/19 > 3/20`。仍保留三项显式检查，以防未来 roster 变化时旧代码静默沿用。若 roster 改变，必须新建版本并重新做 power review。

## 6. 因果和干预边界

- primary intervention 只允许未来 S48 V7 注册的 in-distribution、source-coherent matched edit/replacement；zero dose 必须走同一路径。
- source drop、zero-source、scramble、token deletion 或 layout 改动可能是 OOD，只能作 stress test，不能进入 AOIG、SEM 或 RCSU 主 estimand。
- intervention-validity 必须绑定 source 数量、shape、layout、position、RNG、consumer 输入、分布偏移统计和 positive/negative/placebo controls。
- total-effect 只固定干预前外生条件和非目标初态；目标 source 的所有下游 descendant 必须重算。
- 当前 S48 V6 已被 fresh review 以 3 CRITICAL、4 MAJOR、2 MINOR 阻断，因此本包没有 active reference/endpoint executor。

## 7. 执行前必须依次关闭的门

1. S48 V7 exact source set 通过 fresh non-author review；
2. 本包更新为绑定该 exact V7 hashes 的新冻结版本并重新 fresh review；
3. 20-scene sampling frame、metadata roster 和独立 cluster 身份冻结；
4. 真实 arm 计算预算与资源到位；
5. C1/C2 合法 baseline、相机和质量门关闭；
6. blind execution/analysis 计划另行授权。

当前缺任意一门都不得创建 Stage C data、arm、execution 或 result。

现有本机数据还触发了更具体的门。只读 metadata 报告 `/Users/rocket/Documents/Codex/2026-09-05/users-rocket-desktop-hkust-it-ip/work/resumption_20260908/reference_time_feasibility.json`（SHA256 `02dd1b304fc9e84bc4f99cd3b3ccfcf0fdee0685f7f14907edaa21959e07c8eb`）显示：TUM `fr1_xyz` 与 `fr2_desk` 的 published RGB timestamps 在任一闭 20 ms 窗口内最多各有 1 个 capture，没有 target 能得到当前 S48 同步合同要求的至少 3 个其他 reference；`fr2_desk` original/guarded 的 `rgb.txt` SHA 相同，不能算两个视角。因此它们不能填充当前 `STAGE_C_DATA_ROSTER.json`。这只是否决这两条 single-RGB streams；没有读取像素，也没有检验 clock calibration、多同步传感器、新数据集或另行预注册的静态场景合同。
