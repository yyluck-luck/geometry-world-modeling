# S86：引导时机与累计干预量的解释边界

本批首个实际时钟 2026-09-10 21:22:27 UTC；正式候选合同全文核读截至 21:26:23 UTC；初稿落盘完成时钟21:28:22 UTC。仅文本、源码和两项新原始工作；无生成/参考图、科学数组、模型调用或本轮设置修改。

**结论。** 当前四臂能比较固定策略在这一个已见场景、一次共同噪声上的结果，不能把 Gguide 的优势单独归因于“时机正确”。等权重面积比较日程已有原始文献；它匹配的是指定的系数预算，仍不保证实际扰动、传播或输出变化相同。后续只建议一条同预算的日程对照，不增加新框架或方法名称。

## 当前合同，而非早期建议

正式候选 CONTRACT.json 创建于 UTC 21:25:50.094216，SHA 954c4353745280d5d3f48ac9db124b8a23aa877e1c59e9ecdd13f399416e844f。Gguide 全50步 λ=0.25；Gterminal 只在同一 G0 末步融合 λ=0.25，沿原 Euler FP32 顺序重演；Gpaste 是25% RGB 混合，并非100%贴图。共同 mask 是 **avg_pool8 覆盖比例**，不是本岗位早期 min-pool 建议；均不代表可见性置信度。

主量为四个完整 emitted uint8 画面的等权 RGB MSE：
Δ=MSE(Gguide)−MSE(Gterminal)，负值更好；同时必报 guide−G0、guide−Gpaste。合同采用精确 SSE 差判断算术符号，没有统计显著性阈值，不能擅加“显著改善”或只报最有利比较。

| 比较 | 本轮可回答的条件问题 | 尚不能分离的解释 |
|---|---|---|
| Gguide−G0 | 加入整套50步固定 warp 融合策略是否降低该参考 MSE | 几何正确性、感知质量、长期动态收益 |
| Gpaste−G0 | 原G0末端25% RGB混合是否改善该指标 | 与latent融合的等实际剂量 |
| Gterminal−G0 | 同一G0末步latent融合与原解码流程的整体效果 | VAE非局部效应、错误warp被复制 |
| Gguide−Gterminal | 额外前49步干预及全部后代传播的整体作用 | 累计干预量、施加时机、幅度与状态依赖 |

这是同一条件单位的策略比较，不是四个独立场景或人群平均因果效应。若 guide−terminal 非负，不保留本设定额外多步收益；若 guide−G0 非负，不报总体改善。任何胜出仍不能独立证实“模型理解了几何”。

## 两项直接近邻

**[原文] Wang等，《Analysis of Classifier-Free Guidance Weight Schedulers》，TMLR 2024。** [作者v2](https://arxiv.org/html/2404.13040v2) §5 明确把日程按面积归一化，满足 ∫₀ᵀω(t)dt=ωT，再比较不同形状；§5.1报告这一设计下的结果。由此不能把“等名义总权重比较时机”称为新贡献。其ω作用于条件/无条件预测之差，不是本机clean与warp的凸融合；面积相等也没有在数学上使每步向量扰动范数相等。论文§7还说明调参日程未表现出跨模型/数据通用性。本批未核官方采样代码，不能保证离散采样恰满足连续积分的数值等式。[版本与期刊字段](https://arxiv.org/abs/2404.13040)

**[原文] Bradley与Nakkiran，《Classifier-Free Guidance is a Predictor-Corrector》。** [实际读作者v2](https://arxiv.org/html/2408.09000v2) §3给出不同采样器产生不同分布的反例；§4/定理3只在相应SDE极限及匹配参数下给CFG与predictor-corrector等价。§5.3分别改变引导强度γ与校正次数K，主要作定性示例。它提醒强度、次数、离散化不能只用一个“总量”替代，未提供本项目等warp剂量证明，更不证明有限步Euler融合是后验采样。作者机构确认[TMLR 2025](https://machinelearning.apple.com/research/classifier-free-guidance)；早期是NeurIPS 2024 workshop，不能写成NeurIPS主会。所读v2为2024-08-23，未确认与最终刊版逐字一致。

## [推导] “累计量”至少有三个不同定义

在同一步的同一输入状态，记原CFG clean为 dₖ、固定warp latent为 g、软mask为 m，Euler对应系数
\[
\eta_k=1-\sigma_{{next},k}/\widehat\sigma_k.
\]
沿已核原Euler公式，融合使该步输出增加
\[
\delta x_{k+1}=\eta_k\lambda_k\,m\odot(g-d_k).
\]
这是**该步相同输入的局部差**，不是整条 Gguide−G0 的公式。其后 d、注意力、历史槽预测等都须自然重算。

- Σλ 是系数次数总量；当前 guide为12.5、terminal为0.25，但不能说实际干预强50倍。
- B=Σηₖλₖ 是带Euler步长系数的设计预算；共同 m 下可逐格乘m解释。
- Σ‖δxₖ‖ 是状态依赖的实际局部扰动量，仍不是最终输出差；向量可相消或被后续放大。不得看完结果再调λ把它强行配平，并声称识别了纯时机效应。

**手算反例，非模型实验。** x=0，g=1，普通融合 T(x)=x/2+1/2，后续普通线性传播 F(x)=2x。早施加得到 F(T(0))=1，晚施加得到 T(F(0))=1/2；两者都只施加一次λ=1/2，且这次局部注入都为1/2。不同终态无需复杂反馈或几何理解。再追加共同末端算子 Q(x)=3x/4+1/4，结果分别为1与5/8，差异仍在；对应真参考取1或0时，优劣还会反转。这否定“同系数/同一次注入量即同终态”和“时机收益必然来自新机制”，不预测真实模型表现。

## 唯一后续最小对照：重新分配同一设计预算

**尚未实施，且不进入当前四臂合同。** 在下一独立协议中，最多另跑一条同50步链，保留现有 Gguide 作对照。共同模型、warp/g/m、随机抽样流、计算精度、解码/评分、最后一步λ=0.25全部不变，只重分配前49步的预算。

明确索引 k=0,…,49。先从冻结的Euler噪声日程确定η（必须用实际 sigma_hat，非网络离散索引；同一步各槽共享标量需核）。候选新日程：k=0…24取0，k=25…48取常数
\[
c={0.25\sum_{k=0}^{48}\eta_k\over\sum_{k=25}^{48}\eta_k},
\qquad \lambda_{49}=0.25.
\]
它使前49步的B相等，并保留同一终端融合。执行前只凭噪声日程算c；若分母无效或c不在[0,1]，该候选不可执行，不能静默裁剪破坏预算。全50步denoiser及后代照常重算，不复用冻结的G0/Gguide中间clean预测冒充新轨迹。

可推翻主张是：“当前均匀分配在同设计预算、同终端下优于这种晚分配。”若晚分配MSE不高于原Gguide，就否决此具体优越性；反向结果仅支持这两个分配策略的条件差异。此对照匹配B与网络调用数，**不匹配Σλ、非零干预次数或实际扰动范数，也不识别纯时机因果效应**。权重幅度与位置联合变化仍是日程策略的一部分。不得据此宣称找到普适最优时机；已见场景和单噪声边界继续有效。

## 来源、范围与停止点

- 实际英文查询：Classifier-Free Guidance is a Predictor-Corrector paper；classifier free guidance scheduler constant ICLR 2025 guidance weight；diffusion guidance timing accumulated guidance strength equal integral schedule ablation paper；Analysis of Classifier-Free Guidance Weight Schedulers official ICLR 2025；以及前一标题限定 openreview.net / machinelearning.apple.com。只采用上述两原始工作，不采用搜索返回的二手总结。
- 第一篇：arXiv 2404.13040v2（2024-12-04）；新核§3片段、§4 Eq.4、§5面积约束及§5.1、§7结论。网页定位实读96–107、122–145、240–241，另题名/版本/期刊与相关摘要；非全文、未看论文图片。OpenReview https://openreview.net/forum?id=SUMtDJqicd 进入验证页，未绕过；作者arXiv HTML成功。期刊身份由作者arXiv期刊字段与[作者机构条目](https://researchportal.ip-paris.fr/en/publications/analysis-of-classifier-free-guidance-weight-schedulers/)检索结果交叉支持。
- 第二篇：arXiv 2408.09000v2（2024-08-23）；新核§2部分、§3定理1–2/高斯反例、§4.1–4.2/定理3片段、§5.2–5.3限制与实验说明；网页定位73–98、116–138、158–209、214–228、257–272。非全文，未核证明附录/实现代码/图像，也未把定性样例当统计验证。Apple发表页面全文33行核身份。
- 文献核验窗口：本批首钟21:22:27至正式合同回读21:26:23 UTC；首钟之前的同次工具调用已返回初检，不虚构更早精确开始时间。
- 本地：先读原则v2.11与当时已有 ADAPTER_SOURCE_PLAN、人工合同/独立核验要求；21:25:38时真实CONTRACT尚未存在，随后按root通知全文读上述正式候选。草稿 runner在该时点 SHA 98c5f2f409c88817851f1b3ff74f987879d6274c27b36995bbb69bb76f1bdbd9；仅定点读参数、编码/mask及末端对照，非本岗位完整源码前审。独立要求 SHA fcd42ae4d74042e0ae9f778fe85f4acaf5be3f65d748e9a4aa09604c5e487aa4。本文不替代root及另一作者执行前验收。

NO_METHOD_SELECTED / novelty_authorization=NONE / new_method_validated=false。没有更改当前实验，也没有读取其新输出。
