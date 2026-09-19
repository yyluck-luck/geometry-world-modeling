# confidence、尺度与投影误差：先明确量的含义

本批只读官方训练定义、既有本地优化源码及 DUSt3R 一篇原文的局部抽取；不读 S83 新结果/heads/GT，不运行模型或数学程序，不修改冻结目标。`NO_METHOD_SELECTED`。**结论：显式误差尺度/协方差必须随坐标变换传播；当前学习 confidence 与 log(conf) 并未因此成为校准后的公制精度。不能据此给 S83 的 confidence 擅自乘除尺度。**

**已核的普通机制。** [DUSt3R，CVPR 2024，§3.2 Eq.2–4](https://openaccess.thecvf.com/content/CVPR2024/papers/Wang_DUSt3R_Geometric_3D_Vision_Made_Easy_CVPR_2024_paper.pdf)将点图按平均距离归一化，用欧氏距离 r 训练 confidence：ℓ=cr−α log c，典型 c=1+exp(a)。[官方 DUSt3R loss](https://raw.githubusercontent.com/naver/dust3r/main/dust3r/losses.py)与[官方 CUT3R loss](https://raw.githubusercontent.com/CUT3R/CUT3R/main/src/dust3r/losses.py)确认该执行式；不是平方欧氏距离。

[CUT3R 官方 512 DPT 配置](https://raw.githubusercontent.com/CUT3R/CUT3R/main/config/dpt_512_vary_4_64.yaml)声明 `ConfLoss(Regr3DPoseBatchList(L21,norm_mode='?avg_dis'),alpha=0.2)`，还有 RGB 项。其普通 3D 分支按 metric 标志选择共用 GT 尺度因子或预测/GT 各自因子，随后归一化；不能把全部训练残差说成未经归一化的“米”。`conf_self` 和 `conf` 分别进入对应分支。本次没有追溯发布权重的完整训练履历，当前 main 配置不等于权重训练回执。

本机优化器默认另取 w=log(c)，把它固定为点图拟合权重。**训练时的 c，与推理优化时的 log(c)，必须分开。** 后者是已实现的启发式变换，没有显式噪声分布或协方差归一化项；源码注释中 high/low confidence 的两例标签还与其数值相反，本稿以实际算式为准。

**数学含义（以下为本报告推导）。** 固定 r>0、允许任意 c>0 时，∂ℓ/∂c=r−α/c，驻点 c*=α/r；这只解释该单项倾向，不是实际网络的逐点等式。c 的下界、共享参数、训练归一化、天空/其他监督分支均限制这一解释。若误差被明确建模为三维高斯，负对数似然应含 ½eᵀΣ⁻¹e+½log detΣ；三维各向同性 exp(−c‖e‖) 密度归一化后则给 cr−3log c（加常数）。因此不能仅凭 cr−αlog c 的形状就宣称 c 或 log(c) 是已校准的逆方差/正确概率。

## 三种尺度情况不能混为一谈

1. **同一物理量的确定性坐标变换。** 对预测和真值共同施加 X′=sRX+t，s>0，则 e′=sRe、‖e′‖=s‖e‖。若原先真有协方差 Σ，则 Σ′=s²RΣRᵀ；各向同性标准差乘 s、precision 除 s²。若 c 被另行定义为未归一化距离 r 的逆尺度，才对应 c′=c/s；此时 ℓ′=ℓ+αlog s，仅在 s 固定且无范围截断时是无关参数的常数差。归一化分数的定义若同时消除了单位缩放，则无需这样改 c。
2. **整套相机与场景一起换单位。** 针孔相机、K 不变、相机中心与点一致变换时，相机坐标 q′=sq，π(sq)=π(q)，像素投影不变。故“米制误差乘 s”不等于“像素误差乘 s”。固定相机下，小误差可用 Σu≈JπΣqJπᵀ；Jπ含 fx/Z、−fxX/Z² 等深度/方向项。共同缩放时 Jπ缩小 1/s，与协方差的 s²相抵。近零 Z、遮挡切换和大误差不满足此线性近似。
3. **只变换预测，去拟合保持不变的给定相机/真场景。** 这是几何估计变化，不是单位换算；残差不再必为 sRe。拟合出的 s/R/t 本身也可能不准；若它们由同一预测估出，其不确定性与点误差相关，传播需要联合项，不能只套 s²Σ。固定相机只是优化权限，不代表相机/K 没有测量误差。

一个最小纸面反例：c=2，s=4，若直接按“逆距离”改为 c/s=0.5，再送入现成 log 权重，就变成负权重 log(0.5)，且越过原 confidence 下界。这否决该机械转换规则；**不是修改当前目标的理由**。即使所有 c/s 仍大于 1，log(c/s)=log c−log s 也会改变相对权重，而非简单给总损失乘同一个正数。上述都是普通量纲与概率变换知识，不作为新机制。

**最小可推翻检查（未来另立合同，未执行）。** 先做纯人工“仅改单位”检查：点、相机中心与误差一起从米换到厘米，固定 K/像素身份；投影、明确建模的标准化残差应保持不变，距离/协方差按 s/s²变化。若该检查失败，先修单位或传播实现，不启动新方法。再有独立评分权限时，封存 confidence 到物理误差的映射，在不同场景/尺度上检查误差与覆盖；普通 log(conf) 排序/固定阈值就是对照。若只用校准集有效、换尺度或场景即失效，应否决可迁移“校准不确定性”主张。当前 S83 仍只按既定目标做 100 步普通诊断，其成功/失败均不能单独证明这种概率解释。

**版本/范围。** 首个时钟 UTC 2026-09-10 18:41:00；最终记录时间和本地 SHA 见 `CONFIDENCE_SCALE_SOURCE_SCOPE.json`。官方两个 loss 文件为本次 main（未锁 commit），读 DUSt3R 行 48–55、130–217；CUT3R 行 59–66、274–419、966–1033，并注意批次监督分支；配置只核 model/criterion，postprocess 核 `reg_dense_conf`。论文只采用 CVF 索引返回的印刷 p.20700 §3.2 Eq.2–4，直接 PDF 请求为 403，未声称成功全文读取。没有新增第二篇论文；本地初试 `work/cut3r-local/src/dust3r/losses.py` 不存在，之后使用已知 VMem fork，仅作本地实现对照，不冒充官方 main 字节一致。
