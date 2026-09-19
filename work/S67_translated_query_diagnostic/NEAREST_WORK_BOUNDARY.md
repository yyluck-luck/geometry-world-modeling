# S67近邻边界：深度扰动到记忆选择，尚不是选择收益

完成UTC：2026-09-08T23:50:04.702687+00:00；北京时间：2026-09-09T07:50:04.702687+08:00。作者`/root/negative_result_question_triage`。本轮仅两篇一手论文及既有源码结论；S67两臂定义由root和作者分别同步确认，未读S67程序、科学结果、载荷或图片，未运行模型/renderer，未改主账。

**结论：这条问题有明确的已有机制背景，S67值得作为一次作用路径筛查；它没有建立新方法，也没有证明记忆选择错误。** 按几何找参考、用不确定性/信息增益选视角和用覆盖代理降低成本，都不能仅换到VMem就称创新。

**直接几何记忆近邻：WorldStereo，Yisu Zhang等，CVPR 2026。** 原文§3.1式(1)用深度反投影形成3D缓存；§3.3按目标与参考相机的三维FoV重叠选帧，分别编码参考图，再将目标—参考latent与世界坐标pointmap相加，并限定配对内注意力。已有“几何→选参考→条件消费”机制。§4.4/图5比较记忆组件，附录B/表5另用有真实目标视频的100场景评价：加入完整记忆提高图像保真度，但相机指标并非相对GGM逐项更优。这些是组件消融，已读范围未给出“历史投影兼容的不同相对深度→同查询所选ID”的配对试验；这一有限阅读差别不等于全领域空白。[作者原文v1](https://arxiv.org/html/2603.02049v1)

**可迁移近邻：Coverage Optimization for Camera View Selection，Timothy Chen等，CVPR 2026。** §4先将图元属性回归写成`min ||Wc−C||²`，设`G=WᵀW`满秩、观测行单位范数，式(6)得到`FIG=log(1+wᵀG⁻¹w)`；式(25)转成视向覆盖代理。相机候选受约束时，式(7)不再保证排序等价；§4.4还采用等像素覆盖和主导方向近似。它选择新增训练观测，非缓存参考ID；推导的属性回归不等于未知深度后验。§5.2/表2中Sparse条件与随机接近；§6明确依赖较准确的中间重建，忽略照明变化。附录C/表9中，加入模型自身合成视图的连续优化方案弱于覆盖选择，不能将自生成观测当成独立答案。[作者原文v1](https://arxiv.org/html/2604.05259v1)

**S67只测一段已存在的链。** 固定同一5来源缓存及同一公共平移查询：A保留515点原几何；B沿共中心射线以`λ=m0/z_i`改变位置与半径，normal/source ID不变；`m0`取扰动前的正深度中位数，公共位移为`0.1*m0`乘原query的x轴。检验历史点投影兼容、查询投影分歧，以及参与来源→配额→最终ID/context。两臂相机实际相同是必要控制，不能因各自归一化而偷换查询。这里没有概率校准的深度不确定性估计，也没有新增真实平移观测；径向人工干预不保证完整图像、遮挡和法线等价，不是自然失效频率或新视图规划算法。

| 将来S67结果 | 有限解释与不能声称的内容 |
|---|---|
| 有效扰动但最终ID相同 | 该固定案例没有经所选ID传递差异；不能说深度正确、全部几何路径无用或模型自动抗退化。若同时核context相同，才可报告这段缓存条件也未改变。 |
| 最终ID不同 | 相对深度干预影响了选择；仍不能判断哪组正确、来源有害、视频变差或新方法有效。原成员/配额/NMS链需要解释这种差异，不能直接归给一个“置信度”。 |
| 空覆盖/非有限等技术无效 | 保留无效原因，不将它记成选图鲁棒或选图失败的有效科学样本。 |

同成员、context4且`1≤k≤14`时各配额为1，因此只变票重没有此域的选图作用；几何改变成员则不受该结论约束。k不是历史长度，5批也只增加容量。S67若只能看到权重变化，已有分配机制就足够解释，无需新名字。

**真正还缺的一项证据是独立的收益判据：** 在实际有平移的观测中，证明被深度误差改变的那次来源选择，相对相同预算的普通pose/FoV选择确实造成更大的、由独立返回reference定义的损失。S67没有这样的正确性/收益标签；仅算投影差或ID差不能补上它。近邻的全局重建或组件分数也不能移植成VMem的来源效用证据。保持`NO_METHOD_SELECTED`，不改S66主评分或原C2失败身份。

读取与访问记录：

- WorldStereo复用S53指针，本轮实际重读作者HTML v1 §3.1–3.3（行114–143，式1–2）、§4.4 Memory Mechanisms（216–220）、附录B记忆消融（364–375，表5）。[CVF正式记录](https://openaccess.thecvf.com/content/CVPR2026/html/Zhang_WorldStereo_Bridging_Camera-Guided_Video_Generation_and_Scene_Reconstruction_via_3D_CVPR_2026_paper.html)通过本轮检索核标题、作者与CVPR 2026；直接open返回Internal Error。方法依据作者HTML，未声称正式PDF全文版本已比对或观看图5像素。
- Chen等论文：实际读作者HTML v1 §4.1–4.4（行81–207，式3–25）、§5.1–5.3与表1–2（208–255）、§6（256–260）、附录C与表9（400–411）；附录A证明经工具返回阅读，但本轮不将它当已完成独立数学审稿。[CVF正式记录](https://openaccess.thecvf.com/content/CVPR2026/html/Chen_Coverage_Optimization_for_Camera_View_Selection_CVPR_2026_paper.html)称CONVERGE，作者v1正文称COVER、部分表仍称CONVERGE；本报告按论文标题绑定同一工作，不虚构版本一致。未将搜索摘要作为公式依据。
- 本轮真实web检索：`site.openaccess.thecvf.com uncertainty aware view selection depth next best view 2025 2026`、`site.openreview.net uncertainty next best view depth 2025 2026`，随后仅按以上两篇完整标题定位原文。其他命中只作未采用线索，没有增加精读论文数或据其摘要下结论。
- 本轮工具时钟实际记录为2026-09-08 23:46:13 UTC及23:47:35 UTC；首批请求没有逐个本地打时间戳，不补造单请求耗时。最终访问/阅读记录时间见页首。两作者HTML可完整访问，本次只主张上述阅读范围。WorldStereo/Coverage的CVF页面直接open失败；Coverage的[正式PDF](https://openaccess.thecvf.com/content/CVPR2026/papers/Chen_Coverage_Optimization_for_Camera_View_Selection_CVPR_2026_paper.pdf)及作者站PDF在web open均失败，正式PDF的一次本机只读获取在23:47:11.233473 UTC以SSL UNEXPECTED_EOF失败，未保存/解码PDF，未伪造PDF SHA。改用作者v1 HTML完成方法核查，不扩大检索。
- 本地边界复用：[S65已核数学](../S65_observability_triage/PRIMARY_MATH_REVIEW.md)，SHA `fe2f7a38cf9879c649b671867aa5cbb5dc5dba52df1a28e3233f25f5a35196d6`；[S66下一判断](../S66_s64_camera_scoring/NEXT_SCIENTIFIC_DECISION_REVIEW.md)，SHA `62f3ee5fad654b3a2438585e42af2594cefb7021857b8f38635cf96e89ef02ae`。本轮只交付本页；不以检索篇数或来源可访问性提高创新状态。
