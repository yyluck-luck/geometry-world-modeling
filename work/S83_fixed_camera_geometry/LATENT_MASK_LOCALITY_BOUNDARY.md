# latent mask 不能保证图像像素局部不变

**结论：普通 Gguide 只能称“在指定 latent 位置施加融合”，不能称“只影响有几何支持的图像像素”。** 当前 ft-mse 解码器存在全局空间耦合；这是已有网络算子的边界，不是新方法。只审源码/配置和一篇原文；未加载 VAE、权重、图片或新 heads，未执行解码/生成。`NO_METHOD_SELECTED`。

**实际路径已核。** S75 原合同绑定 `stabilityai/sd-vae-ft-mse` revision `31f26fdeee1355a5c34592e401dd41e45d25a493`，本地配置与 diffusers **0.32.2** 源码；配置里的 `_diffusers_version=0.4.2` 是保存时元数据，不是实际运行版本。wrapper 解码 z/0.18215，S75 源码将原 SD2.1 构造入口替换为该 ft-mse 本地组件，并要求不 tiling/slicing；不能因 wrapper 字符串叫 SD2.1 就混淆组件身份。此次未重新加载核权重。

- **卷积跨相邻位置。** `Decoder` 有 3×3 输入/输出卷积、残差块和多次上采样；一个 latent 格不是独立的 8×8 像素块，8 倍只是网格尺寸比。
- **注意力跨整张 latent 网格。** 配置未关闭 `mid_block_add_attention`，`AutoencoderKL` 默认 True。`Decoder→UNetMidBlock2D→Attention` 把 H×W 展平；本地默认 `AttnProcessor2_0` 对全序列做 self-attention，未传几何 mask，`is_causal=False`。被融合位置的 key/value 可参与别处的输出。
- **GroupNorm 也跨空间。** 残差与输出层按组计算输入统计，eval 模式仍如此；空间一处变化可以改变别处的归一化值。仅关闭 attention、保守 min-pooling 或腐蚀有限圈边界，都不能自动得到严格的像素局部性。

上述是计算图存在影响路径，不是“所有像素每次必然明显改变”的数值结论。S82 `torch.where` 只保证**当次融合输出**中 mask=0 的 latent 元素与输入相同；其后 decoder 已足以破坏像素局部性保证，后续采样步骤还须另核。若记解码为 D，局部修改为 δz，则 δx≈J_D(z)δz；当前源码没有使区域外与修改位置之间的 Jacobian 恒为零的结构约束。

**唯一论文核对。** Rombach 等 [LDM，CVPR 2022，作者 v2](https://arxiv.org/html/2112.10752v2) §3.1 说明感知压缩与网格降采样；§4.5/Table 6 区分带/不带 attention 的 first stage；§5 提醒像素精度可能受 autoencoder 限制。这些不提供 mask 的严格局部保证。实际 ft-mse 的注意力结论来自上面的本地代码，不能拿论文中 denoiser 的 cross-attention 冒充 VAE 证据。

**最小后续验证（尚未执行）。** 另获执行授权后，冻结同一已允许 latent、解码配置、mask 与扰动幅度，仅比较 D(z) 和 D(z+M_lat⊙δ)。先验证 latent 区域外逐元素相同，再报告解码后支持内、边界环和远处的最大/平均绝对变化及超过预定数值容差的比例；零扰动作数值对照。一个远处非零差异即可否决严格局部主张；有限样例低于容差只能支持该条件下近似局部，不是普遍证明。这检查不需要目标 GT，也不衡量变化是否有益。

**已有普通对照。** Gpaste 在最终评分 RGB 数组上用 `where(M_img, warp, G0)` 替换，区域外可由构造保证逐元素相同；需放在共同解码/尺寸处理之后，并说明后续有损编码可能另改像素。Gguide 保留原方案，但同时报告区域外变化和独立质量，不能只计支持区。最终像素合成、保守 mask 降采样与这项常规局部性检查均不算创新，不为此新建框架。

核验窗口 UTC 2026-09-10 18:32:21 起；完成时间、各源码 SHA/行范围见 `LATENT_LOCALITY_SOURCE_SCOPE.json`。本地主要读取：wrapper 全文；`autoencoder_kl.py:80–130,291–335`；`vae.py:222–361`；`unet_2d_blocks.py:620–768,2749–2828`；`attention_processor.py:288–297,3215–3305`；`resnet.py:255–287,317–372`；Torch `normalization.py:228–316`。LDM 作者 v2（2022-04-13）局部读 §3.1、§4.5、§5 与 Appendix G，非全文；[CVF 官方元数据](https://openaccess.thecvf.com/content/CVPR2022/html/Rombach_High-Resolution_Image_Synthesis_With_Latent_Diffusion_Models_CVPR_2022_paper.html)已核，PDF 两种官方入口返回 403 后改读作者 HTML，未虚构 PDF 成功或与会议版字节一致。
