# 人工小张量梯度诊断：执行前范围

记录时钟：2026-09-10 18:09:32 UTC。root 已授权此最小 autograd 检查；只验证当前调用链，不执行完整几何优化、模型、真实数据或历史 S26 重算。

- 固定本地 `cloud_opt/dust3r_opt/optimizer.py` SHA `f78f52eee0fc5e435e2c8b16a868174a285e7155577c11eef0f82a464e207b11`。以 AST 仅提取 `ParameterStack`、`_ravel_hw` 和 `PointCloudOptimizer.get_depthmaps`，不导入原模块。
- 人工输入是两张 1×2 的 log-depth 参数，值分别 `[0,1]`、`[2,3]`；CPU float32，损失只取两个深度图元素之和。不涉及 RGB、真实深度、NPZ、checkpoint、网络或随机初始化。
- 本地组注册 `nn.ParameterList`，原样调用提取的 get_depthmaps；用透明包装记录 ParameterStack 返回的临时叶。对照组在初始化时一次堆叠并注册，此后直接 exp，复现官方 DUSt3R 的相关梯度结构，但不是完整官方 optimizer。
- 两组各做一次 backward 和一次 Adam 更新（lr=.01，betas=.9/.9），优化器参数只取已注册叶。记录叶身份/梯度、临时叶梯度、更新前后值、来源/脚本 SHA、真实起止时间与运行环境。
- 否证规则：如果本地注册叶收到非零梯度并改变，则本次“detach 阻断该链”疑点被否证。若仅临时叶有梯度、本地注册叶不变，而对照组注册叶有梯度且改变，则支持这个人工调用链的断连诊断。其余情况保留为不能判定，不硬写成功。
- 不修改原优化器或实验合同；不以结果声称历史损失无效、所有 optimizer 参数均未更新或真实重建必然失败。本次不重跑作者融合测试。
