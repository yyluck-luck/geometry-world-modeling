# S28 完整代码独立执行前审

实际完成时间：2026-09-06T17:16:07.949061+00:00。审查者 research_novelty_routes 与实施作者、人工测试作者不同。结论 **PASS_STATIC_PRE_EXECUTION**，无阻断性源码问题；这不是 S28 已运行通过。

绑定候选合同 SHA `b3f9472c11656f9a71da7ef5d704b11da4fc0f1c27d9bba91ead9b7942a29472`；runner SHA `d8553d5086bba1b922835fb55a225efe3d04175c63e64eeee7f98644c9d771d8`；scorer SHA `f930391a50d125b40e4775f6c903b08fd6a52636a9c99c59df63c668e041381b`。15 项标准库静态核实通过，记录见 `static_checks.json`（SHA `f341a94514e6a3b04b37feb617db3dd8f85066119536fd2a1e2674c4e17fb46f`）。核实了 22 项文本身份；相机 NPY 仅沿用封存元数据，未读其字节。本次真实数组／GT／模型／MST／backward／Adam／新增人工数值测试均为 0。

## 协议验收闭环

- 修复仅把 getter 中的 ParameterStack 表达式换成对原叶子的 stack/float/exp；没有包装新 Parameter，也未全局改 helper。原 worker 只有 mode、帧数、归档路径三处调度差异，独立归一 AST 后一致。
- 两臂 raw 初态比较覆盖全部注册参数和 buffer 的名称、shape、dtype、flags、SHA 与实际原始字节。原 forward 的预测头、置信权重、像素网格及边索引确实是 buffer，因此包含在匹配门中。跨进程不比较 Python id；同一臂 getter 前后则检查对象身份及值不变。
- 原／修复边界的深度与 objective 字节相同检查位于 Adam 创建前且在 no_grad 中；真实梯度由原每步 zero_grad/forward/backward 产生。B 要求原叶子 grad 存在且有限，允许零范数。A 仍要求原断图路线。
- 每臂保留原 400 步与完整末尾 objective、world 反投影、独立 clean 门；容差未改变。记录区分更新前 loss 与更新前／后统计。两次边界和一次 postfinal 额外 objective 单独标出，总 403 是源码路径推得，未来仍须核实际执行记录。
- 两臂所有产物 SHA、完整 400 步回执、输入封存与 NPZ 身份先核，再读取四张 sensor GT。沿用原深度指标及全分母、等帧均值，无 scale fit／confidence mask／远点裁切。

## 证据与执行边界

复用 root 已通过的人工 getter 检查（receipt SHA `fe9e2e9c029b305bf990540fdd8c5ca42b0f209a8d7985b72bbc229caa84627b`），本次未重复反传。它只验证小人工 all4/mixed8 的 getter 语义，不证明真实 8 帧旧／新冻结链。

Root 仍需另存正式 FROZEN 合同并绑定本审查，执行包装记录该合同自身前后 SHA。这里审的是候选快照，不自动覆盖未来修改。新 A/B 各 400 步是明确的匹配工程对照；不能把普通 autograd 修复、四帧已见数据改善或 loss 下降称创新／泛化／生成增益。任何数值或资源门失败均保留失败产物。
