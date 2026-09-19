# 固定历史 warp 注入去噪：三项最近邻与新颖性边界

本批实际起点 2026-09-10 21:52:16 UTC；原文查阅截至 21:55:38 UTC（北京时间 09-11 05:55:38）。先读项目 AGENTS、原则 v2.11、当前记忆、主账最新条目及 S86 CONTINUE_HERE。沿用已读 idea-evaluator 的最近邻/致命反例步骤；这不是论文全面审稿或创新评分。只读文本和原始文献，0 当前 S86 生成/参考/科学数组读取，0 模型运行，未改合同或主账。

**裁决：S86 的“用固定历史几何 warp 在去噪中约束干净预测”已有直接方法先例，不能称为新算子、新几何后验或首次免训练相机控制。** 尤其 NVS-Solver 不止概念相似：其公开公式已经给出与 S86 对应的干净预测凸组合和 SVD 更新。三项按直接重合程度比较如下；“无需训练”均指无需为该引导重新训练已有生成模型，不表示没有预训练模型、几何估计或推理成本。

| 原始工作、发表状态 | 作者实际方法：注入变量、时机与训练 | 相机/几何来源与 S86 的实质重合 |
|---|---|---|
| **NVS-Solver**，ICLR 2025；作者 v2，2025-04-02。[会议入口](https://proceedings.iclr.cc/paper_files/paper/2025/hash/d74f9efa1d8ca30b31d65cef8de7c2bf-Abstract-Conference.html)；[原文 §4–5](https://arxiv.org/html/2405.15364v2#S4) | 算法1逐步用固定 warp 调制 clean 估计 μ。DGS 将调制后的 μ 直接代入 SVD 的 VE 更新；Post 则反传修改当前带噪 latent，再反向采样。无需微调；论文设置100步。**§5说明实际不用逐点软平均，而按预测与 warp 差异排序，选择规定比例的小差异位置复制 warp，以减轻模糊。** | 输入单/多视图或单目视频、目标位姿；预测深度先构成 warp。多视图取邻近来源，动态视频取同时间帧。与 S86 同属预制几何引导 clean 预测；作者还已有随噪声/位姿距离调权及一致性选择位置。S86 不是其完整 DGS/Post 实现。 |
| **WorldForge / Taming Video Models for 3D and 4D Generation via Zero-Shot Camera Control**，CVPR 2026；作者 v3，2026-03-21。[会议入口](https://openaccess.thecvf.com/content/CVPR2026/html/Song_Taming_Video_Models_for_3D_and_4D_Generation_via_Zero-Shot_CVPR_2026_paper.html)；[原文 §3](https://arxiv.org/html/2509.15130v3#S3) | IRR 在 clean 估计中用有效区 warp latent 替换，再按调度加噪、送回网络；FLF 按流代理选通道，DSG 合并引导/原路径速度。无需微调；Wan默认前20/50步介入，另有流计算与纠正路径成本。 | 源图/视频的预测深度与位姿，经请求相机渲染为部分图和 mask。clean 空间融合直接覆盖 S86 核心操作；S86 只有50步固定软融合，没有 IRR 再噪、FLF 或 DSG，不可冒称完整复现。 |
| **Latent-Reframe**，ICCV 2025；本次方法文本为作者 v1，2024-12-08。[会议入口](https://openaccess.thecvf.com/content/ICCV2025/html/Zhou_Latent-Reframe_Enabling_Camera_Control_for_Video_Diffusion_Models_without_Training_ICCV_2025_paper.html)；[原文 §3](https://arxiv.org/html/2412.06029v1#S3) | 在选定中途步解码 clean 估计，重建/重投影、VAE重编码；重启一段去噪，已知区按较低噪声重置，未知区由网络补全，再全体去噪。无需微调；含额外几何对齐与重复采样。v1示例25步、在标号8重拍、已知区噪声低3级。 | MonST3R 从**当前生成中间视频**估点图/相机并全局对齐，再施加经过归一化/尺度调整的请求运动。与 S86 都把重投影视图带回去噪；但其几何取自生成后代，S86 取固定合法历史，并在生成前封存。 |

**最直接的算子核对（本稿代数推导，不是新实验）。** NVS-Solver 式(11)–(13)先解两个平方距离之和，得到

\[
\widetilde\mu=\frac{\mu+\lambda_N g}{1+\lambda_N},\qquad
dX=\frac{X-\widetilde\mu}{\sigma}\,d\sigma.
\]

S86 对目标 latent 元素的规则是 d′=(1−a)d+ag，a=0.25M，M 为固定 avg8 支持比例。令 λ_N=a/(1−a)，两者的**局部凸组合**相同：完全支持时 λ_N=1/3，M=0 对应零权重极限。这里仅比较精确算术中的 clean 融合形式；骨干模型、相机条件、几何、多帧组织、mask、采样日程和 FP32 运算次序不同，不能推成两条真实采样链等价。更不能忽略上述 §5 的排序复制实现，把公式等价写成“已经复现作者效果”。[NVS-Solver 式(11)–(13)与 §5 实现说明](https://arxiv.org/html/2405.15364v2#S4.SS1)

三项原文共同压缩了可用的创新说法：免训练的几何/相机控制、去噪中重投影、clean latent 内容约束、已知区/孔洞差异处理，以及用预测一致性决定约束位置/通道，都已有先例。四张历史、CUT3R、固定已知历史 P/K、硬 Z 投影、avg8 mask、λ=0.25 和替换为 VMem 消费者，是当前适配/控制条件；组合这些名字本身不构成新机制。NVS-Solver 的 Post 有反传成本，Latent-Reframe 有额外重建/采样，WorldForge 有再噪/流/双路径；S86 未执行这些完整方法，不能以较少计算的简化臂声称已胜过最强近邻。

**原文的“误差界”也不能借来保证这批预测几何有效。** NVS-Solver 式(15)是三角不等式，随后用噪声大小、位姿距离近似两类误差。这个条件模型不提供 S83 深度的已校准误差界，也未处理本项目所有候选集合/遮挡边界跳变。WorldForge 也承认严重深度错误的限制。最小反例无需生成：真实 clean 值 r=0，原预测 d=0，错误 warp g=1，a=1/4；融合后误差从0变为1/4，平方误差变为1/16。把“预测几何是合法输入”解释成“它是正确测量”，或者把与自身 warp 更一致解释成与真实视角更一致，都被这个反例否决。它是标准数学边界，不是反证整篇论文或新方法。

**只保留一个待验差别：在这个已有检索型消费者中，让同一合法历史约束经过后续采样传播，是否比在终端注入同一约束更有实际收益。** 这是体系内的实用性/机制问题，尚非新颖性主张。最便宜的第一轮否证正是已冻结的四臂，无需另拉模型：等待独立保存消费核验与固定参考评分，按原主量 MSE(Gguide)−MSE(Gterminal) 判断；若不为负，则本次全图指标上“全过程更好”不成立。同时必须保留对 G0、Gpaste 的差；若不胜其中某臂，就不能声称同时优于该普通对照。全部16行、支持/孔洞分母仍按原合同，不能挑一帧或区域救结论。

即使三组差都为负，也只支持单场景、四相关目标、一个噪声下的整套策略差异；累计干预量、VAE作用、几何精度和相机服从度仍未被单独识别。已提出但尚未运行的等系数预算时机对照是后续条件，不在此批改设置；它本身也不是新方法。若要将来主张方法贡献，仍须排除 NVS-Solver 的普通调制/选择与完整 WorldForge 等解释，本稿不追加新候选或承诺这些昂贵对照已可本机执行。

**实际来源与读取范围。** 三篇均为局部原文核读，不是全文/官方代码复现；不用第三方摘要支撑方法结论。

- NVS-Solver：ICLR 官方页完整元数据；[arXiv v2](https://arxiv.org/html/2405.15364v2)网页定位行 197–320（§3、§4.1–4.3、算法1、§5 Implementation Details），另读473–507（附录 A.1/A.2 的推导假设边界）及616–640的附录文字。未核每个证明步骤、图像/视频或运行代码；附录自身的数据流形断言不被本文当作已证明的工程保证。官方 README 只作源码入口/版本背景，未审其采样实现。[作者代码](https://github.com/ZHU-Zhiyu/NVS_Solver)。
- WorldForge：复用已核 v3，本次回读网页55、129–180、503–514、589–593（版本、§3.1.2–3.4/式(4)–(8)、§4.1、附录日程与失败限制）；没有浏览案例图。CVPR 官方索引核发表信息；直接会议 PDF 403，合法改读作者版，不声称两版字节相同。
- Latent-Reframe：复用 v1，本次回读38、93–164、269–303（§3.2–3.3/式(3)–(4)/算法1、§4.1、附录 B/C）；原文已知/未知区解释与式(4)的 mask 字母叙述存在歧义，本稿只述区域操作，不据此冻结实现极性。ICCV 官方索引核发表；直接会议 PDF 403，未绕过。v1与最终会议版的具体实现差异本次未核。
- 英文查询包括 “WorldForge ICLR 2026 Taming Video Models”（随后由 CVPR 官方记录纠正会议）、“Latent-Reframe ICCV 2025 geometry denoising camera control”、“geometry guided diffusion clean reprojection inference multi view”、“NVS-Solver official paper reprojection latent”。发现阶段看过 SteerX 的官方摘要/项目概述及 arXiv 元数据；因无需请求相机且以粒子选择为主要入口，未深读方法，改选更直接的 NVS-Solver，未将其列为第四项比较。
- 失败保留：三次 CVF 原页面/PDF 直接打开403；NVS-Solver v3 URL误试404，核元数据后使用实际存在的v2；ICLR Paper链接一次返回工具 Internal Error，方法改读作者v2；SteerX第一次链接调用参数失败，随后按返回引用正确打开元数据。均无绕过限制或循环下载；未取得的正文不称已读。
- 本地绑定：原则 SHA256 549c2bab72ad85a074babdd1f9440d0adf39f3208e011a606de521c1f3c1d698；21:44:33更新的 CONTINUE_HERE SHA256 c648b27890202c0edc1c43bcbb429935f1a622b866331d3f1fb02034bbd42ead；S86 CONTRACT SHA256 954c4353745280d5d3f48ac9db124b8a23aa877e1c59e9ecdd13f399416e844f。本文不把入口中的运行进度当作本批检查真实输出。

状态保持 NO_METHOD_SELECTED / novelty_authorization=NONE / new_method_validated=false。源范围至此收束，不继续扩展论文清单。
