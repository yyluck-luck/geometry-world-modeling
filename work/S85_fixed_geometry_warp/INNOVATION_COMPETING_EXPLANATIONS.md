# S85竞争解释：投影支持不等于可靠约束，全过程引导不等于独立收益

本批检索/文本核读实际时点：2026-09-10 20:01:16–20:03:58 UTC（北京时间09-11 04:01–04:03；这是已记录区间，不是学生工时）。只读文本/原文，0真实数组、目标RGB、模型或投影执行；不更改S85冻结设计。局部采用 idea-evaluator 的最近邻、F1/F3/F6反证步骤，按本次限定只深读两篇，不作完整论文评分或新增方法选择。

**决定：先让普通Gguide面对同一warp的Gterminal。** GenWarp已研究如何偏离错误几何约束，WAVE已做投影范围控制及采样条件干预；“几何不可靠所以加mask/attention/生成先验”本身没有新颖性。我们仍缺一个可检验的作用差别：**较早采样步骤对固定几何的响应，是否比在最后一步才施加同一latent融合带来额外的独立参考收益。** 此差别尚无本机生成证据，也尚不是新方法。

## 两项原文与它们实际覆盖的范围

| 一手来源、发表状态、版本与局部读取 | 机制及对当前候选的压力 |
|---|---|
| **GenWarp**，Seo等，正式 **NeurIPS 2024主会**：[论文集](https://proceedings.neurips.cc/paper_files/paper/2024/hash/92e886487a8354b03d8bf4416eae6d7d-Abstract-Conference.html)。实际方法源：[arXiv 2405.17251v2，2024-09-26](https://arxiv.org/html/2405.17251v2)，§3.1–3.2 Eq.1–5（文本105–143行）、§4.4（183–199）、附录B–D（208–228）；未读全部正文/图片/代码。 | Eq.4将坐标编码投影为条件，保留未投影的源特征；Eq.5联合源与当前目标特征供attention选择：$q=F_j,\ k=v=[F_i,F_j]$。它并非强制复制错误RGB。附录B已有扩大微小hole的普通对照及丢弃更多源信息的代价；C讨论伪深度下显式特征投影的不稳定；D保留远视角/训练数据限制。该双流网络需训练，不能视为现有VMem纯融合函数已实现它。 |
| **WAVE**，Park等，正式 **ICCV 2025**，11906–11915页：[官方题录](https://openaccess.thecvf.com/content/ICCV2025/html/Park_WAVE_Warp-Based_View_Guidance_for_Consistent_Novel_View_Synthesis_Using_ICCV_2025_paper.html)。采用[arXiv 2506.23518v2，2025-08-06](https://arxiv.org/html/2506.23518v2)，§3.1–3.4 Eq.1–2/Algorithm 1（108–164行）、附录E.1–E.2（436–451）、G（479–481）。先见v1后核v2，结论绑定v2；未审代码/全部图。 | 已按warp mask的IoU缩小引用范围，Eq.2以$(A_i\odot M_i)V^*$控制跨视图信息，并把warp低频用于初始噪声。E.2更换深度模型；G仍有薄结构和大视角失败。它是无需额外训练的条件/attention干预，不是深度误差概率模型；稳定跨图一致性不等于逐像素真实投影正确。 |

**原文核读后的限制判断（本报告推论）。** GenWarp提供可学习的替代来源与生成先验，不提供“attention权重=可靠概率”的校准证明。WAVE的mask重叠不是物理对应：两个错误投影也能得到很大重叠。其“非零图像即支持”文字/公式不能直接搬到S85，真实黑色与hole必须用独立mask区分；Algorithm 1先写填噪声的$W'$、后写编码$W$，本批没有源码证据去消除该记号歧义。两篇均不能替我们证明固定预测几何、硬z-buffer或VAE mask正确，更未建立同warp下Gguide胜过Gterminal的结论。

## 当前事实与标准数学解释

S81既有对应在非同步源传感深度/近似K条件下显示显著重投影不一致；对应真假、遮挡与标定仍未独立确定。S83预测拟合目标下降，而S84同一已见sensor参考的Z MAE只从约0.356167降至0.354968米；约1.199毫米的均值变化不证明目标投影更准。S85的支持仅表示存在被硬深度选择的正足迹候选，不是已证可见性、概率或目标真值。本批未查看S85实际输出，不能预报其好坏。

设源射线变换后为$a=RK_i^{-1}p$，平移为$t$，目标点$X_t=Za+t$。固定P/K、无skew的针孔内参及正目标Z，在光栅候选/赢家不切换的连续分支上：

$$
\frac{\partial u}{\partial Z}=
f_x\frac{a_x t_z-a_z t_x}{(Za_z+t_z)^2},\qquad
\frac{\partial v}{\partial Z}=
f_y\frac{a_y t_z-a_z t_y}{(Za_z+t_z)^2}.
$$

这由透视除法直接求导，是标准误差传播。纯旋转$t=0$时深度敏感性为0；平移时同样的米误差可产生不同像素位移，全图Z MAE不能直接排序目标warp质量。$\Sigma_{uv}\approx J\Sigma J^\top$需要小扰动、明确坐标单位及可信协方差，联合P/K/Z时须保留相关项；学习confidence/self-cross差不能凭名字充当$\Sigma$。硬z-buffer赢家切换、足迹跨格、遮挡显露是不连续事件，单一Jacobian不能覆盖它们。以后若试“按敏感性分配约束”，必须胜普通mask收缩/固定权重，否则仅是标准数学的包装；本批不启动该候选。

## 一项最便宜的可推翻实验，留给后续生成合同

**待验H：** 同一四目标20–23、同一warp/输入/随机初态下，Gguide较早步骤的几何响应，使独立目标参考损失低于终端latent融合；不能只要求比RGB贴图好。

root本轮提出待独立封存的Euler竞争解释：若$d'=(1-w)d+wg$，则一步变化为
$x'_{\rm next}-x_{\rm next}=(1-\sigma_{\rm next}/\hat\sigma)w(g-d)$；末步$\sigma_{\rm next}=0$时精确算术输出为$d'$。本报告未重审实际scheduler分支、舍入与保存位置，**不把root通信中的代数式冒称本批已核源码结果**。因此应加入廉价普通强对照：

| 臂 | 未来只改变什么 |
|---|---|
| G0 | 共同生成基线；保存最后clean latent及实际解码输入。 |
| Gpaste | 在G0最终RGB用同一warp和图像mask作末端贴图。 |
| **Gterminal** | 从同一G0最后clean latent出发，只做一次与Gguide相同的几何latent、mask及末步λ融合，再用同一VAE解码；历史槽不改。 |
| Gguide | 用冻结步骤/λ在采样过程中融合，末步设置与Gterminal相同；不看输出调强度。 |

这需要一份共同G0与一份Gguide真实生成；Gpaste只做末端算术，Gterminal只做末端融合/解码，不重跑去噪网络。**只有旧G0的输入、初态及保存latent全部匹配才能复用**；从RGB重新编码不是原最后clean latent，不能冒称零新增G0成本。成本按实际编码、解码、去噪调用分别报告。

最小主量可在下一合同中冻结为四目标等权的全图RGB绝对误差，使用既有目标照片的同576坐标/固定RGB01；预测封存后才重新读取参考。它是外部于warp的图像参考，但仍是已见场景，不是盲测/物理几何真值。同步报告固定支持、hole及仅由warp mask定义的边界区域与完整分母，区域定义须先封存，不能按结果挑边。空区、无效结果、全部目标及反向结果保留，不用像素数伪造独立样本量；S81式几何评分只能作另有对应/缺失限制的辅助证据。

**直接淘汰：** 若$L_{\rm guide}-L_{\rm terminal}\geq-\varepsilon$（$\varepsilon$由下一合同的数值/回放基线先定），则在该固定小实验中不支持“较早采样反馈更有益”；若只胜Gpaste而未胜Gterminal，也不能这样解释。要保留“优于当前普通对照的独立收益”，还须满足$L_{\rm guide}<\min(L_0,L_{\rm paste},L_{\rm terminal})-\varepsilon$，不能用两个融合臂都劣于G0的情况报收益。若只更贴自身warp或跨帧更相似，却未降低独立目标损失，则否决该收益主张。若有收益，仍须排除普通减弱约束/边界处理，并跨场景复验；一次四目标结果不能确立创新或校准不确定性。

## 检索与本地证据范围

实际英文查询含：“CVPR ECCV 2024 2025 novel view synthesis diffusion inaccurate geometry occlusion warped images uncertainty ViewCrafter ReconFusion”；“GeoDiffuser geometry based image editing diffusion models occlusion loss ECCV 2024”；“WAVE Warp Based View Guidance Park 2025 arxiv adaptive warp range selection depth limitations”；“Learning with Unreliability arxiv”；“GenWarp ECCV 2024”（官方域无结果）及“GenWarp NeurIPS 2024”（官方论文集确认）。发现阶段其他标题未深读/采用，没有将GenWarp误记成ECCV。

官方WAVE题录直接open返回工具Internal Error，其发表身份由官方CVF索引确认，方法由作者HTML核实；GenWarp官方PDF直接open也返回Internal Error，采用作者v2 HTML，不循环重试，不称本地已下载PDF。本批截至此处停止检索。

项目去重范围为docs/work的Markdown与TXT：WAVE未找到旧方法表；GenWarp只在VMem/AnchorWeave引用及Lyra2相关工作中出现，未找到专门机制核读表。这是限定文本检索，不是证明全项目从未提及。实际回读S81_RESULTS前65行、S84_RESULTS前65行及S85设计；SHA分别为：

- S81：0a88a42a75232db302179e252ca5823123f330db40f9c44ca964c1e54a831160
- S84：5b221e897ad5783b5a274e4b3a327a1dfdca6ed2abb29612f06ffb02997a0be1
- S85设计：471f0e2748ca666559e52f287cfda06be911c4826438591bbbbc28c316cf3aae

落盘时间依据：工具时钟2026-09-10 20:07:22 UTC；随后只作本文数学条件/比较口径自核。第一次写入调用因字符串语法错误而未执行，已纠正，没有科学执行或旧文件覆盖。结论边界保持：NO_METHOD_SELECTED / novelty_authorization=NONE / new_method_validated=false。本稿提出未来可否决的最小对照，不是执行合同，也未改变当前S85投影。
