# 深度变化能否改变记忆选择：一次实际诊断的结果

记录UTC：2026-09-09T00:16:08.688720+00:00；北京时间：2026-09-09T08:16:08.688720+08:00。

**本轮得到一个有限的负结果：投影位置最多变化约58像素，但最终选中的四张历史帧及其全部返回缓存仍完全相同。** 不同作者已经独立复算通过。它帮助我们排除这个具体案例中的“改变深度便能通过选图改变后续条件”的解释；目前没有得到新方法收益。

可以把实验理解为：把记忆里的物体沿原视线移近或移远，再让同一台虚拟相机向旁边移动一点。我们检查这种深度差异是否会让系统改选参考照片。A使用保存的原几何，B使用预先固定的人为深度变化，两组采用完全相同的新查询相机、历史缓存和选择程序。这里只比较系统如何反应，尚不知道A或B哪一种更接近真实世界。

这是真实执行的保存数据数值实验，使用已有5个来源、515个点；不是新采集数据，也没有重新生成视频。人为改深度和虚拟平移属于实验干预，不是已经观察到的自然失败。原诊断北京时间07:59:29.452768–07:59:34.517464实际运行，外部返回0，用时5.064598秒，两组各执行一次原渲染、检索和缓存返回程序。实际读取1496份数值文件、1,631,256字节；没有读取RGB正文或调用生成模型。

| 检查内容 | 实际结果 | 能说明什么 |
|---|---|---|
| 五个历史相机下的点投影 | 最大差3.33×10⁻¹⁶，原生K坐标；预定容差10⁻¹⁰ | 对这些点，历史纯旋转投影不能区分这两种深度；不保证遮挡、法线或整图等价 |
| 同一个平移查询下的投影 | 最大位移57.9713像素，中位7.5179像素；514/515点超过10⁻⁶像素 | 本次干预确实改变了新视角中的投影 |
| 五个来源的检索权重 | 权重绝对差之和0.0268168 | 中间权重有变化 |
| 参与来源和分配数量 | 两组均为来源0–4，每个来源配额1 | 在本例中没有改变来源成员或配额 |
| 最终有序记忆ID | 两组均为[0,2,4,1] | 最终选图不变 |
| 返回给后续程序的缓存 | 相机、latent、语义embedding、标定及ID五个数组字段逐字节相同；每组348592字节 | 此次选择路径返回的条件不变；没有测量新视频效果 |

![全部515点与5个来源的诊断图](</Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/work/S67_translated_query_diagnostic/figures/S67_projection_changes_context_unchanged.png>)

图左包含全部515个点，图右包含全部5个来源，没有按结果挑点或挑来源。515个点不是515个独立场景。可编辑的[SVG图](</Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/work/S67_translated_query_diagnostic/figures/S67_projection_changes_context_unchanged.svg>)与[图片清单](</Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/work/S67_translated_query_diagnostic/figures/manifest.json>)一并保留。

独立复算由源码作者以外的agent完成：北京时间08:05:49.470835–08:05:49.925290，实际一次返回0，08:07:20.960364封存。采用另一套矩阵求逆与投影算术，实际解包比较缓存，并与原来源缓存逐项对应。历史投影残差与作者的末位差至多1.11×10⁻¹⁶，未改原容差；不能说S67所有数学位级完全一致。核验实际读取1052个科学文件、1,218,136文件字节，没有重新执行原renderer/NMS或模型，也没有重读全部1496份原输入。完整范围见[独立复核报告](</Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/work/S67_translated_query_diagnostic/INDEPENDENT_RESULT_REVIEW.md>)。

创新判断也经过原文对照：[WorldStereo](https://arxiv.org/html/2603.02049v1)已有基于3D视野重叠的参考选择和空间条件；[Coverage Optimization for Camera View Selection](https://arxiv.org/html/2604.05259v1)研究相机覆盖与信息增益，但其固定几何下的属性回归信息量不能直接当作深度正确性的后验。这两项原文使普通“几何选图”或“信息增益”不足以独立构成我们的创新。此次读取的是方法、有关实验与限制，不宣称所有论文或外链已读完；详见[近邻与适用边界](</Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/work/S67_translated_query_diagnostic/NEAREST_WORK_BOUNDARY.md>)。

**下一步先补一个能够判断对错的真实参考。** 查已有真实RGB-D序列中的平移相机、时间同步和标定，确认能否留下独立参考帧，同时设置相同候选数量和计算预算的普通相机距离/视野选择基线。先冻结新的窄问题与参考误差边界，再执行。旧TUM单RGB流不满足原RAIMA的三同步参考合同，新实验若使用它，只能另立更窄的发现性问题，不能宣称旧合同通过。若没有独立的几何或图像答案，仅有投影、权重或ID变化仍不够判断帮助还是损害。

本例不再追加视频生成，也不按看到的结果调整位移或深度重新试到选图改变。当前仍为NO_METHOD_SELECTED、new_method_validated=false、novelty_authorization=NONE；不能说已经达到PhD或CCF A方法贡献。前一阶段真实生成及其评分另见[客厅九帧结果](</Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/docs/S66_FIXED_SCORE_AND_VISUAL_RESULT.md>)：8张模型输出加1张输入，共9张，不能把模型图称为实拍照片。

本轮实际应用Supervisor的vibe-research-workflow小步执行和不同作者复核、handbook2.3隐藏假设审查、idea-evaluator的可验证性/先有问题再选方案两项筛查、本地Claude科学批判skill，以及figure-designer的全数据实验图规范。没有调用Claude模型。S65已有Gemini咨询，本轮没有为这项已固定的诊断重复咨询。绘图第一次因现有解释器缺Matplotlib在导入阶段失败，已保存回执；随后使用另一现有绘图环境成功导出，未安装依赖或改变实验环境。

可追溯证据：[结果前协议](</Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/work/S67_translated_query_diagnostic/PROTOCOL.md>)、[结果前不同作者源审](</Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/work/S67_translated_query_diagnostic/SOURCE_REVIEW.md>)、[实际外部回执](</Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/work/S67_translated_query_diagnostic/external_01/receipt.json>)、[实际数值回执](</Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/work/S67_translated_query_diagnostic/execution_01/receipt.json>)、[最终接受记录](</Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/work/S67_translated_query_diagnostic/ROOT_FINAL_RESULT_ACCEPTANCE.json>)、[完整时间主账](</Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/RESEARCH_LOG.md>)。所有旧失败、旧协议及评分保持原样。
