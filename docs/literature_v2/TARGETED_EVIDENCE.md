# 父任务补充检索：不确定性与选图的最近邻

本轮在三个独立视角之外做针对性补充；详细查询、版本、逐条两步核验与排除记录见 TARGETED_EVIDENCE.json。研究问题保持冻结任务书不变。

**FreeScale，Chenhan Jiang 等，CVPR 2026。** 完整标题检索后在CVF和arXiv核作者、标题、venue，再读原文及作者项目机制。其certainty-aware view graph以共享可靠几何的可见性建立相机联系；该事实否定“只要加置信度选图就是新方法”的宽泛新颖性说法。任务是NVS数据扩增/per-scene reconstruction，与我们的因果历史点来源关联不同。本文不由该论文数值推导本项目收益。

[CVF正式论文页](https://openaccess.thecvf.com/content/CVPR2026/html/Jiang_FreeScale_Scaling_3D_Scenes_via_Certainty-Aware_Free-View_Generation_CVPR_2026_paper.html)；[原文v1](https://arxiv.org/html/2604.10512v1)；[作者项目](https://mvp-ai-lab.github.io/FreeScale/)。VERIFIED。

**MV-DUSt3R+，Zhenggang Tang 等，arXiv 2024。** 完整题名命中作者后直接打开摘要；跨reference-view blocks为参考视图选择的稳健性融合信息。只使用这一摘要范围机制，不把标题里的2秒变成本机实测，不等同视频历史检索。[arXiv](https://arxiv.org/abs/2412.06974)。VERIFIED。

较早pixelwise MVS view-selection论文也可搜到，说明几何/光度辅助选视图有传统来源；其作者preprint和venue作者序存在差异，本轮不纳入最终书目。检索中无关LLM论说、船舶导航、物流等排除，第三方镜像/总结不作主张依据。没有命中具体decision-stability组合不等于证实新颖性。
