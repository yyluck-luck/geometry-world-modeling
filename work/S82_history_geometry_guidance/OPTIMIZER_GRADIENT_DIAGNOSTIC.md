# 人工 autograd 验证：本地深度参数与取值路径断连

**结果：在此次人工调用链中确认断连。** 本地实际函数得到的临时深度叶有梯度，但注册到优化器的逐帧深度参数没有梯度，也没有被一步 Adam 更新。对照采用官方 DUSt3R 的相关注册结构，梯度可以到达注册参数并改变它们。

实际执行 UTC：2026-09-10 **18:11:40.279695–18:11:40.959446**（北京时间 09-11 02:11:40）；脚本内计时 **0.679614416 秒**，不含此前 Torch 导入。CPU / float32 / Torch 2.7.0；解释器为本项目 `.venv/bin/python`。这是真实执行的**人工小张量诊断**，不是模型、真实深度或重建实验。

输入是两张 1×2 的 log-depth 参数 `[0,1]`、`[2,3]`，损失是 `sum(exp(log_depth))`。两组初始损失均为 **31.192874908447266**，各执行一次 backward、一次 Adam（lr=.01，betas=.9/.9）。不以此人工损失解释任何场景质量。

| 观察 | 本地实际 AST 调用链 | 官方结构的小型对照 |
|---|---|---|
| 注册参数 | 两个 `nn.ParameterList` 叶 | 初始化时一次堆叠、注册的一个叶 |
| 注册叶梯度 | 两个均为 `None`，不是数值零 | 四元素 `[1, 2.7182817459, 7.3890562057, 20.0855369568]` |
| 临时叶 | `ParameterStack` 新返回的叶收到上述四个梯度；不在 Adam 参数列表 | 取值时没有新建临时参数 |
| 一步后的注册值 | 完整保持 `[0,1]`、`[2,3]` | 约变为 `[-.01,.99]`、`[1.99,2.99]`，完整 float32 数值在 JSON |
| Adam 状态数 | 0 | 1 |

测试以 AST 从当前本地源码仅提取 `get_depthmaps`（245–249）、`ParameterStack`（303–317）、`_ravel_hw`（320–328），没有导入原几何模块。透明包装只记录 `ParameterStack` 的返回叶，未改变其计算。两个组传给 Adam 的都是各自 `net.parameters()` 中已注册的叶。

源码链解释：本地 `get_depthmaps` 每次调用 `ParameterStack`；后者的 `stack().float().detach()` 已切断与原注册叶的连接，随后另建的 `nn.Parameter` 也没有自动注册回原模块。损失的梯度因而到达临时叶，Adam 仍只持有原叶。官方源码在初始化时堆叠并注册，之后 `get_depthmaps` 直接取 `self.im_depthmaps.exp()`；本次对照只复现这一结构，**没有运行完整官方优化器**。[已读官方源码](https://raw.githubusercontent.com/naver/dust3r/main/dust3r/cloud_opt/optimizer.py)

本地源文件：`work/S20_environment/isolated_vmem_source/extern/CUT3R/cloud_opt/dust3r_opt/optimizer.py`，12212 B，SHA256 **`f78f52eee0fc5e435e2c8b16a868174a285e7155577c11eef0f82a464e207b11`**。脚本 SHA **`fad5b93b2a543e786221b1ac1b5316dd0419571db4a3a7ce96087c7c5e2e9794`**；结果 JSON SHA **`e3c73dc65c8e72e3476ae80bd26d4c037a4fea2cf5b044ccff6b868d4b33faa2`**。执行前范围与否证条件见 `OPTIMIZER_GRADIENT_DIAGNOSTIC_CONTRACT.md`；全部叶身份、梯度、参数前后值与真实时间见同名 `.json`，可复核程序见同名 `.py`。

**下一步意义与局限。** 后续若选固定相机/K 的深度优化，不能原样依赖这条取值路径；应先在隔离修订中恢复梯度连接，再验证深度确实更新、相机/K 保持固定。当前没有修原源码，也没有运行该后续方案。本测试没有执行场景目标函数、初始化/清理、渲染或历史 S26，因此不能声称所有 optimizer 参数都不工作、历史损失无效或真实几何必然失败；边级变换、焦距等其他参数仍可能更新。当前只保存 raw heads 的批次不走此链，不因此失败。修复梯度接线属于普通工程修复，`NO_METHOD_SELECTED / new_method_validated=false` 保持。
