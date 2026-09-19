# 局部深度梯度适配器（仅人工核验）

记录 UTC：2026-09-10T18:24:47.694319+00:00。实际人工检查：2026-09-10T18:23:29.946310+00:00–2026-09-10T18:23:30.302324+00:00，Torch 导入后计时 **0.355864375 秒**；项目 `.venv-cut3r`，Torch 2.7.0，CPU float32。

`gradient_preserving_optimizer.py` 提供 `with_gradient_preserving_depths(base_class)` factory，只返回局部子类并覆盖 get_depthmaps；原 VMem fork、raw runner、原合同与旧结果未改。将每次 detach/新建参数的 ParameterStack 换成直接 `torch.stack(注册深度).exp()`，保留原返回结构；支持同尺寸二维深度，形状/dtype/device不一致明确拒绝，不扩展异尺寸填充。它不设置 P/K、不初始化场景、不调用模型或优化。

人工验证使用4张2×3 log-depth：`arange(24)/10−1`。从固定原源码 AST 提取 get_depthmaps、ParameterStack、_ravel_hw，放到仅有相同注册参数结构的测试对象；没有导入完整几何类。两组的 raw [4,2,3] 与 list（4×[2,3]）输出、float32/CPU **完全相同**。对两个返回分支的平均求和损失，两组初值均35.060264587402344。

| 一次 backward + Adam(.01, betas=.9/.9) | 原 AST 链 | 局部适配器 |
|---|---|---|
| 注册深度 grad | 四个均 None | 四个均有限且非零 |
| 对标量 math.exp 导数最大差 | 不适用 | 1.0459537502782723e−7 |
| 更新的注册深度参数 | 0/4 | 4/4 |
| Adam state 数 | 0 | 4 |
| 注册参数对象身份 | 保持 | 保持；没有新注册叶 |

适配器 raw 输出为非叶 ExpBackward0；梯度到达原 ParameterList。完整24元素前值、梯度与后值在 JSON 中。这里的 2e−6 导数容差仅用于人工 float32 算术检查。**未读取真实 heads/相机NPZ/图片/深度/权重，零 CUT3R 推理、零完整场景优化。** 尚未证明真实 objective 下深度会合理变化，未测试完整 P/K 锁定、MST或清理；原数据的几何质量与创新结论仍未成立。

后续 consumer 可使用 `Fixed = with_gradient_preserving_depths(PointCloudOptimizer)` 后创建 `Fixed(...)`；须保留当前同尺寸限制，并在新合同中另核固定 P/K 和真实梯度。使用方要记录这是局部工程修复变体，不能称原 fork 原样复现。

绑定：adapter SHA `912c277c12e06e6f896cfc6e433b74e1d831ea731cf9201599f2b36f24a18b56`；checker SHA `a054d64b4bcc3164b9f9550e80a91f3923d22dd7f4f85b6c8721e7d1c245d345`；人工回执 SHA `dea084c2c4da703a20ec2a28210b0dd671ee1fab7984ea72e17413b97e7587e5`。原 optimizer SHA `f78f52eee0fc5e435e2c8b16a868174a285e7155577c11eef0f82a464e207b11`。本次为作者功能检查，不是独立验收。
