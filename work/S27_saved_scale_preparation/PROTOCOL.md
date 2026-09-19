# S27：保存深度的尺度与坐标诊断（事后探索，待运行）

本协议在已经看到 S26B 总体评分之后制定：共同旧四帧 AbsRel 约 83.34%，三方法新四帧约 67.83%/93.54%/67.57%（来自根任务已核报告，本准备未重读评分数组）。它不是盲测预注册，也不是新方法、修复或新 GA。按 Supervisor handbook 2.2 的 baseline→错误分类→机制，以及本地 Claude scientific-critical-thinking 的替代解释/因果边界推进。

## 最小问题和输入

先区分共同旧四帧已有的问题与三方法八帧输出的差异。固定 original4 的四份原预测，CUT/TTT/FILT 各前八份预测，共 28 份；四个原消费者保存包：共同旧4（S26 真实400步、S26B IMPORT_VALIDATED导入）与三个8帧真实400步结果；以及已经在 S23/S26B 读取的同八张传感器深度。固定使用全部帧、全部像素、全部24个star边、全部1600条真实loss记录。不运行网络、GA、MST、不导入原模型或优化器。共同旧4原FAILED永久保留；导入PASS不是追认其原执行PASS。

输入来自冻结 S26B manifest 和四个 PASS producer receipt 的既有 SHA。准备只读取源码/JSON元数据，继承数据身份，不打开任何 NPZ/PNG/优化trace。运行时先核合同和全部保存包身份，再解码保存量，最后重新读取已见传感器深度。原S26共同输出/trace与S26B导入对应文件均核SHA相同。输出只写新 results/S27_saved_scale_diagnostic，不改原表/协议/任何输入。NumPy只做终点算术，不把这称为新实验或独立外部复现。

## 坐标与算术合同

- `raw_self_z`：每帧 `pts3d_in_self_view[...,2]`，同帧光学相机轴向z，按原输出名义米单位直接比较，无轨迹Sim3/GT拟合。
- `raw_other_z_reference_only`：原 `pts3d_in_other_view[...,2]` 处于预测共享参考域；包括未消费的第0帧other头，**只报分布，不与同帧传感器深度直接评分**。self/other由两个head输出，不能假设逐点严格刚性等价。
- 原star边为 `(0,j), j=1..n−1`，实际 `consumed_anchor_z_reference_only` 必须逐字节对应第0帧self，`consumed_other_z_reference_only` 对应j帧other；已存权重仅描述，其源是原log(conf)，不可再次log。报告每边两个分布，不把重复anchor计为多张独立图。
- 原目标的坐标契约（本最小版不额外执行变换评分）：`Y=(P * adaptor) @ A.T + t`，A和t直接取已存 `pw_poses[:3,:3]`、`[:3,3]`。原返回矩阵同时缩放旋转和位移，禁止去掉尺度或再次把t乘s。如后续确需解释other的同帧z，应在该变换后再转入对应i/j光学相机；本次只报告other原坐标分布和保存pair尺度，不增加aligned评分。
- `ga_depth_z`：保存GA的每帧depth，不因clean置信度改变而筛选。原消费者的独立backprojection/clean验证已在S26/S26B完成，此次不重复。
- 仅用保存FP32数据转FP64做诊断算术。所有最终pair旋转块奇异值（含尺度）、adaptor、focal/pp、camera baseline、保存权重分布全部报告。原源函数名l1_dist实际上是欧氏范数，不称坐标L1。

## 固定分母、分布、指标

每图网格384×512=196608。分布固定全图，分别报告total/finite/nonfinite/finite-positive/zero/finite-negative；对finite全部值和finite-positive分别给 min, p01,p05,p25,p50,p75,p95,p99,max 及均值。没有置信度/距离筛选、空集合给null，不能只保留正值而不报被排除数量。

GT为原480×640 PNG整数除5000，按 `floor((2*t+1)*source/(2*target))` 最近邻映射到384×512，与S26B完全相同。GTvalid=有限且>0，全部GTvalid是分母；预测非有限或<=0是invalid。只要GTvalid中一个预测无效，AbsRel和RMSE为null；δ1仍将无效计为失败，严格ratio<1.25。GT空则全部指标null。无GT尺度拟合原误差逐帧完整输出。

另给 `sensor_to_prediction_ratio_oracle` 的全finite-positive配对分布、中位比值和完整交集数量。这是借助已见答案描述尺度差异，**不应用该比例修改预测、不输出“修复后主结果”**；也不把它当深度预测或部署时可用量。`ga_to_raw_self_ratio` 不用GT，亦报告完整有效交集和排除数，不等于迭代过程中深度变化。

固定132行深度分布：rawself28、rawother28、GA28、24边×(raw anchor/raw other)48。固定56行可评分量：rawself28、GA28。只有rawself和GA按独立帧分组给均值：common旧4；各方法old4/new4/all8，共20组。每组全部预定帧都定义时才给对应均值；pixel不是独立样本，不给显著性/选择性赢家。consumed重复anchor只保留每边描述，不汇总当独立帧。

400条trace是step前loss和学习率；报告完整1600行、首/末/最小loss；不重新计算优化目标。**没有逐步depth、post-MST初态，故不能倒造初始深度/尺度或声称400步中depth获得梯度或实际更新**。参数requires_grad/入optimizer不等于梯度有效，ParameterStack detach疑点由独立源审负责。

## 解释顺序及否决边界

1. 先并列 common原rawself、实际消费域、最终pair尺度和GAdepth。若rawself名义尺度已不对，保留输入能力/标定契约解释；若rawself尚可而GA终点差，继续区分被消费other域和优化目标，不能直接怪新方法。
2. 新8三臂共用旧depth。旧4对照用于确认继承问题；新4误差不单独证明记忆/缓存/Surfel机制。rawself与actualother不同head，rawself好不保证消费者目标好。
3. 目标的同中心缩放重参数化只说明目标层面的尺度退化可能；非零baseline、learned focal、固定旧depth与实际梯度路径均影响执行。该理论不是本次坍缩因果证明。当前真实8帧跨度仅0.235880秒，不外推长序列/视频生成。
4. 不按已见终点选择阈值、删帧、改400步/学习率/置信度或添加新修复；无init快照和逐步深度时，相应结论写 NOT_RECORDED。必要后续干预另立合同。

## 命令和当前状态

`diagnose.py prepare`：标准库元数据候选生成；没有数组/PNG/trace数值读取。

运行需根任务把审过候选冻结为 `contract.json`、status设FROZEN并提供实际SHA，然后使用本项目 `.venv-cut3r/bin/python work/S27_saved_scale_preparation/diagnose.py run --contract <绝对路径> --sha256 <冻结SHA>`。不通过此准备自动运行。输出含阶段时间/实际读取数量/全部输入前后SHA/完整行数；技术失败不自动覆盖或重试。
