# S30 协议与既有复用边界评审

记录：2026-09-06T18:06:22.882373+00:00。**协议可以进入已授权的最小实现；稳定最终源码前审必须核下面 7 个门。** 本轮只读 S30 协议、已有 S28/S26B 相关源码及 S29 JSON 身份／元数据；没有阅读仍在编写的 S30 runner/scorer，没有数组／GT 字节读取、MST、模型、优化或反传，不新加对照。沿用 Supervisor 2.2 的最少变量失败机制对照。

1. **各臂对自己的 S29 初态。** 我实际读取的两份 S29 raw 元数据均为 33 项，S29 合同已 FROZEN，两 producer 为 PASS_INITIALIZATION_EXECUTED，各 1 MST/3 PnP/1 objective、0 backward/Adam/clean；validation 为 PASS_VALIDATION_EXECUTED 且 hypothesis_passed=true。S30 第一次 Adam 前须绑定这些原回执与输出 SHA，逐项核 33 项名字、shape、dtype、requires_grad、内容 bytes 及 objective bytes；不能以 NPZ 压缩 SHA 相等替代张量比较，也不能要求 C2t/C2a 之间全部初态相同。新建状态的理由成立；不把它记成历史对象恢复。

2. **S28 条件分支要全部改对。** 旧 observer 只有 `arm=='gradient_only'` 才安装 getter，并有两处以 `arm=='original'` 判断 depth grad 应为空，还引用 `output_root/original`。S30 两臂都必须真实安装同一修复 getter，各自引用 S29 对应臂；Adam 前和每步 trace 后都要求 4 个注册 depth grad 非 None、有限，允许零范数。不能只改外层 mode 名或报告字段而留下原对照臂的无梯度路径。原参数／buffer对象、flags、optimizer成员与固定 pose/pp 的逐位不变门保持。

3. **403 次目标求值有具体调用来源。** 原 GA 400 次 forward/backward/Adam；getter 替换前后两次 no_grad `scene()`；原 clean 包装器在 clean 前一次 postfinal `scene()`，合计各臂 403。S29 objective 精确比较应复用 getter 边界已有的 loss_before，不能额外调用后仍填 403。独立 NumPy 原公式复算不属于该数。S29 的 sentinel/禁止 backward 机制不得带入 S30；只保留其 s/T 控制，原优化循环、清理和数学核验按原路径实际执行。

4. **保存／来源门按端点分开。** 两个 S30 终点各需真实 PASS、400 trace/400 gradient记录、400 Adam/backward、1 MST/3 PnP、1 clean、独立 clean/objective/backprojection 通过。两份 S29 初态须原合同与零步回执、完整 raw/decoded 输出身份、已通过的初始化假设回执；保持历史 status/counts 原样。S29 `initial_decoded.npz` 有 prelog/norm/objective 等额外字段而没有 conf，不能伪造 output.npz 或 conf、改成原 producer PASS/clean=1 来套 `seal_producers`/六字段 `decode_outputs`。可以复用后者验证两个真实终点；初态直接读取其原 schema 的 depth，其余来源另验。原 clean 不改 depth/world 的逐位门保留，保证端点差异不混入清理导致的几何变化。

5. **四组全部先封存，再触碰 GT。** 固定 C2t/init、C2t/final、C2a/init、C2a/final 共 4 份科学端点及必要 raw/trace/回执，全部身份通过后才解码用于评分，之后原 4 张 GT 只加载一次。不得单臂先评分再决定另一臂。传感器 PNG 的身份沿用原评分合同；它与允许作为共同条件的 GT camera 是不同输入。原有效分母、nearest、原 AbsRel/RMSE/严格 δ1/无效预测/null 规则直接复用，不按初终点另设过滤或尺度。

6. **完整 16 行和四个四帧组。** 必须明确 `(arm, endpoint, index)` 唯一键，index 均为 0..3；旧 `aggregate` 需要按相同顺序的四帧输入，只改分组路由不改公式。每组保留完整分母、defined_frames 与无效清单；endpoint 差只能 final−init，null 不能转 0，也不从 trace 选最优步。403 计数、clean 和 producer status 只属于 S30 新终点；不能回填到 S29 零步评分行。

7. **派生清单与失败边界。** 最终 AST/diff 应只列臂名、原初始化 s/T 返回、各自 S29 初态门、两臂统一 getter/梯度期望、本轮来源与评分端点路由。原 R0、输入 head 集合、star、depths=None、给定相机、固定项、原 objective/Adam/linear/lr=.01/400 不变。源／资源／初态身份失败先停止并保留；科学负结果也完整报告，不追加 prior、固定 scale、GT 拟合、延长预算或自动重跑。

普通尺度初始化控制仍不等于创新；这里只能比较既见 common4 的预定起点与 400 步终点。若 C2a 初态更准但优化后变坏，这将支持“起点修正不足”这一窄反例，不自动证明全部场景坍缩或某个新方法有效。

本次核验依据（实际读取的是源码／JSON，不是所引用 NPZ 内容）：

- `/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/work/S30_scale_optimization_preparation/PLAN_CANDIDATE.md`：`1d9e7b8f3ef0fb343cb0c0cbb303cc22a3c94f9373a833fbac2f1a3077494156`
- `/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/work/S28_gradient_scale_control/run_candidate.py`：`d8553d5086bba1b922835fb55a225efe3d04175c63e64eeee7f98644c9d771d8`
- `/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/work/S28_gradient_scale_control/score_candidate.py`：`f930391a50d125b40e4775f6c903b08fd6a52636a9c99c59df63c668e041381b`
- `/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/scripts/s26b_consumer_baseline.py`：`61e00503829dad7e9d1260fb408b81e8b281198e3cbf4bcab8367a493f982834`
- `/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/scripts/score_s26b_consumer.py`：`02317889281583ae0fd8a12a1148811c9e9a0afb7bcf75275aea9fd1a34f5cc7`
- `/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/work/S29_scale_control_preparation/contract.json`：`b9b6255c303c8e1a27853d64bd21838b5bf86b3b7d4b4a681e0f2d85f23d753f`
- `/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/results/S29_scale_control/validation/receipt.json`：`148ffc2b9f0832c0f5a5c4bd44551e1b526d1b913ea7149d885039fb68fb647f`
- `/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/results/S29_scale_control/C2t/receipt.json`：`0bac1a4a732292bd13be1901f8a7932f8b7d9cc355612c509011a50c9711870e`
- `/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/results/S29_scale_control/C2t/initial_raw_metadata.json`：`add9ac41afe179cfa1680d0b5b579f24f0dad2883af9cb5ed8c909414f5124f9`
- `/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/results/S29_scale_control/C2a/receipt.json`：`ce7dd2e2311751545077169ad28e41b0bcb98bb78a9c2922c16c407f456f3787`
- `/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/results/S29_scale_control/C2a/initial_raw_metadata.json`：`d933537dde41da52a8510ec018d00f18af3091dfb971aeb450265c9c08184950`

后续：等 root 通知稳定最终源码后做唯一一次实现前审；本文件不触发运行或等待文件循环。
