# 可冲击顶会的创新候选：扩大检索与数学筛选

## 先说结论

检索显示，显式 3D、长期空间记忆、相机轨迹检索、深度重投影和不确定性视角选择都已有强近邻。顶会级机会不在“再加一个模块”，而在把你的 proposal 重新定义为一个可测量的问题：**在固定历史预算下，如何选择对未来可见几何状态最有用、且风险可校准的记忆**。

## 已被覆盖的数学路线

FisherRF（ECCV 2024）用 Fisher information 和 Expected Information Gain 做主动视角选择；NeRF Director（CVPR 2024）讨论不确定性视角选择的偏差；NVF（CVPR 2024）把位置场不确定性组合成射线不确定性；2025 年已有子模视角选择。因而“最大化信息增益”“用不确定性选视角”“子模贪心选历史”不能直接声称新颖。

Conformal prediction 已用于场景图不确定性（CVPR 2025）和动态系统预测区间；因此“给几何预测加置信区间”本身也不足够。必须证明几何风险校准直接改变记忆选择，并改善未来状态预测。

## 候选 1：几何风险校准的固定预算记忆选择（最强）

令历史候选为 $H=\{h_i\}$，目标未来状态为 $y_{t+1:t+K}$，选择集合 $S$ 满足 $|S|\leq k$。定义每个候选的几何残差向量 $r_i=(r_i^{repr},r_i^{depth},r_i^{vis})$，用校准集得到风险上界 $q_{1-\alpha}(r_i)$。选择目标可写为

$$S^*=\arg\min_{|S|\leq k}\;\mathbb E[\ell(\hat y_{t+1:t+K}(S),y_{t+1:t+K})]+\lambda\,\mathrm{Cost}(S),$$

其中 $\hat y$ 是生成器或几何预测器的未来状态，风险项由 conformal 校准而不是未经验证的网络 confidence 给出。候选增益可定义为

$$\Delta(i\mid S)=\widehat I(y_{t+1:t+K};h_i\mid S)-\beta q_{1-\alpha}(r_i).$$

算法每次选择最大 $Δ$，并记录 coverage、风险和总 FLOPs。理论目标不是宣称全局最优，而是证明在近似单调次模条件下，贪心达到 $(1-1/e)$ 型收益下界；若条件不成立，报告反例并把方法降级为经验方法。

**真正的新颖点**：选择的是“未来任务误差 − 几何风险”的联合效用，而非相机距离、像素相似度或单独不确定性。

**必须通过的实验**：相同 eligible history、相同特征、相同 $k$、相同生成预算；比较最近帧、相机距离、随机、覆盖贪心、Fisher/EIG、单独 confidence 和本方法。在遮挡、视角变换、变点和跨场景 held-out 上报告未来位置误差、重投影误差、校准 coverage、RGB 质量和成本。

## 候选 2：几何一致性约束下的风险敏感选择

把记忆选择视为 constrained optimization：

$$\min_S \; L_{future}(S)\quad\text{s.t.}\quad P(\mathrm{reproj\ error}>\epsilon\mid S)\leq\delta.$$

用拉格朗日形式 $L_{future}(S)+\eta[\hat P_\alpha(e>\epsilon)-\delta]_+$，可以把“不能把低 RGB MSE 当几何真值”变为正式约束。顶会价值来自风险约束与生成质量之间的 trade-off 曲线，而非一个最佳点。

近邻风险：constrained active perception、safe exploration 和 conformal risk control 已存在；必须把约束绑定到 world-model 的未来状态而非静态重建。

## 候选 3：共同合法前缀的变点模型

令每个历史观测带有隐变量 $z_t\in\{\text{same-geometry},\text{changed-geometry}\}$。用几何残差和可见性建立变点后验：

$$p(z_t\mid r_{1:t})\propto p(r_t\mid z_t)\sum_{z_{t-1}}p(z_t\mid z_{t-1})p(z_{t-1}\mid r_{1:t-1}).$$

只保留后验超过阈值的共同前缀，再把变点后的片段作为新状态。它比固定时间窗更贴近遮挡和物体运动，但 HMM/BOCPD/分段记忆已有大量近邻；创新必须来自几何可见性条件与生成未来误差的联合建模。

## 候选 4：对象状态的集合覆盖与可见性账本

把记忆从帧改为对象状态 $o_j=(x_j,\Sigma_j,m_j,a_j)$，其中 $x_j$ 是位置，$\Sigma_j$ 是不确定性，$m_j$ 是可见性，$a_j$ 是外观证据。用集合覆盖目标

$$F(S)=\sum_j w_j\log\det(I+\sum_{i\in S}A_{ij})$$

选择覆盖不同对象和视角的证据。该形式有子模优化基础，但对象中心记忆、slot memory、遮挡跟踪已有强近邻，暂不推荐作为第一贡献。

## 候选 5：最小充分几何记忆（信息瓶颈）

学习压缩记忆 $M=g(H)$，同时保持未来状态信息：

$$\min_g I(H;M)-\gamma I(M;Y_{future})+\rho\,D_{geom}(M,H).$$

可解释版本是固定 token/字节预算下，最小化未来预测误差并约束几何重投影误差。信息瓶颈、记忆压缩和 token pruning 已很成熟；只有在证明“几何充分统计量”比通用压缩更稳定时才有机会。

## 推荐研究路线

先做一个四格诊断：可信/受扰几何 × 普通/几何约束 RGB。若确认几何风险与重影存在稳定交互，冻结候选 1；若不存在，停止几何记忆创新，转向数据或模型误差分析。候选 1 的第一版不需要训练新大模型，可在现有保存特征、相机 JSON 和小规模真实配对上验证选择器与校准器。

## 顶会判据

必须同时满足：新问题定义；与至少三类强基线的公平比较；一个明确数学目标；风险或近似保证；跨场景 held-out；失败案例；开销报告；独立复算。只有报告 MSE 下降、生成图更清晰或选择了更少历史帧，不能构成顶会贡献。

## 主要核验来源

- [FisherRF, ECCV 2024](https://www.ecva.net/papers/eccv_2024/papers_ECCV/html/2130_ECCV_2024_paper.php)
- [NeRF Director, CVPR 2024](https://openaccess.thecvf.com/content/CVPR2024/papers/Xiao_NeRF_Director_Revisiting_View_Selection_in_Neural_Volume_Rendering_CVPR_2024_paper.pdf)
- [Neural Visibility Field, CVPR 2024](https://openaccess.thecvf.com/content/CVPR2024/papers/Xue_Neural_Visibility_Field_for_Uncertainty-Driven_Active_Mapping_CVPR_2024_paper.pdf)
- [Conformal Prediction for Scene Graphs, CVPR 2025](https://openaccess.thecvf.com/content/CVPR2025/papers/Nag_Conformal_Prediction_and_MLLM_aided_Uncertainty_Quantification_in_Scene_Graph_CVPR_2025_paper.pdf)
- [Video World Models with Long-term Spatial Memory, NeurIPS 2025](https://papers.nips.cc/paper_files/paper/2025/hash/467655d26fcc207bca08915dc91964c6-Abstract-Conference.html)
