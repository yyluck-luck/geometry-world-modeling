# S4–S5 learned-geometry report：独立引用与外部来源审核

审核记录时间：2026-09-05 23:31:14 Asia/Shanghai，来自本机实际时钟。对象为 `LEARNED_GEOMETRY_REPORT.md`，读取版本 SHA-256：`0b79d0b815ddd7bb84cfc3fdd727d04f1429d44b5993f747a3b5d0a60627e251`。后续只补来源链接或局部文字时，应在下方追加复核记录，不能把此哈希用于新版本。

结论：**PASS，3篇书目均 VERIFIED；未发现未解决的外部事实错误、虚构文献、错误归属或文献过度推断。** 有3项不改变结论的直接证据链接建议，见文末。本审核不重新计算实验结果，也不把引用通过等同于全文或实验通过。

## 独立性与范围

本审核由未参与该稿撰写的代理独立执行，读稿后重新检索来源。按 `paper-writer/references/verification-ladder.md`，每篇均执行题名、作者加主题年份、核心关键词三种检索。判断依据是作者论文、作者项目网站、会议官方记录、数据集官方说明及固定官方源码，不使用模型记忆作为来源。项目说明、记忆与最新日志仅用于识别本地工作范围；本审核没有改正文、实验代码或主研究日志，也没有运行模型。

审核覆盖3条正式参考文献、正文全部外部技术说明和Figure 1数据许可。所有本地参数数量、文件哈希、时点、像素计数、分数、设备差异、独立检查数和训练外实验执行事实均留给对应数值及运行审核；此处只核对外部来源是否支持相应方法语义。

## 书目与主要引用

| 参考 | 独立检索结果 | 正文支持关系 | 状态 |
|---|---|---|---|
| 1. Li, Torr, Vedaldi, Jakab，VMem，ICCV 2025 | 题名、4位作者和会议年份与[作者项目](https://v-mem.github.io/)及会议记录匹配；另读取[作者稿全文](https://arxiv.org/html/2506.18903v2)。 | §1所述surfel索引与参考视图选择有方法说明支持；§6没有把作者的生成能力移植为本项目结果。 | VERIFIED |
| 2. Wang, Zhang, Holynski, Efros, Kanazawa，Continuous 3D Perception Model with Persistent State，CVPR 2025 | 题名、5位作者和会议年份与[会议官方记录](https://openaccess.thecvf.com/content/CVPR2025/html/Wang_Continuous_3D_Perception_Model_with_Persistent_State_CVPR_2025_paper.html)、[作者项目](https://cut3r.github.io/)和[arXiv 2501.12387](https://arxiv.org/abs/2501.12387)匹配。 | 持续状态、按输入观察更新和3D输出的概括有来源支持。具体实现另查固定源码，不将论文摘要代替实现证据。 | VERIFIED |
| 3. Sturm, Engelhard, Endres, Burgard, Cremers，A Benchmark for the Evaluation of RGB-D SLAM Systems，IROS 2012 | [作者论文全文](https://jsturm.de/publications/data/sturm12iros.pdf)与[官方数据集书目](https://cvg.cit.tum.de/data/datasets/rgbd-dataset)匹配题名、5位作者与年份。 | Kinect RGB/深度、motion-capture轨迹参考和测量限制有全文依据。正文没有称传感器深度或轨迹为无噪三维表面真值。 | VERIFIED |

检索期间出现两次直接打开失败：CUT3R的CVF HTML返回内部错误，VMem的CVF PDF返回403。官方搜索索引内容、作者项目及作者稿可访问，交叉核对后已解决；不能将这些抓取错误记成论文不存在。

## 外部技术主张与固定来源

以下CUT3R源码均独立下载自官方提交 `8bc15dc92a6d7fd92920b4ec81540d3dec7d3ecf`，并在独立工作目录记录下载时间、字节数和SHA-256。

| 正文位置与主张 | 支持与边界 | 状态 |
|---|---|---|
| §2.1：224 linear是中间检查点，512 DPT是最终检查点 | [官方README模型表](https://github.com/CUT3R/CUT3R/blob/8bc15dc92a6d7fd92920b4ec81540d3dec7d3ecf/README.md#download-checkpoints)明确区分两者。本文没有声称复现最终512模型成绩。 | VERIFIED |
| §2.1及§5.1：外部FP32不表示所有算子FP32 | [CroCo encoder attention](https://github.com/CUT3R/CUT3R/blob/8bc15dc92a6d7fd92920b4ec81540d3dec7d3ecf/src/croco/models/blocks.py#L122)在RoPE前将q/k转FP16，再转回；[dust3r decoder attention](https://github.com/CUT3R/CUT3R/blob/8bc15dc92a6d7fd92920b4ec81540d3dec7d3ecf/src/dust3r/blocks.py#L112)使用 `.float()`。这支持精度描述；不验证两设备每一算子的实际执行轨迹。 | VERIFIED |
| §2.2：pose token负位置与fallback/CUDA公式差别 | [model.py](https://github.com/CUT3R/CUT3R/blob/8bc15dc92a6d7fd92920b4ec81540d3dec7d3ecf/src/dust3r/model.py#L825)生成负一位置；[fallback](https://github.com/CUT3R/CUT3R/blob/8bc15dc92a6d7fd92920b4ec81540d3dec7d3ecf/src/croco/models/pos_embed.py#L152)用embedding查表；[CUDA实现](https://github.com/CUT3R/CUT3R/blob/8bc15dc92a6d7fd92920b4ec81540d3dec7d3ecf/src/croco/models/curope/kernels.cu#L52)以有符号位置计算角度。文稿正确保留“未做CUDA硬件对照”的边界。 | VERIFIED，限源码说明 |
| §2.3：实际head与Direct类的区别 | [factory](https://github.com/CUT3R/CUT3R/blob/8bc15dc92a6d7fd92920b4ec81540d3dec7d3ecf/src/dust3r/heads/__init__.py#L25)的linear/pts3d+pose分支返回 `LinearPts3dPose`。[该类](https://github.com/CUT3R/CUT3R/blob/8bc15dc92a6d7fd92920b4ec81540d3dec7d3ecf/src/dust3r/heads/linear_head.py#L298)通过proj、pose_head、cross_proj产生输出；Direct类才显式做坐标变换。因此不强加other=pose×self成立。分支仍共享特征，不能将“separately predicted”扩写为统计独立。 | VERIFIED |
| §2.3：camera_c2w语义 | [官方pose decoder](https://github.com/CUT3R/CUT3R/blob/8bc15dc92a6d7fd92920b4ec81540d3dec7d3ecf/src/dust3r/utils/camera.py#L396)将旋转及平移写入c2w矩阵。本文另明确点图与pose平移共尺度是评分假设。 | VERIFIED |
| §3.1：640×480 RGB经299×224后裁为224×224，LANCZOS | [官方loader](https://github.com/CUT3R/CUT3R/blob/8bc15dc92a6d7fd92920b4ec81540d3dec7d3ecf/src/dust3r/utils/image.py#L65)的round及中心裁剪规则推得 `[37,0,261,224]`。这里只验证算法及尺寸语义；实际像素一致性由独立实验审核负责。 | VERIFIED |
| §3.1：深度除5000，不重复Freiburg尺度修正 | [官方格式说明](https://cvg.cit.tum.de/data/datasets/rgbd-dataset/file_formats)给出PNG深度单位、零值缺测、预注册和已完成尺度修正。深度与RGB有对应像素不意味着完美配准。 | VERIFIED |
| §5.1：顺序更新、块内causal语义 | [模型前向](https://github.com/CUT3R/CUT3R/blob/8bc15dc92a6d7fd92920b4ec81540d3dec7d3ecf/src/dust3r/model.py#L816)每次调用初始化状态，按i读取当前特征并更新；[编码入口](https://github.com/CUT3R/CUT3R/blob/8bc15dc92a6d7fd92920b4ec81540d3dec7d3ecf/src/dust3r/model.py#L570)把图像放入batch维度，未将不同帧token合并做跨帧encoder attention。reset在输出和更新后应用。正文对后一个tail可以访问前一个tail RGB的解释合理。 | VERIFIED，限当前结构与入口 |
| §1、§6：测量并非完美真值，时间关联保留限制 | TUM论文§VI.B–D报告深度噪声、外参残差和RGB/depth时间差，并明确提醒轨迹参考不能直接生成高精度场景模型。正文没有把残差单独归因为模型错误或状态漂移。 | VERIFIED |
| Figure 1：TUM数据CC BY 4.0 | [当前官方许可段](https://cvg.cit.tum.de/data/datasets/rgbd-dataset#license)明确为CC BY 4.0（除非另有说明）。2012论文写的是当时CC BY 3.0；当前稿采用官网现行说明有依据。 | VERIFIED |

## 建议的精确补链（不改变数值或结论）

1. §2.1精度段，句子“The retained official CroCo encoder …; the decoder explicitly uses FP32 for this operation.”后，在现有CroCo链接旁增加上表的 `src/dust3r/blocks.py#L112` 链接。现有链接直接支持encoder部分，decoder证据在另一文件；本次已独立确认，所以不是未解决的OVERCLAIM。
2. §5.1第二段，在“State was initialized anew at the start of each block.”后增加上表 `src/dust3r/model.py#L816` 链接，便于读者核对官方状态更新与初始化语义。
3. Figure 1的“Image source: TUM RGB-D, CC BY 4.0.”将数据集或许可文字链接至官方 `rgbd-dataset#license`。无需把4.0改回旧论文的3.0。

没有需要删除或降低强度的外部来源句子。本文把S4/S5与S3、实测和合成、局部模型和VMem全流程、诊断与视频质量分开，没有用文献为未完成实验背书。

## 独立证据记录

独立抓取文件和哈希清单位于本次工作区 `work/learned_citation_audit/`：`source_manifest.json` 保存11个固定官方文件；`audit_record.json` 保存稿件哈希、实际记录时点、9种检索式、官方来源与抓取异常的解决情况。它们是工作证据，不覆盖项目已有vendor或实验输出。

本次审核未验证全体科学事实、全部本地数字、学生实际工时或课程提交资格。最终提交仍须结合独立数值审核与作者的学术判断。
