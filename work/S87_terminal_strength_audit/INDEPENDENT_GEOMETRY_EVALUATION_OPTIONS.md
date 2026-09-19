# 独立检查请求相机与物体位置：两个公开入口及边界

状态：SOURCE_ONLY / NO_NEW_EVALUATION。本批 UTC 2026-09-10 23:42:32 开始检索，最后原文/元数据核读 23:46:55，23:47:28 开始落盘；北京时间为次日 07:42–07:47。本批只读文本/官方源码与文件列表，未下载数据包、未看拟用测试图像、未读本轮生成数组、未运行评价模型。S87 主量和合同不变；主账由 root 维护。

**决策：WorldScore 提供有用的普通评价先例，但不能独立证明物体位置正确；PointOdyssey 的模拟器标签更接近所需外部几何参考，却尚不是本机可执行数据。最便宜的近期动作，是让已有 S81 传感锚点观察器先通过真实照片正对照与错误相机负对照。若该观察器不能区分二者，应停用它解释生成几何；随后只核 PointOdyssey 一个固定时刻、多视角小片段的可获取性与标签身份，不直接上完整基准。** 这些都是评价选择，未提出或验证新方法。

## 1. 本地先查与当前问题

先检索 work 内 WorldScore / PointOdyssey / 相机评价记录，完整回读 `work/S86_fixed_warp_consumer/CAMERA_ADHERENCE_FOLLOWUP.md`。已有 CamI2V / CameraCtrlII 的位姿估计、尺度对齐及成功率边界，不重复深读。PointOdyssey 仅在旧 CUT3R README 和 S21/S22 的 loader 源码回执中出现；**源码回执不代表数据已下载**。本批不检查任何数据数组的存在或内容。

S86 的低 MSE 与 root 已记录的非盲重影观察同时成立。S87 目前结果以 root 最新接受为准；本文没有新评分。待解决的问题是：生成位置是否服从共同请求相机，物体是否在外部参考规定的位置，而不是它能否匹配自己的预测 warp。一个“稳定但错误”的世界可以内部一致；把模糊处剔除也可以使剩余匹配误差看起来更好。

## 2. 选项 A：WorldScore，适合拆分观察维度，不能代替物体位置真值

Haoyi Duan、Hong-Xing Yu、Sirui Chen、Li Fei-Fei、Jiajun Wu，**WorldScore: A Unified Evaluation Benchmark for World Generation，ICCV 2025**。本批方法依据作者 arXiv **v2（2025-11-29）**，不把它与会议版逐字等同。[作者原文](https://arxiv.org/html/2504.00983v2)、[官方项目](https://haoyi-duan.github.io/WorldScore/)。

- 原文 §3 / Appendix A：给定初图、后续场景文字和预设相机轨迹。这里相机“ground truth”是**请求的轨迹**，不是对生成视频进行外部传感得到的真实运动。对象可控性用指定对象的检测命中率；没有由此得到逐对象真实 3D 位置或形状标签。
- Appendix C.1–C.2：输出位姿由 DROID-SLAM 估计；旋转误差与经最小二乘尺度拟合的平移误差组合。3D 一致性来自该观察器重建、深度/位姿调整后的共视点重投影残差。它不使用我们的 CUT3R warp，但**不同模型的自洽仍不等于外部几何正确**。
- 最小迁移是分别报告旋转、平移、观察器失败和有效分母，不以单个总分替代这些量。官方安装路径包含 CUDA 12.1、DROID-SLAM 编译及多个权重；本机 Apple Silicon 执行未核，不能称可直接运行。[官方 README](https://github.com/haoyi-duan/WorldScore)

**纸面反例，非真实实验：**论文式 (3) 的误差为 \(e_c=\sqrt{e_\theta e_t}\)。若请求与输出均不旋转，\(e_\theta=0\)，但平移误差 \(e_t=1\)，则该组合仍为 0；因此不能只看它判断两项都正确。另若估计轨迹恰为请求轨迹的两倍，允许拟合尺度后可以得到零平移误差，不能据此说米制相机移动正确。前者只是原文公式的条件推论；**本批未审相机评分执行代码，不将它宣称为实现漏洞或实际基准结果**。纯旋转、弱视差、重复纹理和重影均可能令观察器不可靠；没有可靠失败处理，低误差仍可能是伪正确。

数据入口已由官方 `download.py` 确认是作者 Hugging Face 的 `WorldScore-Dataset.zip`；本次文件列表标 **1.22 GB**，仓库总量 **6.08 GB**，卡片许可 MIT。这里是公开文件列表状态，未验证下载或包内 schema。仓库脚本按整体 ZIP 获取，不是已核可选取单例的最小读取入口。[下载脚本](https://github.com/haoyi-duan/WorldScore/blob/main/download.py)、[作者数据文件列表](https://huggingface.co/datasets/Howieeeee/WorldScore/tree/main)

## 3. 选项 B：PointOdyssey，提供外部模拟标签，但不是现成生成评价器

Yang Zheng、Adam W. Harley、Bokui Shen、Gordon Wetzstein、Leonidas J. Guibas，**PointOdyssey: A Large-Scale Synthetic Dataset for Long-Term Point Tracking，ICCV 2023**。作者原文只有 **v1（2023-07-27）**；当前项目数据为 **v1.2**。论文统计 104 视频，当前项目描述 159 视频，不能混成同一版本。[原文](https://arxiv.org/html/2307.15055v1)、[官方项目及 v1.2 入口](https://pointodyssey.com/)

原文 §3.3 / §3.5：相机轨迹可从真实视频 SfM 借用或人工设置，但实际 RGB 是 Blender 渲染；输出相机内外参、网格顶点的 2D/3D 轨迹、深度、实例分割和可见性。可见性由顶点投影深度与渲染深度比较得到。**这些标签独立于我们预测的 warp，却是模拟器真值，不能叫真实 RGB-D 传感器测量。** 项目当前明确只有一部分场景有同步多视角。

原文 §5.2 的普通位置指标包括：在统一 256×256 坐标中，对 1/2/4/8/16 像素阈值平均的位置准确率、轨迹误差中位数、超过 50 像素后定义的跟踪存活长度比例。它们评价点跟踪；数据集没有自动给生成图中新增、变形或重影对象赋真值身份。原文 §6 也将动态新视角生成列为尚未探索用途。因此不能把本数据的现成 tracking 分数直接称为生成几何正确率。

**源码给出的最小坐标入口：**官方 `utils/reprojection.py`（114 行，网页标 3.46 KB）读取 `annot.npz` 的 `trajs_3d / intrinsics / extrinsics`，先计算 \(X_c=RT[X_w;1]\)，再经 K 投影；RT 因而是 world→camera。反投影使用 \(RT^{-1}\)。示例将 `depth_00244.png` 对到 annotation 索引 243；深度换算写为 `raw / 65535 * 1000`，并将 10 m 截断明确用于可视化。**不能沿用这个可视化筛选去评价，也不能把 S81 的深度缩放/相机约定直接搬过来。** v1.0 有专门坐标修正注释；具体 v1.2 小片段仍须校验版本、起始帧编号、单位和全部必需字段，未读任何 annot 数值。[官方坐标源码](https://github.com/y-zheng18/point_odyssey/blob/main/utils/reprojection.py)

作者数据列表当前显示总 **185 GB**，最小列出包 `sample.tar.gz` **3.32 GB**、`test.tar.gz` **26.5 GB**；并非“小样例几 KB”。官方 GitHub README 将数据许可写为 **CC BY-NC-SA 4.0**，作者 HF 卡却标 **MIT**，二者不一致；本批只记录声明，不替作者解决许可冲突。未证明存在可单独获取、含完整标签的更小分片，也未核 sample 是否属于独立测试场景。[官方 README](https://github.com/y-zheng18/point_odyssey)、[作者文件列表](https://huggingface.co/datasets/aharley/pointodyssey/tree/main)、[作者卡片](https://huggingface.co/datasets/aharley/pointodyssey/blob/main/README.md)

**对本问题最重要的限制：**物体在动时，不能拿历史点 \(X(t_0)\) 仅换相机投到未来帧并当真值，应使用该目标时刻的真实 \(X(t)\)。最小公平选择是固定同一时刻的同步不同视角；否则相机错误与物体运动错误混在一起。若任务本身允许不可预测的未来运动，也不能强迫唯一未来照片成为所有合法生成的答案。现有多视角子集、测试划分、模型训练重合和帧级时间 schema 均须确认；仅有 test 文件名不证明对当前模型未见。

## 4. 一个最小可推翻的入口，不新增本轮指标

后续问题只保留一个：**相比普通末端策略，多步引导是否改善外部参考规定的点位置，并且没有靠丢失/合并难点取得好分？** 普通对照保留原 G0、Gpaste、Gterminal；不能只拿 Gguide 对自己的 warp 评分。

本机近期入口复用 S86 的 `CAMERA_ADHERENCE_FOLLOWUP.md` 所指 S81 单张 sensor19：由传感 camera-Z、既有 P/K 产生请求视角中的预期点坐标；观察器匹配不能先用被检验的请求几何筛掉错误点。先用对应真实目标照片作正对照、重复源图却声明新相机作负对照；冻结同一候选点、完整无匹配/越界/缺测分母。若二者无法可靠区分，则生成几何结论停止，不继续替换评分器直到某臂获胜。这是旧已见单场景的资格诊断，不是新独立数据验证。17.126 ms 不同步、近似 K、无去畸变、遮挡与缺深度限制继续保留。

真正独立的新入口优先 PointOdyssey **同一时刻多视角**的一个未参与选参场景，但需先满足三个实际缺项：①可取得的有界小片段及其许可/版本/独立划分；②源输入与目标评分标签分离，单位、坐标、帧号、可见性 schema 明确；③普通观察器在原渲染正对照和错误相机/重复图负对照上合格，重影多重匹配与完全失败都有固定处理。GT 给了位置，仍需独立识别生成图里“哪一个点是它”；这一环未解决就不能声称位置可测。若以 GT 深度构建引导，它属于额外 oracle 输入，必须另列，不能与当前仅预测历史几何的结果混报。

**否决边界：**只有 MSE 更低而外部位置不改善，或完整失败比例更高，不支持“几何引导使位置更正确”。若固定外部位置和完整分母改善，可支持该条件下的几何收益；仍不证明新的融合算子、动态长期记忆、跨场景泛化或总体感知质量。当前先收束 S87 已冻结实验，不因找到论文而自动加跑。

## 5. 实际查阅范围和可复核来源

| 来源 | 版本 / 本次实读范围 | 没有核到的部分 |
|---|---|---|
| [WorldScore 作者原文](https://arxiv.org/html/2504.00983v2) | v2；标题/作者、概述；§3 对象/相机定义；Appendix A 世界规格；C.1–C.3、C.8，HTML 163–173、369 附近、437–466、487–494 | 非全文精读；未核 DROID-SLAM 实际评分执行链或失败分母 |
| [WorldScore 官方仓库](https://github.com/haoyi-duan/WorldScore) | 当前 main README 数据下载、CUDA/权重、评估命令；`download.py` 全部 33 行；worldscore 目录列表 | GitHub 未固定 commit；未执行脚本；未读数据包 |
| [WorldScore 作者数据](https://huggingface.co/datasets/Howieeeee/WorldScore/tree/main) | 文件列表/尺寸/许可标签；页面短版本 42c4e26 | 未读取 ZIP、parquet、任何测试行/图 |
| [PointOdyssey 作者原文](https://arxiv.org/html/2307.15055v1) | v1；§3.1–3.6、§5.2、§6；HTML 107–140、189–204；另局部读跟踪/可见性段落 | 非全文；未核官方 tracking 执行器；不以文中性能当本机预期 |
| [PointOdyssey 项目](https://pointodyssey.com/) / [官方仓库](https://github.com/y-zheng18/point_odyssey) | 当前 v1.2 项目文字、Download / Multi-view；114 行源码 `utils/reprojection.py` 的投影、反投影、数据读取/缩放部分（网页 453–556 行）；raw 入口已打开 | 当前 main 未固定 commit；未执行或渲染；未读图/标签值；不称全部可视化尾段已审 |
| [PointOdyssey 作者数据](https://huggingface.co/datasets/aharley/pointodyssey/tree/main) | 文件列表及 129 B README，短版本 4a2ec94；卡片写 v1.2 | 不知道最小包内部哪些场景/划分，下载与解压未验 |

初始英文定点检索限定 WorldScore camera controllability / ground-truth evaluation 与 PointOdyssey long-term tracking；上述两个 work 够用后停止，不扩第三篇。CVF 官方 PointOdyssey PDF 的 web open 返回 InternalError；初次误试不存在的 arXiv v2 HTML 也失败，随后依据实际 abs 页确认唯一 v1，合法 HTML 成功。失败未算阅读。WorldScore 会议身份由官方项目/仓库接受记录及 CVF 官方搜索条目核定；方法依据明确采用后续作者 v2，不声称会议 PDF 已全文核读。所有访问均发生于上述本批时间区间，网页缓存时间不冒充源码提交时间。
