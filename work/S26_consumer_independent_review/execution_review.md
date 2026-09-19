# S26 执行前独立静态审查

结论：当前候选可以由父任务冻结并按既定顺序执行。没有发现剩余阻断；这不是实际 GA、深度评分、CPU8 数值兼容或科研方法有效性的 PASS。具体时刻和全部绑定身份见 `execution_pre_review.json`；之前的 source-preparation 回执保持原样。

审查者 `/root/supervisor_full_readthrough` 与 adapter、runner、scorer 作者分别不同，仍是同一 AI 团队内的独立作者审查，不是外部实验室复现。

## 版本和审查范围

- 当前候选 SHA：`2af4f8bb13caee8923ce180e0dcc02bb2a6538b3a3c0f87684bd8db33af0dccf`。
- runner SHA：`c07fd1b3c93f0034b1e61edc9d75ebfb9e71094f30b0800a205360a8e24d074e`。
- scorer SHA：`5e10c2a990ac7e9db8337740854b49a02fa18fdd0793e222984091acc1c2ff63`。
- 全文审查 runner、scorer、freeze helper、两份正式协议，衔接此前已读 adapter/plan/原消费者源码和 S17C 独立数值参考。对 TTT/FILT 的嵌套 `prepare_input` 做完整函数 AST 比较。
- 565 份 source/control 身份中，559 份非图像文件的字节 SHA 与候选一致；其余 6 份是源码附带的 CroCo 示例图片，本审查没有打开。5523 个依赖身份从 S17C 继承，不声称逐个重新验证或实际加载；运行器将验证实际使用的 overlay 模块。
- 新执行标准库检查 18 项通过。没有导入被审实验程序、NumPy/Torch，没有读取真实预测、RGB、GT 图片或 GT 相机坐标，没有运行 prepare/freeze、模型、GA 或真实评分。

## 科学对象与允许输入

原 `prepare_output` 的固定相机/旧 depth 路径和 star `(0,j)` 得到保留，目标实际使用 anchor self/conf_self 与其余 other/conf。S21 original4 单独进行一次给定前4相机、无 depth 先验的 GA；输出以 receipt、NPZ SHA、depth tensor SHA、相机前缀 tensor SHA 绑定，三个8帧方法共用它。GT depth 不进入这条生产路径。

TUM c2w 作为显式共同 oracle 相机直接进入 optical 接口。原 pipeline 的 Y/Z 列翻转是右乘基变换；本入口位于该变换之后，不重复翻转、不做 GT 尺度或首帧对齐。该设计不能评价可部署的自由相机估计。

baseline 预处理在独立进程加载各源码 loader，沿用 S21 的 TTT `prepare_input` 提取方式；FILT 的同名函数 AST 与它一致，原 CUT checkout 没有该 launch 文件。原 VMem PIL 路径与三份实拍 tensor/shape 的精确比较在真正 GA 之前执行。它检验的是实际输入兼容，不把不同 backbone 当作嵌入原 VMem 网络的逐位复现。

## 原优化和数值核验

原 MST、PnP、Adam、linear 400 步及 lr=0.01 原调用均委托执行，observer 记录真正的 Adam.step，检查每一步序号及同一优化器，没有用循环次数代替更新次数。保留原 PnP 未解情形和原 fallback，不强制成功。所有导入和 observer 安装之后重新设四类随机种子。

全部 pose、旧4 log-depth、原固定 pp 等不参与梯度的约束参数在 preset、MST、优化后和 clean 后逐值不变；im_conf 虽无梯度，但原 clean 允许修改，故排除于该不变集合，另走独立 clean 公式。可优化 focal 与新4 depth 保持原角色。输入与解码输出的 FP32 往返容差与内部参数不变检查分开。

完整原返回先完成 schema/domain 和颜色检查，再保存六字段结果，之后才执行独立数值公式门。颜色来自输入实拍，不是生成图；颜色重建的 `.5*x+.5` 与原 `rgb` 实现一致。post-final 无梯度目标为第401次目标求值；原返回最后一步更新前 loss 另存，不混用。

S17C reference 的 clean 实现维度支持4/8，按有序 i/j 对动态更新置信度，边界不豁免。pair_objective 每边包含两侧全部像素，因所有边 H/W 相同，对全部 star 边取平均对应原堆叠目标；核验阈值已固定。世界点另用 NumPy 行向量路径重建。源码检查认为接口/数学相符，真正多图 CPU8 FP32 是否通过仍需执行。

## 冻结、生产者与评分接口

freeze helper 要求 `passed:true` 及绝对路径 `identities`，必须绑定本候选 SHA，并重验审查所列身份和候选 source/control，才写全新 `run_manifest.json`。已有文件拒绝覆盖。运行入口要求其调用者提供精确 manifest SHA，每个子进程重新核 source/control；dispatcher 先要求 S24 完整 PASS，再依次运行 control、三预处理、compat、四 GA、score，不重新启动 backbone。

runner 的六字段形状、4/8帧模式名称、PASS/输入 seal/output SHA 与 scorer 完全一致；scoring 对象与已封存 metadata candidate 一致。全部四份生产者 receipt、input seal 和 output NPZ 字节 SHA 通过后才解码任何预测；共同旧4往返约束通过后才读 GT PNG。八个 GT SHA 从已有 S23 receipt 继承，准备时不读 PNG；曾见数据的事实保持明确。

深度评分只按同一 GT 有效域取分母；无置信度筛选、远深度裁切或尺度拟合。保留无效预测和空 GT；新4主表要求完整等帧均值。源码完整阅读确认 AbsRel、RMSE、严格 δ1、nearest 索引、old4 容差与协议一致。本审查没有运行 scorer 人工数组；父任务另有22项独立人工核验回执，作者另有58项，不能合并成我们运行的真实实验。

## 已解决的问题与仍待运行验证

冻结前已发现并纠正嵌套 `prepare_input` 提取、`CommonOldDepth` 新增身份参数、真实 step/MST/PnP 观察与封存不足、随机种子时序，以及 clean 修改 im_conf 被误判为约束破坏。最终候选已经包含修复；没有要求看结果后调阈值。

作者的21项 CPU1 synthetic preflight 绑定较早 runner `671559e0…`。它用了两处明确的 CPU1 专用 shim，并委托 spy 代替 GA；当前新增颜色和 overlay 身份检查经本次静态审查，没有据此冒称最新 runner 或 CPU8 GA 已通过预检。若真实执行触发任何资源、兼容、数值或封存失败，保留结果和原合同，另做具名修复与重新绑定，不静默放宽。

本轮仅首8帧、约0.236秒、旧4/新4组件 pilot。即使执行和评分 PASS，也不能判断长期记忆、S/M 因果、新算法、自由 ATE 排名传递、检索收益或视频生成成功。若消费者未呈现重要自然失败，不为追求创新包装这段数据；继续按 Supervisor 第2章的强 baseline→真实失败分类→机制假设推进更有辨别力的消费者实验。

## 技能的具体应用

沿用已通读并固定版本的 Supervisor `02_Idea_Generation`：先核原消费者这一强基线是否成立，避免自由几何指标替代 proposal 的消费者终点。读取本地 `/Users/rocket/.claude/skills/sci-scientific-critical-thinking/SKILL.md`，局部应用构念效度、共同控制、偏差与缺失值、结论强度审查；没有调用 Claude 模型，没有宣布完成整个技能的文献综述或临床证据分级。两份协议已有原生 Mermaid 说明输入和评分顺序，本审查复用其结构，未生成新的无关插图。

下一步由父任务冻结这一候选，等待现有 S24 全部完成后执行。最终真实结果仍需不同作者复算并解释；本回执仅解除静态准备阶段的代码阻断。
