# S26B 最终执行前独立审查

结论：**PASS_STATIC_PRE_REVIEW**。当前候选可由root冻结；本审查没有运行真正的import、GA、模型或深度评分。实际时刻与身份绑定见同目录 `execution_pre_review.json`。审查者为 `/root/supervisor_full_readthrough`，与S26B派生程序作者不同；同一审查者此前编写了数值恢复参考，因此没有将这里对新clean的复查称为又一份独立数值复现。root仍另行审查。

最终候选 SHA 为 `d84a395c02514ba26f4eca2664af22551195d688cc6e1fe2db4342728540993f`。它包含作者补充的恢复验证代码/回执身份闭包、最后一次身份核对完成后才写common PASS，以及root发现的评分回执来源文案修正。此前 `1b4610c4…` 的19项检查记录保持原样；最终又对来源文案增量做9项检查，没有重复人工导入或数值实验。

## 继承与新运行范围

候选完整保留原S26的8帧、28头档案身份、共同oracle相机、original4共同depth来源、原GA源码、预处理与核心版本。只导入已完成的4图结果和已PASS的control/views/compat，随后运行三个8图GA；总计3次新GA、1200次新Adam step、0新模型前向。CLI和ga_worker均拒绝重新执行common_old。

原 `ga_worker` 与新版本去除common_old拒绝语句和checkpoint记录后，完整AST一致；SceneObserver去除新增日志方法/调用后也与原版本完整AST一致。原输入/约束、实际Adam/MST/clean计数、种子、所有数值阈值和真实消费者返回均保持。checkpoint只保存已产生的report/计数/几何模块路径，不进行前向、梯度、RNG操作或张量更新；状态明确是 `OBSERVED_NOT_FINAL_PASS`。耗时包含日志记录，不能当纯优化速度基准。

桥接参考核对两份固定SHA：pair_objective沿用原S17不同作者FP64公式，clean调用已通过保存量验证的新FP32数值合同。原真实clean没有改变。新clean共享Torch inverse/matmul数值原语的独立性限制沿用恢复报告，不改称跨库逐位验证；它在未来8图是否通过仍需实际执行。

## 保存输出导入的可信边界

importer核原冻结manifest、独立 `IMPORT_VALIDATED` 回执、原output SHA、新clean SHA、全部恢复输入和验证代码/seal身份。候选里每一份待复制common文件与共享文件，都同时存在于恢复回执和新候选身份表中。旧common FAILED和旧父身份必须匹配。

复制操作只向新WORK/OUT写入，原路径保持只读。相机/view/output等逐字复制并核SHA；导入的control/compat/preprocess回执保留原PASS字段，同时明确原manifest、原receipt SHA和导入时刻。新common_old PASS附 `producer_kind:IMPORT_VALIDATED_SAVED_ORIGINAL_GA`、`validation_status:IMPORT_VALIDATED`、0新GA/step，以及恢复回执中的 `historical_observations_not_recorded`。原S26没有被追认PASS，原历史标量/flags/PnP/module inventory没有被补造。

新common输入seal与producer字段满足原8图worker和scorer接口，depth tensor SHA、camera prefix SHA直接继承独立恢复结果。最终再核原输入与恢复控制身份，之后才写新common PASS；复制中发生变化时保留未完成目录，dispatcher停止，不进入后三次GA或评分。

## 评分与答案隔离

新scorer除BASE、PROTOCOL两个顶层赋值和一条来源说明外，其完整AST与原scorer一致。来源说明已改为“1份IMPORT_VALIDATED保存producer与3份新GA producer”，避免原文错误地说成4次新GA；指标、门和执行顺序无改动。候选scoring除了producer/output路径及新scorer/protocol SHA，其他项逐项与旧冻结对象相同，包括8张已见GT身份、old4容差、新4主表、全部GT有效像素分母和无效/空值规则。实际候选对象通过当前 `validate_config` 的纯metadata校验。

评分仍在四份新目录producer/seal/NPZ身份通过、旧4depth输出约束通过后才读sensor PNG。新common的PASS是已明示的保存量导入，另外三个是完整前瞻运行；报告必须保留该差别。没有新增GT尺度、conf筛选、远点裁切或自由ATE结论。

## 本次实做检查

全文阅读plan、importer、桥接、派生工具、全部runner/scorer diff和新协议；原代码已在此前审查读过。19项标准库/AST/metadata/人工文件检查通过，记录在 `work/S26B_independent_review/check_receipt.json`；文案修订后仅做9项增量绑定，记录在 `delta_check_receipt.json`，确认只变动预期4个控制身份，importer/runner及全部数组身份保持。589个非数组/图像源或控制文件重新核SHA；21个数组/图片身份从已验证合同继承，本轮没有重读，实际import和每个运行worker仍会重新核验。

三个微型人工文件场景分别检查：有效导入精确复制且保留原FAILED/历史未录信息；错误恢复状态在写输出前拒绝；复制中验证源码改变时拒绝且不留下common PASS。这些文件是明确标记的假字节，不能解码成预测，也不提供实验数值。只执行scorer的纯metadata验证和importer对假目录的复制语义，没有导入NumPy/Torch、真正import旧结果、读传感器GT或启动GA。

未发现剩余阻断。用户已授权本机继续科研，本审查不引入额外许可步骤。root可冻结本精确候选后按import→CUT→TTT→FILT→score执行；若发生失败，保存新目录和合同，仍不得静默调整阈值。

遵循Supervisor第2章的强baseline优先及本地scientific-critical-thinking的输入控制、偏差、证据强度原则。本次解决的是复现与验证工程，不能视为创新方法、长期自然失败、Surfel/检索收益或完整视频生成结果。
