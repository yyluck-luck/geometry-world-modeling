# S63通过后的最小生产下一步：源码评估

实际完成：2026-09-08T20:18:21.887817+00:00（北京时间 2026-09-09T04:18:21.887817+08:00）。**条件建议：S63实际通过并获独立复核后，只准备一个新声明的renderer单位工程变体，从living_room.jpg、seed44重新完成两批。当前不批准启动，也不声称S63已通过。** 本次仅源码/JSON元数据；没有读取模型、RGB、张量体，没有生成程序或修改launcher。沿用S61已核近邻：这是已知单位规范与接口工程，不是新方法或物理尺度标定。

## 1. 最小接线位置

在新目录的C2 `runtime_adapter.create_runtime` 中，完成既有模型/VAE检查后、返回runtime之前（当前478–550行），只替换该实例的 `pipeline.render_surfels_to_image`。闭包先保存原bound renderer，再调用固定S61 `render_in_canonical_units`；**对原调用者仅返回maps字典，receipt另存**，避免把二元组送入原检索函数。无需改S35 `runtime_factory.py`、原pipeline、导航、模型权重、生产几何或历史cache；包装在整个新worker内生效，不改类或模块的全局renderer。

此时S35 `run_original` 尚未安装观察器（453–460行），因此后装的原观察器仍在最外层：`原输入归档 → 单位hook → 原renderer → 规范深度输出归档`。保留wrapper的原函数来源链，适配 `require_source` 的 `inspect.unwrap`（266–274行），但这只证明底层原函数身份，**不能据此把hook称为未改原方法**。新wrapper及S61文件须明确加入新source身份集合；旧219来源数不能直接当新变体的完整来源数。安装后不得再次包观察器或递归调用自己。

复用现有create-only写盘助手（runtime_adapter:40–65）保存每次单位receipt：规则、实际中位单位、点数/正深度数、adapter和原renderer SHA、调用序号；在实际终态绑定该文件SHA。新manifest、protocol及runtime_loading中记录同一个 `retrieval_variant`，保留原ft-mse VAE的component variant，明确相对深度与 `cos/(1+z/m)` 权重变化。当前gate的差异政策只允许输入与seed（generation_gate:966–992），因此新候选必须显式加入这项科学行为差异及新输出身份，不能复用V9已消费的授权/终态，也不能只改运行名称而声称同一baseline。

## 2. 为什么应从头，不能把五份cache当完整检查点

档案seq50/52保存5份真实历史cache与map；seq52/54保存导航pose/K，seq56保存第二动作目标pose，seq64保存当次NMS阈值。这足够S63有限context接线，**不是严格生成恢复状态**。最后的Python、NumPy、Torch CPU RNG快照是seq36 sampler_output，时间17:07:58.435445Z；其后仍有解码、CLIP、几何，直到seq50的17:08:43.311060Z，没有同切点RNG快照。

这个缺口已有具体源依据：`surfel_inference.prepare_output`（173–195、403–405行）在第一批采样之后构造PointCloudOptimizer；其 `optimizer.py:29–34` 用 `torch.randn` 生成每图深度与pose，`base_opt.py:115、163–165`随机初始化pair pose。故直接恢复seq36 RNG会跳过后续随机消耗；第二批 `do_sample` 又在util.py:712–713读取全局Torch RNG产生噪声。即使之后preset覆盖了参数，也不会撤销已消耗的随机数。

此外，保存的是选择性cache/map与输出，不是pipeline/sampler/模型可变状态的完整快照。模型权重可由固定文件重载，但重载本身消耗RNG；global_step等字段可从原流程推导，仍没有完整状态恢复与切点一致性证明。不能把eval模式当成所有状态恒定的证明，也不声称这些模型必有隐状态变化。严格恢复若另做全状态及所有切点间RNG消耗证明，理论上可以研究；这不是本轮最小动作。原S35入口还明确要求空history后依次initialize、left、right，恢复会额外改变入口、trace与两批证据语义。

## 3. 一次完整新变体的计算和结果范围

复用既有worker、模型/来源绑定、外部监督和后处理路线，仅作上述明确差异。固定CPU8/FP32、seed44、576×576、T8/context4/target4、50步、400次几何迭代、`initialize → turn_left(5) → turn_right(5)`，一个worker加载一次、两批间不重置RNG，历史1→5→9。S61/S62与若通过的S63有限检查直接复用，不新增扫参或测试矩阵；新hook需一次来源/安装顺序/回执字段核查，不把过去组件检查说成新生产运行。

实测预算依据：V9第一批边界1380.447秒、失败总1382.540秒；B0完整2737.984秒（45.63分），C1完整2684.242秒（44.74分）。据此为同机完整新变体预留约45–50分钟，属于估算，不是已执行时间或成功保证。保留每批1800秒、总3600秒、进程树45GiB与空盘至少10GiB；三次历史峰值约22.53–24.09GiB，不能当作新运行实测峰值。renderer副本成本相对两批去噪很小，但本报告未测生产hook开销。

新结果按**看过C2失败后设计的工程恢复变体**单列；原V9 return1/partial、原B0/C1分数、S42阈值与原cohort状态全部保留。新变体即使生成完成，也不能补成原cohort的同条件C2行或救回已不可达的旧2/3假设。只在取得真实outer return、终态/完整档案、两批真实cache消费读回、完整九帧评分后，报告该单例是否恢复生成及其原规则分数；不用成功图反推尺度/画质收益。后处理可复用既有S58/S45数学，但须新绑定变体、终态与来源，不能原封不动宣称新输入已通过。保持 `NO_METHOD_SELECTED`。

下一动作交给root：S63最终证据核收后，制作这一处实例hook及明确变体字段的新候选，完成针对差异的独立源码审查，再决定一次完整执行。本文件只评估位置、状态缺口与成本。来源、完整SHA和读取范围见 `PRODUCTION_NEXT_STEP_SOURCE_RECEIPT.json`。
