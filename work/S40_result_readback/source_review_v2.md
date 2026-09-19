# S40 保存量读回：独立增量审查 v2

时间：2026-09-07T05:09:58.188647+00:00 UTC。结论：**源码增量审查通过，尚未执行真实验收**。绑定 `readback.py`：`4c7a4208c4a67b003bae7b5574b48ce44d6034797bf2e9c5ab021e4d04e4cbf6`（382 行）；协议、作者准备和 revision 回执的引用 SHA 均一致。v1 与初审问题保持原件。

R1 已补齐单 session、两唯一非重叠批、完整 sample/sampler/cache/map 状态转换、denoiser 回调归属与计数，以及 archive 的真实 batch_id 对应。R2 已补齐 sampler 输出→samples_z、全部目标 samples→实际 encoder 输入/输出→commit，以及目标相机/K后缀和 translation 标量。新比较只读既有保存值，没有重算网络。

另核原 VAE wrapper 用 `z / scale_factor` 创建解码输入，而非对 sampler 原 latent 做原位除法；因此新增 sampler 输出字节对应没有引入已知的错误等值假设。标量比较也保留 Python scalar 与 Tensor 的原类型/位模式边界。以上均为源码观察，未加载模型验证。

CPU1、300秒、2GiB仍必须由父任务的实际外控落实并记录；协议已明确协作 tick 与硬时限的区别。本轮没有 import/运行 readback，没有跑旧人工或空 case，没有读真实预测/权重/原图/GT，没有网络请求。不能将本记录称作 S40 实际结果 PASS。

完整身份与已解决项见 source_review_v2.json。
