# RAIMA V4 统计与可行性方法评审（只读、source-only）

- 审查时间：2026-09-08 19:20 CST（11:20 UTC）
- 审查对象：`work/S43_paradigm_shift_audit/raima_v4/` 冻结包，`FROZEN_SOURCE_SET.json` SHA-256 `051f06b2a1963cb95cdf50f54648d55d878ed82fe00ee52def2013e71fe75d2c`
- 边界：只读文件与标准库精确算术；未改 V4，未运行模型、launcher 或 Stage C，未读取图片/像素
- 裁决：**计数检验的数学实现内部一致；科学解释与现实执行仍 BLOCKED。V4 可保留为严格模板，不能据此启动 Stage C。**

## 核心核查

| 项目 | 判定 | 依据与后果 |
|---|---|---|
| Null / alternative | **形式上一致，科学对象需收窄** | 对“冻结分类器判定的 scene-positive”定义 `H0: p<=0.20`、`H1: p>0.20`是清楚的；`p=0.50`只是设计功效点，不是已知效应。精确复算得到零假设边界一类错误 `0.0299787823`，`p=0.50`功效 `0.8501148224`。但 `p=0.40`功效仅 `0.5617`、`p=0.30`仅 `0.2153`，所以它只对很高流行率有足够把握，阴性不能说明现象不存在。|
| 两阶段规则 | **正确但保守** | `n1=10`、阳性数 `<=2` 停止，最大 `N=20` 且总阳性数 `>=8`，标准库枚举与冻结值一致；早停未膨胀一类错误。当前 scene rate 只能取 `0, 1/2, 1`，因此 `count>=8`已经推出总体均值与 LOSO 两个条件；所谓“复合 gate”在 V4 实际等同一个两阶段计数 gate。二者可留作防版本漂移的断言，但不能宣传为三重独立稳健证据。`count_power_upper_bound`字段名与同文件“在精确 roster 下为 exact”的文字也应在未来版本统一。|
| 复合 endpoint | **操作性 union 可检验，潜在构念未识别** | 两条轨迹、每条一个 unit、每个 unit 对 AOIG/SEM/RCSU 取 OR，回答的是“六个预定义机会中至少一个触发”，不是统一 memory-quality 量。队列层面的 `alpha`只控制该已分类 scene event 的计数检验，不校准三个测量器本身的误判。反例：若六个 endpoint-opportunity 在“无真实异常”时各有独立 4% 假阳性，scene union 假阳性率已达 `1-0.96^6=21.72%`。因此通过只能先称“注册测量器阳性普遍”，除非另有盲负控证明 AOIG/SEM/RCSU 的联合特异度。|
| 独立单位与 20-scene 抽样 | **单位选择正确，抽样总体未成立** | scene 作为独立单位、seed 仅作 paired technical repeat、trajectory 嵌套 scene，均合理。问题是候选 registry 尚未建立；公开固定 hash seed 对一个后来组装的便利 registry 不自动产生概率样本。若目标是冻结 registry 的有限总体，无放回抽样更适合有限总体/超几何推断；若目标是更广的 physical-scene 超总体，则需说明 registry 如何覆盖该总体并支持 exchangeability。现有“假设失败就只报 roster 描述”诚实，但此时二项 p 值和广泛 prevalence claim 都必须撤回。|
| 缺失与功效 | **防偏倚但极脆弱** | 任一 scene 缺 endpoint/reference 就使全 cohort `BLOCKED`，避免了 complete-case 偏倚，却使报告的功效严格条件于 20/20 全部可评价。若单 scene 完整率仅 95%，20 个全完整的概率只有 `0.95^20=35.85%`；当前本地三-reference资格率实际为零。因此 `0.8501`不能当现实无条件功效。|

## 三张 ±10 ms reference 的必要性

“至少三张且在 ±10 ms”是项目自定稳健性合同，不是识别 pairwise conditional risk 的普遍必要条件。对一个在任何输入、memory、conditioning 和 replacement roster 中从未出现、且相机/姿态/内参/状态/曝光/有效域均已冻结校准的真实 target capture `R`，预先定义

`Delta_R = loss(Y_original-reinsert, R) - loss(Y_matched-replacement, R)`

即可识别**这一个 scene-target-camera-time-reference 条件下**的成对风险差。它不能识别跨时间、跨视角或“真实世界反事实”的期望风险，也不能排除共享的姿态误差、warp、曝光、传感器噪声、遮挡和状态漂移。

三张 reference 可作为抗单帧偶然误差的稳健性面板，但只有在 reference 来自预定义分布、依赖性被披露且聚合规则固定时才增加证据。V4 的“多于三张就全部纳入、每张同号”还让不同 scene 的判定难度随 reference 数变化：若单张同号概率为 0.9，三张全同号概率为 0.729，五张降至 0.590。这会破坏 scene 间可比性，并不能消除共同系统偏差。本机 TUM 单 RGB 流任意闭 20 ms 窗口至多一张，故无法实现 V4 的三张合同；同一 `rgb.txt` 的两个路径也不能当两个视角。

## 算力与执行可行性

最小 Stage C2 为 5,600 个 target process，乐观串行 `90.53` 天；expanded 为 `140.46` 天。即使真阳性率为设计点 0.50，早停后的最小期望仍为 `88.06` 天。现有本机安全并发为 1、无远程 GPU，且这些数字还未计失败、reference metric、I/O 和审查，所以 **Stage C 当前不可执行**。若要求 30 天内结束，最低估算也需约 `3.02x` 的审计后吞吐；14 天约需 `6.47x`。一 seed 的 Stage D `10.86` 小时尚可做 hook、运行时和失败率否证，但没有确认性效力。

## 不改 V4 的低成本后续设计

1. **保留 V4 原件为严格三-reference稳健性版本。** 在查看任何新 Stage C 输出前另建 V5：primary 改为“一张校准、never-conditioned 的真实 target reference”所定义的 conditional pairwise risk；不降低现有 effect floor、seed、matched-zero、positive/negative/replay/placebo 控制。
2. **把额外两张以上 reference 注册为 secondary robustness。** 固定 result-blind 数量或使用 scene 内聚合，逐张全报且不得用来挽救 primary 失败；共享偏差仍由 reference-negative、pose/warp residual、曝光/色彩和 state-lock 证据处理。
3. **先做 metadata-only 可行性。** 在不生成模型输出的情况下，冻结至少 40 个独立 cluster 的 registry、reference泄漏检查和采样顺序；registry 封存后再用外部不可预知随机种子抽 20，或明确改成有限总体推断。
4. **只做最小 Stage D 工程否证。** 测一 seed 的真实 arm 时间、失败率和 snapshot equivalence；若不能取得审计后约 3x 以上吞吐，停止 Stage C。任何缩减 scene/seed/arm/control 都必须形成新的统计版本，不能沿用 V4 的 `alpha/power` 或在见效应后改门。

最终允许的科学表述是：V4 提供了一个条件于完整测量、exchangeable scenes 和精确分类器的保守 prevalence gate。它尚未建立可抽样总体、可用 reference roster、联合测量特异度或可承受算力，因此不授权现象、方法、创新或 Stage C 执行。
