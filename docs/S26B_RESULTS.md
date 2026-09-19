# S26B：真实地图优化结果与下一步诊断

报告写入UTC：2026-09-06T16:24:25.227118+00:00；北京时间=UTC+8。

**三种已有方法的真实几何优化已经完成，但本次8帧组件的深度质量很差，不能据此宣称新方法或记忆改善。** 更关键的是，共同旧地图本身已有83.3382%的相对深度误差，后续所有方法都继承这份被固定的旧深度。下一步应先定位这个共同起点的问题，再讨论三方法差异与创新。


**后续源码勘误（UTC 2026-09-06T16:33:02.122629+00:00）：** 本报告中的“可训练/优化”必须分清参数声明和实际更新。原`get_depthmaps→ParameterStack`包含`detach`，两个独立源码审查与极小人工helper反向传播检查确认其切断注册depth参数的梯度；原400次Adam计数不能证明depth实际改变。历史MST后depth/每步梯度没有保存，因此下一项以真实保存头作0参数更新的MST/一次backward核验，不能倒造历史。三次真实400步执行和原评分保持不变。详[原源码审查](../work/S27_scale_diagnosis_source/audit.md)及[独立理论与人工检查](../work/S27_scale_objective_review/review.md)。

## 本次究竟做了什么

真实TUM fr2_desk先前已见的连续8帧，首尾0.235880秒；0–3为共同旧帧，4–7为新帧。复用S21/S22实际神经预测的六个头，原VMem几何优化器执行star anchor0、400 Adam步、lr.01、CPU8。8个GT相机是显式共同oracle控制输入，不是算法预测，也不是深度答案。旧depth来自原4图GA，不是GT传感器depth。

共同旧depth、给定相机和pp保持固定，所有focal及新4depth按原程序声明可训练；新depth是否实际获得梯度见上述勘误。每方法完整封存后才读取8张已见传感器depth评分。原像素单位/5000、中心最近邻映射、不拟合尺度、不切远点、不按置信度筛选。只新增3次GA共1200步，0新神经前向；共同旧图400步是此前已做的历史运行。

## 全部新4主结果

AbsRel是逐像素相对深度误差的帧内均值，再对四帧等权平均；RMSE也是四个帧RMSE的均值，不是所有像素合并RMSE。δ1为预测/答案比值落在1.25倍范围内的像素比例，越高越好。

| 方法 | AbsRel，越低越好 | 逐帧RMSE均值（m） | δ1，越高越好 |
|---|---:|---:|---:|
| CUT3R | 67.8259% | 1.400540 | 0.01314% |
| TTT3R | 93.5431% | 1.902778 | 0.00000% |
| FILT3R | 67.5730% | 1.394245 | 0.02444% |

每方法新4的有效GT像素访问共547012，缺失239420；所有786432网格位置纳入缺失统计。有效GT上的预测均为正且有限，无无效预测替代或删除。8张相邻照片和像素不是独立实验重复，没有显著性、泛化或长程结论。FILT和CUT在这里很接近，不能把小幅数字差写成已达成proposal。

![全部新4深度误差](../work/S26B_reporting/new4_depth_scores.png)

![全部新4原始实拍](../work/S26B_reporting/all_new4_real_photos.png)

图中是全部预定新帧，不按误差挑图。旧4共同AbsRel83.3382%、逐帧RMSE均值1.725768m；三方法返回的旧depth仅有预定log/exp数值往返差，旧4分数基本相同。**当前不能把失败归因于新观测破坏记忆：共同旧图在新8优化之前就已经很差。** 尺度/坐标转接、短片段条件和原目标的约束必须先排查；目前没有确定根因。

## 锁住旧深度，旧点的位置仍变化了吗

预先写好的描述诊断验证旧depth/pose在原容差内、pp完全相同，所有28帧的world point均符合自身depth/pose/pp/focal反投影。随后保留每方法旧4全部786432像素。结果如下，单位和范围不能与GT误差混淆：

| 方法 | 旧world点位移均值（cm） | 位移P95（cm） | 去除focal算术项后剩余最大范数（m） |
|---|---:|---:|---:|
| CUT3R | 2.34637 | 7.65552 | 2.609e-07 |
| TTT3R | 0.60429 | 1.97886 | 2.355e-07 |
| FILT3R | 2.11660 | 6.91634 | 2.593e-07 |

公式为`X=R[d(u−cx)/f,d(v−cy)/f,d]+t`。仅代入变化后的focal，已可解释这里绝大部分保存点位差，余量约1e-7m。**这只是保存字段的算术分解，不是冻结focal后重跑GA的因果实验，也不是几何伤害。** TTT点位变化更小却深度更差，正说明“变化小”不能自行充当正确性指标。

S26B没有实例化或提交Surfel，没有运行query/cache/选图或视频生成。另做的历史12份focal与当前8份的均值算术重放，相对差CUT1.7702%、TTT0.3969%、FILT1.6401%；它是对源码列表行为的假设两轮计算，不是实测缓存错误，当前8均值也不是已证明正确的策略。原common4与CUT8同时改变头上下文、3/7图边、初始化和联合目标，不能把差异称单变量作用。

## 失败与复用如何处理

1. 原S26共同旧4完成400步及clean后，独立NumPy clean参考在12/786432值失配而FAILED。11个半像素取整翻转与1个传播差异已逐点解释；独立dense-gather参考保留原Torch FP32矩阵运算顺序后全值字节相同，没有放宽容差或豁免边界。
2. 29项保存量复核允许IMPORT_VALIDATED导入。原FAILED保留；历史未保存的PnP细节、module inventory、原postfinal标量等明确NOT_RECORDED，新纯函数重算不冒充原记录。
3. S26B首次启动在读取数据前因未显式导入importlib.util失败，0新GA/GT。新启动合同只显式预加载标准库，用runpy执行同一冻结worker；原失败和所有科学源码保持。成功的独立外控在work/S26B_execution_attempt2，16:17:18.533534–16:19:06.814613UTC。

| 方法 | GA连同观察/校验秒数 | 外控总秒数 | 观察到的峰值GiB |
|---|---:|---:|---:|
| CUT3R | 31.729 | 35.831 | 1.495 |
| TTT3R | 31.409 | 35.266 | 1.495 |
| FILT3R | 31.678 | 35.624 | 1.494 |

每臂400次Adam、1次MST和1次clean完整；真实clean全像素与新参考完全相等，固定参数阶段检查和中间observer日志均落盘。不是优化后的速度benchmark。

不同作者的OpenCV/逐行全网格复算已实际完成28行及10组×4均值，共5505024网格像素访问、3802488有效GT访问；主指标最大差2.23e-16。它是同一已见数据的团队内不同实现复核，非外部复现。不是把所有JSON辅助字段都独立核了一遍。全旧点描述诊断另耗约24.53秒，0模型/GA/GT。

## 科研决策与技能落实

遵循Supervisor第2章的强基线→具体失败→根因→方法：本轮已找到需要解释的真实组件劣化，但先审输入契约，不能把程序转接或弱约束误当研究发现。S27正准备保存数据的尺度诊断与原程序坐标审计，先区分原头是否已错、优化后是否改变尺度、共同旧depth是否把错误固定给后续。

本地Claude科学批判技能用于区分数值变化、真实误差、因果与外推。近邻原文已排除泛化“同步旧地图/缓存/按变化优先修图”的新意：[BAD SLAM](https://openaccess.thecvf.com/content_CVPR_2019/papers/Schops_BAD_SLAM_Bundle_Adjusted_Direct_RGB-D_SLAM_CVPR_2019_paper.pdf)、[BundleFusion](https://arxiv.org/pdf/1604.01093v3)、[ElasticFusion](https://roboticsproceedings.org/rss11/p01.pdf)、[DSO](https://arxiv.org/pdf/1607.02565)。具体对象与适用范围见[原文排重](../work/S26B_commit_prior_check/review.md)，不把这四篇说成穷尽所有近邻。

完整视频生成仍未完成，新机制与跨场景确认尚缺；PhD深度/CCF A质量仍是目标，不是本报告已达到的状态。

## 复查入口

- 原S26失败：results/S26_consumer_baseline/common_old；[保存量恢复](../work/S26_clean_recovery/DIAGNOSIS_AND_IMPORT.md)。
- S26B父合同SHA `147357aa1b24caeb813c01fd822cb96f754c2573437d0db6ac8a05b7cbd4d90c`，work/S26B_preparation/run_manifest.json。
- 第二启动合同SHA `15912f6f012cad51986bb67669997da1a9fc4fae08d16eb0c3d88c9cf9a7cb46`，work/S26B_execution_attempt2_preparation/contract.json；成功回执work/S26B_execution_attempt2/receipt.json，原dispatch仍FAILED。
- 所有真实输出与评分：results/S26B_consumer_baseline；不同作者复算work/S26B_root_numeric_review。
- 旧点完整描述与逐像素NPZ：work/S26B_commit_diagnostic/results；固定协议与执行三SHA同上级目录。
