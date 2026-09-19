# S33 保存结果独立复核候选

这是不同作者对已完成 S33 的保存量复核。准备期只读源码、JSON 和既存 CSV 身份；实际执行由 root 绑定已完成的 producer/scorer 后单次启动。原 S32/S33 文件和主账不修改。

## 固定范围与完整分母

- 原 S32 的 48 行、12 组、3 个端点汇总保持原顺序和数值；原 JSON/CSV 的独立字节副本与合并 CSV 前缀逐字比较。不重评分旧端点。
- S33 新端点 `common_pair_scale_400` 固定 4 窗 × 4 帧：实际 3 个 PASS 窗的 12 行重算，原缺 pose 窗的 4 行为 NA；总表 64 行、16 组。若实际 producer 失败，则该窗新 4 行也为 NA，不使用部分输出。
- 读取所有 PASS producer 的输出 SHA，继承同一 S32 初态引用，全部预测及 12 个既存 sensor GT 字节先封存，然后才解码任何 NPZ/PNG。四窗终态和主 scorer 必须已完成并 SHA 绑定。
- 新深度仅原 FP32 `(4,384,512)`。GT 由 OpenCV 独立解码为原 uint16 `(480,640)`，复用已冻结 S28 的整数最近邻索引、逐行标量累加与 `math.fsum` 方法，不调用主 scorer 指标函数。GT / 5000，完整有效 GT 分母；不新增置信筛选、远深度截断、GT 尺度拟合或选窗。
- 全部新逐帧与组均值复核 AbsRel、RMSE、delta1、无效比例、整数计数、状态/NA；复核合并/独立新表 JSON 和 CSV。四窗总体含缺失，保持 NA；三窗汇总仅描述。

## 保存日志及原始状态

每个实际 PASS 窗检查 S33 初态 33 个 raw tensor 与同一 S32 初态的 shape、dtype、metadata、完整 tensor bytes 相同；完整 decoded 初态（含 objective）和 alignment 也逐字相同。验证新初末全部 66 个 raw tensor 和四张注册深度叶子的二维形状、exp 解码及保存边界统计。

复用已通过的 S32 v2 `saved_trace_review`，仅改初态 gate 文件名及两个对应字段名；由 AST 检查这三处各替换一次。保留原 400 个 optimization/gradient 记录、0…399 顺序、Adam 1…400、梯度字段 finite/non-None、保存首尾深度边界，以及 403 objective/1 MST/3 PnP/1 clean 的 producer 观测。它是保存量审计，不重反传，不宣称独立重算了梯度。

新增完整 400 个 scale trace，检查每步前后共 800 个边界的固定目标、三条正有限 raw/effective scale、公共 factor、有效 log mean、乘积和相对比例；初末 log scale 与 raw 参数连接。原协议 `abs(effective_mean − m0) <= 1e-5` 不改；独立 Python 标量与 FP32 保存值的算术比较用既定 `abs_tol=rel_tol=1e-5`。完整 3×4 矩阵的每步相等断言来自 producer 记录；不冒充独立重构了未保存的每步矩阵。

## 原协议要求的深度漂移判别

每个 PASS 窗使用全体 `4×384×512 = 786432` 个初态/新终点正有限深度，计算 `mu = math.fsum(math.log(float(new)/float(initial))) / N`。旧自由 400 步的 `mu` 来自同窗 S32 已封存 `decomposition.json`，绑定其历史 producer SHA；报告两个 mu、绝对值及 `abs(mu_new) < abs(mu_free)`。不筛像素，不计算新 k，不改深度，不使用 GT 定标。此项只回答原先规定的共同深度偏移是否减小，不能等同准确度、机制充分证明或创新结论。

不复算 S32 component SS/RMS，不新增模型/GA/MST/backward，不重哈希无关依赖树。实际旧 GT 已见，非盲测。

## 执行合同

`prepare_candidate.py` 生成 `candidate.json`（`CANDIDATE_UNBOUND_DO_NOT_EXECUTE`），绑定 reviewer 源码、两份独立 helper、正式 S33 producer/scorer 合同、scorer 全部 controls、旧表来源、全终态、旧初态 metadata 和旧 mu JSON。准备不读取 NPZ/PNG/权重。

Root 审读后另建 `binding.json`，包含 `schema: s33-independent-saved-review-binding-v1`、`status: FROZEN`、`candidate_sha256`、`scoring_manifest: {path, sha256}`、`scoring_receipt: {path, sha256}`。以实验 Python 和 `--binding … --sha256 …` 单次运行；外控 CPU 1、120 秒、2 GiB。已有 attempt/receipt 时拒绝覆盖。所有输入结束时重哈希；失败保留独立 FAILED，不修改原 PASS 或选择新窗口。

报告记录实际 UTC、资源、12 新评分/4 NA/48 导入、99 个匹配旧初态 raw、198 个新初末 raw、1200 条各类保存日志及 2359296 个预测 log-change 像素（数量随真实 PASS 窗计算）。数值尚未执行时不能写独立 PASS。
