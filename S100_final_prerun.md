# S100 最终运行前独立审查

裁决：**`S100_FINAL_PRERUN_PASS`**。允许依据以下绑定版本进行一次有界 select → freeze → predict → score；这不是已运行结果或新方法验收。审查时尚未扫描候选幅度；审查者未读 GT 文件、历史候选数组或 S100 新评分。

绑定文件及 SHA256：

- `work/S100_context_matched_swap/run.py`：`f2316915885856c76161fd539320d751e62b9f50811720707cad578e96c705d1`
- `work/S100_context_matched_swap/PROTOCOL.md`：`19340640def65bf54fecdd8da51c5ea60f07368f6ad465db867f3386a141fc08`

审查范围为该源码、该协议和继承的 `scripts/s15b_memory_consumer.py` 输入验证/renderer 源码。沿用前一设计审查所述 scientific-critical-thinking 技能，只应用偏差、混杂和证据范围检查。

## 已核对

1. **历史限定与先冻结规则。** select 在读取历史幅度前写 BEFORE_SCAN 的源码、协议与 S99 FREEZE SHA。候选是同 source 的 top39 差集，mean/RMS 双幅度 caliper 分别固定 1.10/1.25；零幅度边拒绝；排序与贪心无复用一致，不合格不会放宽规则。
2. **同一背景成对替换。** 焦点来源排除两候选后抽 38 块，另三源各 39 块，分别加入一个候选；每臂每源 39 块，总 156 块。背景 RNG/seed/遍历顺序明确，两臂由同一 bg.copy 构造；完整消费者重算所有投影和 z-buffer 赢家。
3. **预算。** 至多 4 对/source × 4 sources × 2 contexts × 2 arms × 4 targets = 256 主渲染，另 1 个首条件 target20 exact replay，故 **257 总渲染上限**，不是 256 总渲染。已有 S99 端点验证不重复。独立重投影复核若另有渲染须单列；0 神经推理不能混同为0渲染。
4. **失败停止修复已落盘。** 初版 freeze 未检查选择阶段失败。最终版本现在要求 select RUN 为 PASS、SELECTION 为 READY，并核对 BEFORE_SCAN 的 S99 FREEZE 身份；全零匹配不进入预测。源码/协议/选择产物及继承身份整体进入 FREEZE，预测 PASS 后才形成 SEAL。
5. **GT 隔离。** select/predict 路径读取历史 bridge/proposals、允许的 query camera/K/scale、rule masks 与身份文件。继承 renderer 模块在 import 时没有 GT 文件读取。GT 路径虽然作为常量存在，但首次读其字节/数组只在 score 中、验证预测封存与 PASS 之后发生。哈希读取也算读取；此处 GT hash 检查确实放在 score 内。
6. **缺失安全主指标。** 每 target 使用自身 GT finite positive 全域，同 target 所有条件分母一致。预测缺失承担对应 cap 的最高损失；cap 0.5/1/2 都计算并保存。有效预测自身 AbsRel 是补充，不是公平固定域主分数。fractional worst5 定义正确，缺失造成的饱和须在报告中如实解释。
7. **收益与聚合。** B=low loss−confidence loss，正号定义一致。每 source 内因各对均有2背景×4目标，直接平均 paired rows 等价于协议的逐层等权；最终对可匹配 source 等权，避免某 source 多匹配几对就获得更大权重。原始 paired rows 保留每 target/背景结果；root 将在报告脚本中从这些原始行形成每 target 的 source 等权聚合，并核查其与整体均值一致。
8. **交互与决策。** 对同 pair/target 的两个背景按 ±1e-10 检测反号，所有 cap 同报；它只检测本次两个背景的局部反例。平均 B<=1e-10 时不保留正平均替换解释。正平均不等于无反号，零反号不证明可加性。

## 已实际执行的合成核验

在现有 `.venv-cut3r/bin/python` 中，用 AST 只提取 blocks/pixels/tail 三个纯函数，未 import 实验运行模块、未读项目 NPZ 或 GT。源码语法通过；4×196 块的完整索引与16×16像素映射逐值一致；tail 对 N=1/4/20/21/100 的常量与小数边界权重通过；固定四像素缺失惩罚示例得到 [0,1,1,1]。这些是实现检查，不是科学结果。

## 执行与解释边界

- 单 BLAS 线程由 root 启动命令显式设置，源码本身不负责设置环境变量。每阶段600秒与8GiB按当前 macOS 的 ru_maxrss 字节单位记录；不要直接宣称该RSS单位实现可跨Linux运行。
- 只重复首条件的一个 target，属于有界确定性检查，不能说所有条件都独立重放过。正式结果仍需不同作者重算选择、至少一个新条件投影及全部主要聚合。
- 未匹配 source 只表示这个冻结 caliper 下无合格候选；不作该 source 替换收益判断。两个背景和四目标不是独立场景，不做泛化显著性。
- 截断损失限制极大误差影响，不能冒称普通 AbsRel 或据此宣称尾部风险已经解决。幅度近似匹配仍保留位置、遮挡和几何内容差异；即便结果有利，也不能证明 confidence 等于新增信息量。
- 当前为已见场景保存模型输出的几何消费者局部诊断；不是神经网络新推理、VMem生成、正式S91、GRC校准或方法成立。`new_method_validated=false`，`novelty_authorization=NONE`。

本文件落盘后作为冻结输入保持不变。任何对绑定协议或源码的进一步修改须在扫描/运行前重新审阅与绑定；结果不得反向修改本次前审。
