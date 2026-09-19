# S28 协议独立前审（尚待代码）

实际记录时间：2026-09-06T17:05:01.791771+00:00。审读者 research_novelty_routes 与实施作者不同。本轮仅完整读候选协议；真实数组、GT、模型、GA 与人工张量执行均为 0。结论是 **协议方向可接受，尚未给予执行前 PASS**。

绑定文件：`work/S28_gradient_scale_control/PLAN_CANDIDATE.md`，SHA256 `e4cbee7ed699d04b2b3ef0e022e588e95f8bc14c8a7be8dc22701038c8292192`。

新 A 与新 B 各自原初始化、各 400 步，且只在原 MST 之后切换深度 getter 的梯度连接，能比旧历史终点更明确地区分修复效应。保留原相机方向初始化与目标、两臂封存后评分、已见四帧及非创新的边界均合理。

代码审核必须关闭以下检查点：

1. 跨进程初态比较全量注册 parameter/buffer 的名称、shape、dtype、原始 tensor bytes 与 parameter flags；不可比较跨进程 Python id，不可仅用 NPZ 容器 SHA 代替张量相同。单臂 getter 前后才检查对象 identity。
2. 只修改 getter 的单一表达式，不全局改 ParameterStack，不新建 Parameter；保存 AST 差异和实际加载模块身份。
3. 第一 forward 原／修复数值相同且发生于更新前；诊断额外求值单独计数，不累积梯度，不改变初态。B 仅要求原可训练叶子的梯度存在且有限，不能把零范数错判为断图。
4. 初态全 raw 参数／buffer 落盘；B 任一不符即在优化前停止。同 seed 不能替代此门。
5. 每臂实际 400 Adam 步，完整末尾 objective/world/clean 验证使用原容差；日志明确 before-step 与 after-step。
6. 两臂各自 PASS、封存身份核实后才读取任何 sensor GT 字节；固定四帧原分母与原尺度评分。

上述是落码验收项，并非已发现实现错误。待作者完成源码、合同与人工检查后再做最终审读；不重复真实实验，也不把本记录当效果验证。
