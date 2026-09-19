# S42：S40 真实 baseline 自然回访失败预注册与最小测量协议

预注册时间：2026-09-07T14:12:20+08:00。状态：**已冻结设计，尚未执行**。本协议没有加载模型、没有读取尚未产生的数组、没有查看 S40 或任何聚合替代输出，也不批准启动生成。

## 给新手的一句话

相机先向左看，再回到原方向。我们现在先把“考哪几张图、看哪块区域、怎么算、多少算严重失败”写死，之后才看结果。这样就不能看到某个坏画面后临时挑它来证明想法。

## 1. 唯一研究问题与证据边界

**RQ-B0：** 在保持 S40 原始两批流程、组件变体和随机条件不变时，模型回到起点相机条件后的最终图像，是否在预先固定的外侧背景区域出现可重复的严重 RGB 漂移？

这里只检验一个**自然 baseline 现象**：所有聚合仍用 VMem 原源码，不能插入 zero-CLIP、nearest、medoid、weighted mean、attention、router 或任何其他替代。即使判为失败，也只能写成“该具名组件变体在该预注册小样本上出现严重回访 RGB 差异”。它不能证明 CLIP mean 是原因，不能证明记忆模块是原因，也不能证明创新。

S40 的 `changi`、seed 42 是开发筛查行。为了不把一次随机坏样本当作稳定现象，本文现在同时冻结两个 baseline-only 确认行；在三行完成前不得查看任何聚合替代输出。两个确认场景从同一 VMem `test_samples` 目录中排除 `changi` 后，按原图像素总数从大到小机械选前两名；没有依据生成结果或人工偏好选图。

| 行 | 角色 | 输入与 SHA-256 | 原尺寸 | seed | 轨迹 |
|---|---|---|---:|---:|---|
| B0 | S40 开发筛查 | `changi.jpg`; `12fc2c4ddfccee952d5390b147b813a8f062209832ec675013f82283e796e54a` | 3648×2736 | 42 | `initialize → turn_left(5) → turn_right(5)` |
| C1 | baseline-only 确认 | `jesus.jpg`; `d611976bb9d3e8d6e1740b86ead24028bfd7857944eba118458e09e7e645f3e1` | 1702×1276 | 43 | 同上 |
| C2 | baseline-only 确认 | `living_room.jpg`; `e9d718849d2ddbe5dda7ed3fa80df7d93e99f2d509b07a46019818c2e188d278` | 1588×958 | 44 | 同上 |

C1/C2 不是当前 S40 manifest 的一部分。它们只能由后续另行冻结、另作者前审、独立目录的 baseline 执行实现；不能直接改 S40 已冻结 worker 后偷偷运行。若资源只够 B0，结论必须停在“单场景筛查”，不能写“稳定失败”。

## 2. 每行不可改变的生成条件

三行均使用同一具名系统：`VMem + stabilityai/sd-vae-ft-mse`，VAE revision `31f26fdeee1355a5c34592e401dd41e45d25a493`。它不是 exact-original VMem。除输入和 seed 按上表变化外，全部沿用 S40：CPU、FP32、8 线程、576×576、T=8、context=4、target=4、50 sampling steps、默认 NMS、`step_size=0.1`、每次动作 4 个插值帧、Surfel global alignment 400 iterations、lr=0.01；两批处于同一个 fresh worker 和 pipeline 中，批间不重置 RNG。

每行都必须形成 9 个历史 ID，且按“左为正角”解释：

| ID | 身份 | 计划 yaw |
|---:|---|---:|
| 0 | 唯一真实输入，经固定 center-crop/area-resize 转为 576×576 | 0° |
| 1,2,3,4 | 第一批生成 | +1.25°, +2.50°, +3.75°, +5.00° |
| 5,6,7,8 | 第二批生成 | +3.75°, +2.50°, +1.25°, 0° |

主比较永远是 `(ID0, ID8)`。不得改成“最坏的一帧”或“最好看的一对”。生成—生成的同条件配对固定为 `(ID1,ID7)`、`(ID2,ID6)`、`(ID3,ID5)`；ID4 没有独立回访配对。

## 3. 固定 ROI

所有坐标都定义在归档后的 576×576 RGB 网格上，采用 Python 半开区间 `[y0:y1, x0:x1]`。唯一主 ROI `M_outer4` 是四个互不重叠的 192×192 方块的并集：

- R1 `[0:192, 0:192]`
- R2 `[0:192, 384:576]`
- R3 `[192:384, 0:192]`
- R4 `[192:384, 384:576]`

该掩码在看到任何生成输出前固定。它在 B0 中避开中央瀑布和底部人群这两类可能运动的内容；同一坐标不经人工调整地用于 C1/C2。不得移动、膨胀、腐蚀、配准或按输出显著性重画 ROI。四块逐块分数和全图分数可以作为诊断附表，但均不得替代主判据。

## 4. 唯一主判据

从已经通过独立归档审查的 `pipeline.pil_frames` 取 ID0 和 ID8，统一执行 PIL `convert("RGB")`，再以 `uint8 → float64/255` 得到 `I0,I8 ∈ [0,1]^(576×576×3)`。不做几何配准、裁边、直方图匹配、颜色校正、超分辨率或感知特征选择。

对 `M_outer4` 的全部像素与 RGB 通道先合并求均方误差：

`MSE_M = mean((I8 - I0)^2 | pixel ∈ M_outer4)`

再计算：

`ReturnPSNR_M = 10 log10(1 / MSE_M)`；若 `MSE_M = 0`，记为 `+∞`。

**唯一最终判据：三行 B0/C1/C2 均技术有效时，以未四舍五入的 float64 `MSE_M > 0.01` 作为单行严重漂移事件；三行中至少两行发生该事件，记为 `CONFIRMED_SEVERE_RETURN_RGB_DISCREPANCY`，否则记为 `NO_CONFIRMED_PREDECLARED_FAILURE`。** 这与 `median(ReturnPSNR_M) < 20.0 dB` 完全等价。`MSE_M = 0.01`（PSNR 恰好 20.0 dB）不算失败。20 dB 等价于该 ROI 的合并通道 RMSE 大于 0.10，是事前固定的“明显漂移”工程筛查线，不是领域公认阈值，也不能检测所有细微失败。MSE 是判定用的权威表示；PSNR 只把同一数值单调换算成更熟悉的 dB，不构成第二主指标。

三行必须按 B0→C1→C2 全部完成，不能根据 B0 的好坏提前停止确认行。单独 B0 可以作为进度记录，但不能产生科学终态。不得用新场景替换无效、不支持假说或“不够明显”的行。

## 5. 主判据之前必须通过的守卫

以下是有效性守卫，不是额外主指标。任一守卫失败时，该行记为 `INVALID_OR_UNINTERPRETABLE`，三行总判定保持 `INCOMPLETE`；不得删除该行后在剩余行上取中位数。

1. **身份、尝试与执行守卫。** 组件、输入、seed、源码、参数和唯一执行目录须由各自行前冻结 manifest 与 SHA 绑定；旧失败目录保留。每行的**首个技术有效 attempt** 是唯一科学结果。只有客观的异常、超时、部分封存或下列守卫失败才能重试；有效完成后禁止再次运行同一行挑选更好结果。重试须保持冻结条件、使用新目录并报告全部 attempts；任何源码、权重或参数变化都必须成为新协议。
2. **两批历史消费守卫。** 历史必须为 1→5→9；另一作者必须逐数组核第二批实际读取的生成历史 cache 与第一批已提交的 `samples_z`/相应元数据一致。仅有 `ID>0`、PNG、退出码 0 或 history=9 不够。
3. **相机条件闭环守卫。** 权威计划相机只取 full archive 中 `capture_complete(name="batch_input")` 的两个 occurrence：第一批 `target_c2ws[:4]`/`target_Ks[:4]` 对应 ID1–4，第二批 `target_c2ws[:4]`/`target_Ks[:4]` 对应 ID5–8；第一批三个 padding 位不分配 ID。它们还须分别与 `cache_commit` occurrence 0 的 `cache.c2ws/Ks[1:5]`、occurrence 1 的 `[5:9]` 逐值交叉核。计划 yaw 序列从 ID0 的原 c2w 左乘 Y 轴旋转推导，矩阵元素最大绝对误差须 `≤1e-6`；ID8 与 ID0 的原 c2w/K 也分别须 `≤1e-6`。`condition_input` 的 c2w 已经过 `get_translation_scaling_factor` 居中；`condition_output.all_c2ws` 与 `sampler_input.inputs.c2w` 还经过 `get_cond` 的轴翻转和尺度变换，对应 K 则随接口归档但未做同样的 c2w 坐标变换。这些字段只能按冻结源码公式交叉核，禁止直接拿它们与计划矩阵混比。不满足则记 `NO_VALID_REVISIT`，不算回访失败。
4. **权威像素与图像身份守卫。** ID0/ID8 和全部诊断配对只取 full archive 中第二个 `capture_complete(name="cache_commit", occurrence=1)` 的 `cache.pil_frames[id].pixels` tensor blob；禁止在 PNG 容器、`navigator_return` 快照、live PIL 对象或其他 cache occurrence 之间任选。按冻结 archive codec 解码后，权威 dtype/shape 必须是 `uint8[576,576,3]`。`M_outer4` 恰有 147456 个像素、442368 个 RGB 标量；用这些标量的 float64 和累加/求均值，保存未舍入 MSE、由它换算的未舍入 PSNR、像素数、tensor descriptor SHA、blob SHA 和评分脚本 SHA。若 9 个 ID 映射或 SHA 不齐，任一帧不是有限 576×576 RGB，或归档别名造成 ID 错配，记技术无效。
5. **复制捷径守卫。** 条件矩阵的外出角确实非零仍只证明“请求了移动”。若 ID1–ID8 的 canonical RGB SHA 全部等于 ID0，或 8 张生成图彼此全部逐字节相等，记 `DEGENERATE_COPY/CAMERA_CONTROL_UNRESOLVED`；高回访相似度不能当成功。
6. **盲评分顺序。** 先由固定脚本只按 ID 和 ROI 生成机器可读分数回执，再允许人工打开生成图或九帧拼图。评分者不能先看图后决定 ROI、阈值、配对或要不要保留某一行。

## 6. 四类证据必须分开报告

| 类别 | 本协议如何测 | 可以说什么 | 不能说什么 |
|---|---|---|---|
| **真实参考 RGB** | ID0 是起点的真实观测；实际 c2w/K 闭环后，ID8 在同一 576 网格的固定 ROI 与 ID0 计算主 PSNR | 该返回端点与真实起点观测相差多大 | 不能称深度 GT、完整 3D GT、动态物体 GT 或整段视频 GT |
| **无 GT 配对一致性** | 固定报告 `(1,7),(2,6),(3,5)` 在同一 ROI 的 PSNR，逐对列原始值 | 两次生成的同相机条件是否彼此一致 | 两张图都可能一致地幻觉；不能代替 ID0/ID8 主判据，也不能证明几何正确 |
| **相机服从** | c2w/K 数值检查只证明输入条件被正确请求；九帧条件序列与外出/返回顺序完整报告 | 执行和条件轨迹是否闭环 | 它不证明画面真的按照相机运动。当前没有冻结的独立真实相机 GT；因此任何 RGB 差异先记为“相机原因未解决”，不能直接叫 memory failure |
| **视觉质量** | 所有九帧按 ID0→ID8 固定排成一张图；逐帧报告缺失、常量/空白、饱和、撕裂和明显重复，不能只挑代表图 | 是否存在全局生成崩坏或复制退化 | 这是全序列 QA，不得替换主 PSNR，也不能用“看起来不错”推翻数值失败 |

若将来增加 SIFT、CUT3R/VGGT、LPIPS、NIQE、人工偏好或其他相机/质量评估器，必须在看 A0–A5 之前另行冻结模型/权重/版本、输入、阈值和失败处理。预测深度、预测位姿或 learned perceptual score 都必须标为代理，不得重命名成真实 GT。**在独立画面相机服从代理尚未冻结并通过前，即使唯一主判据成立，状态也只能是 `RETURN_RGB_DISCREPANCY_CAMERA_CAUSE_UNRESOLVED`，不得进入 S41 的 A0/A1 memory-consumer 归因。** 若全局空白/撕裂等视觉崩坏解释了差异，也应先归为视觉质量失败，不能拿它支持 memory-consumer 假说。

## 7. 结果状态与下一步

| 状态 | 条件 | 唯一允许的下一步/结论 |
|---|---|---|
| `INCOMPLETE` | B0/C1/C2 任一行尚未运行或技术无效 | 只说协议已冻结或执行未完成；无科学终态 |
| `INVALID_OR_UNINTERPRETABLE` | 任一身份、cache、姿态、归档或复制守卫失败 | 保留失败，修技术/相机问题；不能进入聚合实验 |
| `NO_CONFIRMED_PREDECLARED_FAILURE` | 三行均有效，但不足两行满足 `MSE_M>0.01` | 当前窄假说停止；不得移动 ROI、改阈值或另挑输出救回它 |
| `RETURN_RGB_DISCREPANCY_CAMERA_CAUSE_UNRESOLVED` | 三行均有效且至少两行满足 `MSE_M>0.01`，但独立画面相机代理尚未冻结/通过 | 只确认最小样本上的严重返回 RGB 差异；不能进入 A0/A1，不能归因于 memory 或 mean |
| `CONFIRMED_SEVERE_RETURN_RGB_FAILURE_CAMERA_GUARD_PASS` | 上一行成立，且另行预注册的画面相机服从代理通过，视觉质量崩坏也不是解释 | 才可按 S41 先做 A0 exact replay，再做 A1 通路影响门；仍不能直接归因于 mean |

任何普通聚合臂改善后都先成为更强 baseline。该协议本身不是方法、贡献或创新证据。

## 8. 固定报告表

每行必须输出一行，不得只报均值：

| row | attempt | input_sha | seed | execution_sha_set | cache_readback | pose_K_guard | ID0_pixels_sha | ID8_pixels_sha | n_pixels | **MSE_M_raw** | ReturnPSNR_M_dB_raw | R1–R4_dB | pair_1_7/2_6/3_5_dB_noGT | visual_QA_all9 | camera_proxy | status |
|---|---:|---|---:|---|---|---|---|---|---:|---:|---:|---|---|---|---|---|

聚合替代实验若以后获准，必须复用每行相同输入、seed、实际 noise tensor、历史 IDs/顺序、pose/K、sampler 和主评分代码；所有逐行原始结果先保存，随后才算汇总。

## 9. 依据

- 原 proposal：先稳定刻画相机运动、遮挡/再观察等条件下的 baseline 失败，再根据最重要失败设计机制，并分开评价视觉质量、几何保真与时空一致性。
- S40 协议与源码前审：固定两批连续生成、1→5→9 历史、seed/RNG、完整 cache trace 和具名 VAE 变体边界。
- 当前 S41 根审：Gate 0 必须先冻结自然失败、场景、轨迹、seed 和目标区域；A0 exact replay 与 A1/A2–A5 只能在此之后；输出影响、目标失败相关性、改善方向、相机/质量代价不能混为一谈。
- Supervisor-Skills，固定 commit `207bc6f7a1aa107e544099c2c7cc86816fba9628`：[`2.2 想 Idea 的思路`](https://github.com/HKUSTDial/Supervisor-Skills/blob/207bc6f7a1aa107e544099c2c7cc86816fba9628/handbook/02_Idea_Generation/2.2_%E6%83%B3Idea%E7%9A%84%E6%80%9D%E8%B7%AF_%E6%9B%B4%E9%AB%98%E6%9B%B4%E5%BF%AB%E6%9B%B4%E5%BC%BA.md)要求从强 baseline 的失败与根因出发，而不是拿方案找问题；[`Experiments`](https://github.com/HKUSTDial/Supervisor-Skills/blob/207bc6f7a1aa107e544099c2c7cc86816fba9628/skills/benchmark-paper-template/references/experiments.md)要求按 RQ 冻结输入、输出、指标、重复和一个 headline metric。

本文件只完成“看结果前把规则写死”这一步。
