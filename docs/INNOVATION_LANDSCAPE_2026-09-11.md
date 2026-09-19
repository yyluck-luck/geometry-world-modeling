# Geometry-aware World Modeling：创新方向检索（2026-09-11）

> **实验编号说明（给新读者）**：本文保留项目内部编号以便追溯；首次出现时应写成“编号（具体试验名称）”。统一名称见 [`work/S90_proxy_resumable_index/EXPERIMENT_NAME_LEGEND.md`](../work/S90_proxy_resumable_index/EXPERIMENT_NAME_LEGEND.md)：S86（单场景四目标几何条件注入基线实验）、S87（末端引导强度控制与多步引导必要性反例实验）、S88（RTMV相机JSON元数据与静态投影数据资格检查）、S89（RTMV配对数据TLS接续失败审查）、S90（RTMV归档配对数据恢复与索引协议审查）。S88–S90是数据资格、传输和协议审查，不是模型性能实验；编号也不表示实验成功。


## 研究问题

RQ1：当前生成重影究竟来自错误几何、历史记忆选择，还是扩散/末端混合？

RQ2：哪些方向已经被现有工作覆盖，不能直接作为 proposal 的创新？

RQ3：在本机资源和现有证据下，哪个候选最值得先做可证伪实验？

## 已覆盖方向

显式深度与跨帧重投影已经被 GeoVideo（NeurIPS 2025）用于视频扩散的几何正则化；World-consistent Video Diffusion（CVPR 2025）直接把显式 3D 建模放入视频生成；Geometry-guided Online 3D Video Synthesis（CVPR 2025）用时空深度和 TSDF 累积指导多视角融合。这意味着“预测深度 + 重投影损失”“建立 3D cache”“用几何引导融合”都不能单独构成新方法。

长程空间记忆也已有 Video World Models with Long-term Spatial Memory（2025）和 Context-as-Memory（2025）等路线；后者还包含基于相机轨迹的历史检索。因此“保存历史帧”“按相机距离检索”“把历史帧拼到条件输入”属于已有设计空间。

多视角 RGB-D 生成和几何一致性已有 MVD-Fusion（2024）、MVGD（CVPR 2025）、MVDD（ECCV 2024）等工作。单纯增加 RGB-D 条件、epipolar attention 或多视角深度约束，近邻覆盖风险很高。

## 候选创新轴

### A. 几何不确定性感知的记忆选择

不是按最近相机或固定数量取历史，而是估计每个历史观测在目标区域的几何不确定性，并在固定计算预算下选择能最大幅度降低未来状态预测误差的子集。必要实验：相同 eligible history、相同特征、相同 k、相同总 FLOPs，对比最近帧、相机距离、随机、覆盖贪心和 uncertainty-aware 选择。只有在 held-out 场景、遮挡前后和变点轨迹上稳定降低后状态误差，才有创新依据。

风险：如果不确定性只是匹配置信度或深度误差的重命名，会被视为已有 selective retrieval。

### B. 共同合法前缀记忆（带几何有效期）

把历史记忆拆成“仍由同一相机/物体几何解释的共同前缀”和“发生变点后的新段”，在检测到几何关系失效时只截断失效部分。候选新点是把记忆有效性定义为跨视角重投影残差与可见性共同满足的条件，而不是单独按时间或相机距离检索。

风险：事件分段、变点检测和历史 cache 替换已有先例；必须证明共同合法前缀在遮挡、视角变化和物体运动下带来新的预测收益。

### C. 几何错误与外观混合的诊断分离

建立 2×2 诊断：可信/受扰几何 × 普通/几何约束 RGB。目标不是先提出融合器，而是证明重影来自 geometry error 与 conditional averaging 的交互。若可信几何仍重影，应停止“几何修复”方向；若只有受扰几何重影，再设计针对不确定区域的条件门控。

风险：这是诊断协议，暂时不是方法；只有诊断揭示稳定、可重复的新失效机制后才值得方法化。

### D. 对象级几何状态而非帧级记忆

将记忆单位由整帧改成对象轨迹状态（位置、尺度、可见性、外观证据及置信度），在目标视角中只渲染可解释区域，剩余区域交给生成器。与已有整帧 cache 的差异是对象级状态和显式可见性账本。

风险：对象持久性、slot memory、遮挡推理已有广泛工作；必须先作近邻检索和严格对象级基线。

## 当前排序

第一优先：C（最便宜、能直接解释 S86/S87 的重影来源）。

第二优先：A（若 C 证实几何不确定性是关键，再做固定预算选择）。

第三优先：B（需要动态/变点数据，数据缺口较大）。

暂缓：D（近邻最多、需要对象标注或可靠跟踪）。

## 结论

当前没有证据支持已选定创新。最合理的研究门是先取得同一视角 RGB、深度和相机配对，完成 C 的四格诊断；然后根据结果决定是否进入 A。所有候选都必须与相同历史信息、相同特征和相同计算预算的强基线比较。

## 核验来源

- [GeoVideo, NeurIPS 2025](https://proceedings.neurips.cc/paper_files/paper/2025/file/536d18fbb454f80221465f1a42c6f389-Paper-Conference.pdf)
- [World-consistent Video Diffusion, CVPR 2025](https://openaccess.thecvf.com/content/CVPR2025/papers/Zhang_World-consistent_Video_Diffusion_with_Explicit_3D_Modeling_CVPR_2025_paper.pdf)
- [Geometry-guided Online 3D Video Synthesis, CVPR 2025](https://openaccess.thecvf.com/content/CVPR2025/papers/Ha_Geometry-guided_Online_3D_Video_Synthesis_with_Multi-View_Temporal_Consistency_CVPR_2025_paper.pdf)
- [MVD-Fusion](https://arxiv.org/abs/2404.03656)
- [Video World Models with Long-term Spatial Memory](https://arxiv.org/abs/2506.05284)
- [MVDD](https://eccv.ecva.net/virtual/2024/poster/573)
