# S86实际结果报告：仅源码/模板准备

目前没有生成PDF，也没有填入任何S86结果值或临时占位分数。未读取当前数组、参考或新图；实际生成/评分/复核/导出完成前不会构建。本目录与已经交付的10页原理报告分开。

## 四页结构

1. 正式完成状态与科学截点；4臂全四帧主均值/完整整数SSE；guide相对terminal、G0、paste的3项有符号差；实际链、派生、编码、进程/监督成本和峰值。明确包含关系，不能加总重复计费，不能说每目标独立50步。
2. 所有16行完整full/support/hole MSE及full SSE；四目标support/hole像素/通道分母；NA政策、区域等帧与pooled区别；不同作者复核范围和实际最大算术差。这里的latent算术差与MSE展示差是不同单位，不能当视觉精度比较。
3. 已正式导出并验收的四行六列总览，直接复制原PNG，不改像素，不裁选获胜图；总览缩小仅供定位，保留32原生图与1总览的导航。真实参考/预测几何投影/生成/灰格孔洞分别说明。
4. 按真实完整SSE差生成最窄解释，包含负结果/等值/不胜强对照/胜强对照等分支；Gterminal必要性、累计干预量竞争解释、proposal推进、组件身份、单已见场景和4相关帧的限制、导师问答及证据导航。不重复前10页的手算，也不宣称创新。

## Root提供接受绑定后才执行

新建 `RESULT_REPORT_BINDING.json`，模式为 `S86_ROOT_ACCEPTED_RESULT_REPORT_BINDING_V1`，要求：

- `accepted: true`；`accepted_utc`实际root接受时间；`scientific_cutoff_utc`覆盖全部被绑定阶段完成时间，且不晚于接受时间。时间必须显式带时区。
- `builder_sha256`、`template_sha256`为当前最终源码/模板完整SHA。
- `accepted_full_overview_visual_QA: true`：root已实际核完整总览的确认，不能提前填。
- `inputs`包含8个对象，每个都有实际`path`和`sha256`：`generation`、`supervision`、`scoring`、`consumption_review`、`score_review`、`export`、`root_acceptance`、`visual_acceptance`。前6路径在脚本ROLES中固定，后2是S86内真实root科学与视觉接受文件。

`generation`是execution_01/RECEIPT；`supervision`是supervision_01/SUPERVISION；`scoring`是scoring_01/RECEIPT；两项review是INDEPENDENT_CONSUMPTION_REVIEW与INDEPENDENT_SCORE_REVIEW；export是visuals_01/EXPORT_RECEIPT。root_acceptance要求accepted=true、scope=saved-consumption and descriptive RGB scores only、novelty_authorization=NONE，并逐项绑定generation/scoring/consumption_review/score_review四SHA。visual_acceptance固定ROOT_VISUAL_ACCEPTANCE.json，要求accepted=true和export_receipt_sha256与当前导出一致。此处只有schema说明，没有创建含假SHA的绑定JSON。

运行：

```text
/Users/rocket/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 build_result_report.py --binding-sha256 <实际RESULT_REPORT_BINDING.json完整SHA>
```

脚本核完整状态、所有精确SHA和跨阶段来源关系；从评分回执的产物列表进一步绑定FRAME_SCORES、ARM_SUMMARY、CONTRASTS，从export绑定唯一overview。只读取小JSON和那1张已接受PNG；不读NPY/NPZ、原RGB/GT或模型，不再次评分。

缺字段、未知状态、空值语义错误、目标缺失、输入身份变化会停止，不能变成0或占位结果。失败保留BUILD_RECEIPT，不覆盖重试；即使实际有失败阶段，也不能构造完整四臂结果。若科学过程不完整，root应另写真实失败说明，不能使用本成功完成模板。

## 实际构建与验收边界

到时使用已有本机XeLaTeX双遍，要求恰4个非空页面、0缺字/Overfull，然后用Poppler渲染全4页。构建成功状态仅为 `BUILT_PENDING_ALL_PAGE_VISUAL_QA_AND_ROOT_REPORT_ACCEPTANCE`，不是已完成报告视觉验收。作者必须逐页实际view，root再独立视觉/数字核，完成后另写QA，不篡改科学数据。

输出：可编辑 `S86_固定历史投影四臂实际结果.tex`、build下同名PDF、全部qa页面图、BUILD_RECEIPT。模板源文件本身不是可以发给导师的结果稿，不能直接编译后交付。配套旧10页和旧142页不改动。

PDF skill的artifact marker已在此次第一条模板写入命令之前成功执行一次（create/pdf/count1）。本准备阶段只做AST和内存compile，没有实际调用构建main、XeLaTeX、render或科学数组。最终实际编译和全页visualQA尚未发生。
