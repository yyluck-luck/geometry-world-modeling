# S40 → readback → B0 盲评分执行准备审计

- 初始审计时间：2026-09-07T12:11:41Z；真实 readback 终态更新：2026-09-07T12:19:47Z
- 审计者：`/root/vmem_recovery_diagnosis`
- 当前裁决：**BLOCKED_BY_READBACK_REPRESENTATION_BUG_AND_UNREVIEWED_SCORER**
- 边界：本审计只读了协议、源码、冻结 manifest 和小型身份/失败回执；没有打开、解码、导入或评分任何 S40 图片、PNG、tensor/result array，也没有运行评分器、模型、生成器或 gate。readback 由根任务独立启动，本审计者不是执行者。

## 1. 新手先看这一段

S40 的两批真实生成已经有一个成功终态回执，但首次 readback 在读取权威像素以前失败了。失败原因已经定位到保存格式的表示差异：第一批 `context_time_indices` 在冻结 pipeline 中是 Python 列表 `[0]`，归档后仍是列表；旧 readback 却把它当成带 `blob` 字段的单一 tensor descriptor。这是 readback 软件错误，不是模型失败，也没有产生 B0 数值。必须先修复并重新审查 readback，随后才能运行只输出 JSON 数字、完全不显示图片的 B0 评分器。

B0 的问题很窄：返回起点后的 ID8，在事先固定的四个外侧方块中，与真实起点观测 ID0 的 RGB 均方误差是否严格大于 `0.01`。B0 只有一个场景，所以无论数值多大，都不能称为“稳定失败”；C1、C2 尚未完成。归档 c2w/K 只能证明模型收到了外出再返回的相机条件，不能证明画面真的服从相机。当前没有冻结的画面相机服从代理，因此 B0 即使触发阈值，也只能记为“返回 RGB 差异，相机原因未解决”，不能进入 A0/A1，更不能归因于 memory 或 mean。

## 2. 可执行性清单

| 项目 | 当前状态 | 身份/含义 | 是否阻断 B0 评分 |
|---|---|---|---|
| B0 原预注册 | 已冻结并获独立回归 PASS | `PROTOCOL.md` SHA `89fb44e0b77a85a66fe611cd2f885fed0288229cbb027e04da25fc0631507b3f`; `receipt.json` SHA `5336c838de1714a6ab1f65be56312d21148d9dc6114162a7ee59497f3bbb2cf7` | 否 |
| S40 B0 manifest | 已冻结 | `review_attachment_01/manifest.json` SHA `9951a78909a7d792dd536cea067c14e369cff776115a078d2f61c66c085cdebe` | 否 |
| S40 生成终态 | 已有成功 pending-review 终态 | `execution_01/receipt.json` SHA `4c771df1e46f96e218b92f01339b55ebd056ef002fdc28e0083a5bb0907300d4`; worker SHA `a564a67e63036b3195390b5059476c1729c99e74bb0a8fe0ef26e0c1211b4911`。本轮仅从独立监督器源码审查的小型 metadata 记录复核状态，未读生成结果。 | 否；仍须 readback |
| readback worker v2 | 源码曾获独立 PASS；真实 attempt 01 发现其运行表示错误 | `readback.py` SHA `4c7a4208c4a67b003bae7b5574b48ce44d6034797bf2e9c5ab021e4d04e4cbf6`; failed receipt SHA `4b762c3061d395a6767f319a553e681dbea8fe4d90bd49e5ac8a563d36bf35c6`; `TypeError: list indices must be integers or slices, not str` at line 273 | **是：必须修复、换 SHA、再审** |
| readback 外控 attempt 01 | 已真实运行并正确保留失败 | supervisor `c86c3f96e5c7b4b6827037c358780479aeb3c1dea10ea9b2cd9a4c2ca6ff8cad`; protocol `bb11b68280268e1a63c4dc6f06561937e112db1bf795a2e4b19ba3393bdd7aaf`; source review `7026d4ce8c7eb8c8f5cf551b4b947f6c7847715373566c0f4451c11535755597`; terminal receipt `f269dc2486478e65176c38445ab97251f31a5a4ac6c9f50cbd344a73daefd5da`; status `FAILED_OR_PARTIAL_SUPERVISED_S40_READBACK`, rc=2；源/输入/worker identity stat 在关闭时未变 | **是：不能同法重跑** |
| readback 结果独立审查 | 不存在 | 必须绑定 supervisor receipt、worker receipt、report、manifest 的实际双 SHA，且确认审查前未查看图片 | **是** |
| `M_outer4` | 原协议已冻结；新增机器合同和实现尚未审查 | 当前 draft contract SHA `a5bba67105180d49b8767ae61e943c51959c9f4d553fa0235bd9d836344d4cb8`，仍绑定失败的旧 readback worker | **是：readback 修复后须 rebase 再审** |
| B0 盲评分器 | 已准备 draft、AST 可解析、从未 import/运行 | 当前 draft `score_b0_blind.py` SHA `6cb18e5f3d97f106861086a3f68acbd7962916314ae19610328c8e2d7dae16ec`，会拒绝未来修复后的 readback SHA | **是：当前版本禁止执行/签 PASS** |
| 评分前盲态入口 | 模板已准备；真实声明不存在 | template SHA `4ee45ec3f800907afd0a9a405fcaab606c0d2a5173e76bc231c1e418d4a5fd8b`；模板本身不会被评分器接受 | **是** |
| 请求相机条件 guard | 评分器已实现、尚未审查 | 只查两个 `batch_input` 的 retained targets、对应 `cache_commit` 行、计划 yaw 和 ID8→ID0 c2w/K 闭环，容差 `1e-6` | **是：随评分器源码审** |
| 画面相机服从 proxy | **不存在，未冻结** | 没有冻结模型/版本、输入、方向、阈值、失败处理或源码 | 不阻断 B0 数值筛查；**阻断 memory 归因和 A0/A1** |
| 九帧人工视觉 QA | 入口由原协议定义，但当前禁止执行 | 必须在机器评分 receipt 封存后按 ID0→ID8 全部查看，不得挑案例 | 不阻断先评分；阻断视觉质量解释 |
| 统计确认协议 | 校准阶段 PASS，确认阶段 REVISION_REQUIRED | 尚缺 SESOI、replay tolerance、camera/quality margin、场景/episode/seed/replay 数量与 power/precision simulation | B0 可作开发筛查；阻断确认性主张 |

真实 attempt 01 已生成并必须保留 `supervision_01/` 与 `executed_01/`。前者只有外控证据和失败 receipt；后者只有失败 receipt，没有 `report.json`，也没有任何 result-review 文件。因此目前不能运行 B0 评分。

## 3. 冻结输入与唯一评分规则

### B0 输入

- 场景：`changi.jpg`，SHA `12fc2c4ddfccee952d5390b147b813a8f062209832ec675013f82283e796e54a`。
- seed：`42`。
- 轨迹：`initialize → turn_left(5) → turn_right(5)`；两次动作各保留 4 个插值帧。
- ID/yaw：`0/0°, 1/1.25°, 2/2.5°, 3/3.75°, 4/5°, 5/3.75°, 6/2.5°, 7/1.25°, 8/0°`。
- 权威图像：full archive 中 `capture_complete(name="cache_commit", occurrence=1)` 的 `cache.pil_frames[0..8].pixels` 原始 tensor blob。不得改用 PNG、live PIL、`navigator_return` 或另一个 cache occurrence。
- 权威主配对：`ID0` 对 `ID8`。ID0 只是在相同起点相机条件下的真实 RGB 参考，不是深度、3D、运动或整段视频 GT。

### `M_outer4`

坐标位于归档后的 576×576 RGB 网格，均为 Python 半开区间：

- R1 `[0:192, 0:192]`
- R2 `[0:192, 384:576]`
- R3 `[192:384, 0:192]`
- R4 `[192:384, 384:576]`

四块互不重叠，共 `147456` 像素、`442368` 个 RGB 标量。评分器将 `uint8` 转为 float64 后除以 255，再在四块与三个通道上合并累加。

### 唯一判据

- 权威值：未四舍五入的 float64 `MSE_M`。
- B0 严重差异事件：`MSE_M > 0.01`。
- `MSE_M == 0.01` **不算事件**。
- `ReturnPSNR_M = -10 log10(MSE_M)` 只作单调显示；`<20 dB` 与上述严格不等式等价。
- R1–R4、全图，以及 `(1,7)、(2,6)、(3,5)` 仅为预先固定的诊断。后三对都是生成—生成比较，没有 GT，不能替代主判据。
- B0 成功评分后的 cohort 状态仍是 `INCOMPLETE`，必须继续完成 C1/C2，且三行至少两行严格满足 `MSE_M>0.01` 才能进入原预注册的 cohort 差异状态。

## 4. 评分器做什么、明确不做什么

新增的 `score_b0_blind.py` 在读取权威像素 blob 前会依次验证：

1. 自身、机器合同、原预注册、原预注册 receipt 的 SHA；
2. 不同作者的 B0 scorer 源码 PASS，且审查者没有看 S40 图片或解码结果数组；
3. 最终 S40 manifest、成功终态 generation receipt/worker receipt；
4. 成功的 supervised readback 及其独立结果审查；
5. 评分前盲态声明；
6. full archive manifest 和 `events.jsonl` 哈希链；
7. 两个 `batch_input` 与两个 `cache_commit` 的相机字段映射；
8. ID0–ID8 的 `uint8[576,576,3]` tensor descriptor、body SHA 和 sidecar；
9. 复制捷径：ID1–ID8 全等于 ID0，或 8 个生成帧彼此全等时，记技术无效。

随后才延迟导入固定环境中的 NumPy 1.26.4，以 memmap 读取 tensor body，计算 MSE。它不导入 Torch/PIL/模型，不打开 PNG，不输出图像或 crop，不执行配准，也不读取原始 JPEG 像素。成功只产生 `report.json` 与 `receipt.json`；当前仅做过 AST 解析，没有 import 或执行。

源码中的相机 guard 只给 `PASS_REQUESTED_CAMERA_CONDITION_ONLY`。它不能产生 visual-camera PASS。没有另行冻结的 visual proxy 时，严重 B0 事件的解释上限是 `RETURN_RGB_DISCREPANCY_CAMERA_CAUSE_UNRESOLVED_SINGLE_ROW`。

## 5. 串行执行路径与命令

以下给出失败后唯一合法的接续路线。本审计者没有执行任何命令；attempt 01 是根任务在本审计进行中独立启动的。

### 步骤 1：保留 attempt 01，修复 readback 的双表示读取

不得再次运行旧 SHA。`supervision_01/` 与 `executed_01/` 必须原样保留。实证失败链是：

- worker receipt SHA `4b762c3061d395a6767f319a553e681dbea8fe4d90bd49e5ac8a563d36bf35c6`，status `FAILED_OR_PARTIAL_S40_READBACK`；
- `readback.py:273` 调 `r.array(info['context_time_indices'], ad)`；
- 第一批冻结源码路径 `pipeline.py:632` 明确产生 Python `[0]`；archive metadata 解码保持 list；
- `Reader.array()` 只接受 tensor descriptor，于 `d['blob']` 对 list 使用字符串索引而报 TypeError；
- 外控 receipt SHA `f269dc2486478e65176c38445ab97251f31a5a4ac6c9f50cbd344a73daefd5da`，rc=2，未发生 limit/survivor/source-change/input-change。

最小不同修复是在同一处只对 `context_time_indices` 接受两种冻结表示：

1. Python list：必须非空，元素必须是非 bool 的 Python int；直接复制为 `ids`；
2. tensor descriptor：维持原 `r.array()`、一维 integer dtype 和 blob/hash 验证；
3. 两个分支汇合后继续执行原有唯一性、范围、trace/cache 对照；不得放宽其他数组或字段类型。

修复必须保留旧源码/协议/审查，产生新的 worker SHA、protocol/preparation/delta-review SHA；外控必须更新 pin 并再获不同作者审查。只有这些新 SHA 全部冻结后，下一候选命令才可使用 `supervision_02/` 与 `executed_02/`：

```sh
S40_ROOT='/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling'
"$S40_ROOT/.venv-cut3r/bin/python" -B \
  "$S40_ROOT/work/S40_result_readback/supervise_readback.py" \
  --supervisor-sha256 '<revised supervisor reviewed SHA>' \
  --supervisor-review-sha256 '<revised supervisor review SHA>' \
  --manifest "$S40_ROOT/work/S40_declared_variant_generation/review_attachment_01/manifest.json" \
  --manifest-sha256 '9951a78909a7d792dd536cea067c14e369cff776115a078d2f61c66c085cdebe' \
  --s40-execution-receipt "$S40_ROOT/work/S40_declared_variant_generation/execution_01/receipt.json" \
  --s40-execution-receipt-sha256 '4c771df1e46f96e218b92f01339b55ebd056ef002fdc28e0083a5bb0907300d4' \
  --execution-directory "$S40_ROOT/work/S40_result_readback/supervision_02" \
  --out "$S40_ROOT/work/S40_result_readback/executed_02"
```

当前不存在可直接执行的实际 SHA 命令；占位符不是授权。只有 revised source/protocol/review 全部一致，且 fresh `_02` 目录仍不存在时才可启动一次。只有新 supervision receipt 为 `S40_READBACK_RETURNED_PENDING_INDEPENDENT_REVIEW`、return code 0、没有 limit/survivor、worker receipt 为 `PASS_SAVED_S40_IDENTITIES_AND_CACHE_CONSUMPTION_ONLY` 时，才进入步骤 2。

### 步骤 2：不同作者审查真实 readback 结果

另一个未编写/执行 readback 的审查者必须审查并封存例如：

`work/S40_result_readback/result_review_02.json`

评分器要求其最小状态为：

- schema `s40-readback-result-review-v1`；
- status `PASS_S40_READBACK_RESULT_REVIEW`；
- 逐一绑定 manifest、supervisor receipt、worker receipt、report 的绝对路径和实际 SHA；
- 绑定修复后 readback source review 的实际 SHA；
- `generated_images_or_montages_viewed=false`；
- `metric_roi_pair_or_threshold_selected_from_outputs=false`；
- `blocking_findings=[]`。

这一步只能确认身份与 cache 消费链，仍不确认视觉质量或 B0 数值。

### 步骤 3：rebase 后由不同作者审查 B0 评分源码

当前 scorer/contract draft 分别固定旧 worker/review SHA，所以不能对它们签最终 PASS。readback 修复并通过真实 readback result review 后，先只更新相关 pin 和结果审查 schema 绑定，再计算新的双 SHA。另一个未编写评分器的审查者随后全文审查新版本。当前 draft 仅供差分起点：

- `score_b0_blind.py` SHA `6cb18e5f3d97f106861086a3f68acbd7962916314ae19610328c8e2d7dae16ec`；
- `B0_SCORING_CONTRACT.json` SHA `a5bba67105180d49b8767ae61e943c51959c9f4d553fa0235bd9d836344d4cb8`；
- 原预注册 SHA `89fb44e0b77a85a66fe611cd2f885fed0288229cbb027e04da25fc0631507b3f`。

rebase 后的审查结果须写到固定路径 `B0_SCORER_SOURCE_REVIEW.json`，schema/status 分别为 `s42-b0-blind-scorer-source-review-v1` 和 `PASS_S42_B0_BLIND_SCORER_SOURCE_REVIEW`，绑定新的 scorer/contract 与原 protocol，`executed=false`、`s40_generated_images_viewed=false`、`s40_result_arrays_decoded=false`、`blocking_findings=[]`，并证明 author/reviewer role 不同。

重点复核：最终 cache occurrence 选择、tensor descriptor/body 双哈希、M_outer4 合并顺序与数量、严格 `>0.01`、batch→cache 映射、Y 轴左乘公式、`1e-6` 容差、复制守卫、首个技术有效 attempt、失败终态及“无 visual proxy”状态。

### 步骤 4：在任何人看图之前生成真实盲态声明

复制 `B0_BLINDNESS_ATTESTATION_TEMPLATE.json` 到一个新文件，例如 `B0_BLINDNESS_ATTESTATION_01.json`。只有事实确实成立时，才能填：

- status `PASS_B0_BLINDNESS_PRE_SCORE`；
- 当前 manifest SHA；
- `generated_images_or_montages_viewed=false`；
- `s40_result_arrays_decoded_for_metric_selection=false`；
- `roi_pair_metric_or_threshold_changed_after_output=false`；
- 真实 attestor role 和 UTC。

模板的 null 值与 `TEMPLATE_NOT_AN_ATTESTATION` 永远不会通过评分器。

### 步骤 5：运行一次 B0 机器盲评分

前四步均通过、scorer 已 rebase 且所有 `<...>` 被实际 SHA 替换后，唯一首轮命令形状是。当前 draft SHA 不能放入该命令：

```sh
S40_ROOT='/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling'
"$S40_ROOT/.venv-cut3r/bin/python" -B \
  "$S40_ROOT/work/S42_baseline_failure_preregistration/score_b0_blind.py" \
  --scorer-sha256 '<rebased scorer reviewed SHA>' \
  --source-review-sha256 '<B0_SCORER_SOURCE_REVIEW.json actual SHA>' \
  --manifest "$S40_ROOT/work/S40_declared_variant_generation/review_attachment_01/manifest.json" \
  --manifest-sha256 '9951a78909a7d792dd536cea067c14e369cff776115a078d2f61c66c085cdebe' \
  --s40-execution-receipt "$S40_ROOT/work/S40_declared_variant_generation/execution_01/receipt.json" \
  --s40-execution-receipt-sha256 '4c771df1e46f96e218b92f01339b55ebd056ef002fdc28e0083a5bb0907300d4' \
  --readback-supervisor-receipt "$S40_ROOT/work/S40_result_readback/supervision_02/receipt.json" \
  --readback-supervisor-receipt-sha256 '<actual SHA>' \
  --readback-result-review "$S40_ROOT/work/S40_result_readback/result_review_02.json" \
  --readback-result-review-sha256 '<actual SHA>' \
  --blindness-attestation "$S40_ROOT/work/S42_baseline_failure_preregistration/B0_BLINDNESS_ATTESTATION_01.json" \
  --blindness-attestation-sha256 '<actual SHA>' \
  --out "$S40_ROOT/work/S42_baseline_failure_preregistration/B0_score_attempt_01"
```

评分器没有任意命令参数、不 spawn 子进程，内部时限为 300 秒。预注册没有为这个小型只读评分任务规定 RSS/CPU 外控，因此当前没有另一个 process-tree supervisor；不同作者源码审若认为这构成阻塞，应先冻结外控再运行，不能临时包裹任意命令后把它叫正式证据。

### 步骤 6：机器 receipt 之后才允许看图

只有 `B0_score_attempt_01/receipt.json` 为 `PASS_B0_MACHINE_SCORE_SINGLE_ROW_COHORT_INCOMPLETE` 且 `technically_valid=true`，才允许按原协议打开九帧，并必须 ID0→ID8 全看、固定顺序、完整报告空白/常量/饱和/撕裂/重复。不能只看最差或最好帧。建议在写入主账或作任何科学陈述前，再由不同作者核对 score report 的 SHA、MSE 原值、像素数、事件不等式和边界状态。

## 6. 失败保留与重试

- readback：`supervision_01/` 与 `executed_01/` 任何失败/部分内容都保留；修复必须新版本、新 SHA、新目录，不能覆盖。
- B0 评分：一启动就独占创建 `B0_score_attempt_NN/`。正常异常会写 `receipt.json`；技术 guard 失败写 `INVALID_OR_UNINTERPRETABLE`，前置条件失败写 `NOT_READY_BEFORE_B0_BLIND_SCORE`，读取/评分中异常写 `FAILED_OR_PARTIAL_B0_BLIND_SCORE`。
- 只有技术无效、异常、超时或部分封存可在冻结输入不变时使用下一个连续编号重试；所有 attempts 都保留并报告。
- 首个 `technically_valid=true` 的 B0 attempt 是唯一科学结果；一旦存在，评分器拒绝再次运行 B0 挑更好数值。
- 主机掉电、目录无法创建或最终 receipt 自身写盘失败仍可能没有完整终态；目录残留本身就是失败证据，不能删除后伪装首轮。

## 7. 剩余硬门

1. 真实 supervised readback attempt 01 已运行但因 list/tensor 表示 bug 技术失败；修复版尚未准备、审查或运行。
2. 成功 readback 的不同作者结果审查尚不存在；失败 attempt 01 不能获窄 PASS。
3. 当前 B0 scorer/contract draft 固定旧 readback SHA，必须在修复后 rebase；`AST_OK` 只证明语法树可解析，不证明控制流或数学正确，也不是执行授权。
4. 真实 pre-score blindness attestation 尚不存在。
5. 画面相机服从 proxy 尚未设计、冻结和审查；这不阻止 B0 机器筛查，但阻止把差异称为 memory failure，也阻止进入 A0/A1。
6. C1/C2 生成、readback 与评分尚未开始；B0 永远不能单独产生“可重复/已确认失败”。
7. 确认性统计设计仍是 `REVISION_REQUIRED`，因此所有当前工作都属于 baseline 校准/开发证据。

在这些硬门关闭前，准确状态是：**真实 S40 生成终态已存在；B0 测量规则已冻结；首次 readback 发现并保留了一个表示层软件错误；评分 draft 已准备但须随修复 rebase；尚无 B0 数值结果、画面相机 PASS、稳定 baseline 失败或创新证据。**
