# S85足迹权重与颜色融合：一篇原文核验

核验日期：2026-09-10 UTC（北京时间09-11）；本批已记录时点19:20:23、19:24:03 UTC。只读原文及 `NEXT_RUN_DESIGN.md`，没有读取真实数组、执行投影或修改设计。结论：**S85当前选择是“双线性正足迹支持下的硬z-buffer颜色选择”，不是双线性加权颜色融合，也不是完整Softmax Splatting。** 这是传统算子语义核对，不是方法创新。

**唯一原文及实际范围。** Niklaus与Liu，*Softmax Splatting for Video Frame Interpolation*，CVPR 2020，5437–5446页；核[官方CVF题录](https://openaccess.thecvf.com/content_CVPR_2020/html/Niklaus_Softmax_Splatting_for_Video_Frame_Interpolation_CVPR_2020_paper.html)及[作者arXiv v1，2020-03-11](https://arxiv.org/abs/2003.05534)。局部读取[原文HTML §3.1](https://arxiv.org/html/2003.05534v1#S3.SS1)：Eq.3–6的投影/核/求和，average与linear段落，Eq.13分子与分母，以及其后尺度极限说明（工具文本499–514、582、620–622、659–701行；HTML箭头宏破碎，分段定位核公式）。不是全文、图像或官方代码审查。英文查询为“Softmax Splatting for Video Frame Interpolation Niklaus Liu 2020 bilinear kernel normalization equation”。[官方PDF](https://openaccess.thecvf.com/content_CVPR_2020/papers/Niklaus_Softmax_Splatting_for_Video_Frame_Interpolation_CVPR_2020_paper.pdf)直接访问403，只采用已成功的作者HTML；初次未核实的2003.12036v2地址访问失败，随后据题录改正，未用该错误地址作证据。

**原文算子。** 以源点投影位置 $t_i=(x_i,y_i)$、目标整数像素 $p=(u,v)$ 重记符号，Eq.4给出

$$
b_i(p)=\max(0,1-|u-x_i|)\max(0,1-|v-y_i|).
$$

Eq.5累加 $\sum_i b_i C_i$；Eq.13则为

$$
C_{\rm soft}(p)=\frac{\sum_i b_i(p)\exp(s_i)C_i}{\sum_i b_i(p)\exp(s_i)}.
$$

这里 $s_i$ 是论文的importance（原文写Z），**不能直接与S85正camera-Z混用**。权重真实进入颜色分子及归一化分母；$s_i=0$时得到归一化双线性平均。分母为零处没有该颜色定义。[依据：§3.1 Eq.4、5、13](https://arxiv.org/html/2003.05534v1#S3.SS1)。

**对S85的直接推论与纸面反例。** 以下是根据公式及当前设计作的解释，不是论文实验结果：

- 正足迹要求两轴距离均严格小于1；一般最多四个整数邻点，落在整数轴上时退化为两个或一个。零权重不参与。S85另先限制连续位置在[0,575]²，这是自己的边界政策；它会拒绝中心略越界但核仍触及边界的候选，不能称论文必然要求。
- S85先以 $b_i(p)>0$ 定义资格，再按“最小正目标Z、19/18/13/12顺序、原像素ID”取 $i_*$，最终 $C(p)=C_{i_*}$。保存的正权重**只影响资格，不控制颜色混合比例**。即使写成 $b_{i_*}C_{i_*}/b_{i_*}$，也只是一名赢家的颜色。
- 纸面例子：同一目标像素有红色(1,0,0)与蓝色(0,0,1)，足迹权重分别1/4与3/4；红点更近。归一化平均得到(1/4,0,3/4)，S85得到(1,0,0)。若误写 $b_{i_*}C_{i_*}$ 而不归一化，则变暗为(1/4,0,0)，也不是当前设计。
- 很小的正足迹同样可以凭更近Z获胜，因此有支持不等于颜色可靠或精确射线可见。若用 $s_i=-\alpha Z_i$，唯一最近候选在 α趋于无穷时成为上述软公式的赢家；同深度平局仍按足迹比例混合，而S85按身份只取一个，所以两者并非无条件等价。

后续最小实现只需逐项核“资格、排序、最终RGB、hole mask”是否与上述硬选择一致；保留weight字段不能成为“已做加权融合”的证据。`NEXT_RUN_DESIGN.md`核读身份SHA：`471f0e2748ca666559e52f287cfda06be911c4826438591bbbbc28c316cf3aae`；本文不改变该设计。`NO_METHOD_SELECTED / new_method_validated=false`。
