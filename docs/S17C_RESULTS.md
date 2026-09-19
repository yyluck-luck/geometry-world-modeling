# S17C 结果：VMem嵌入CUT3R无先验建图与全局对齐组件

**这一组件已经在本机真实运行，并通过不同作者独立数值核验。** 两张已见的 Bonn 实拍进入 VMem 自带的 CUT3R 分支，先得到模型预测，再执行原生400次几何优化和一次置信度清理。过程没有提供姿态或深度先验，没有训练网络、读取GT或生成视频。最终保存70个数组，原照片和整个优化过程都可追溯。

对初学者来说，S17B是“模型看照片并给出预测”，S17C进一步是“原VMem几何程序调整相机和每个像素的深度，让两幅预测在同一套坐标里更一致”。这次确认的是该程序真实跑通、计算可复核；没有测量它是否更接近现实答案。

## 两张固定照片与实际输出

![两张已见照片、相机深度与置信度变化](../work/S17C_reporting/s17c_two_frame_geometry.png)

左列来自模型已保存的输入tensor，显示的仍是这两张真实照片。中列是优化后的**相机坐标深度**，两图共用运行结果读取前固定的0至5色域；单位是自由尺度下的模型单位，不能读成米。右列橙色表示原清理程序降低置信度的位置，灰色表示未改。它不是“错误答案”的掩码，也不表示这些几何点已经被删除。

| 全像素统计 | Frame 0 | Frame 1 |
|---|---:|---:|
| 像素总数 | 196,608 | 196,608 |
| 正且有限的相机深度 | 196,608 | 196,608 |
| 相机深度最小值（模型单位） | 0.488269 | 0.459661 |
| 相机深度最大值（模型单位） | 2.064978 | 1.971752 |
| 超过预定显示上限5 | 0 | 0 |
| 清理前置信度为0 | 0 | 0 |
| 清理后置信度为0 | 13,908 | 105,351 |
| 清理后置信度仍为正 | 182,700 | 91,257 |
| 置信度改变像素数 | 13,908 | 105,351 |
| 改变比例 | 7.073975% | 53.584290% |

两帧的清理比例差异很大，但不能据此说frame1几何更差：这里没有GT。原清理依据跨视角投影深度及两边相对置信度，按固定顺序更新；其效果还受当前估计相机和遮挡影响。原函数只改confidence，清理前后的点、相机、深度、focal、主点、颜色、pair transform/adaptor全部逐元素不变。没有对显示或统计再加置信过滤，所有像素均保留。

图可导出：[PNG](../work/S17C_reporting/s17c_two_frame_geometry.png)、[PDF](../work/S17C_reporting/s17c_two_frame_geometry.pdf)、[SVG](../work/S17C_reporting/s17c_two_frame_geometry.svg)。固定两帧是S15A原index0/1，没有挑出获胜样本。S17B与S17C的深度颜色也不能直接用来判断改善：S17C对齐有自由尺度与不同相机参数，数值变小本身不代表更准。

## 完整400次优化发生了什么

![全部400轮损失、学习率和置信度计数](../work/S17C_reporting/s17c_full_trace_and_confidence.png)

蓝线包含全部400轮更新前目标值，没有平滑、抽样或删掉开头峰值。绿色曲线是原线性学习率，下面是两帧清理前后的全部像素计数。末端空心圆是在第400次更新结束后，额外做的一次只读目标计算；它没有继续优化。

| 记录 | 实际数值 |
|---|---:|
| 第0轮更新前目标值 | 0.008256965316832066 |
| 第1轮更新前目标值（最大值） | 0.21385997533798218 |
| 第399轮更新前目标值 | 0.007406100630760193 |
| 最后更新后的只读目标值 | 0.007406073622405529 |
| 原生优化迭代 / Adam step | 400 / 400 |
| 额外只读目标计算 | 1次，无额外step |
| 总场景目标调用 | 401次 |
| 学习率第0 / 第399轮 | 0.01 / 0.0000259975 |

这个目标衡量估计几何与原模型预测之间的加权三维欧氏距离；权重来自原置信度的log变换，不是与传感器真值的误差。曲线明显非单调，399个相邻变化中有196次上升。最终值比初始值低，不能因此声称优化达到最优、真实几何更准或视频更好。

图可导出：[PNG](../work/S17C_reporting/s17c_full_trace_and_confidence.png)、[PDF](../work/S17C_reporting/s17c_full_trace_and_confidence.pdf)、[SVG](../work/S17C_reporting/s17c_full_trace_and_confidence.svg)。机器可读的400行原始记录在 [optimization_trace.jsonl](../results/S17C_embedded_geometry/optimization_trace.jsonl)。

## 实际运行、来源与成本

固定使用 VMem commit `39291e4f272f6b4f270691d930926ab5930f942e` 的原 `run_inference_from_pil`。只在隔离源副本增加有符号CPU RoPE兼容和 `weights_only=True`，未改原建图、优化、清理数学。使用作者公开完整512 DPT权重，3,173,761,006 B，SHA256 `45f7e98a0a64dbeb54901ae2b878cd8cd125f20a4497316483f0bd6f109f8103`。模型仍有793,307,858个固定参数，几何优化实际可优化393,240个场景参数；两者对象不交叉，网络没有梯度或训练。

原输入是两张640×480照片，原函数处理成512×384，CPU8线程、seed0、FP32及原q/k精度接口。Python/NumPy/Torch/OpenCV随机种子均记录。原两帧只形成边`[(0,1)]`，实际发生1次模型前向、1次MST初始化和1次PnP调用，PnP成功返回。这里“PnP成功”只说明求解器返回结果，不是与真实相机比较通过。`poses=None,depths=None` 与VMem完整pipeline传入已知姿态/已存深度的用法不同。

| 资源与时间口径 | 实际记录 |
|---|---|
| worker时间（UTC） | 2026-09-06 11:36:30.084167—11:37:03.474344 |
| worker时间（北京时间） | 2026-09-06 19:36:30.084167—19:37:03.474344 |
| worker元数据耗时 | 33.417429秒（包含最后元数据写出时刻） |
| 原模型inference计时 | 2.431692秒；不包含整个几何对齐/保存过程 |
| worker自身峰值RSS | 6,888,161,280 B，约6.415 GiB |
| 外caller观测耗时 | 37.076673秒 |
| 外caller轮询峰值RSS | 6,350,372,864 B；轮询与进程自身峰值是不同测量口径 |
| 停止界 | 600秒 / 32GiB；本次外caller PASS |
| 真实RGB解码 / 模型前向 | 2 / 1 |
| 真实ray / query / GT / 主生成器 | 0 / 0 / 0 / 0 |
| 官方全零dummy ray编码 | 实际1次，未隐藏该计算 |

依赖位于新overlay，原模型环境不改。最初import smoke因漏掉`viz.py`顶层viser/sklearn依赖失败，后按新冻结闭包补齐34个wheel再实际导入通过；原失败及安装回执保留在 [环境记录](../work/S17C_environment/environment_ready.json)。这些依赖准备、此前权重下载的时间不包含在33.42秒worker耗时中，也不能把钟表时间当成人的工时。

主证据：[运行前协议](S17C_EMBEDDED_GEOMETRY_PROTOCOL.md)、[实际manifest](S17C_EXECUTION_MANIFEST.json)、[原运行metadata](../results/S17C_embedded_geometry/run_metadata.json)、[外caller](../work/S17C_execution/model/caller_receipt.json)、[输出seal](S17C_OUTPUT_SEAL.json)。manifest SHA `a9d74acb5d79e81696a7cb2cb665577071f47e5af19292230e768638f311c885`；seal SHA `424090fd2e1de5cdcf7cd124ed893b9a1dea380cf772420cbb48e57834f31df8`。全部5761个输入/源码身份在worker前后相符。

## 独立核验与图表检查

另一位agent使用NumPy/SciPy的不同实现，不运行模型、不优化、不重新解码原PNG、不读取GT；读取封存数组（含2个处理后的RGB tensor），并对原输入文件做SHA字节核验。它独立验证了70个已保存数组（包含成功PnP的额外pose）。由深度、focal、主点及相机重建世界点；重新计算相机旋转、完整清理过程和最终目标。[独立verification.json](../results/S17C_embedded_independent/verification.json) 于UTC11:37:40.470839结束，状态PASS。

- 完整393,216个清理像素中，独立实现与原函数的confidence结果**0个不一致**，没有剔除边界像素或看结果后放宽容差。
- 最终目标的独立值是 `0.007406074786801078`，原Torch值是 `0.007406073622405529`，在事先冻结容差内。
- 6303项检查表示身份、结构和数值条件被检查，不是6303个独立场景，也不是准确率或论文贡献。

准备阶段还发现状态位置网格假设的错误：B检查器漏掉了原代码“奇数宽度加1”的规则，C前审与人工packet在冻结之前同步改为实际宽度28，旧v1–v3准备记录保留。没有因此重跑B模型，也没有修改C真实结果；详 [C代码前审与验证说明](S17C_CODE_REVIEW_AND_VERIFICATION.md) 及 [B状态位置勘误](S17B_STATE_POSITION_VERIFIER_AMENDMENT.json)。

绘图遵循figure-designer的实验结果与质检步骤，以Matplotlib生成PNG/PDF/SVG。首次两图渲染读取6个已存数组，其中2个是归一化RGB tensor，另外4个是前/后depth和confidence；**0次原PNG解码、0次GT读取、0次模型运行**。我实际看图后发现第一版曲线图的底部图例与说明重叠，保留首版，随后只使用原metadata与已算全像素计数重绘曲线图，新增数组/RGB读取均为0；再次实际看图确认排版通过。几何图未重画。详 [plot receipt](../work/S17C_reporting/plot_receipt.json)、[排版更正](../work/S17C_reporting/layout_fix_receipt.json) 与 [可视QA](../work/S17C_reporting/visual_qa.json)。

## 可以向老师说什么、下一步是什么

可以说：公开512几何模型已实际嵌入原VMem无先验几何入口，本机完成400步原生对齐，输出与清理规则有独立实现复算，完整失败/资源/照片/数组记录可以重查。这是一个可复现的工程与组件验证结果。

现在不能说我们提出了新算法、提高了真实深度精度、完成了Surfel地图合并或VMem视频生成。两张已见照片是一个小组件测试，没有GT、米尺度或未见场景评价；原函数调用成功也不等于整个科研项目已经完成。下一项实质工作应继续原proposal中尚缺的实际消费者与完整视频路线，或先冻结一个可被反驳的新机制假设和公平对照；不把现有作者算法换个名字当创新。

原作入口：[VMem官方仓库](https://github.com/runjiali-rl/vmem/tree/39291e4f272f6b4f270691d930926ab5930f942e)、[作者公开512权重](https://huggingface.co/liguang0115/cut3r/tree/b14faf986da0df405cff1b41e60e2975c4da2745)、[Bonn作者数据发布页](https://www.ipb.uni-bonn.de/data/rgbd-dynamic-dataset/)。源码与数学界限的逐项核查见 [S17C接口审查](S17C_INTERFACE_REVIEW.md) 和 [独立数值合同](S17C_INDEPENDENT_NUMERICAL_CONTRACT.md)。
