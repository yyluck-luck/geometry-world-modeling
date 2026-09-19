# S28 不同作者保存输出数值复核协议

本轮仅准备，不执行脚本，不启动等待循环。父任务审核本代码并明确启动后，复算 S28 两个已完成 common4 分支。源码依据为冻结 S28 runner/scorer 及 S26B 原公式；方法沿用不同作者 OpenCV 解码、逐行累加参考。采用 Supervisor 第 2 章“baseline → 真实失败 → 机制”的证据边界及已读科学批判性思考 skill，不把普通梯度修复称作创新。

## 固定问题与完整范围

1. 两个 producer 和 scorer 均须 PASS，合同、源版本、全部 producer/scorer 输出及输入封存记录匹配，四个原始 head NPZ 全字节校验。完整四个 GT PNG 先逐文件读取与 SHA 封存，全部完成后才允许任何 NPZ/PNG 解码。先写 input_seal.json，失败立即停止，不以部分结果继续。
2. 两组各 4 帧，共 8 个完整 384×512 深度网格、1,572,864 次像素访问。GT 原图为 480×640 uint16，除 5000 为米；整数中心最近邻坐标 `(5*(2*t+1))//8`。GT 在目标网格 >0 为唯一有效分母；无距离截断、置信度过滤或尺度拟合。
3. 全数重算 AbsRel、RMSE、严格 δ1、无效预测比例，以及 6 个计数和状态；任一有效 GT 上预测无效则该帧 AbsRel/RMSE 为 null，δ1 仍以全部有效 GT 作分母。逐行 float64 累加、math.fsum 汇总；δ1 用两边乘积不等式，与原除法表达独立。空帧及无效帧规则原样保持。浮点比对沿用既有独立参考 abs_tol=1e-12、rel_tol=1e-10；整数、null、状态要求精确相同，不改容差。
4. 两组完整 4 帧等权均值共 8 个浮点聚合量，全部 defined_frames、分母和异常帧清单；JSON 与 CSV 全 8 行也必须一致。不能删帧、改成像素池化或仅汇报有定义的帧。
5. 解码 initial_raw 中全部 parameter/buffer，逐个验证原封存元数据中的名字、形状、dtype、requires_grad 和张量内容 SHA；A/B 全初态原始张量逐字节一致。initial_decoded 全部 9 个字段报告字节比较，其中 depth 和 objective 要求精确相同。
6. 对各自初态比较终点：A 的 4 张注册 log-depth 与解码 depth 必须逐位不变；B 的 4 张全像素变化数量、最大与平均变化和深度比值完整报告，不要求改善，也不把目标降低视作误差降低。这里“原版 A”是此次新 matched A 分支，相对于它自己的初态；不重读旧 S26 结果冒充同次比较。
7. 两份 ordinary trace 和两份 gradient trace 各 400 条；逐条核完整 0..399 步序、Adam 实际步号、对应 loss/lr、原线性学习率、每步 4 深度及 focal/pair-pose 的记录、所有帧边界统计。A 深度 grad 为 None；B 深度 grad 存在且有限，允许范数为 0。覆盖共 800 步，不根据正负结果选取步骤。
8. 末尾重核本次读取的源与数据 SHA，保存独立 metrics、initial/depth、全部 step 摘要与 receipt。失败保留，不自动复跑或更改方法。

## 已知实现与证据边界

- 自己实现指标数学，不导入模型、GA、MST、scorer 或 Torch；不调用 backward。仅 NumPy 和 OpenCV 处理保存文件。
- 800 条梯度记录属于有源版本约束的历史观测，本复核检查记录的完整性/一致性，未重新计算梯度，也不能重造历史内存。
- 只绑定 5 个直接执行源码与父 manifest；全部大依赖的既有检查来自 producer PASS 与冻结来源链，不再重 hash 967 个依赖。
- 四帧是既见数据的技术诊断，不是独立测试集、泛化、生成视频成功或新方法收益。根任务告知修复后误差更大；本协议不为该终点改变评分或参数。
- 当前准备工作为源码与 JSON 合同读取、AST parse/compile。0 真实数组解码、0 GT 图片字节读取、0 模型/GA/MST/backward，未运行复核入口。

## 明确执行入口

父任务审查本目录 candidate.json 中的 self SHA 后，运行其 command 列表。脚本只接受显式 --contract、--sha256、--script-sha256，不扫描或轮询结果。正式执行将新增 attempt.json；如果已有 attempt/receipt，拒绝覆盖。
