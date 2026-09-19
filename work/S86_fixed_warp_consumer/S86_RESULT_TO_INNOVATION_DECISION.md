# S86 实测之后：保留数值收益，拒绝软融合新方法主张

实际开始 2026-09-10 22:21:33 UTC；文本/已核分数读取至 22:23，按 root 新指示于 22:24:16 UTC 实际查看四目标六列总览。本文是结果后的决策，不是事前预测。状态仍为 NO_METHOD_SELECTED / novelty_authorization=NONE / new_method_validated=false。

## 1. First impression：有用的消费者适配结果，尚非新方法

本批应用 [idea-evaluator](</Users/rocket/.codex/skills/idea-evaluator/SKILL.md>) 及其 fatal-flaws 规则。评估对象是“把固定历史 warp 的多步 soft clean 融合升级为创新主张”，不是否定已经完成的普通强基线科研。论文类型目前最多是既有机制在特定消费者上的 New Setting/适配证据；没有新问题或新机制被确认。

**实测支持的一句话：在一个已见静态场景、四个相关目标、一次共同噪声下，固定 50 步 Gguide 的 emitted uint8 RGB MSE 低于当前 λ=.25 的两个末端对照及 G0。** 全 16 行如下，来自 FRAME_SCORES.csv；各帧 331776 像素、995328 通道，原指标按 255² 归一化，四帧等权。

| 目标 | G0 | Gpaste | Gterminal | Gguide |
|---|---:|---:|---:|---:|
| 20 | 0.084403 | 0.054283 | 0.059402 | 0.036913 |
| 21 | 0.148326 | 0.097893 | 0.107796 | 0.045401 |
| 22 | 0.164819 | 0.118518 | 0.128373 | 0.068264 |
| 23 | 0.127119 | 0.093179 | 0.097195 | 0.059111 |
| 四帧均值 | **0.131167** | **0.090968** | **0.098192** | **0.052422** |

原主差 guide−terminal = −0.045769379867616554；guide−paste = −0.038545789994676734；guide−G0 = −0.07874444524001062。每个目标的三组差均为负，支持区和孔洞区亦均同方向。区域结果仍是固定 mask 下的描述：孔洞变好不证明正确补全，支持区变好不证明真实可见性；不能把相关像素、四目标或区域当独立场景。

不同作者消费审查 PASS：123 项已保存算术/保护检查、50 步融合核验；没有重跑 denoiser/VAE，不能称模型外部复现。评分审查 PASS：16 行/48 区域、821 个精确标量比较、174 个 Fraction 标量；其已记录浮点最大差 1.3877787807814457e−17。本文仅读这些 JSON 检查条目和分数，不另读 NPZ/NPY 或再次评分。

**视觉失败必须同时保留。** root 报告了 Gguide 的重影、涂抹与形状模糊；本岗位随后实际看了同一 [4×6 总览](</Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/work/S86_fixed_warp_consumer/visuals_01/overview_4targets_6columns.png>)，在显示器/桌边等处也看到重复轮廓，21–23 的 Gguide 尤其模糊，20 亦可见叠影。此次查看工具将 3540×2720 缩为 1790×1376，未逐张原尺寸复查。这是事后、非盲人工观察，**不是新感知分数或盲评**。它足以阻止“全面画质更好”的措辞，不改写原 MSE 胜出。

## 2. Fatal-flaws：最多两项，先否掉不成立的论文叙事

| 项 | 严重度与具体证据 | 决策 |
|---|---|---|
| F1：将已有核心算子称新方法 | **CRITICAL，限于此新颖性主张。** 固定 warp 调制 clean 估计、再进入采样已有直接公式与实现先例；换成 CUT3R/VMem、四历史、avg8 或 .25 不产生新的作用机制。 | Reject and Pivot：不再包装 soft 融合新算子。不能靠更好 MSE、命名或多做消融修复这一主张。 |
| F6：从本指标推“去噪反馈理解了几何、总体画质/长期动态更好” | **MAJOR。** 本批同时改变前 49 步注入及全部后代，累计量不同；只有同场景同噪声、非盲选图与 RGB MSE，而且出现可见模糊。 | 缩为固定策略的条件效果。先用最便宜普通对照挑战收益必要性，后续几何/感知主张要有自己的可识别测量与未见事件。 |

这次**没有**触发 skill 中“核心机制已被本次数据击败”的规则：Gguide 确实赢了事前固定的 .25 对照。否决的是创新/过度解释，不是抹去数值结果。因 F1 已达 CRITICAL，按 skill 的短路规则不输出装饰性的五维打分、生命周期年限或录用预测。

新颖性依据复用此前局部原文及本轮已读代码审查，不用摘要替代方法：

- **Meng You、Zhiyu Zhu、Hui Liu、Junhui Hou，NVS-Solver: Video Diffusion Model as Zero-Shot Novel View Synthesizer，ICLR 2025。** [v2 §4.1 式 11–13/§5](https://arxiv.org/html/2405.15364v2)：clean 凸调制先例；[固定官方代码](https://github.com/ZHU-Zhiyu/NVS_Solver/blob/40c6555e53f45d6532a00b5c1e13aaa120dc9973/src/diffusers/schedulers/scheduling_euler_discrete.py#L923-L970) 实为 C×H×W 标量差排序后的硬替换。它明确面对直接平均导致模糊的问题，是未来普通强反方；代码的孔洞计数、ties、日程与 S86 不等，尚未在本机适配/运行。
- **Chenxi Song 等，Taming Video Models for 3D and 4D Generation via Zero-Shot Camera Control / WorldForge，CVPR 2026。** [v3 §3](https://arxiv.org/html/2509.15130v3)：已有 clean/warp 约束及进一步修正；S86 无其完整 IRR/FLF/DSG，不能将简化融合称原创或完整复现。
- **Zhenghong Zhou、Jie An、Jiebo Luo，Latent-Reframe: Enabling Camera Control for Video Diffusion Model without Training，ICCV 2025。** [已读 v1 §3](https://arxiv.org/html/2412.06029v1)：已有中途重投影/编码/继续去噪；几何来自生成中间态，与本批固定真实历史输入不同，但“投回去噪”概念已覆盖。

具体原文范围和版本差异见 NEAREST_GUIDANCE_NOVELTY_AUDIT.md、NVS_SOLVER_SOURCE_COMPARISON.md、NVS_BOUND_TRANSFER_LIMITS.md。本轮只新增打开三篇作者 arXiv 元数据页，核题名/作者/版本，未重新深读正文或扩展论文清单。

## 7. Verdict：只推荐一次便宜的反证，先于再跑长链

**Reject and Pivot（针对软融合新方法叙事）；保留已实现基线，下一问题是“当前 MSE 优势是否也能由尚未测试的普通末端强度获得”。**

唯一建议的下一实验是**有限末端强度审计**：复用已封存 G0 真实末步状态、同 warp latent / avg8 mask / VAE / emitted uint8 规则，在 λ∈{.5,.75,1} 分别形成 Gterminal；同样对 Gpaste 使用这三个强度。既有 0 与 .25 直接复用。所有目标共享一个 λ；完整列出两族、全部强度、四目标与原 full/support/hole 指标，不许每张图选不同系数。这是一个有界控制族，不是新算法。

此审计新增 **0 次 denoiser、0 次深度模型、0 条完整去噪链**；最多三组同原 8 槽 VAE 解码及三组 RGB 合成，真实调用/成本后续实记。必须重演 G0 末步原 FP32 Euler 顺序，不能仅按精确算术等式偷换真实执行；λ=1 且 avg8 mask<1 时仍非全替换，latent 全替换也不能推出某一 RGB 区域相同。它是可替代实现的普通对照，不声称与 Gguide 等累计剂量或识别纯时机。当前仅写建议，不读取其所需数组或执行。

**为何先做它。** 两个现有末端对照只测试 .25。用最简单的人工标量反例说明混杂：g=1、初始值 0、每次算子 T(x)=.75x+.25。两次 T 得 7/16，对参考 1 的平方误差为 81/256，胜一次 .25 融合的 9/16；但单次 .5 融合误差为 1/4，已更低，单次全替换为 0。没有学习、空间结构或几何理解，也会出现“多次赢固定弱末端”。这是纸面反例，不是本机扩散结果，更不预测真实 λ 曲线。

**预定的停/走问题仅限原 MSE，不宣判画质冠军：**

- **STOP 这条必要性叙事：** 如果任一共享 λ 的普通末端策略四帧总 SSE ≤ Gguide 已有的 **13571317266**，就不再主张“达到当前 MSE 需要多步引导”；原 .25 四臂结果仍完整有效。若某个末端图更模糊，仍须照报，不能把较低 MSE 叫全面更好。
- **GO 仅到下一次机制区分：** 若这组有限普通末端全都严格更差，只支持“当前 Gguide 超过了这个有限末端族”，不证明超过连续最优 λ、真正理解几何或恢复形状。若 Gguide 重影/形状问题仍在，方法目标仍未满足；不能因为通过 MSE 检查就进入方法投稿主张。
- **INCOMPLETE：** 某强度生成/保存/评分失败保留原失败与完整分母，不略过它宣称全族被击败。

这是**看过结果后提出、用已见参考形成的事后最佳末端包络**，只用于便宜否证。报告最小 MSE 必须标记为事后选择；不能把所选 λ 的同场景分数当验证集成绩，也不靠这批图继续细搜系数。用于未来正面比较的 λ 应在独立开发资料上定好，再到未见场景检验。

此前等 Euler 系数预算的晚半程日程仍有价值，但现在不优先加一条 50 步链：c=0.3983359511819322、B=1.6658483881895556 已有纯日程及 root 复核；它只匹配 Σηλ，Σλ/非零次数仍不同，不能隔离纯时机。NVS 的普通排序替换则针对眼下可见模糊，但需另外冻结软 mask→候选、ties 与日程，不是零成本可直接调用。**本批只提交上述末端反证，不同时排队这些新臂。**

待这个便宜反方处理后，创新岗位应围绕实际“低 MSE 仍重影”的失败继续找必要机制差别；至少需要请求相机服从与形状/感知证据分开于 MSE，并面对已存在的普通选择/融合方法。本批不事后增加这些指标、不给非盲观察打分、不下载动态数据，也不从静态结果恢复旧记忆必要性假说。

## 证据身份与审读限制

- FRAME_SCORES.csv 全16行：SHA 58aca1dd8e734819c4695c4d2aeda97bccc750fb5407fc32d0d49c45280b99a5。
- ARM_SUMMARY.json：d825ff9af39ac876334941e1b5ee82ded83203cf040abbe84fe1d52f90f95f4e；CONTRASTS.json 全文：52cfb2d0176720931fba3bc69d46f9036c99b980e0d640078d1d605a754def8d。
- INDEPENDENT_CONSUMPTION_REVIEW.json：03913b38f624cc961131f67d82c908a572cc1903e5d2b587d2cb3f1cc8115fff；INDEPENDENT_SCORE_REVIEW.json：33843b76816bae4965717d898c702dc676bf8ee1c9044f10cbe40eea5a60cb7a。读状态/范围/绑定；程序遍历原 JSON 的123检查、174浮点容差和方向条目，无不通过项。未把该遍历称为第三次像素复算。
- NVS_SOLVER_SOURCE_COMPARISON.md：7d5419c1bc909452e6521a33f2e48aec7a49b4cccad03bafa88e483ff5a73845；时机稿：b26eec75c010490a5eebd1cfe55cd18463908fbd6128cb451660ef7138a17f18；root 日程审查：cce8caa6566c7b6efdc4e2d6a5d8ab6b680d6e8b5cc71c3d92533774bab444d1。三者及已有日程 RESULT、NVS_BOUND、三近邻稿实际回读。
- 本轮新网页仅 [NVS 元数据](https://arxiv.org/abs/2405.15364) 8–28、[WorldForge 元数据](https://arxiv.org/abs/2509.15130) 8–30、[Latent-Reframe 元数据](https://arxiv.org/abs/2412.06029) 8–27；取得于本批 22:23–22:24 UTC。正式会议身份沿用已存官方入口核验，方法不从摘要新增断言。
