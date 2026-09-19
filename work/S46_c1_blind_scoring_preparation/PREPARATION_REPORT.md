# S46：C1 盲评分与独立复算的结果盲态准备

记录时间（UTC）：2026-09-07T18:30:16Z  
状态：`PREPARED_NON_EXECUTABLE_IDENTITY_UNBOUND`  
作者角色：`/root/c1_blind_score_builder`

## 给新手的一句话

真实 C1 还在生成时，我只把“以后怎么算分”写死，并用假数据检查两套算法是否一致；我没有打开 C1 的图片、张量或分数。等生成、读回和独立审查完成后，只把那些文件的路径和 SHA-256 身份填进去，不能再改评分数学。

## 1. 本阶段做了什么、没有做什么

本阶段把 S42 已冻结的 C1 数学条件翻译成两个彼此不导入的候选实现，并提供只绑定终态身份的元数据渲染器。它属于 Vibe Coding 的“小步、先定输入输出、每步验证”阶段；AI 只做机械实现和检查，不能替用户声称已理解、已验证创新或已满足投稿规范。

完成的工作：

1. 固定 C1 行身份：`jesus.jpg`、输入 SHA-256 `d611976b...e1`、seed 43、ID0–ID8。
2. 固定主比较、ROI、运算顺序、阈值、诊断配对、复制退化守卫和首个技术有效 attempt 规则。
3. 建立非执行 contract、盲态证明和独立复算 binding 模板。
4. 建立 `bind_identity_only.py`；它只接受路径、SHA、状态断言和九个像素身份，拒绝含 MSE、PSNR、row event 等结果字段的 binding；它本身不打开被引用的 C1 文件。
5. 建立主评分数学候选与不导入主候选的独立复算数学候选。
6. 仅用程序生成的合成数组做静态与数值检查。

明确未做：

- 没有读取、列举或查看正在生成的 C1 输出目录内容。
- 没有打开任何 C1 tensor/blob、PNG、PIL 图像、montage 或指标。
- 没有调用模型、generation、readback、render、正式 scorer 或正式 recompute。
- 没有创建 `C1_score_attempt_01` 或独立复算 `execution_01`。
- 没有改动 S42/B0 文件，也没有改动 S44 C1 冻结/执行文件。
- 当前文件不是冻结 contract、不是源码 PASS、不是盲态签名、不是评分结果，也不是创新证据。

## 2. 只读依据

| 依据 | SHA-256 | 用途 |
|---|---|---|
| `work/S42_baseline_failure_preregistration/PROTOCOL.md` | `89fb44e0b77a85a66fe611cd2f885fed0288229cbb027e04da25fc0631507b3f` | C1 行、ROI、阈值、守卫和证据边界 |
| `B0_SCORING_CONTRACT.json` | `1143f700855ab32df3d703fc91b2ff8707ca3dc3e217407156be9247d677c11b` | 终态身份、双源码审查和盲态签名结构 |
| `B0_BLINDNESS_ATTESTATION_PRE_SCORE.json` | `e4b18ed519832f43518fede0e32cb9efe5408cbb0f814dbd9ade4974553d8cf5` | 签名顺序与精确 false 字段 |
| `score_b0_blind.py` | `f36be25001f5138bd985ca186d49c6d44e66b5b9c599b8c0dfc6e8691a4719de` | float64 数学、诊断、attempt 和回执边界 |
| `B0_independent_recompute/PROTOCOL.md` | `e3086d3ea373295b83f08dbba919d016a96243e31ebf15142bb609de0d68f0b7` | 独立复算范围、同 FD 身份和单次输出规则 |
| `B0_independent_recompute/recompute_b0.py` | `0b91de7f35eb5e128aad81128657861ae5218b37ccbba78e4f8c282b1a61c741` | 不导入主 scorer 的复算模式 |

这些 B0 文件只作只读参考，原件未修改。

## 3. 已固定且以后不得因 C1 结果改变的数学

| 项目 | 冻结值 |
|---|---|
| row | `C1` |
| 权威帧 | ID0–ID8，共 9 个 `uint8[576,576,3]` |
| 主比较 | `(ID0, ID8)` |
| 主区域 | `M_outer4 = R1∪R2∪R3∪R4`，四个 192×192 半开区间 |
| 运算 | 每块分别 `uint8 → float64 / 255.0`，float64 平方和后除以精确 RGB 标量数 |
| 主分母 | 147456 pixels / 442368 RGB scalars |
| 严重事件 | 未舍入 float64 `MSE_M > 0.01`；恰等于 0.01 不算 |
| 展示换算 | `PSNR=-10 log10(MSE)`；MSE=0 时用 `null` 加 `+inf` 标记 |
| 固定诊断对 | `(1,7)`、`(2,6)`、`(3,5)`，均无 GT，不能替代主比较 |
| 其他诊断 | R1–R4 分块与 ID0/ID8 全帧 MSE/PSNR |
| 复制守卫 | ID1–ID8 全等于 ID0，或 ID1–ID8 彼此全相同，均判技术无效 |
| cohort 边界 | C1 是第二行；C2 仍强制，C1 单独不能形成三行终态 |

contract 内 `frozen_math` 的 canonical SHA-256 为 `9bee0abe9392e04e061adb7cf8b39297d7730e7045ed856486f1e03ee8d82812`。身份渲染器会逐位保留这棵数学子树；任何数学改动必须成为新协议，不能假装只是“补 SHA”。

## 4. 当前文件怎样协作

- `C1_SCORING_CONTRACT_TEMPLATE.json`：保存固定 C1 语义和待绑定槽位；当前 status 明确为 non-executable。
- `bind_identity_only.py`：未来接收一份只含身份的 JSON，生成仍待双审的 bound candidate。它禁止结果型字段，防止把看过的 MSE/PSNR 混进预评分 binding。
- `score_c1_blind_candidate.py`：保存主评分数学。当前只有 `--synthetic-self-test` 入口；没有正式 C1 I/O wrapper，直接执行会 fail closed。
- `C1_BLINDNESS_ATTESTATION_TEMPLATE.json`：未来两份源码审查都完成后，由 root create-only 填写；四个盲态布尔值必须全部为 false。
- `C1_INDEPENDENT_RECOMPUTE_BINDING_TEMPLATE.json`：必须等主 C1 score receipt/report 封存后才可绑定。
- `recompute_c1_independent_candidate.py`：不导入主评分实现，当前同样只有合成入口。
- `synthetic_crosscheck.py`：只构造算法图案，逐字段比较两套实现。

当前候选刻意没有完整 archive/readback 执行 wrapper。等 C1 readback schema 和终态 SHA 已知后，只允许新增一个薄的、受审 wrapper 来验证那些身份并把九个只读 `uint8` 快照交给已冻结数学函数。wrapper 不得重新定义 ROI、配对、归一化、累加、阈值或输出选择。

## 5. 合成与静态验证

使用项目 `.venv-cut3r` 的 NumPy 1.26.4，所有检查都只涉及新建源码、模板和程序生成数组：

- 四个 Python 文件 AST 解析通过。
- 主候选合成自检通过；MSE=1 的严格事件为 true，像素/标量数精确。
- 独立候选合成自检通过，且未导入主候选。
- 第一次跨实现检查发现 R4 最后一位浮点差异：独立实现最初使用“乘以 `1/255`”，与预注册的“除以 `255`”并非逐位同义。失败被保留在本工作记录中；源码改为明确除法后重跑。
- 修正后，主值、四块诊断、全帧诊断、三对诊断、事件、等号边界和 row status 全部逐字段精确一致。
- 两个候选在不带 `--synthetic-self-test` 时均 fail closed，不读取任何 C1 文件。
- 模板 `frozen_math` canonical SHA 复算一致；新代码不导入 torch、PIL、cv2 或 diffusers。

这些检查只证明翻译出的数学候选在合成数据上自洽，不能证明 C1 readback、评分或独立复算已经完成。

root 随后对当前源码/模板做了静态复核，回执 `ROOT_STATIC_PREPARATION_AUDIT.json` SHA-256 为 `b97aa3286c3be55589947a5ce7ceb8775a60acca5404ab48a42771e6407549c8`，状态 `PASS_ROOT_STATIC_PREPARATION_AUDIT_NOT_SOURCE_AUTHORIZATION`。它确认候选范围内无 blocker 和零 C1 payload 访问，但明确不是后续所需的两份不同作者源码授权。

## 6. C1 结果出现后的唯一合法顺序

1. C1 生成先形成终态 receipt；独立审查确认它是冻结条件下的首个技术有效 attempt。无效/部分 attempt 必须保留。
2. 对保存量做另行冻结的 readback；完成其源码审查、唯一执行和不同作者结果审查。此时仍不得人工看 C1 图。
3. 由元数据审查者建立一份 `s46-c1-upstream-identity-binding-v1`，只包含八类上游 JSON 路径/SHA/预期状态、九个权威像素 descriptor/body 身份、身份所在 JSON pointer、archive tensor 目录和行有效性断言；禁止放入分数。
4. 使用 `bind_identity_only.py` 生成 bound contract candidate；重新计算其 SHA。此动作仍不授权评分。
5. 新增最薄的正式执行 wrapper；它只能验证身份、用同 FD 只读快照加载九个精确 body、调用当前数学候选、原子 create-only 封存 report/receipt。不得改当前数学候选。
6. 两位不同非 root 作者分别做源码审查：
   - primary：`PASS_S46_C1_BLIND_SCORER_SOURCE_REVIEW`
   - adversarial：`PASS_S46_C1_BLIND_SCORER_ADVERSARIAL_SOURCE_REVIEW`
   两份都必须绑定 scorer kernel、正式 wrapper、bound contract、S42 protocol 的精确 SHA，且声明 `executed=false`、`C1 payload read=false`、`C1 images viewed=false`、`blocking_findings=[]`。作者与两位 reviewer 三者必须两两不同。
7. 双 PASS 后才 create-only 形成 `PASS_S46_C1_BLINDNESS_PRE_SCORE` 盲态证明；时间必须晚于两份审查且不晚于正式 score start。任何人已看 C1 图片、像素或分数都要如实阻断该盲评分链，不能补写 false。
8. 正式 scorer 再核终态 identities、首个技术有效 attempt、cache/readback、pose/K、复制守卫和盲态证明；仅在全部通过后计算唯一 C1 分数并原子封存。技术有效回执出现前不允许人工视觉 QA。
9. 主 report 封存后，才把 receipt/report SHA 填入独立复算 binding。独立复算执行源码必须由另一作者审查，且不能导入主 scorer；随后只读九个 report-bound body 复算并比较 float hex。
10. 无论 C1 是否发生 `MSE>0.01`，C2 仍必须按原协议完成。

## 7. 当前执行门

当前门状态为 `BLOCKED_BY_DESIGN_AWAITING_C1_TERMINAL_AND_READBACK_IDENTITIES`。这不是实验故障，而是盲法的预定暂停点。缺少以下任一项都不能正式评分：

- C1 首个技术有效生成终态及独立结果审查；
- 保存量 readback 的冻结源码、双审、正式回执和不同作者结果复核；
- identity-only bound contract；
- 只做身份/I/O 的正式 wrapper；
- exact scorer+wrapper+contract 的两份不同作者 PASS；
- 双审之后的 create-only 盲态证明；
- 新鲜顺序 attempt 路径和全局非阻塞锁。

独立复算还额外需要 sealed primary receipt/report identities、独立源码审查和新鲜 `execution_01`。它只能证明数值复算一致，不能替代 C2、视觉质量、画面相机服从、因果实验、方法增益或创新判断。
