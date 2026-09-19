# B0 盲评分器在 readback v3.3 后的只读重绑审计

- 审计时间：`2026-09-07T14:33:06Z`（Asia/Shanghai `2026-09-07 22:33:06`）
- 审计角色：`/root/readback_schema_audit`
- 裁决：**BLOCKED_PENDING_ATTEMPT02_RESULT_REVIEW_AND_B0_SCORER_REBASE**
- 本文性质：准备性、只读、静态审计；不是 B0 scorer 源码 PASS，不是 readback result review，也不是 B0 数值结果。
- 严格边界：没有 import 或运行 `score_b0_blind.py`，没有执行 B0、readback、模型、生成、GA、renderer 或 gate；没有打开、解码或查看任何生成图片、PNG、montage；没有读取 tensor/image payload body 或映射科学数组。只读取了源码、合同、模板、readiness 和 attempt02 的 JSON receipt/report 元数据。

## 1. 给新手的当前结论

真实 S40 保存量的第二次 readback 已经技术性返回成功，但状态仍明确是 **等待独立结果审查**。它证明的是保存文件身份和两批 cache 消费链，不是画面质量，也不是 B0 指标。

现在还不能运行 B0，原因有四个：

1. `score_b0_blind.py` 和 `B0_SCORING_CONTRACT.json` 仍固定旧 attempt01 的 supervisor/readback SHA；新 attempt02 会被当前 scorer 拒绝。
2. scorer 的 archive metadata decoder 仍有 readback v3.2 曾经出现的同类来源问题：list/tuple 被折叠，scalar 标签和值没有精确核对，真实 tensor 与“长得像 descriptor 的普通 dict”都会变成普通 `dict`。
3. 截至本审计时间，固定路径 `work/S40_result_readback/result_review_02.json` 不存在；并行语义审查者也确认当前只是 pending，没有可绑定的 schema/status/SHA。
4. rebase 后的 scorer/contract 尚无新的不同作者源码 PASS，真实 pre-score blindness attestation 也不存在。

因此目前允许的动作只有：完成 attempt02 独立结果审查，最小重绑并修复 scorer/contract，再做不同作者源码审查，最后在任何看图或输出驱动选指标之前生成真实盲态声明。不得跳到评分。

## 2. 本审计绑定的精确身份

### B0 当前 draft

| 文件 | 当前 SHA-256 | 当前含义 |
|---|---|---|
| `score_b0_blind.py` | `6cb18e5f3d97f106861086a3f68acbd7962916314ae19610328c8e2d7dae16ec` | 729 行；旧绑定，禁止执行 |
| `B0_SCORING_CONTRACT.json` | `a5bba67105180d49b8767ae61e943c51959c9f4d553fa0235bd9d836344d4cb8` | status=`PREPARED_UNREVIEWED_NOT_EXECUTABLE` |
| `B0_BLINDNESS_ATTESTATION_TEMPLATE.json` | `4ee45ec3f800907afd0a9a405fcaab606c0d2a5173e76bc231c1e418d4a5fd8b` | 模板，不是真实声明，永远不能直接通过 |
| `S40_B0_EXECUTION_READINESS.md` | `3ba751321e337270295f8044ba213e29d0c81c3820a85bd60755eb384d41166b` | 仍描述 attempt01 表示错误，已经过时 |
| `PROTOCOL.md` | `89fb44e0b77a85a66fe611cd2f885fed0288229cbb027e04da25fc0631507b3f` | 原冻结 B0 预注册，不应因 rebase 改动 |
| `receipt.json` | `5336c838de1714a6ab1f65be56312d21148d9dc6114162a7ee59497f3bbb2cf7` | 原预注册 receipt，不应因 rebase 改动 |

当前不存在 `B0_SCORER_SOURCE_REVIEW.json`、真实 `B0_BLINDNESS_ATTESTATION_NN.json` 或任何 `B0_score_attempt_NN/` 目录。若保持该状态，未来第一个合法输出目录仍是 `B0_score_attempt_01/`。

### readback attempt02 的现有窄结果

| 证据 | SHA-256 | 已观察状态/边界 |
|---|---|---|
| `work/S40_result_readback/supervision_02/receipt.json` | `f69b903b2f2987547e7e612c1234eaa7e1d3caa86a8ce2f2e7bee9f04178a894` | `S40_READBACK_RETURNED_PENDING_INDEPENDENT_REVIEW`; rc=0；一次调用、零重试；source/input/worker stat close seal 为 true；无 limit/survivor 字段 |
| `work/S40_result_readback/executed_02/receipt.json` | `24bc325c4740589b548e0bbe7c9244cb57168f5a032af605f71b3cd09965f18e` | `PASS_SAVED_S40_IDENTITIES_AND_CACHE_CONSUMPTION_ONLY`; `passed=true`; quality=`NOT_EVALUATED`; readback source 为 v3.3 |
| `work/S40_result_readback/executed_02/report.json` | `a15e4264090361847a57516499d3bf4f1203de80bf26fbba5fd63f181ec5ea21` | 210 个保存量比较；两批 context IDs 为 `[0]` 与 `[0,2,4,1]`；scope 明确不含模型、render 或视频质量重算 |

attempt02 外控绑定：

- supervisor source：`f04b9bcd4a0e2908d2bc3ead9a732e16d4f4ef651a60541a87f37a7b37f2b238`
- supervisor protocol：`e16832daf1fbda8f98e61da368cf00a319659f8d6970c79d582b0e35685827b3`
- supervisor source review v2：`9c608a57a54e716103dbf83d4aca73151d8fafed8d0e0099802cd9daabf2ab1e`
- readback worker v3.3：`d4c22504569ad1fb1fcc74ea1da83b4f244f4de803f5d0fadc16e8da06777933`
- readback protocol v3.3：`257e1b7583b000e907cde8baf3e4e3fcefb9f2c81037ed98887d0f6367483163`
- primary source review v3.3：`70d4c48a6940778247763c901637e18e231b926f4733ac8edb64923ef0240484`
- adversarial source review v3.3：`8ca313e712eec18d275122c95181aff987ae1ff5ceb04a880af61bb41b5a3ec7`
- revision v3.3 receipt：`bebc80b8fccf6e8699d4768f6ffab097bcc75f6bca4a7f101ef53e827b0e2e9d`

外控记录的资源值是 1 个数值库线程、300 秒、2 GiB sampled process-tree RSS、10 GiB free-disk floor、0.5 秒轮询；本次真实 attempt02 的 sampled peak RSS 为 `190955520` bytes，最后一次 terminal-receipt 写入前 wall time 为约 `3.635` 秒。这些只是 receipt 元数据，本审计没有重跑它。

## 3. 必须替换或新增的旧 SHA、路径和状态门

### scorer 源码中的旧常量

`score_b0_blind.py:38-42` 必须重绑：

| 当前旧字段 | 旧值 | 必须替换/新增的值 |
|---|---|---|
| `READBACK_SUPERVISOR_SHA256` | `c86c3f96e5c7b4b6827037c358780479aeb3c1dea10ea9b2cd9a4c2ca6ff8cad` | `f04b9bcd4a0e2908d2bc3ead9a732e16d4f4ef651a60541a87f37a7b37f2b238` |
| `READBACK_SUPERVISOR_REVIEW_SHA256` | `7026d4ce8c7eb8c8f5cf551b4b947f6c7847715373566c0f4451c11535755597` | `9c608a57a54e716103dbf83d4aca73151d8fafed8d0e0099802cd9daabf2ab1e` |
| `READBACK_WORKER_SHA256` | `4c7a4208c4a67b003bae7b5574b48ce44d6034797bf2e9c5ab021e4d04e4cbf6` | `d4c22504569ad1fb1fcc74ea1da83b4f244f4de803f5d0fadc16e8da06777933` |
| `READBACK_SOURCE_REVIEW_SHA256` | `ea599804589dc4c10b2ca65c972bbf1ae8a1c3c04c327f7605c5a45e2f08ec19` | primary v3.3 `70d4c48a6940778247763c901637e18e231b926f4733ac8edb64923ef0240484`，并新增 adversarial/revision/protocol 绑定，不能继续只绑一个旧 review |

同时新增以下固定路径和 SHA 常量，不再把真实 attempt02 当成未冻结的任意动态 receipt：

- `supervision_02/receipt.json` → `f69b903b2f2987547e7e612c1234eaa7e1d3caa86a8ce2f2e7bee9f04178a894`
- `executed_02/receipt.json` → `24bc325c4740589b548e0bbe7c9244cb57168f5a032af605f71b3cd09965f18e`
- `executed_02/report.json` → `a15e4264090361847a57516499d3bf4f1203de80bf26fbba5fd63f181ec5ea21`
- 当前 supervisor protocol、readback protocol、primary/adversarial source reviews 和 revision receipt 的上述精确 SHA。
- 独立结果审查完成后，再新增固定 `result_review_02.json` 绝对路径和它的实际 SHA；现在没有值，禁止填占位符或猜测 SHA。

`verify_readback()` 的状态门应保留并加强：

1. supervisor status 必须仍是 `S40_READBACK_RETURNED_PENDING_INDEPENDENT_REVIEW`，`success_pending_independent_review=true`，一次调用、零重试、rc=0、所有 close seal 为 true，且无 limit/survivor。
2. worker status 必须仍是 `PASS_SAVED_S40_IDENTITIES_AND_CACHE_CONSUMPTION_ONLY`，`passed=true`，worker SHA 必须是 v3.3，quality=`NOT_EVALUATED`。
3. report 必须绑定同一 manifest、同一 worker receipt、同一 generation receipt，并保留原窄 scope；不得把 pending readback status 直接提升为 B0 评分许可。
4. result-review 必须是另一个角色对这组三文件的明确 PASS；只有它可关闭 pending 状态。

### contract/readiness 中的旧绑定

`B0_SCORING_CONTRACT.json:41-54` 仍固定 attempt01 supervisor/protocol/review、v2 worker 和 v2 source review，必须按上表全部替换，并新增 attempt02 三文件及独立 result-review 的精确路径/SHA。修改后 contract SHA 必然变化，因此 scorer 的 `CONTRACT_SHA256` 也必须随后更新；不能只改 scorer 常量而保留旧 contract SHA。

`S40_B0_EXECUTION_READINESS.md:5,21-25,32,87-147,201-211` 仍把 readback 描述为“修复版尚未准备/运行”。它必须改成：attempt01 失败永久保留；v3.3 attempt02 已返回窄 PASS、仍 pending 独立 result review；B0 scorer/contract 因旧绑定和 decoder 问题继续 BLOCKED。readiness 文档不能把 attempt02 窄 PASS写成画面、B0 或创新 PASS。

## 4. metadata decoder 的同类问题

结论：**有，而且在 B0 scorer 获不同作者源码 PASS 前必须修复。**

| 问题 | 当前证据 | 影响 | 最小严格修复 |
|---|---|---|---|
| list/tuple 来源折叠 | `score_b0_blind.py:329-330` 对两种 kind 都返回 list | verifier 无法证明原归档容器类型；与 readback 旧问题同类 | `kind=list` 返回 list，`kind=tuple` 返回 tuple；下游只用索引/迭代时无需放宽 |
| scalar 标签和值未绑定 | `:331-332` 直接返回 `node["value"]` | `type=bool,value=0` 或错误标签可悄悄变成另一 Python 值类型 | 只对当前固定 archive 的 `str/int/bool/NoneType` 建 exact type map，并要求 `type(value) is expected_type`；明确这是当前固定 archive 范围 |
| raw tensor 来源丢失 | `:335` 让真实 raw `kind=tensor` 原样成为普通 dict；归档普通 Python dict 也在 `:325-328` 解码成普通 dict | `tensor_path():383-410` 只能看到 descriptor 形状，无法证明它来自 raw tensor 节点；普通 descriptor-shaped dict 可冒充 | 新增仅由 raw `kind=tensor` 分支创建的 `TensorDescriptor(dict)`；`tensor_path` 首行要求 `type(desc) is TensorDescriptor` |
| PIL pixels 标记会在简单修补后丢失 | 当前 `pil_image` 走 `:335` 原样返回，其 `pixels` 没有递归解码 | 若只给 tensor 分支加 marker，`score_pixels():528-531` 仍收到普通 dict 并被严格 gate 拒绝 | 为 raw `kind=pil_image` 单独复制外层 dict，并让 `pixels=decode_tree(node["pixels"])`，与 readback v3.3 相同 |
| descriptor 完整绑定不足以表达 archive 注册关系 | 当前核 body SHA、canonical SHA 与 sidecar 全等，但没有显式要求事件 descriptor 等于 `archive_manifest.tensor_descriptors[blob]` | provenance 修复后仍应避免只凭可达 blob/sidecar 建立比较输入 | 将固定 archive manifest 的 descriptor registry 传入 `tensor_path/array`，要求完整 mapping 全等；保留现有 body/canonical/sidecar 检查，不得用路径存在替代 |

本审计只查看了 archive `events.jsonl` 元数据。固定 archive 的实际 B0 相关节点目前是可达的真实 raw tensor：`batch_input` occurrence 0/1 的 `target_c2ws/target_Ks` 均为 raw `kind=tensor`；最终 `cache_commit` occurrence 1 的 9 个 `pil_frames[*].pixels`、9 个 `c2ws` 和 9 个 `Ks` 也均为 raw `kind=tensor`。整个固定 archive 的 scalar 标签只观察到 `str=12357`、`int=11060`、`bool=6`、`NoneType=2352`。这说明严格修复不会排除当前真实输入；它不消除 scorer 当前无法证明来源的源码缺陷。

## 5. 独立 result-review 必须新增的绑定

固定候选路径为：

`/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/work/S40_result_readback/result_review_02.json`

截至本审计时间该文件不存在，不能创建虚假 PASS。未来 review 至少要满足：

- schema/status 使用被 scorer 和 contract 同时固定的明确版本；若沿用当前 draft，应为 `s40-readback-result-review-v1` / `PASS_S40_READBACK_RESULT_REVIEW`。
- 精确绑定 manifest path/SHA `9951a78909a7d792dd536cea067c14e369cff776115a078d2f61c66c085cdebe` 和 generation receipt path/SHA `4c771df1e46f96e218b92f01339b55ebd056ef002fdc28e0083a5bb0907300d4`。
- 精确绑定 attempt02 supervisor receipt `f69b...a894`、worker receipt `24bc...f18e`、report `a15e...a21` 的完整实际 SHA 和绝对路径。
- 精确绑定 supervisor source/protocol/source-review `f04b...b238` / `e168...27b3` / `9c60...b1e`。
- 精确绑定 readback source/protocol/primary review/adversarial review/revision `d4c2...7933` / `257e...3163` / `70d4...0484` / `8ca3...ec7` / `bebc...e9d`。
- 明确检查 supervisor/worker/report 的 status、return code、一次调用、零重试、无 limit/survivor、close seals、manifest/generation receipt 一致性、210 comparison 清单及窄 scope。
- `generated_images_or_montages_viewed=false`、`scientific_arrays_mapped_or_compared=false`、`tensor_or_image_payload_bodies_read=false`、`metric_roi_pair_or_threshold_selected_from_outputs=false`，并保留 `blocking_findings=[]`。
- `author_role` 与 `reviewer_role` 不同；result reviewer 不能是 readback/supervisor 的作者或执行者。结果审查仍不能声称画质、相机视觉服从、B0 数值或创新。

scorer 不应只核一个旧 `readback_source_review_sha256`。它应核上述完整 review bundle 和 result-review 的实际 SHA，并要求 result-review 内部的每个路径/SHA与传入的固定 attempt02 文件完全一致。

## 6. 最小补丁顺序

这里只给修复合同，不修改作者文件。

1. **先完成 result-review**：只审 attempt02 JSON/比较语义，保持不看图、不读 payload body；若有 blocker，停在这里。
2. **改 decoder**：加入 `TensorDescriptor`、list/tuple 分支、scalar exact-type gate、PIL pixels 递归、`tensor_path` exact provenance gate与完整 registry equality。其他 shape/dtype/body/canonical/sidecar 检查全部保留。
3. **重绑 scorer**：替换四个旧 SHA；新增 supervisor protocol、readback protocol、双 source review、revision、attempt02 supervisor/worker/report、result-review 的固定路径/SHA；`verify_readback` 核其完整字段。
4. **加强 attestation gate**：除现有三项 false 外，要求 `manifest_path` 等于冻结 manifest、`created_utc` 是真实非空 UTC、传入文件不是 template 本身，并把 attestation SHA写入最终 receipt。建议先核 generation/readback/result-review JSON，再核 attestation，之后才读取 archive events 和 tensor body；这些上游 JSON 不含图像解码。
5. **更新 contract**：同步全部新身份、decoder provenance 合同、result-review schema/status、固定评分顺序和 blindness 真实条件；生成新 contract SHA，再回填 scorer 的 `CONTRACT_SHA256`。
6. **更新 readiness**：只更新状态与新 SHA，不改原预注册的 ROI、pair、阈值或解释边界。
7. **不同作者源码审查**：新 `B0_SCORER_SOURCE_REVIEW.json` 必须绑定新 scorer/contract、原 `PROTOCOL.md`，声明 `executed=false`、未看图、未解码结果数组、阻断为空、author/reviewer 角色不同。
8. **生成真实 attestation**：只有事实成立才从模板另存新文件并绑定 SHA。完成以上所有步骤后，才允许创建第一个评分目录并运行一次。

这个补丁应是“只修 gate 和 provenance”的增量。不得借 rebase 改 `REGIONS`、`PAIRS`、阈值、归一化、像素数、相机容差、copy guard 或解释上限。

## 7. 固定评分顺序、指标和输出目录

### 唯一允许的工作流顺序

1. attempt02 独立 result-review PASS。
2. scorer/contract 最小重绑和 decoder 修复。
3. 不同作者 B0 scorer 源码 PASS。
4. 在任何看图、montage 或输出驱动指标选择之前，生成真实 blindness attestation。
5. 创建下一个连续且不存在的 `B0_score_attempt_NN/`；当前应为 `B0_score_attempt_01/`。
6. scorer 先验身份核验：自身、contract、原 prereg protocol/receipt、source review、manifest、generation receipts、attempt02 三文件、result-review、attestation。
7. 核 archive manifest 与 events hash chain，保留 raw metadata provenance；随后才延迟 import NumPy 1.26.4。
8. 先核两批 `batch_input → cache_commit` 的 c2w/K、计划 yaw 和 ID8→ID0 requested-camera closure，容差固定 `1e-6`。
9. 再按 ID0→ID8 顺序核 9 个 `uint8[576,576,3]` 权威 pixels tensor 的 descriptor、body、sidecar、registry；先做 copy/degeneracy guard，再计算指标。
10. 先封存唯一 `report.json` 和 `receipt.json`，之后才可能进入九帧人工 QA。

### 冻结指标

- 权威帧：最终 `cache_commit` occurrence 1 的 `cache.pil_frames[0..8].pixels`，不能改用 PNG、live PIL、另一个 occurrence 或挑帧。
- 主配对：ID0 对 ID8。
- `M_outer4` 固定四块，按 R1、R2、R3、R4 顺序累加：`[0:192,0:192]`、`[0:192,384:576]`、`[192:384,0:192]`、`[192:384,384:576]`。
- 精确计数：147456 像素、442368 RGB 标量。
- 计算：uint8 转 float64 后各自除以 255，再做平方差；主值是未四舍五入的 float64 `MSE_M`。
- 唯一事件：`MSE_M > 0.01`；`==0.01` 不算事件。
- `ReturnPSNR_M=-10 log10(MSE_M)` 只作显示。
- per-region、full-frame 和 `(1,7)/(2,6)/(3,5)` 只作固定诊断，不能替代主判据。
- B0 只有一行；即使事件为 true，cohort 仍是 `INCOMPLETE`，不能称稳定或已确认 baseline failure。

### 输出目录和尝试政策

- 只允许直接子目录 `B0_score_attempt_NN`，编号连续、目录事前不存在、所有失败保留。
- 当前无历史 attempt，因此首次合法目录是 `B0_score_attempt_01`。
- 首个 `technically_valid=true` 的 attempt 是唯一科学结果，之后禁止重跑挑数值。
- 只有技术无效、异常、超时或部分封存才可在冻结输入完全不变时使用下一个编号；每次都必须保留 receipt/partial evidence。

## 8. blindness attestation 的真实条件

模板 SHA `4ee45...fd8b` 的结构可作为起点，但 `status=TEMPLATE_NOT_AN_ATTESTATION` 和 null 值绝不构成证明。真实文件必须是新路径、新 SHA，并且以下条件在事实层面全部成立：

1. attestor 在机器 receipt 封存前没有查看任何 S40 生成图片、PNG、montage 或挑选帧；项目 contract 的更强口径是此前没有任何人用这些输出调整 B0 规则。
2. attestor 没有为选择 ROI、pair、metric 或 threshold 解码/映射 S40 result arrays；只读上游 receipt/report 元数据不等于看像素。
3. R1-R4、ID0/ID8、float64 MSE、严格 `>0.01`、诊断 pairs 和 copy guard 都来自输出前冻结合同，未因 attempt02 或任何图像内容改变。
4. `manifest_path` 与 SHA 精确等于冻结 B0 manifest；`created_utc` 是真实创建时间；`attestor_role` 是真实且未受输出污染的角色。
5. 三个布尔值必须是精确 JSON false：`generated_images_or_montages_viewed`、`s40_result_arrays_decoded_for_metric_selection`、`roi_pair_metric_or_threshold_changed_after_output`。
6. 如果任何一项事实不成立，不得把字段填成 false，也不得签 `PASS_B0_BLINDNESS_PRE_SCORE`。应停止正式 blind B0；最多另立清楚标注为 non-blind exploratory 的分析，不能冒充原预注册结果。

当前 scorer `verify_blindness_attestation():183-196` 没有核 `manifest_path` 或非空 `created_utc`，也没有禁止把模板路径直接改写后使用；这些应在 rebase 中补上。真实盲态不能只靠 JSON 字段自我声明，最终源码审查还要核 attestation 的生成时序和角色边界。

## 9. Kill criteria

以下任一项发生，都必须停止正式 B0，不创建“可执行/PASS”声明：

### 启动前

- `result_review_02.json` 不存在、不是独立 PASS、SHA未冻结，或没有绑定 attempt02 supervisor/worker/report 三件套。
- scorer/contract/readiness 仍出现任何 attempt01 旧 SHA、旧路径或“修复版未运行”的旧状态。
- decoder 的 list/tuple、scalar exact type、TensorDescriptor provenance、PIL pixels 或完整 registry equality 任一问题未关闭。
- 新 scorer/contract 没有不同作者源码 PASS，或 source review 看过生成图片/解码过结果数组。
- blindness attestation 任一 false 不真实、时间/角色/manifest 不完整，或有人已根据输出改 ROI/pair/metric/threshold。
- 目标不是当前下一个连续 fresh `B0_score_attempt_01`，或已经存在 technically valid attempt。
- 任一绑定文件 SHA、路径、schema、status 或 close seal 漂移。

### 运行中

- archive manifest/events hash chain、capture occurrence、raw tensor provenance、descriptor registry/sidecar/body/canonical SHA 任一失败。
- 两批 target→cache c2w/K、计划 yaw、固定 K 或 ID8→ID0 requested-camera closure 超过 `1e-6`。
- 9 帧不是精确 `uint8[576,576,3]`，缺 ID，出现非有限指标、M_outer4 计数不为 147456/442368，或超过 300 秒。
- ID1-ID8 全部复制 ID0，或 ID1-ID8 相互全部 byte-identical：必须 `INVALID_OR_UNINTERPRETABLE`，不能计算成科学 B0。
- scorer 打开/输出图片、读取 PNG、导入/运行模型、执行生成/renderer/gate，或写出预期外图像/crop。

### 结果解释

- B0 单行不得声称可重复/确认的 baseline failure；C1/C2 未完成前 cohort 永远 `INCOMPLETE`。
- requested c2w/K closure 不等于画面服从相机；没有冻结 visual proxy 时，事件解释上限仍是 `RETURN_RGB_DISCREPANCY_CAMERA_CAUSE_UNRESOLVED_SINGLE_ROW`。
- 不得把 B0 差异归因于 memory、mean aggregation，不得进入 A0/A1，也不得称为创新证据。

## 10. 下一步的唯一合法状态转换

当前状态保持：**BLOCKED**。

下一步只能先得到 attempt02 的不同作者 result-review。若它不是无阻断 PASS，则 B0 继续停止；若它 PASS，再按第 6 节做最小 rebase 和新的 scorer source review。直到真实 blindness attestation 也通过之前，仍不得执行 B0。任何后续文件都必须重新计算实际 SHA，不能复用本文中的 draft scorer/contract SHA 作为执行授权。

