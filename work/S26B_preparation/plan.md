# S26B：保存输出导入后继续三个消费者基线（待独立审查/冻结）

**最小执行方案：导入已经算完的原 common-old 4 帧 GA 输出，继承已通过的控制相机/预处理/六头拼装验证，只运行尚未执行的 CUT/TTT/FILT 三个8图 GA。** 原S26目录和 `FAILED` 回执保持原样。0新增模型前向；若冻结后执行，只有3次新GA、1200次新Adam step，旧400步只记历史投入，不重复计为新运行。本目录当前只写新源码、diff、候选合同；没有GA/真实数组解码/GT文件读取，没有正式manifest。

## 已有结果能够复用到什么程度

S26原manifest `d517d349ed34cedaa2c2c45b812698bf02d6f4ab5220899e3e34fefe6fd847ce`；原common-old output `fcb001fdba0a728d39366ea7219db3407e807b87b3132df71fce30adf4ee31cd`。旧失败发生在原400步+clean完成、完整输出保存之后的独立NumPy clean参考核查（12/786432个conf像素不等）。模型/优化输出不因修正参考而重算。

不同作者已在 `work/S26_clean_recovery/recovery_receipt.json` 完成 **`IMPORT_VALIDATED` / passed:true** 的保存后恢复核验。新clean保留原CPU FP32 batched inverse/矩阵乘法顺序，以独立dense gather/全网格谓词实现；不是放宽容差。原pair objective仍用既有S17参考，不能把数值reference简单换成一个只有clean函数的文件。

新 `results/S26B_consumer_baseline/common_old/receipt.json` 的 `status:PASS` **只表示本次窄范围IMPORT_VALIDATED**，必须同时保存 `producer_kind:IMPORT_VALIDATED_SAVED_ORIGINAL_GA`、`validation_status:IMPORT_VALIDATED`、原失败/manifest/恢复回执与完整字节身份。它不是原S26所有门通过，也不是S26B新跑的一次GA。原未落盘的PnP细节、模块inventory、postfinal标量等沿用恢复回执的 `historical_observations_not_recorded`，不能伪造。原forward纯函数只读重算与独立目标复算是现在新做的评价，不能冒充原进程当时记录。

可接受的证据由root明确限定：既有精确400行trace、固定旧runner到异常点之前的约束检查控制流、原输入/源码身份，加当前输出schema/给定pose/positive depth/world/输入颜色/目标/clean全像素核验。独立恢复回执绑定全部输入，既不新增优化，也不恢复“从未见过数据”的状态。若恢复变为非IMPORT_VALIDATED、任何身份不符或未满足所需科学量，import必须停止；本续跑入口禁止自行重跑common4。

## 新源码与最小修改面

- `scripts/s26b_consumer_baseline.py` 从冻结S26 runner派生，`runner.diff`列出全部修改：新PREP/WORK/OUT；adapter仍导入原冻结S26目录；增加已验证结果import入口；dispatch跳过control、三源views、compat和common-old GA；调用新scorer；增加observer事件落盘。三个8图 `ga_worker` 的原GA函数、400/.01、种子、旧深度/pose、star、目标与容差不变。
- 每个8图仍按原 `original_context` 重新构造本臂所需PIL views。这是继承原输入准备语句，不是重跑三源比较/28头兼容测试，更没有新神经推理；不为省掉这一步引入额外view重建适配器。
- `work/S26B_preparation/import_previous.py` 核全部旧/恢复身份后复制已保存字节，生成新父manifest下的导入回执。共享相机NPY与三个views NPZ逐字相同；control/compat receipts保留旧PASS内容，并明确原manifest、旧receipt身份、import时间和“未重跑”的范围。
- `work/S26B_preparation/numerical_reference.py` 桥接**原S17 `pair_objective`** 与 `work/S26_clean_recovery/clean_reference_torch_fp32.py:clean_reference`，两份源码SHA均固定。真实original clean始终不变。
- `scripts/score_s26b_consumer.py` 改 `BASE` 与 `PROTOCOL` 两个赋值，并把一条 `evidence_scope` 来源说明改为“1份IMPORT_VALIDATED保存结果+3份新GA”。归一化这两项路径和该句后AST与原scorer完全一致，见 `derivation_proof.json`。GT路径/SHA、单位、像素映射、old4容差、新4指标、无效分母、原始尺度和全部封存之后才读GT的顺序不变。只使用 `score`，不运行旧metadata的 `prepare-inputs`。
- `docs/S26B_CONSUMER_SCORING_PROTOCOL.md` 继承原评分正文，并在首段声明新路径与common-old窄PASS边界。新manifest.scoring从旧对象直接继承，只改producer/output路径与新scorer/protocol SHA。

新增observer持久化只记录，不改优化：MST检查后、GA检查后、clean检查后、GA调用退出写 `observer_events.jsonl` 和最新 `observer_checkpoint.json`。保存当时计数/report/模块路径，状态为 `OBSERVED_NOT_FINAL_PASS`；最终来源/数学核验仍执行原门。这避免后续失败再次丢失已经产生的观测，但不将这些新日志反填到旧S26。

## 冻结后的唯一顺序

1. Root审完另一个作者意见后，基于 `manifest_candidate.json` 建正式 `work/S26B_preparation/run_manifest.json` 并冻结所有身份。候选中的旧source/adapter/目标参考/GT scoring配置全部保留。若恢复回执尚未完成，候选不允许冻结。
2. 新鲜受监督import worker（120秒/2GiB）只验证并复制旧字节；不解析GT或跑GA。导入common-old范围按上述合同判定。原S26失败不变。
3. CUT、TTT、FILT各一个新进程、CPU8/FP32、400/.01、单臂1200秒/16GiB、启动空盘≥10GiB。原400 Adam/MST/clean、旧参数冻结、输入颜色、schema、独立clean/目标/反投影、真实模块来源门全部照原前瞻执行。每臂不得overwrite/retry/改帧/改步数。
4. 四个新目录均有符合身份与范围的完成seal后，才运行未改数学的S26B scorer。它看新common-old窄PASS及三个完整新GA PASS；不把窄PASS的历史未录项补写成已知。

最低新增监督时限120+3×1200秒（另原scoring上限180秒），实际耗时未知。S24须已完成原barrier。本准备不创建实验结果，不启动任何上述worker。原S26已成功control/compat不重跑；保留共享条件是继续比较新4深度的充分配置选择，不是宣称导入样本提供了新的独立证据。

## 必须保持的结论边界

这是已有0.236秒、首8配对帧的组件pilot；不是新方法、长期自然失败、Surfel/查询/完整生成结果。修正独立数值参考是复现工程校正，不能当创新。common-old复用的理由是保存科学量可核验，重算同400步对该控制不增加实质信息；完整原进程historical inventory不可恢复的限制须随最终报告保留。

候选准备只读取source/JSON。为定位恢复合同曾读取独立诊断JSON；其包含保存相机的派生数值，故不声称本作者从未接触该相机的派生信息。没有打开GT文件、读取PNG/NPZ数组或执行数值验证。正式执行前仍需不同作者审查runner diff、import范围和新参考，随后由root冻结。
