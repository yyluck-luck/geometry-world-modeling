# 最新科研进展

更新于北京时间 2026-09-06 20:28:37。

**本机已把两张真实照片的模型几何接入原VMem地图：501个面片，两个已知相机都能找回照片0、1。** 独立63数组复核通过，全部地图像素ID无差异。本轮复用此前模型输出，实际新计算约5.07秒，没有重新跑模型或生成视频。

- [先看本轮地图与照片来源图](outputs/S18_S19_地图连接与研究反证_2026-09-06_202729/work/S18_reporting/s18_memory_visibility.png)
- [S18完整结果和证据](outputs/S18_S19_地图连接与研究反证_2026-09-06_202729/docs/S18_RESULTS.md)
- [当前227文件交接包入口](outputs/S18_S19_地图连接与研究反证_2026-09-06_202729/从这里开始.md)（约30.4MB，含代码、输入、输出、协议、失败和复核；逐文件SHA一致）
- [两张原始实拍与模型预测对照](outputs/S15BC_S16_S17_研究进展与证据_2026-09-06_194851/work/S17B_reporting/s17b_two_photos_dpt_depth.png)
- [全部20张真实照片索引](outputs/S15BC_S16_S17_研究进展与证据_2026-09-06_194851/work/S15A_reporting/s15a_all_20_real_history_photos.png)
- [上一轮三维点云查看器](outputs/S15BC_S16_S17_研究进展与证据_2026-09-06_194851/work/S17C_viewer/viewer.html) · [本机HTTP预览](http://127.0.0.1:8766/viewer.html)
- [研究方向的原文筛选](outputs/S18_S19_地图连接与研究反证_2026-09-06_202729/docs/S19_RESEARCH_QUESTION_TRIAGE.md) · [随后源码否证及最终处置](outputs/S18_S19_地图连接与研究反证_2026-09-06_202729/docs/S19_FEEDBACK_PATH_AUDIT.md)
- [最新研究记忆](</Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/RESEARCH_MEMORY.md>) · [实际时间日志](</Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/RESEARCH_LOG.md>)

地图图像是模型几何的显示，真实照片在上面的实拍链接中。可见比例不是深度准确率；两个相机已参与建图，不是泛化测试。

**创新还没有证实。** 本轮按Supervisor和本地Claude skills排除了两个不成立的版本：已有论文覆盖的射线差异gate，以及原代码中不存在的旧面片坐标改写。来源关联影响后续生成条件是另一个待验证问题，不继承原评分；没有把否定结果包装成新算法。

下一步应先建立原规格真实生成闭环并记录条件依赖，再决定是否值得研究反馈机制。原生成权重访问、指定VAE/CLIP与完整资源验证尚缺；当前没有完整视频。已查清作者4目标导航的padding与保存语义，后续不能混用长轨迹入口的NMS条件。

S18数值与图文审查已完成；每30分钟实查最近为北京时间20:20:19，创新仍待证据。新包是S18/S19增量，旧约418MB完整包及20实拍保留；大模型和环境仍在主项目，未声称换机器已复跑。点云直接file访问此前被内置浏览策略拒绝，本机HTTP预览才是已经实测的入口。
