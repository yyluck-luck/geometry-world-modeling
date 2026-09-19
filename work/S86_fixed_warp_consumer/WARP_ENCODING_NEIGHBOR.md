# S86：带孔洞 warp 的编码近邻与普通基线边界

核验开始 2026-09-10 21:11:33 UTC；初稿落盘完成时钟 21:15:05 UTC。只读源码、配置与既有报告。本批新增两个官方源码入口，同属 LDM；没有新论文榜单、模型调用、真实数组读取或参数修改。建议由 root 在执行前统一决定，不改变已运行的臂。

**结论。** 最简单的候选处理是保留既有黑色填洞，独立传递 S85 支持 mask，使用同一 VAE 编码并冻结共同 latent；保守降采样只决定哪里融合，不能保证这些 latent 未受孔洞填充值影响。这里的“污染”专指对填充值的潜在依赖，不是已经测得的质量下降。填洞、降采样及门控都是普通处理，不是创新。

## 1. 原始实现实际做了什么

**[官方源码：LDM inpainting](https://github.com/CompVis/latent-diffusion/blob/main/scripts/inpaint.py)。** 原脚本用 H=1 表示洞，先在 [0,1] RGB 上令 masked_image=(1−H)I，再把图像及 mask 整体映射至 [−1,1]。因此洞进入编码器时为 −1，即黑色；归一化后的 0 对应灰色，二者不能混写。脚本编码 masked_image，将缩至其 latent 尺寸的 mask 拼接为条件，再采样，最后在 RGB 空间保留原图非洞区域。其 interpolate 未指定 mode；本地 PyTorch 默认为 nearest。脚本加载 inpainting_big 专用检查点，未核其条件编码器类型/训练全链；不能直接称它就是本机 ft-mse VAE，也不能据此认定 VMem 已会处理这种缺失条件。

**[官方源码：LDM Encoder/Attention](https://github.com/CompVis/latent-diffusion/blob/main/ldm/modules/diffusionmodules/model.py)。** Encoder 默认 vanilla attention，经过卷积、残差、降采样及中间 attention。AttnBlock 展平 H×W 后作全位置注意力，Normalize 使用 GroupNorm。该结构没有洞 mask 输入来屏蔽这些影响路径。此处是默认源码结构，不冒称已核任意检查点的实际配置。

**[本地源码：实际 ft-mse 路线补核]。** S83 已绑定 diffusers 0.32.2 和 ft-mse revision 31f26fdeee1355a5c34592e401dd41e45d25a493。本批新读 Encoder 与构造参数：配置未关闭默认 mid attention，编码端也有 3×3 卷积及跨空间 GroupNorm。结合既有 attention 源审，潜在跨空间影响在编码前半程已经存在。VMem wrapper 使用 posterior mean×0.18215，不作 posterior sampling；直接调用另一种 sample 接口会改变协议。没有加载权重，未检验具体输入上的影响量。

## 2. 可实施的最小建议，尚未冻结

令 W 为 [0,1] 浮点 warp，M=1 为有预测足迹；M 与上述 H 的方向相反。

1. **填值与输入。** 候选固定为 F=M⊙W，洞为 RGB 0；归一化只做一次 2F−1。保留浮点源值，不经过展示 PNG、灰格或 JPEG；黑色有效像素仍由 M=1 标识，不能用 RGB 非零推断支持。不要用目标 RGB、G0 生成内容或动态插值偷偷补洞。
2. **编码。** 沿现有 wrapper 的 mean、尺度、精度和 chunk 口径，得到 g；Gterminal/Gguide 使用同一保存字节。先核输入尺寸与合法范围，异常保留；不新增量化、随机采样或特殊 VAE 权重。
3. **mask。** 对本机 576→72 网格，可候选采用非重叠 8×8 的 min(M)；等价于任何一个洞都关闭该格。它比 nearest 的“只抽一个位置”保守，但这是本项目普通策略建议，**不是 LDM 源码原样复现**。M_lat=1 只说明这 64 个输入像素均有足迹，不说明整段 encoder 感受野均有效。mask 仍不是可见性/正确性置信度；不凭空追加腐蚀半径或质量阈值。
4. **对照。** G0 原样；Gpaste 用图像 M 与原始 W；Gterminal/Gguide 共享 g/M_lat 及终端强度。四臂的作用空间差异必须保留，不能把 RGB 与 latent mask 说成同一作用区域。λ、日程及评分均由 root 冻结，本稿未选择。

## 3. 保守 mask 不能提供的保证

**[推导，未执行]** 对两个填充值 c₁/c₂，令 F_c=M⊙W+(1−M)c，则支持格中的变化为
\[
M_{\rm lat}\odot\{E(2F_{c_1}-1)-E(2F_{c_2}-1)\}.
\]
min-pooling 并不使该式恒为零：卷积可跨单元，attention/GroupNorm 可跨全图。即使关闭 attention，也不能忽略 GroupNorm；有限边界腐蚀不是严格隔离证明。后续 decoder 的非局部性还会进一步阻止 RGB 局部保证。计算图存在影响路径，不等于每次都产生明显非零变化。

首轮不必增加填值生成臂。若日后主张“支持 latent 与填洞无关”，最便宜反证是另行冻结两种常数填值，只比较同一编码器在支持格的差；一个超过数值容差的差即可否决严格无关，有限样例无差不能证明普遍性。当前四臂若 Gguide 未胜 Gterminal，仍不能报额外多步收益；胜出也没有自动排除共同填洞偏差、编码器效应或累计干预强度。以上均是普通机制辨别，不成立新方法。

## 实读范围与版本

- 英文查询：site:github.com/CompVis/latent-diffusion scripts inpaint.py masked_image interpolate mask；site:github.com/CompVis/stable-diffusion inpainting make_batch masked_image mask encoder。搜索返回的用户 issue 评论未作科学依据。
- inpaint.py：网页全文；原始文本成功保存并全文核读，98 物理行，关键 11–30、59–62、75–97。实际 URL 为 https://raw.githubusercontent.com/CompVis/latent-diffusion/main/scripts/inpaint.py 。UTC 21:12:58.073435–21:12:58.816462，3644 B，SHA 87abe579d548519dede8ae985b379a005502a1460945356b98f15b2469b8a912。
- model.py：网页局部读 Normalize、AttnBlock/make_attn、Encoder；网页工具行号 34–35、134–196、338–423，非全文。实际 URL 为 https://raw.githubusercontent.com/CompVis/latent-diffusion/main/ldm/modules/diffusionmodules/model.py 。网页访问成功；随后归档请求于 UTC 21:12:58.817206–21:12:59.248176 遇 curl 35 TLS 失败，未重试，未保存源码字节，不能提供它的原文 SHA。两入口均为 main，未冻结 Git commit；归档字节身份只对成功的 inpaint.py 成立。回执在 warp_encoding_sources/SOURCE_RECEIPT.json。
- 本地新读：autoencoders/vae.py 45–205（Encoder；SHA 316d2971d1c9806ed9d95e191aa7a58cc054a3a8e89a5e0723fc5e6db6240a91）；autoencoder_kl.py 90–135（SHA ed47d3851678665a2cdce463052ff5e5767cb8e69b5e1f69c2126867bddd73db）。完整路径前缀为 R/work/S20_environment/site-packages/diffusers/models/。
- wrapper 全文：R/work/S20_environment/isolated_vmem_source/modeling/modules/autoencoder.py，SHA ccb94f107fd07302fa34593f7b840b3066f73548fe800e647eccfd66da473807；ft-mse config.json 全文，SHA 92d3dfb746fca211a2c9e019e285f8597412211728dce3c5bcf4eda0f2d62e7e。另核本地 torch/nn/functional.py 4453–4465 的 nearest 默认签名。
- 复用 R/work/S83_fixed_camera_geometry/LATENT_MASK_LOCALITY_BOUNDARY.md 与 LATENT_LOCALITY_SOURCE_SCOPE.json 中既有全局 attention/GroupNorm 依据；未重读 LDM 论文、GenWarp/WAVE/DDNM/interval。R 指项目根目录。

NO_METHOD_SELECTED / novelty_authorization=NONE / new_method_validated=false。
