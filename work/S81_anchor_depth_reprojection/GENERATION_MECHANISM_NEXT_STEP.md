# 下一步生成选择：先建立普通的几何引导生成基线

本批起始时钟：2026-09-10 17:01:43 UTC（北京时间 09-11 01:01:43）；来源/落盘时间见 `GENERATION_MECHANISM_SOURCE_SCOPE.json`。只复核三个已有近邻和本机接入源码，**没有读取新图像/深度数组、执行生成、修改合同或结果**。本批只收到 S81 测量准备材料，本文不填入任何 S81 观察结果。`NO_METHOD_SELECTED`。

**选择：在现有 VMem 变体上实现一条普通的“历史几何重投影＋遮罩生成引导”基线，随后做一次固定历史、固定请求相机的生成对照。** 这直接改变生成过程，比继续增加相似诊断更接近 proposal 的原型与生成质量目标。当前问题仍需准确表述：S80 的接受匹配和部分可辨局部结构说明存在外观关联，但不证明接受点就是精确三维对应；大残差尚不能唯一定位成相机模块故障。

## 三个最近邻已经做到了哪里

| 已复核的一手来源 | 可迁移机制、输入与代价 | 对本项目的决定 |
|---|---|---|
| **WorldForge / Taming Video Models for 3D and 4D Generation via Zero-Shot Camera Control**，[作者 v3，2026-03-21](https://arxiv.org/html/2509.15130v3) | 由输入图像估深度/位姿，按请求相机渲染部分图与 mask；IRR 在干净 latent 估计中融合，再按调度加噪重进网络。FLF 选通道，DSG 使用引导/未引导路径差。额外推理和几何处理有成本；论文另展示 SVD 适配。 | 最贴近现有采样器。其“GT trajectory flow”来自渲染代理，不是被扣留的目标照片。标准重投影、干净预测融合、再采样纠正均已有近邻，不能换名当创新。 |
| **Latent-Reframe**，[作者 v1，2024-12-08](https://arxiv.org/html/2412.06029v1) | 中途解码预测，以 MonST3R 估时变点云/位姿并全局对齐，重拍、编码、再次去噪及补洞。需要额外几何估计和重复去噪段。v1 的相机评测只用 800 中可共同恢复位姿的 463 条，并人工调整平移尺度。 | 证明“生成中途重拍再补洞”也不是新主张；首轮不选该重型流程。不能照搬幸存样例评价，也不能把生成视频的估计相机当外部真值。 |
| **Gen3C**，[作者 v1，2025](https://arxiv.org/html/2503.03751v1) | 输入视图的预测深度构成带时间/视角的 3D cache，按请求位姿渲染，以 mask 和多视图融合条件化视频模型；§4.4 明确微调模型。缓存几何不一致仍可引入伪影。 | 是更强的已训练几何条件生成近邻。把它的渲染 latent 接入未训练过该接口的模型，不等于复现 Gen3C；本机首轮不重新训练此系统。 |

实际局部读取：WorldForge §3.1.1–3.4、§4.1 的硬件说明和附录运行时/SVD 适配文字；Latent-Reframe §3.2–3.3、算法1、§4.1–4.2；Gen3C §4.1–4.5 中缓存、渲染、融合、训练与推理文字。未查看案例图、运行官方代码或通读全部证明/实验。Gen3C v2 入口失败后采用此前已核 v1，不称最新版；论文版本不与会议 PDF 冒充逐字一致。

## 为什么这条选择能在本机实现

本次直接核了既有源码：`get_cond` 提供历史 latent、外观条件和相机射线，目标 replace 槽原本为零；`do_sample` 已有 CPU 路径、一次联合八帧采样和最后 VAE 解码；`EulerEDMSampler.sampler_step` 在 CFG 合成后、`to_d` 前持有干净预测。因而可在隔离副本中加入目标槽的空间 mask 融合，无须换 backbone 或训练新网络。[条件接口](</Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/work/S20_environment/isolated_vmem_source/modeling/pipeline.py:1124>)；[采样入口](</Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/work/S20_environment/isolated_vmem_source/utils/util.py:673>)；[实际接入点](</Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/work/S20_environment/isolated_vmem_source/modeling/sampling.py:398>)

**现有 VMem 已有几何，但当前显式条件没有目标视图 RGB warp。** 本批追到 `render_surfels_to_image` 的实际返回值是 depth、surfel index、cosine 三张图，随后用于来源计票和选帧；虽然函数说明写了 RGB render，返回接口没有 RGB。`prepare_context_data` 按索引直接取原缓存 latent/CLIP，而不是先投影到目标视图；`get_cond` 的 replace 是原历史 latent、concat/dense_vector 是相机射线，`MultiviewCFG` 调整引导强度。故新增操作补的是**在目标坐标中对干净预测施加有来源支持的空间内容约束**，不是再造检索渲染，也不是声称网络原来没有学到几何。结论仅覆盖已读显式路径，不冒充整个网络能力证明。[检索渲染返回](</Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/work/S20_environment/isolated_vmem_source/modeling/pipeline.py:397>)；[缓存取用](</Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/work/S20_environment/isolated_vmem_source/modeling/pipeline.py:517>)

建议的最小操作为 `ẑ₀′=(1−λₛM)⊙ẑ₀+λₛM⊙z_warp`，仅作用于四个目标槽，然后继续现有 Euler 更新。`z_warp` 由同一 VAE 编码历史几何渲染图；M 表示有来源支持的目标区域。第一实现只考察固定早期融合时段，结束后让普通去噪完成；时段、λ、像素 mask 到 latent mask 的规则须在输出前固定，不能据 target22 的分数调参。这里是**普通干净预测约束的简化基线**，不包含完整 IRR 的递归再噪、FLF 或 DSG，不冒充 WorldForge 复现或已获其鲁棒性。

现有 S76 已在 CPU 完成同类四目标、50步生成，但它不能保证新增路径已经可运行，也不能把论文的 A100/A5000 秒数当本机时间。实际接入后仍须核张量/噪声参数化、VAE 编码来源、mask 有效域、联合帧索引、零干预一致性和 RNG 保存；本批只核源码接入可行性。VAE 的空间感受野使 latent mask 不等于严格独立像素，不能承诺遮罩外完全不变。

## 几何信息的权限必须分开

| 信息 | 本次建议用途 |
|---|---|
| 原 A0 四张历史 `[19,18,13,12]`、其相机、已给定的四个目标请求相机 | 各臂共同允许输入；保留完整四目标 `[20,21,22,23]`，不挑更容易的单帧。 |
| 仅由上述合法历史推断的 CUT3R 几何 | 主生成基线的渲染输入。先核缓存的来源/单位；若缓存曾包含目标或更多历史，则不可复用，应通过已有本机模型仅重建允许历史。估深和对齐的真实成本单列。 |
| S81 关联的 source19 **传感器深度** | 当前用于测量，不能因为文件在本机就悄悄进入 RGB-only 生成臂。历史 RGB-D 若被明确允许，可另定义传感器辅助基线；它是新增模态/特权信息对照，不与旧 A0 称同输入。源传感器深度不是未来答案，但也不是模型预测几何。 |
| 目标 RGB/depth、目标评分及用目标拟合的几何修正 | 仅用于封存输出后的评价，不能选择 warp、校准尺度、调 mask 或融合强度。用同一 oracle depth 构造约束再按它评分，不能独立证明几何推断能力。 |

**本机关键前置是统一预测几何与 consumer 的尺度/坐标。** 建议 warp 在原光学相机坐标中计算，保留原 A0 的 consumer 归一化路径，不把已归一化的平移与未缩放的预测深度直接相乘。若历史几何在预测世界系，先仅用合法历史相机/重建建立一个一致的相似变换 `X=sRₐX̂+b`；同一变换必须同时适用于点、相机中心和深度。尺度不可辨认、退化或缓存来源不明时先停在此缺项，不能用 source/target sensor depth 或目标照片偷偷定尺度。

原 `get_translation_scaling_factor` 对完整八相机中心化并给出 α，`get_cond` 再作基轴约定和缩放；它们含原地修改，渲染必须持有独立的光学位姿副本。若把光学世界点与相机中心共同变为 `X′=α(X−c)`、`tᵢ′=α(tᵢ−c)`，在旋转/K不变时投影应与未归一化方式相同；相机基轴转换须沿 S69 已核接口只应用一次。这个可核的投影等价是普通单位/接线检查，尚未执行。不要改 K 的像素单位，也不改变 A0 八相机的中心化集合来凑结果。[现有中心化/尺度源码](</Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/work/S20_environment/isolated_vmem_source/modeling/pipeline.py:1089>)

## 一次最小生成对照与最强普通反方

固定 A0 的有序历史、相机/尺度后代、同一实际噪声流、模型与 VAE 版本、分辨率、联合帧数及原采样步数。保留三项结果：

1. **原生成 G₀**：在零干预路径与输入/随机流可证明一致时复用保存 A0；无法证明时做必要同条件重放，不把不一致归为机制收益。
2. **廉价强对照 Gpaste**：将同一预测几何的 warp 在同一可见 mask 内直接与 G₀ 作最终像素合成，洞内保留 G₀。它无需新增去噪，能直接否决“仅复制可见内容就算生成过程改善”的解释。
3. **普通引导 Gguide**：上述采样中融合版本。第一实现保持原网络前向/批形状与步数，暂不加入递归额外去噪；估深、渲染、编码、临时内存和实际耗时照实计费。这一轮不是等总算力优越性证明。

**完整 WorldForge 是方法新颖性必须面对的强普通近邻，本轮不启动其整套移植。** 简化 Gguide 即使胜过 G₀/Gpaste，也不足以战胜该近邻或支持新方法。本轮只实现上述一种 Gguide，并保留 Gpaste 反例；不再扩展基线榜单。其意义是给 proposal 的后续同预算历史选择提供一个可检查的共同生成消费者，不能把额外引导算力算成记忆收益。

评价保留四目标全部样例、支持分母和未知项；几何、内容保留及洞/边界伪影同时报告。生成引导用预测几何，评价另用已有实拍对照和独立传感器测量边界；有 warp 支持区、洞区及全图分开统计，不能仅按强制复制区评分。S80 的双向极线均值与 S81 的前向重投影也不能混成同一量。

**停止/保留决定：** 若 Gpaste 已解释全部可见区改善，或者 Gguide 增加几何支持却恶化内容/边界/洞区，则不把结果称为生成器控制改进；若 source-only 几何来源或尺度不可核，就先停在输入缺项，不用 oracle 替代主臂。只有 Gguide 在固定范围内显示超出末端复制的实用改善，才考虑扩大这条普通生成基线；仍不能宣称学习到三维世界、找到唯一根因或创新成立。

这是一项比继续加相似测量更推进原 proposal 的**下一实现选择**，不是本批已经执行的合同。它不启动有 reader/任务语义缺项的杯球实验，也不声称 S80/S81 已证明旧动态证据必要。原合同、旧结果与 `NO_METHOD_SELECTED / novelty_authorization=NONE / new_method_validated=false` 均保持。
