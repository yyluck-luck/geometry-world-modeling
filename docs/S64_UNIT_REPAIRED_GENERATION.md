# 单位修复版本已真实跑完两批，保存数据传递通过复核

更新UTC：2026-09-08T22:34:01.965179+00:00；北京时间UTC+8。

此前客厅样例进入第二批时，检索把所有几何点都排除了，程序因此报错。本轮将已验证的统一单位换算接入原生成流程，**实际运行45分29秒，完成8张模型生成帧，加上1张输入图形成9帧历史**。不同作者已核对运行终态和实际保存数据，确认第二批确实使用了第一批的生成记忆。

| 动作 | 实际结果与UTC时间 |
|---|---|
| 完整模型运行 | 21:28:11.696408–22:13:40.726069，外部return0、2729.029596秒、未超时；CPU8/FP32、576、两批各50步 |
| 越过原故障位置 | 21:51:04.937626–21:51:06.786334实际单位调用完成；515点，中位正深度单位5.19512286700774e-6；21:51:07.746534第二批开始 |
| 独立终态核验 | 22:22:39.492631完成；9生产文件/221源码身份、资源消费、1张真实单位调用票、两批事件链通过；7个登记进程均已退出 |
| 实际正文读回 | 22:23:14.145845–22:23:15.307107外控return0、1.161150秒；205项数据比较，两批50/50，历史1→5→9 |
| 不同作者数值复核 | 22:29:09.800953–22:29:10.241445实际return0；22:31:26.813140最终封存。自行组织173项绑定/统计/数据检查，没有调用原读回函数 |

第二批选中了来源`[0,2,4,1]`。其中2、4、1是第一批生成的帧，它们的四类缓存通过真实条件计算进入了保存的采样器输入。本轮记录100次主模型计算、2次解码和2次场景构建，完整归档有6698个文件、229336164字节；全归档只核清单/大小，不能称所有正文均已复核。

主读回和不同作者各自核了92个唯一载荷、161552008字节，其中RGB正文147308544字节。独立检查从旧C2与新S64档案自行提取第一批噪声、生成结果、缓存和保留帧等27项，**27项实际字节全部相同**。27项涉及每侧23个唯一路径，不是27个独立样本；这不证明全部中间随机状态或其他运行也相同。

**目前确认的是工程恢复和这次保存数据的传递。** 新图没有在本轮显示，画质尚未评分；正文已读取，不能称“未读像素”。数值相机、画面是否遵循相机指令、长期一致性和新方法收益仍未由本轮建立。

本次为独立工程变体`C2_UNIT_REPAIRED_S64`，使用原living_room.jpg、seed44、声明的ft-mse VAE，左转5度再右转5度。统一单位也改变了深度票重语义。它在原C2失败后设计，**不补原C2行、不修改原三行试验或阈值**；原失败与先前B0/C1两个false保留。普通单位适配不算创新，`NO_METHOD_SELECTED`、`novelty_authorization=NONE`。

下一步已经定位到可复用的原相机数学与评分函数：给S64绑定自己的九帧权威数据，先核相机数值，再按固定数学评分并独立复算，最后导出全九帧供查看。最小实现路线见[相机与评分复用说明](</Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/work/S64_unit_repaired_generation/NEXT_CAMERA_SCORE_REUSE_NOTE.md>)；不重跑本次已完成模型。

并行创新工作已实际使用Gemini Pro Extended与正式论文，独立核查后否决了其尺度混淆及过强因果解释。保留的问题是“历史没有约束清楚的深度，是否在新视角真正改变记忆选择”；当前仍是问题，尚无合格方法。见[一页新手说明](</Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/work/S65_observability_triage/S65_BEGINNER_RESEARCH_NOTE.md>)与[数学和原文核验](</Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/work/S65_observability_triage/PRIMARY_MATH_REVIEW.md>)。

证据：[生成外部回执](</Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/work/S64_unit_repaired_generation/external_launch_01/receipt.json>)；[终态独立核验](</Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/work/S64_unit_repaired_generation/INDEPENDENT_TERMINAL_REVIEW.md>)；[实际读回报告](</Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/work/S64_unit_repaired_generation/postrun_readback_01/report.json>)；[不同作者结果复核](</Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/work/S64_unit_repaired_generation/INDEPENDENT_POSTRUN_RESULT_REVIEW.md>)；[全部时间主账](</Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/RESEARCH_LOG.md>)。
