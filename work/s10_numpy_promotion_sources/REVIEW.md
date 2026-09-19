# S10 NumPy 标量与数组比较：官方原文核验

这是一份文档核验，不是本机数值探针或真实地图实验。完整 HTML 已独立保存；下载时间为 2026-09-05 21:07:02.338850 至 21:07:03.686274 UTC，逐文件 SHA 见 `sources.json`。首次 urllib 请求 HTTP 403，随后 curl 取得四份原文，没有将失败页当作证据。

| 比较操作的两个输入 | NumPy 1.26 的普通 legacy 规则 | NumPy 2.x 的普通 weak 规则 |
|---|---|---|
| Python `float` 与 `np.float32` 标量 | 全部为标量，按类型提升；以 FP64 比较 | Python 浮点精度不主导，按 FP32 比较 |
| Python `float` 与非零维 FP32 数组 | 按标量数值选最小类型；常规 FP32 范围内以 FP32 比较，超范围可能提升 | 按 FP32 比较；超范围可能转无穷 |
| `np.float64` 标量与非零维 FP32 数组 | 同样可能忽略标量精度而按 FP32 比较 | 显式 FP64 精度保留，以 FP64 比较 |

表中 FP32/FP64 指输入的比较精度；比较的输出仍为布尔值。1.26 的按值规则不是“检查每一位能否精确表示”：浮点范围内也会丢失精度。旧规则及仅标量时的例外由 [NumPy 1.26 result_type 的 Notes](https://numpy.org/doc/1.26/reference/generated/numpy.result_type.html#notes) 与 [NEP 50 的旧实现节](https://numpy.org/neps/nep-0050-scalar-promotion.html#old-implementation-of-values-based-promotion) 交叉支持。

[NumPy 2.0 迁移指南的类型提升节](https://numpy.org/doc/2.0/numpy_2_0_migration_guide.html#changes-to-numpy-data-type-promotion) 明确给出低精度 NumPy 标量混合 Python 浮点的改动，以及 FP32 数组混合显式 FP64 标量的相反方向改动。[NumPy 2.3 的 Python 标量节](https://numpy.org/doc/2.3/reference/arrays.promotion.html#detailed-behavior-of-python-scalars) 明确将规则边界标为 2.0。NEP 50 的 Abstract 明确规则适用于 comparisons，Backward compatibility 还给出浮点相等性变化的实例；因此不是仅从加法的返回类型猜测比较。

对本 renderer 的直接推论：原语句是 `avg_depth = float(np.mean(...))`，之后比较 Python `float` 与缓冲区提取出的 FP32 标量。在固定 2.x weak 规则下，把右侧换为 FP32 子数组而保留左侧 Python `float` 可保持这项提升规则；若删去 `float(...)` 留下显式 `np.float64`，可能在相邻 FP32 值附近改变严格 `<` 的胜负。保持 FP64 比较并不自动等于忠实重现原实现。

版本限制：NEP 50 记载自 1.24 起已有可选试用状态 `NPY_PROMOTION_STATE`，还有进程级设置接口。因此上述 1.26 一栏指 legacy，2.x 一栏指 weak，不能只根据版本字符串保证运行状态。精确安装版本、promotion 状态、边界比较及完整 renderer 一致性，应由执行方的实际环境探针和人工 fixture 核验。本轮没有执行它们；也没有断言跨版本 renderer 输出逐值相同。
