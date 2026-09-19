# Proposal / handoff 同步复查（S100–S101）

**复查日期：** 2026-09-15（Asia/Shanghai）  
**复查者：** proposal-alignment agent  
**目的：** 检查两个交接入口是否反映最新 S100 结果和 S101 GPU 迁移合同，避免下一位接手者从旧的 S99/S90 待办开始。

## 1. 结论速览

| 文件 | S100 状态 | S101 状态 | 主要问题 |
|---|---|---|---|
| `docs/PROPOSAL_PROGRESS_CURRENT.md` | **已同步**：末尾有“2026-09-15 实时研究计划审计与 S100 更新”，包含 144 次保存几何消费者重渲染、三个 cap 的收益、8/36 反号和 `new_method_validated=false` | **未完整同步**：有 GPU 阶段原则和 S102–S109 类型的实验方向，但没有明确写入 `S101_GPU_RUN_MANIFEST_TEMPLATE.md`、`gpu_experiment_contract_20260915.md` 及 `TEMPLATE_ONLY_NOT_SUBMITTED` 状态 | 文件基本能导向正确科学状态，但接手者看不到 S101 的正式合同/模板入口，也看不到“尚未 SSH”的明确清单状态 |
| `docs/RESEARCH_HANDOFF_CURRENT.md` | **事实已附加但不是顶部当前入口**：文件第 932 行附近有 S100 段落，说明结果和下一步 | **未同步**：全文未出现 S101、S102–S109、GPU 合同或运行清单模板 | 文件顶部仍以 `S99_CURRENT_BEGIN`（第 1 行附近）作为“最新研究状态”，其下一项仍写固定上下文实验草案；这会让接手者误以为 S100 尚未执行，并可能重复 S100 |

所以，**S100 的事实在两个文件中都存在，但 RESEARCH_HANDOFF_CURRENT.md 的优先入口排序没有更新；S101 只在主账和 work/agents 文件中存在，两个交接入口没有完整接线。**

## 2. 已核实的 S100 内容

两个文件（尤其 `PROPOSAL_PROGRESS_CURRENT.md` 的末尾新增段和 `RESEARCH_HANDOFF_CURRENT.md` 的第 33 节）均应保留以下事实：

- 这是已见 S15B 缓存输出上的几何消费者重渲染，不是新的神经网络推理，也不是完整 VMem 视频生成。
- 同源近似幅度匹配形成 9 对候选，来源 0/1/3，2 个固定背景，4 个目标，low 与 confidence 两臂，共 144 次主重渲染；预测封存后才读取已见 GT。
- `B = loss(low) - loss(confidence)` 在 cap 0.5/1/2 的平均值分别约为 `-2.289363e-6`、`+1.215670e-7`、`+7.355809e-6`；36 个 pair-target 中 8 个出现跨背景反号。
- 解释等级只能是“局部上下文依赖线索”。它不证明稳定收益、因果记忆价值、跨场景泛化或 GRC-Memory 创新；`new_method_validated=false`、`novelty_authorization=NONE`。
- 下一步必须先取得合法未见 RGB-D/pose、真实记忆槽位预算和完整生成消费者，不能把 source-block 改写数量等同 proposal 中的记忆槽位 (k)。

证据文件：

- `work/S100_context_matched_swap/PROTOCOL.md`
- `work/S100_context_matched_swap/FREEZE.json`
- `work/S100_context_matched_swap/predict_01/SEAL.json`
- `work/S100_context_matched_swap/score_01/SCORES.json`
- `work/agents/S100_claim_boundary.md`
- `work/agents/S100_final_prerun.md`

## 3. 需要同步到两个交接入口的遗漏

### 3.1 `docs/PROPOSAL_PROGRESS_CURRENT.md`

该文件末尾的 S100 更新已经足够准确，但建议补 4 个交接指针：

1. 增加 S101 的一句状态：**“S101（学校 GPU 迁移实验合同与运行清单模板）已完成文档冻结，但仅为 `TEMPLATE_ONLY_NOT_SUBMITTED`，尚未获得服务器地址、账号、调度器、GPU 型号或 SSH 运行结果。”**
2. 链接 `work/agents/gpu_experiment_contract_20260915.md`，说明它把 proposal 的 GPU 阶段拆为 S102–S109。
3. 链接 `work/S101_GPU_RUN_MANIFEST_TEMPLATE.md`，说明远端字段仍为 `UNKNOWN`，禁止猜测或提前 SSH。
4. 把“当前下一步”写成“先过 S102 held-out RGB-D/相机配对 Gate0，再做 S103 长时程 baseline”，避免接手者直接提交 S105 GRC。

这些是**交接可读性缺口**，不改变 S100 结果，也不需要修改旧实验材料。

### 3.2 `docs/RESEARCH_HANDOFF_CURRENT.md`

这里有较严重的入口排序遗漏：

1. 文件顶部仍是 `S99_CURRENT_BEGIN`；该段写着 S100 只是“下一项候选”，与后面已完成的 S100 第 33 节矛盾。应在文件开头新增 `S101_CURRENT_BEGIN` 或至少新增一段“当前状态以 S100/S101 为准”，并明确旧 S99/S90 段为历史。
2. 顶部当前状态应列出 S100 的 144 次重渲染、三个 cap 收益和 8/36 反号，链接到 `SCORES.json` 与 `S100_claim_boundary.md`。
3. 顶部下一步不应继续以 RTMV 修复或 S100 草案为首要任务；应改为“先取得合格未见 RGB-D/pose，通过 S102 Gate0，再根据 S101 合同执行 S103–S109”。RTMV 索引仍可作为数据获取支线，但不能覆盖最新主线。
4. 增加 S101 合同和模板两个链接，并明确 `TEMPLATE_ONLY_NOT_SUBMITTED`；不要把 GPU 服务器、SSH、CUDA、队列或数据许可写成已获得。
5. 增加远端未知字段表：`host/user/port/scheduler/gpu_model/cuda_driver/remote_project/data_root = UNKNOWN`。这能阻止接手者凭旧聊天记录猜测服务器。
6. 将 S102–S109 实验名称写在顶部或链接到合同，尤其说明 S104 是同候选池同预算基线，S105 才是 GRC pilot，S107 是源级反事实干预；这样不会把 S100 的局部反号直接升级为方法。

## 4. S101 的真实状态与 proposal 对齐

`work/agents/gpu_experiment_contract_20260915.md` 已把 proposal 的后半段转为可执行合同：

- S102：未见场景 RGB-D/相机配对资格审计（Gate0）。
- S103：跨场景 VMem 长时程几何基线复现（确认真实神经 forward）。
- S104：固定记忆槽位、同候选池、同预算的强 baseline。
- S105：GRC-Memory 风险校准选择实验，只用历史可见输入。
- S106：遮挡后重访和视角变化压力测试。
- S107：源级反事实记忆干预，先检查 replay 噪声。
- S108：尾部风险和几何支持定位。
- S109：多 seed 与 GPU 资源审计。

`work/S101_GPU_RUN_MANIFEST_TEMPLATE.md` 明确了远端字段、上传冻结对象、GT 隔离、每个 job 必须保存的回执，以及发生 Gate0 失败、预算不一致、GRC 不超过 confidence、指标反转或只有模型加载没有 forward 时的停止规则。

这些文件是**执行前合同和模板，不是结果**。目前没有学校服务器信息、没有 SSH 连接、没有 GPU forward，也没有新的 held-out 数据；因此两个交接入口若只写“GPU 阶段待做”而不链接 S101，容易让读者误把计划当运行结果。

## 5. 推荐同步顺序（由主 agent 执行）

1. 先在 `RESEARCH_HANDOFF_CURRENT.md` 顶部加一段 S101/S100 当前入口（保留全部历史段，不删除旧记录）。
2. 在该入口明确 S100 是已完成的保存数据诊断，S101 是已写合同的模板状态，`new_method_validated=false`。
3. 在 `PROPOSAL_PROGRESS_CURRENT.md` 的最新审计段补 S101 两个链接和 `TEMPLATE_ONLY_NOT_SUBMITTED`。
4. 在主账/`workflow_checks.jsonl` 记录同步时间、修改文件和上述遗漏，不重算 S100，不重新运行 S100。
5. 未来拿到真实学校服务器信息后，先填 S101 模板并做无 GT 环境 smoke test；接着只在 S102 Gate0 通过后提交 S103。SSH 连通本身不算 proposal 实验完成。

## 6. 不应做的“同步修复”

- 不要删除或覆盖 S99/S100 的历史段；它们仍是可追溯证据。
- 不要把 S101 合同、GPU 计划、服务器登录或作业模板写成已经运行。
- 不要把 S100 的局部背景反号包装成“交互记忆方法”或“新颖性已证明”。
- 不要把没有独立 held-out RGB-D/pose 的 GPU 图像当作几何真值结果。

**复查结论：** S100 结果本身已在两个文档出现；真正需要修的是 `RESEARCH_HANDOFF_CURRENT.md` 的顶部优先级和 S101 链接/状态，以及 `PROPOSAL_PROGRESS_CURRENT.md` 对 S101 合同的交接指针。上述同步完成后，下一位接手者才能从“未见数据 Gate0 → GPU baseline → 固定预算强基线 → GRC pilot”正确继续，而不会重复已完成的 S100 或提前宣称方法有效。
