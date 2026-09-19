# S17可行性增补：本机CPU原生FLASH已经小型实测

记录时间：2026-09-06T11:07:00.880236+00:00。本增补不改原 [S17_FULL_VIDEO_BASELINE_FEASIBILITY.md](S17_FULL_VIDEO_BASELINE_FEASIBILITY.md) 的文件身份；它以随后取得的实际数值证据更新其中尚待验证的attention分派问题。

**PyTorch 2.7.0在本机CPU支持原代码指定的FLASH后端。** 独立agent实际运行四组小型随机张量，profiler记录 `aten::_scaled_dot_product_flash_attention_for_cpu`。因此默认应保留CPU原生FLASH，不必为了能运行而改成完整dense数学attention。原报告计算的8.009GiB只适用于假设显式保存整张分数矩阵的实现，不能用它声称本机原生FLASH实际分配了8GiB或已经内存不足。

实际预检于 **2026-09-06 UTC 11:04:17.899667–11:04:19.117603** 完成，123项均通过。它包含原生attention与独立公式、保留完整K/V的query分块备用路径、正负位置RoPE及实际FP16接口、原CUT3R Self/CrossAttention接新RoPE的人工输入对照，以及带假sampler/decoder的CPU设备传递测试。原代码在无curope时没有定义RoPE2D、`do_sample`把三个张量硬搬CUDA的失败也被实际保留。源checkout和已有环境未修改。

这些结果证明小型组件可保持预定数值容差运行，**没有加载训练权重、解码真实RGB/深度、运行完整VMem或测试CUDA/MPS数学一致性**。检查数不是精度或创新分数。新VMem隔离RoPE适配也不自动覆盖随后独立CUT3R512实验；S17B仍按自己的固定协议使用已有已审适配。

证据：[实际数值回执](../work/S17_cpu_preflight/numeric_receipt.json)，SHA-256 `7e8e8021e2fc25917971b62b5753a46550496bb833d9b219d42f1c38af341d2e`。本增补是读取该已完成回执后的判断，没有新增张量实验。主VMem gated权重、指定VAE入口和真实完整视频内存/耗时仍需解决。
