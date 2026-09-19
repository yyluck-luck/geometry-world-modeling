# S14C生产实现准备

本文件记录运行前实现准备，不是实际资料的测量结果。作者为 `/root/s14c_measurement_implementation`，最终源码和人工检查身份见 `work/S14C_implementation/receipt.json`。真实执行需根冻结并取得不同作者前审结论。

已实现 `scripts/measure_s14c_selection_disagreement.py`，两个独立CLI阶段共用同一份冻结源码：

```sh
.venv/bin/python scripts/measure_s14c_selection_disagreement.py --stage measure --manifest docs/S14C_EXECUTION_MANIFEST.json --output results/S14C_selection_disagreement
.venv/bin/python scripts/measure_s14c_selection_disagreement.py --stage associate --manifest docs/S14C_EXECUTION_MANIFEST.json --input-result results/S14C_selection_disagreement --output results/S14C_exploratory_association
```

以上是待根执行的命令，没有在本次准备运行。脚本拒绝既有输出目录。manifest使用 `s14c-selection-disagreement-v1`、`source_sha256`、恰好32项预测侧 `inputs` 以及单独的 `score_input`。后者只能指向既定S12 records.json；measure阶段只核该路径及SHA的manifest格式，不打开文件。

measure先缓存32份固定路径字节并全部核SHA，再解析两份CSV和30份JSON。points仅把phase/block/stride/point_id/m/radius转成输入，旧W/B/A/D不参与；帧表使用质心及来源身份，像素数只保留为结构信息，不作权重。沿原四图/14候选/NMS记录核身份，保存共同域逐点pair分量、25格来源数、三种覆盖率、主差值与三个固定方向基线。空共同域保留null和状态，同行相机基线仍保留。保存的CSV空格值表示JSON null。

measure的八个载荷文件为rows.json、rows.csv、point_details.json、selection_provenance.json、input_identity.json、frozen_manifest.json、source_snapshot.py、run_metadata.json。第九文件measure_seal.json含这八项SHA；它不含自身SHA。根执行调用者需另核该seal和全部输出身份。标签联结前根核测量封存、身份及完成记录；associate只在核完整seal、SUCCESS、同一源码/manifest、24行以及measure评分读取0后打开既定评分文件。不同实现的全量数值复核在两阶段完成后进行；独立核验器内部先从预测输入重建测量，之后才首次读取标签。输入32份在associate仅做字节身份检查，不重新提取或优化。

associate精确核24主条件的键、候选顺序、原四图顺序、整数分子/分母和保存support，标签复用 `-geometry14_minus_pose14_pp` 并精确核 `100*(P.support-G.support)`。不把改换运算顺序的整数差式当逐位基准。输出全部24行标签联结和8组×4指标的signed Spearman；场景S7/S8各12，六块各4，无混合场景rho。每组四量使用同一有效query集合；平均秩仅按精确相等并列，n<3或对应常量rho保留null与原因。来源或相机基线常量不使其他量失效。

完整重复选择对/重复x的计数由根从已独立核验的24行及来源文件报告，不新增可筛选指标。两场景已见且相关，输出不构成模型优越性、独立信息、校准风险、新方法或视频结果。

人工检查脚本 `scripts/check_s14c_artificial.py` 从自身字面量创建独立synthetic_root，不读取真实CSV/JSON/NPZ；39项检查覆盖选择不变性、固定质心像素重复、k=2恒等式、不均衡来源、空域null、25格、基线方向、ties/常量/n<3、非法半径/ID、标签错位/候选顺序/分母、seal前标签不可读、源/输入变更和既有目录保护。其完整人工measure在评分路径尚不存在时成功，随后才写入人工评分并验证associate。预期失败目录全部保留。

初版人工检查在UTC 2026-09-06T06:41:46.513174–06:41:46.565972通过39项。随后审查失败计数路径，发现先整体赋值会在中途解析失败时少记已解码输入，故在真实读取前将CSV/JSON计数移到每次实际解码后。旧源码/检查器保存在 `work/S14C_implementation/pre_counter_revision/`，初版人工目录保留。最终版人工检查于UTC 2026-09-06T06:42:13.893725–06:42:13.942860同样通过39项；详见artificial_v2/receipt.json。这个修改只修正失败回执计数，不改变测量公式。

使用已有 `.venv` Python3.12与NumPy2.3.5，无安装、下载、模型运行或Claude模型/CLI调用。本地Claude scientific-critical-thinking用于反例、条件域偏差、缺测、相关非因果与证据等级；Supervisor路径由独立设计作者在草案中实际应用。固定协议表格、公式和机器来源已经可审，没有加入无必要的AI示意图。当前是代码实现，所需字段由原writer静态确认，无新文献事实主张而不重复检索。

准备阶段读取：AGENTS、当前RESEARCH_MEMORY、最新RESEARCH_LOG、S14B结果说明、S14C设计草案、S14A提取器字段接口、S14B writer表头、S12 writer评分字段和上述本地SKILL。没有打开真实的32输入、标签文件、S14A逐query特征、真实NPZ/原图，也没有重跑成功S14B。代码数值正确性仍由不同作者前审与独立核验负责，作者39项人工自检不能代替它们。
