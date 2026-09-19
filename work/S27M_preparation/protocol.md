# S27M：common4 原初始化与深度梯度最小诊断（待独立审查／冻结）

**仅新增一次原MST/PnP初始化和一次原目标forward/backward，0 Adam step、0网络前向、0传感器GT读取。** 比较的是“本次重放的初始化depth”与“旧common4最终depth”；不得称前者是原历史快照。此检查不改善分数，不修改原ParameterStack，不重跑已完成的400步。

起因与source推导见 `work/S27_scale_diagnosis_source/audit.md`。两个判别量：原注册 `im_depthmaps.0..3` 的grad是否None；本次MST depth是否与原common4最终保存depth相同。科学结果不作为PASS强制条件；出现非None或不相同也是有效反证，应报告和定位，不能改容差让结果符合猜想。

## 输入与执行路径

- 原S26B固定manifest及完整源/依赖合同不变；原common4的四份S21 `original4` 六头、same optical c2w控制数据、seed=0/CPU8/FP32。控制相机已是显式GT输入；只加载已封存c2w，不重新解析TUM轨迹或读取sensor depth。父manifest的身份核验可能读取已允许camera源文件的字节，仅用于SHA，不假称这属于盲测。
- 复用冻结S26B runner的 `original_context`，保持原common4相同的初始化顺序：原PIL入口重建8个views，再只用前4和4份原头组装星形。此前三源预处理/28头兼容PASS只引用，不重新执行独立兼容或任何网络。
- 使用原adapter的完整 `prepare_output(...poses=common4,depths=None,niter=400,lr=.01)`；`global_alignment_loop`入口用观察器替换成一次原 `scene()` 和 `backward()`，抛出专用 `DiagnosticComplete` sentinel。原MST已完成、原Adam尚未创建，该sentinel是本协议合法终点；不调用原clean和原输出后处理。
- 观察器对 `ParameterStack` 仅调用原函数并保留其返回对象用于读取grad，不替换Tensor、不调用retain_grad、不改数学/数据。分别记录注册depth和临时叶子是否位于原 `net.parameters()` 可训练列表。记录focal/pairwise及其他注册梯度，让“所有梯度均不可达”的异常与单独depth断图区分。
- `Adam.step` 和clean设拒绝护栏；要求实际尝试次数均0。backward前后注册parameter的完整名称集合与对象identity完全相同，再核所有值逐元素相同；只有grad缓存允许变化。一次反向传播是新诊断计算，不计为400步中的任何一步。

保存 `mst_state.npz`（depth、注册log-depth、pointcloud、focal、pp、c2w、pw-scale、pw-transform、adaptors），每次原 `align_multiple_poses` 的源/目标相机与s/R/t，每次PnP成功与focal/pose，`gradient_report.json`，`old_final_comparison.json`，源身份与回执。先落盘新MST/梯度，再只从旧common输出读取depth比较，旧depth不传入场景。

结束时按父manifest的 `source_identities` 核实际载入的geometry模块；对全部实际loaded overlay模块逐路径核 `dependency_identities` SHA并写回执，不冒称启动时已重核全部5523依赖。最后重新核父 `identities` 全量以及本合同全部身份，覆盖未进入loaded模块清单的AST wrapper/adapter/源与控制文件。

## 身份、资源与解释

`contract_candidate.json` 中真实输入SHA继承已封存metadata；本准备阶段不读取NPZ、RGB、控制相机或GT字节。独立审查后root把合同另存为 `contract.json` 并置FROZEN，CLI要求确切合同SHA。输出新目录 `results/S27M_mst_gradient_diagnostic`，已存在即拒绝，任何失败保留。

建议root沿用原外层资源监督：`.venv-cut3r/bin/python`，原S17C overlay环境，CPU8、120秒、8GiB进程树RSS，磁盘至少1GiB；超时/内存停止并留失败，不自动重试或改分辨率。这个上限是待审预算，不是实际测量。脚本本身没有后台重跑/调度。

比较同时报告bitwise equal、最大/逐帧差和固定 `atol=rtol=1e-6` 的描述性allclose；allclose不改变原分数，也不是覆盖数值不相同的许可。若深度完全相同且注册depth无梯度，可支持“该兼容重放中depth由初始化决定，原目标没有给注册depth梯度”；仍不说明初始化为什么失准，不把该结果概括为所有场景。若不同，先查原RANSAC/seed/载入源或额外写入，不能把重放强称历史初态。

本脚本审查用静态AST compile，不调用模型/GA/数组。实际执行尚未授权给本子agent，交root审查冻结后决定；所有原S26/S26B冻结脚本、失败/成功记录保持。
