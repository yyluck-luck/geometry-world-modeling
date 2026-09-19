# Gterminal近邻：末步满足约束，不能证明多步响应有益

本批开始时钟：2026-09-10 20:19:16 UTC（北京时间09-11 04:19:16）；只检索两篇原始工作及其作者入口，不重读GenWarp/WAVE，不读模型/真实数组，不改S85或主账。以下区分“原文已报告”与“本项目条件代数”，不宣称新颖成立。

**具体结论。** 逐步校正clean预测、选择引导区间、逐个采样步启停测试都有先例。此次未核到与我们的固定warp、末步latent融合、同一G0终态完全相同且单列结果的Gterminal对照；这是限定读取范围内的未确认，不是“没人做过”。当前值得执行的仍是普通机制区分：全过程引导必须胜过同末步算子的Gterminal，才能保留较早干预带来额外收益的主张；这不自动证明几何推理或新机制。

## 两项最接近来源

**1. DDNM：每步clean校正是已有机制，一次终端校正也可满足测量一致性。** Wang、Yu、Zhang，ICLR 2023，[作者项目](https://wyhuai.github.io/ddnm.io/)与[官方会议列表](https://iclr.cc/virtual/2023/papers.html)确认发表。实际方法读取[arXiv 2212.00490v2，2022-12-07](https://arxiv.org/html/2212.00490v2)，§3.1 Eq.12–14（文本134–148行）、§3.2–3.3（194–206）、§4.2/Table 2（255–270）、附录E校正核心（514–540）。

它在每个反向步骤计算clean估计$x_{0|t}$，用
$$
\hat x_{0|t}=A^\dagger y+(I-A^\dagger A)x_{0|t}
$$
替换后推进下一步；附录E软化为$x_{0|t}+\lambda_t A^\dagger(y-Ax_{0|t})$。Table 2比较噪声处理与time-travel；本批未见“其他步骤完全无校正、仅末步校正”的单独结果。已核源是像素空间已知线性测量模型，DDNM+另设噪声假设；不能把预测深度warp或VAE latent mask自动当作真实线性测量。[原文§3.1、3.3及附录E](https://arxiv.org/html/2212.00490v2#S3.SS1)

**2. Guidance interval：已报告单步启停测试，但不能外推为warp末步结论。** Kynkäänniemi等，正式NeurIPS 2024，[官方论文](https://proceedings.neurips.cc/paper_files/paper/2024/file/dd540e1c8d26687d56d296e64d35949f-Paper-Conference.pdf)；实际读取[arXiv 2404.07724v2，2024-11-06](https://arxiv.org/html/2404.07724v2)，§2–3 Eq.1–6（67–106行）、§4.1–4.2（122–140）、§4.3/结论（176–186）。

Eq.5–6只在噪声区间内增强CFG，区间外$w=1$，即保留条件模型而关闭CFG外推。§4.2明确报告逐个采样步启用/关闭的测试，并指出其低估连续多步积累的负效应；因此不能把单步消融思想当新增贡献。正文没有列出每个单步的配置/结果，本批无法确认末步单独的数值与实现。它操纵条件/无条件denoiser的差，评估分布质量；不是固定warp替换，也不能证明我们末步融合无用。[原文§4.2](https://arxiv.org/html/2404.07724v2#S4.SS2)

## 两个直接反证，均是条件代数

**测量残差为零不能识别此前过程。** 对二值对角mask $M$，一次终端算子$T(d)=Mg+(I-M)d$便满足$MT(d)=Mg$，任意输入$d$都成立。例如只观测第一坐标，$g_1=1$，原预测$d=(-100,7)$，终端得到$(1,7)$；第一坐标残差为0，而第二坐标若真值为0仍错7。若$g_1$本身是错误warp，终端还会精确复制该错误。此反例由投影公式手推，不是DDNM论文或本项目实测。

**同一个末步会覆盖部分早期变化。** 令共同终端算子为
$$
T(d)=(1-w)\odot d+w\odot g.
$$
仅在两臂使用**同一固定$g/w$、末步$\sigma_{\rm next}=0$、保存位置对应，且使用精确算术**时，沿用root提出的Euler末步等价条件，记$d_G$为Gguide末步融合前的clean预测，$d_0$为G0对应量，则
$$
z_G-z_{\rm terminal}=T(d_G)-T(d_0)
=(1-w)\odot(d_G-d_0).
$$
所以$w=1$只消去相应latent位置/通道的早期差异；$w=0$处则原样保留。VAE非线性及非局部耦合意味着此式**不能推出相同RGB区域或整个结果**；这里只描述解码前latent。真实FP32必须按原Euler算术顺序实现并读回，不能把代数简式当作逐位等价替代。本批没有核root最新实际Euler运行或验证这些条件已实现。

## 现有实验仍排除不了什么

- DDNM的整体结果/噪声与time-travel消融不能替本机回答“末步就够不够”；CFG区间实验也不能替代同warp对照。没有末步单列结果不证明未做，只能记为未查证。
- Gguide只胜Gpaste，可能源于latent编码/解码与RGB贴图的差异；仍需Gterminal。Gguide胜Gterminal，只说明这组更早干预的整体作用有益，尚不能归因为特定反馈机制、错误几何被理解或正确遮挡被恢复。
- 相同每步λ不等于相同累计约束强度。作为最简单反例，忽略denoiser和其他更新，仅把同一个仿射融合连续做两次，λ=0.1等价于一次λ=0.19。真实Euler/denoiser并不必服从此简化等价，但它说明“多步胜末步”还可能是普通强度/平滑差异，不能靠术语排除。

未来最小反证沿用已提出的共同G0、Gpaste、Gterminal、Gguide，不在本批追加模型。必须保存G0真实末步clean latent、相同warp编码与终端mask/λ，不能从G0 RGB重新编码冒充。若Gguide未比Gterminal降低冻结独立参考损失超过预定容差，停止“更早引导有额外收益”的解释；若两者都劣于G0，不能以二者相对改善报总体收益。任何胜出仍保留单场景/已见参考和成本差异，不等于创新通过。

## 访问范围、失败与停止点

实际英文查询包括：diffusion inverse problems “last step” “projection” “ablation”；“DDNM” “last” “ablation”；“diffusion” “terminal” “data consistency” “projection”；“Denoising Diffusion Null-Space Model” “ICLR 2023”；“Applying Guidance in a Limited Interval” “2024”；“diffusion” “final-only” “guidance”；DDNM完整标题加arxiv/github。初批泛查询主要返回不相关结果，未采用；随后定点两篇并停止扩展。

DDNM [OpenReview论坛](https://openreview.net/forum?id=mRieQgMtNTQ)触发浏览器验证页，未绕过；一次未经版本确认的v3 HTML访问返回Internal Error，随后由[作者abs](https://arxiv.org/abs/2212.00490)确认实际v2并成功读取。[Guidance-interval作者abs](https://arxiv.org/abs/2404.07724)确认v2。对两份HTML检索last，DDNM另检only once/ablation，再结合上述正文核读；关键词无命中本身不能证明不存在对照。读取[DDNM官方仓库README](https://github.com/wyhuai/DDNM)的设置段用于区分简化/SVD版本，但未审具体仓库采样源码，未冻结Git commit，因此没有作代码实现完整性断言。两篇均不是全文/全部补充图审查，也未下载权重、论文图片或实验数据。上文行号是本次网页工具文本行号，只用于定位实际读取范围。

原文检索与初稿完成区间：2026-09-10 20:19:16–20:22:28 UTC；末步算术边界补充：20:26 UTC。本批没有运行生成或真实数组评分。

NO_METHOD_SELECTED / novelty_authorization=NONE / new_method_validated=false。本稿只为未来普通对照提供来源与反证边界。
