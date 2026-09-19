# S10 浮点比较：原始文档与本机探针

结论：固定 NumPy 2.3.5 环境中，保留原 `float(np.mean(...))` 的 Python float 身份至关重要。对小反例 x=1.0000000894069672，写入 float32 后为1.0000001192092896，但原 Python float < float32 标量仍为 False；Python float < float32 数组也为 False。若将左侧转为 np.float64，或把缓冲区转为 float64，比较变 True，会改变严格覆盖顺序。

这是实际运行结果，不是从版本记忆推断。完整探针与时间在 `results/S10_renderer_edges_baseline_v2/verification.json`，当前已用两次同深度人工surfel确认强制FP64的错误实现会被拒绝。测试也覆盖略近但同一个float32舍入区间不覆盖、跨区间近点覆盖。只说明固定环境的行为，不允许把输出改变叫“精度修正”后仍声称原实现等价。

[NEP 50](https://numpy.org/neps/nep-0050-scalar-promotion.html)明确包含比较运算；[NumPy2.0迁移文档](https://numpy.org/doc/2.0/numpy_2_0_migration_guide.html#changes-to-numpy-data-type-promotion)与[NumPy2.3标量规则](https://numpy.org/doc/2.3/reference/arrays.promotion.html#detailed-behavior-of-python-scalars)解释Python标量与显式NumPy标量的不同。对于旧版legacy规则，[NumPy1.26 result_type说明](https://numpy.org/doc/1.26/reference/generated/numpy.result_type.html#notes)区分仅标量与数组混合情形；本轮没有运行1.26环境，也不宣称跨版本一致。

四份官方全文由独立代理在UTC21:07:02.338850–21:07:03.686274获取并核相关段，源SHA已再次复核；首次urllib403及成功curl回执均保留于 `work/s10_numpy_promotion_sources/`。NEP50还记录1.24起的可选promotion状态，故不能只看版本号：本次以显式比较探针锁定观察到的行为。比较输出类型仍是bool，所谓FP32/FP64指比较输入的精度。

`docs/S10_RENDERER_EDGE_AUDIT_DESIGN.md`与人工脚本另覆盖1e-15 polygon epsilon、整数边界、near/far、退化/背面、部分顶点和逐surfel先后。有限测试不是全域证明，普通向量化不是论文创新，也尚无候选速度结论。
