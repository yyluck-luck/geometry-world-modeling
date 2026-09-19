# S11 既有地图回归：独立执行前审查

结论：**PASS，限168条新增候选回归这一侧。** 无主要或次要必修项。来源人工编辑的独立脚本、协议与执行冻结不包含在本PASS内。本审查没有授权或创建执行冻结，也没有运行任何新候选。

完成时间：**2026-09-05T21:57:41.446010+00:00**。已读项目约束、最新主记忆/日志，全文核新入口和协议，并对照原renderer、S9/S10加载/观察/验证代码及S6/S7选择器。未解码NPZ、读取图像/GT、调用模型、renderer、selector或真实计时。另只读旧S10的三个JSON状态文件，确认脚本期望的 completed/PASS/passed 大小写与转换SHA字段实际存在。

## 条件域与证据继承

固定域为S7/S8各3块×2档stride×4地图×4查询，192条map/query条件，共48张旧图，仍只有24个旧相机查询、两个场景且含S7 development。新执行精确排除stride8/A0P0的24条，因此是168次候选调用、42张map，每条一次；不能称168个独立新查询、新场景或外部泛化。

24条旧条件固定继承S10 correctness/candidate的实际数组和完整trace，不根据耗时或输出挑一次。脚本核S10 completed、336调用及固定日程、672实际产物、全部清单SHA与两份通过审计；随后重开所选24份候选数组，对各自旧S7/S8参考核shape/dtype/C bytes，并对票权、配额、完整trace/decision、返回ID与数组身份逐值核对。这里只重读已存证据，不再次执行这24条候选或原renderer。

新168条与继承24条最终按condition_index覆盖0–191，缺失/重复不能通过。来源编辑条件另立范围，不混入本192条。

## 新加载器及原计算路径

新loader按stage/block/stride/arm定位对应地图、来源、pose、selection和query参考，逐案例核旧封存SHA。加载后逐数组核shape/dtype/C bytes及旧memory_digest，来源仍受原_history检查。每个map建一个独立kernel，共42个，不误用S10仅六A0P0/stride8实例的硬编码域。

每图只用前20个history pose；query20–23保持原转换。原160平方尺寸、20历史/4 context、K与surfel_Ks、初始NMS阈值、FP64几何、默认FP32排序和小占位latent/embedding保持。按arm读取对应原trace，不用A0P0参考替代其他arm。

完整get_context_info检查为原函数身份且没有计时插桩，只绑定同一冻结S10 renderer与共同observer。候选SHA、原源SHA、NumPy版本、唯一pixel loop替换/恢复AST身份均核；整个转换回执须与S10一致。S9 validate_output验证时的临时getter只返回刚产生的当前结果，不额外调用renderer；原NMS与完整decision_trace在外部记录并核旧参考。

本侧沿用的完整trace末尾要求四个ID，与既有192条参考域一致。来源不足1/3的新增人工边界不属于此侧；其记录器适配须在来源侧单独审查，不能顺手改本侧冻结S7 helper。

## 输出、失败与完整性

每次新调用前清空last_render，先记录调用开始。若renderer返回后selector或验证失败，保存本次实际数组；不会把上次缓冲误记为当前返回。成功必须有原三数组shape/dtype/C bytes全同（含±0），并有完整票权、配额、排序/NMS步骤、返回有序ID与旧参考一致；不只比较照片集合。

每条初始状态身份保存到独立JSON，完整成功trace记录state_after并逐项核对；最后再核全部实例。168次保存168个实际render与168个完整trace；coverage和清单均须完整才completed。失败立即终止并保留新目录、已完成数组/trace、failure记录和失败metadata，不改容差、不筛失败例、不重试候选。

执行前后核13项源码/许可、316个旧输入、682项S10继承证据、新审查文件，以及协议/本次和前次冻结。新316文件含旧S10的全部52输入且SHA相同。四个归档各检查精确成员、CRC、SHA和原件不变；冻结身份与实际时间必须早于执行。

数值库仅在封存后导入，NPZ随后才解码；锁定Python/NumPy/Torch/SciPy版本、Torch线程和默认dtype。Python I/O guard及600秒/16GiB预算是软守卫，不是OS沙箱或整机资源隔离。本阶段只有预算总wall时间与UTC/峰值记录，没有逐调用性能时钟、预热、速度或比值，也无原renderer/模型/图像/GT路径。

## 独立轻量核验

在标准库中仅抽取并执行CONTRACT、schedule和路径生成函数的AST，没有import新旧runner或数值库。**10项纯静态检查全部通过**：机器合同一致、192唯一完整域、168精确补集、24固定继承、42新增map、48总map、24真实query身份、316唯一输入路径、682唯一旧证据路径、无perf_counter调用。回执：`work/S11_pre_run_review/broad_pure_precheck.json`，实际UTC 2026-09-05T21:56:29.543152+00:00。路径生成只是枚举名称，未据此宣称全部文件SHA已经在本轮重算；这些执行门留给冻结后的runner与结果审计。10是软件检查项数，不是样本数。

## 结论边界与最终身份

这份PASS只说明已读版本的准备设计与代码路径未发现必修错误；真实168条候选是否通过仍未知。已有S10的提速结论不能直接扩展到本192条，本阶段也不测速度。有限既有输入回归不证明全域等价、真实连续导航、视频质量或科研新颖性。

- 入口：`a6fa8ee30fd4b72905f0c954b04193dcffb46c6b4cab91b01ed0dc22fc9b53c0`。
- 协议：`0a427ad89df0a642300034f2b78c6e1548d38aba8e9dcffbaf31049c95609926`。
- 固定候选：`3e079d0bbbaed962b24bce599a5cf7198b6bbc2891ac3c91761f4ea5c4f0e521`。
- 固定原renderer：`35825a3989f368906cba08808616f0c6922ff08d0a92c7205fddb4822652e2b3`。

完整路径/SHA见同名JSON。版本改变后本PASS不能自动沿用；旧结果、源、冻结和账本在本审查中均未修改。
