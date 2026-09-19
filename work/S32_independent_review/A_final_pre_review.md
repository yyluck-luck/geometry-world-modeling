# S32 A 稳定源码最终前审

**PASS_A_SOURCE_PRE_REVIEW，无阻断、无需修改。** 绑定 runner `6246b7255a324653279429be770dcc7c07a478729bea9d172b182cb35fb7851d` 与候选 `7c9612253d32d18bb3da09f51212c33ade65b3255c460e80770b08e31be226a6`。本结论只覆盖 A 新推理阶段，不覆盖尚未执行的 CPU 数值兼容、准确率或 B 优化。

已全文读 A runner、prepare、plan、source-read manifest 和候选的配置／窗口字段，逐项程序核候选全部 10 个直接身份及 203 个继承源码身份。203 项是身份核验，不声称这轮逐行重新读完所有依赖。没有读取 RGB、sensor PNG、GT pose 原文件、NPZ 或 checkpoint 字节；图片 SHA 只与 root 已封存 JSON 对应。标准库 AST/compile、候选拒绝门与一次 `--help` 实际通过，未导入 NumPy／Torch／PIL，未运行模型。

核验要点：

1. 候选状态在数值导入和输出创建前被拒绝。四个窗口及原 RGB 索引／路径／时间与原选择和 root RGB seal 一致；A 没有因 `fr2_desk_j1` 缺 pose 而跳窗。已有输出不覆盖，失败保留并中止，不自动换窗／重跑。
2. fresh worker 通过已绑定 adapter 只建立原函数 namespace，再走原 PIL 与 **`src.dust3r.inference.inference`**。模型由 `dust3r.model` 导入；两种前缀实际来源都在同一冻结 embedded 根核验，未混入 S21/TTT/FILT。原函数每 call 新建 `_init_state` 与 pose memory；观测门要求一个 model call、一次 state init、四次 downstream head 和五份 state history。
3. 保留原 `eval()`、CPU8、外层 FP32、seed0、identity 输入 camera、未用 NaN raymap、image-only/update=True/reset=False。A 不使用允许的 GT 相机，也不读取 GT pose 文本或 sensor depth。合同哈希路径仅是源码与 JSON；JSON 内的 GT 路径不会被递归打开。
4. **使用 S17 已绑定 `models.pos_embed.RoPE2D.cpu_impl` → `models.rope_cpu.RoPE2DPyTorch`。没有安装 S21 的 helper。** 已读 wrapper 和 CPU forward，类／F0／base 的检查与源码字段一致；实际 CPU 模块必须存在且被调用。该既有兼容层仍需在此次模型执行时通过，静态审查不代替运行。
5. head hook 挂在实际 `model.downstream_head`，原 DPT forward 返回六键；每帧保存完整六个 FP32 张量，核 shape／finite／正 confidence。`to_cpu` 保持 Torch tensor 接口，因此返回值 `.detach().cpu().numpy()` 有效。每窗全部 24 个 tensor 与存档内存副本逐字对照，hook 不返回替代输出。星形由原 assembly 创建，再核三个 edge 的 self/conf_self 与 other/conf，共 12 个实际消费 tensor；不调用 `prepare_output` 或 GA。
6. `preprocessing.npz` 保存原 PIL 的 img／true_shape，支持未来 B 重新读取同四张图后逐字检查；当前的输入身份 PASS 不代表 A→B 已经比较。完整六头、输入 seal、实际加载模块和 SHA 会进入最终 producer。原权重采用已有 SHA 加固定 size/mtime 的继承方案，不虚称本轮完整重哈希 3 GB。
7. dispatch 顺序运行全部四个 fresh child，每窗复用已核监督器的 180 秒／16 GiB RSS／10 GiB 空闲磁盘门。CPU8 在 worker 内明确设置，失败或资源超限保留外控回执。总计四个 model call／16 个 head forward 只有全窗 PASS 后才写入；无 GA／MST／Adam／GT 评分调用。

不需要追加 recurrent 兼容模型运行、人工大数组测试或新的科学门槛。Root 可以冻结当前 A 并按合同单次运行；成功也只能写为新照片推理与存档完成。B 的缺相机窗 NA、其余三窗三控和完整 48 行设计矩阵继续按 `selection_addendum.md` 保留。
