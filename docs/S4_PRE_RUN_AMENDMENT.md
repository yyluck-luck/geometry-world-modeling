# S4运行前修正：点图与位姿是分别预测的

本修正在任何真实CUT3R输出出现之前由独立源码审查触发。原协议S4_TWO_FRAME_PROTOCOL.md保留原文与首次冻结哈希，以下取代其中“self点图经位姿必然等于other点图”的错误前提。

固定官方head_factory为linear、pts3d+pose实际选择LinearPts3dPose。该类分别预测自视点图、位姿和other点图，其中other点图来自cross_proj。原协议误读了同文件中未被该factory选中的LinearPts3dPoseDirect；后者才通过位姿代数变换生成other点图。

因此：

- 不将other = camera_c2w × self作为必须通过的不变量，也不据不相等判模型坏了。
- 保存两条路径的数值差作为描述性的点图/位姿自洽诊断，既不筛像素，也不改模型或评分。
- 继续使用self_view的正向Z比较深度；运行时必须记录实际downstream_head_class为LinearPts3dPose。
- 位姿相对误差沿用CPU第一帧深度尺度，明确是在点图与位姿共享尺度的假设下作诊断，不使用第二帧或GT位姿另行对齐。
- 矩阵形状、有限值、旋转正交性、输入/输出哈希仍为必须满足的运行检查。

第一帧校准、第二帧留出、采样/有效性、CPU/MPS比较和所有其他规则均保持不变。来源为固定提交8bc15dc92a6d7fd92920b4ec81540d3dec7d3ecf的src/dust3r/heads/__init__.py与linear_head.py。实际纠正时间和修正文件哈希追加到研究日志。
