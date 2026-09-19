# S61 作者最终交付

`unit_consistent_renderer.py` 提供唯一入口：

```python
maps, unit_receipt = render_in_canonical_units(
    bound_original_renderer, surfels, pose, focal_lengths,
    principal_points=principal_points,
    image_width=width, image_height=height)
```

相机须已经采用原 renderer 的约定。适配器以全部正相机深度的中位数作单位，复制后一起缩放位置、半径、相机平移；保留其他量及索引次序。原 renderer 恰好调用一次，返回原 depth/index/cos 字典及明确的无量纲单位回执。不导入 pipeline、模型或图像库，不修改缓存。

唯一一轮人工有限测试实际时间：2026-09-08T18:22:45.396158–18:22:45.408174 UTC，返回 0；5 项测试、0 失败/错误，耗时 0.011846375 秒。共享长度倍率固定为 1e-9、1、1e9，R 非单位、t 非零；最大投影误差 1.4210854715202004e-13 px，半径端点误差不超过 8.526512829121202e-14 px。还验证了输入副本隔离、无效数值/无正深度时零 renderer 调用、renderer 自身失败时恰好一次调用且异常传出。这里的 renderer 全是人工 spy/数值小函数，不是原栅格化器。

检查前已固定 [协议](PROTOCOL.md)，实际结果见 [有限测试回执](FINITE_TEST_RECEIPT.json)。本阶段未新增读取 S60 真实数值载荷、未读 RGB、未调用原 renderer 或模型、未集成生产路径。root 的真实保存数据验收与不同作者审查另行完成；当前不声称 C2 已修复。

本适配器有意把检索 depth 改为无量纲数值，可能改变原 `1+depth` 权重。未来采用它生成，须声明新的工程基线变体；原 C2 V9 失败保持原样。它没有恢复真实物理尺度，也不是新方法。后续更正只能另存文件，不能改写最终 SHA。
