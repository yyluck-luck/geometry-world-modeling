# S32 保存输出的独立数值复核候选

此任务现在只准备源码、元数据和执行契约，**未读取当前 RGB、预测 NPZ、sensor-depth PNG，也未执行数值复算**。根任务全文审后，将实际 B 合同、评分合同、全部四窗终态及主评分 PASS 和封存回执 SHA 绑定到单独 `binding.json`，才可单次执行本脚本。候选保留原状；没有等文件轮询或自动启动。

沿用 Supervisor 第2章的普通强基线、负结果和证据边界，以及此前已读 Claude scientific-critical-thinking 的完整分母要求。本任务不调用 Claude 模型，不新增方法、超参数、窗口或科学实验。

## 固定对象与前置屏障

四个预定窗口顺序为 fr2_desk_j1、fr2_desk_j2、fr1_xyz_j1、fr1_xyz_j2。每窗三个端点 initial_0step、corrected_getter_400、global_rescaled_400，每端点四帧；**48 行、12 组**始终保留。缺相机的首窗固定 12 行 NA；其余三个窗口若全部 PASS，复核 36 个实测行、9 个实测组、12 张 GT、3×786,432=2,359,296 个尺度像素。整窗失败则保留额外 NA，不能重选或评分失败半成品。

启动必须明确 `--binding PATH --sha256 SHA`。binding 的 schema 为 `s32-independent-numeric-binding-v1`、status 为 FROZEN，并包含原 candidate_sha256，以及 B_contract、scoring_manifest、scoring_receipt 三个 `{path,sha256}` 引用、root_seal_receipts 清单。A 合同和选择身份在候选中预先固定。root_seal_receipts 必须非空且与正式评分合同的 upstream_seal_receipts 完全相同；绑定实际历史证据，不猜其未记录事件或宣称恢复盲测。

先核源码、两阶段合同、四份 B 终态和主评分 PASS、每个 PASS producer 的**全部输出**以及主评分全部输出 SHA。核固定帧关联、三端点 FP32/FP32/FP64 声明、已有 scorer prediction/GT seal 的身份和时间顺序；不重扫 967 项环境依赖。随后将全部所需 GT 图片重新读成字节并核原 SHA，在本复核的任何 NPZ 或 PNG 解码之前写 input_seal。之后才导入 NumPy/OpenCV 并解码。失败窗口的部分数组、缺相机窗的 sensor PNG 均不读。所有输入在末尾再核一次。

## 两套独立算式

深度评分使用先前冻结的不同作者 S28 `independent_frame` / `metric_match`，源 SHA `2bef151226649a87b5c8cc29e6bd5173b2ece63900837f100dbf4338006d40f2`。不导入主 scorer 的 loader、depth_metrics 或 aggregate。OpenCV 解码原 uint16 480×640 PNG，以整数索引 `floor(5*(2*i+1)/8)` 取目标 384×512 的中心最近邻，除 5000 得米；逐行累加 AbsRel、平方误差，`math.fsum` 合并；δ1 用严格双侧乘法不等式。既有阈值边界测试不重复运行。

每行核全部六项网格/GT/预测/δ1 计数、四个指标、metric_status、row_status、缺失原因；null 和整数必须精确一致，指标沿 S28 已冻结容差 abs=1e-12、rel=1e-10。GT 有效处任何无效预测使 AbsRel/RMSE 为 null；δ1 仍以全部有效 GT 为分母。无 confidence 筛选、远点截断、GT 尺度拟合。未读取的 NA 行计数为 null，不能填 0。

尺度用本窗所有初/末 FP32 像素，转 Python float 后逐个 `math.log(float(final)/float(initial))`，再 `math.fsum / 786432` 与 `math.exp(-mu)`，区别于生产者向量 `log(final)-log(initial)`。完整数组均须有限正值，不筛选子集。核 FP64 保存的归一 depth 每个像素等于独立 k×final（abs/rel=1e-12），核 normalization_arrays 的完整五键、log_change 全像素、四个 frame mean、mu/k，以及 decomposition 和 producer receipt 中的全域计数及 mu/k/geometric mean。该任务不重复独立计算 decomposition 的 SS/RMS 分量占比，回执清楚列明此范围。

独立重建全部 12 个四帧等权组和三种端点的两种窗级汇总。只有预定四帧或预定全窗的对应指标全有定义才能算均值；显式核 defined_frames/windows、未知与已知计数、缺失/空GT/无效预测列表。四窗总均值必须因固定首窗缺失为 NA；另报的三 pose-eligible 窗也是事前固定，失败后不得缩成两窗。再核主 CSV 全48行与全部字段。

## 保存轨迹和首末状态审计

按根任务追加的有界要求，每个实际 PASS 窗口复用 S28 已冻结 trace_review，显式把它的 BASE 指向该窗 GA 目录并以 C2a 为模式；函数数学不改。逐一核全部 400 对原/梯度 JSONL：index 从0至399恰好一次、actual_adam_steps 从1至400、原线性 lr、两记录 loss/lr 对齐，四个 depth.grad 每步非 None、finite、非负 norm，所有既有统计字段均完整有限。检查内层原 GA PASS、403 objective 字段、3 PnP/1 alignment 和外层全部产物身份。

逐项核初/末完整33项 raw 与各自 metadata 的 dtype/shape/flags/内容 SHA；核内层 initial_decoded/output depth 与外层初/末端点逐字一致。四个注册 raw log-depth 的初/末全部像素通过独立 FP64 exp 对应 FP32 depth（既定 abs/rel=1e-6），不导入 Torch。首条 before 和末条 after 的 raw/depth extrema 精确对应，均值及累积 log-change/深度比例均值用 math.fsum 对应原 FP32 统计（固定 abs/rel=1e-5）；记录原 depth 是否改变，但不强制改善。首条原 loss 对初态 objective、末条 loss 对原返回的 pre-last-step loss；postfinal objective 单列，不能混为末次 step 前的 loss。

这是**全部保存日志及边界一致性审计**，不是重算梯度或证明每个梯度数值正确。最多 1200 条实际 step/梯度记录，失败窗不补造400条。

## 运行与结论范围

根任务外控 CPU1、120 秒、2 GiB RSS；脚本导入 NumPy 前设置线程环境，OpenCV 线程1。一次实际复核有 attempt/progress/input_seal/recomputed/receipt；已存在 attempt 或 receipt 就拒绝重跑。身份、shape、null 或数值不符整体 FAILED 保留，不以调容差或改 NA 掩盖。

本次只重新计算**既有保存输出**。0 模型、0 GA、0 MST、0 backward；不会产生新梯度或独立验证原优化器全部计算。PASS 仅表示完整表及普通单标量的数值一致，不表示三控改善、像素独立样本、原理创新、世界坐标修复或视频成功。S32 是原 inference/eval 入口，S21 曾用 recurrent；跨 S30/S32 的差不能只归因新窗口，主结论只比较 S32 同窗三端点。场景与部分图像早已暴露，不能称盲测。
