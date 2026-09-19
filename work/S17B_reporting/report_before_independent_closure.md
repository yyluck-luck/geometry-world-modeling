# S17B 结果：两张真实照片已跑通公开 512 DPT 模型

这次实际运行了模型。我们把 Bonn 数据集中两张已使用过的真实照片，送入作者公开的 **512 DPT CUT3R** 完整权重，获得每张图的几何、置信度和相机预测。模型在本机 CPU 成功结束，保存19个数组；没有使用传感器深度、没有训练、没有生成视频。独立核验目前还有一项状态位置检查待更正关闭，不能把整个验证流程写成全部通过。

![两张固定真实照片与512预测深度](../work/S17B_reporting/s17b_two_photos_dpt_depth.png)

左列是原生640×480实拍，中列显示512×384模型输入，右列是模型自己预测的相机方向深度。右图颜色只表示**模型单位**，还没有标定成米，也没有与正确答案比较。两帧固定使用0至5的同一色域；没有挑图、调尺度或过滤低置信像素。图中前面的纸箱与后方桌椅呈现不同预测深度，但这张图不能证明预测准确或方法创新。

可直接打开 [PNG](../work/S17B_reporting/s17b_two_photos_dpt_depth.png)、[PDF](../work/S17B_reporting/s17b_two_photos_dpt_depth.pdf)、[SVG](../work/S17B_reporting/s17b_two_photos_dpt_depth.svg)。本次使用 figure-designer 的实验结果设计与质检要求，以 Matplotlib 作标准科研图，并实际检查了输出图片：照片/深度标签明确，标题和色条可读，没有裁字遮挡。绘图额外解码2次已见RGB、读取2个已存self pointmap数组，只消费Z；没有新增模型推理或GT读取。

## 做了什么

此前本机只有224 linear权重。这次完整下载并核验了作者公开512 DPT权重，真实运行512架构；没有把旧224输出放大后冒充512。

| 项目 | 实际记录 |
|---|---|
| 输入 | S15A Bonn index 0/1，同两张原640×480 RGB |
| 模型 | CUT3R官方commit `8bc15dc92a6d7fd92920b4ec81540d3dec7d3ecf`，512 DPT、24层图像编码器、793,307,858参数 |
| 权重 | `cut3r_512_dpt_4_64.pth`，3,173,761,006 B；SHA256 `45f7e98a0a64dbeb54901ae2b878cd8cd125f20a4497316483f0bd6f109f8103` |
| 本机执行 | CPU，8线程，seed0，FP32及原RoPE内部精度接口 |
| 输入处理 | 官方size512，640×480→512×384，全幅保留；每帧768个图像token |
| 实际模型调用 | 1次两帧历史推理；图像编码器1次、2真实图；0 query、0真实ray |
| dummy ray | 官方分支实际另编码1个全零ray，占位运算如实计入 |
| 保存 | 12原始头数组、5最终状态数组、2相机编码/矩阵数组 |
| 时间（UTC） | 2026-09-06 11:26:56.793111—11:27:07.441553 |
| 时间（北京时间） | 2026-09-06 19:26:56.793111—19:27:07.441553 |
| 运行进程耗时 | 10.648449秒；其中模型前向2.430449秒 |
| 进程峰值RSS | 6,746,161,152 B，约6.283 GiB；低于32GiB/600秒界 |

10.65秒不包含此前网络下载耗时，也不是整个研究阶段的工时。证据为 [真实运行metadata](../results/S17B_dpt_two_frames/run_metadata.json)、[外部调用回执](../work/S17B_execution/model/caller_receipt.json)、[运行前协议](S17B_DPT_TWO_FRAME_PROTOCOL.md)、[输入manifest](S17B_EXECUTION_MANIFEST.json) 和 [输出seal](S17B_OUTPUT_SEAL.json)。输入manifest SHA为 `f9fe025e2a389e2a679ebc3dbfbd4257bd9611c73d29b94b3f68a302565ff298`；模型输出及原输入的前后身份检查通过。

## 图里哪些是测量，哪些不是

两帧各有196,608个正且有限的预测Z；frame0范围0.976542—4.130104，frame1范围0.886484—3.852935，全部是未标定模型单位。两帧都没有超出预定显示上限5。这些统计仅检查预测数组是否完整、是否被图的色域截断；196,608个像素不是196,608个独立实验，正且有限也不是准确率。

我们没有在本阶段读取GT、计算深度误差、比较512和224哪个更准，也没有声称它比S15C或S15B其他协议提升多少。图片属于此前已见的同一个Bonn短片段，不能称泛化评测。

## 保留的失败与待关闭项

公开权重的最初整文件下载发生curl18中断，只保留533,225,219 B；后来的分段合同也到达时间界，已有成功片段保留。最后一个新冻结的有界续传仅补398,184,074 B，于UTC11:26:48.580724得到完整文件，作者LFS SHA匹配后才加载。[首轮回执](../work/S17A_checkpoint_acquisition/receipt.json)、[分段回执](../work/S17A_checkpoint_resume_ranges/receipt.json)、[最后获取PASS回执](../work/S17A_checkpoint_remaining_v2/receipt.json) 均保留。这些是网络与获取失败，不是模型失败。

模型本身SUCCESS，随后独立检查器在 `state_pos` 检查失败：检查器预设了 `floor(sqrt(768))` 二维网格。原始19数组的身份/形状与SciPy独立相机转换已通过，相机矩阵最大绝对差 `2.898347528645928e-8`，但最终状态位置必须按该512权重的实际配置审查，不能以旧网格假设代替。当前 [原独立失败回执](../results/S17B_dpt_independent/verification.json) 和 [调用链失败回执](../work/S17B_dispatch_v2/receipt.json) 保留；另一位agent正在更正检查器，**不重跑模型、不改已封存数组**。本报告此版将最终独立通过状态保留为待关闭。

## 对项目的意义

实质进展是：VMem需要的公开512几何模型已经在本机真实运行，完整权重、实际耗时、原图和输出都能复查。它补上了一个真实组件缺项；采用作者模型并跑通不是我们的新算法贡献，也不保证论文等级或老师的反应。

下一步S17C会调用VMem源码里的原生建图与全局几何对齐入口，固定这两张照片、400次原生优化，不给姿态或深度先验，检查相机/深度和清理置信度的真实输出。其运行前协议见 [S17C](S17C_EMBEDDED_GEOMETRY_PROTOCOL.md)。完整VMem视频仍受主权重访问及其他生成依赖限制；[完整可行性报告](S17_FULL_VIDEO_BASELINE_FEASIBILITY.md) 和 [CPU补充实测](S17_FULL_VIDEO_BASELINE_FEASIBILITY_ADDENDUM.md) 说明这些边界。

原作来源：使用 [CUT3R官方源码](https://github.com/CUT3R/CUT3R/tree/8bc15dc92a6d7fd92920b4ec81540d3dec7d3ecf)，公开权重来自 [作者的CUT3R仓库](https://huggingface.co/liguang0115/cut3r/tree/b14faf986da0df405cff1b41e60e2975c4da2745)。照片来自 [Bonn作者发布页](https://www.ipb.uni-bonn.de/data/rgbd-dynamic-dataset/)，相机约定的来源链见 [已核原文记录](S15B_BONN_POSE_RESOLUTION.md)。这一阶段是组件验证，未复制完整作者视频评测协议。
