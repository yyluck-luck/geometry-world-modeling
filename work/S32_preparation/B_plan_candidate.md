# S32 B 执行前合同说明：同一新窗口的三种普通对照

本稿只实现已有计划，不因 A 预测值或任何新 GT 结果改变选择。作者截至准备时仅读 A 的 JSON 回执及源码，没有读取真实预测 NPZ、GT 或运行 GA。A 已由 root 真实完成：正式 A 合同 SHA `1749d83fac56a8c7f50b74d37e2278239df25534318967fa93f4798eb5054124`。A 的 4 窗 fresh4 各自拥有正确 anchor；不切旧长序列的 other 头。

固定选择沿用 root 已封存 JSON SHA `ac2c04437afa62fbaa5f03e5159ba06960131d9a2405afd5f94eef0c2f9ed318`。fr2_desk_j1 的共同相机条件缺失，整窗三个端点均 UNAVAILABLE，不能换窗／插值／放宽 20 ms 规则。另三窗均使用自己的四张 RGB、自己的 fresh CUT3R 六头、预选的相机，保留已见场景／已见部分轨迹的历史暴露。设计矩阵仍为 48 行／12 组：在其余三窗全部成功且 GT 足够时，36 个实际评分行与另 12 个缺相机 NA 行并列。

## 最小源码复用和允许差异

`run_consumer.py` 复用冻结 S26B `ga_worker` 的完整原 GA、原目标、clean、独立目标重算、独立 FP32 clean 与 backprojection 门。AST 只改变 dispatch guard、n=4、archive route 三项；给它本窗口的真实输入和控制。原 `prepare_output` 函数体不改。B 每窗为新 CPU 进程，避免 A 的 model namespace 或状态混入。

observer 使用 S28→S30 已验证的派生链，但将**历史 S29 初态引用检查**替换为**本窗口同一次 MST 的真实初态保存检查**，报告标签也据此重命名。后者在任何 Adam 前 clone 完整 33 参数/buffer、metadata、decoded depth/world/focal/pp/c2w/初目标，并核保存的 raw 与同内存快照逐字一致。继续原 getter 单表达式修复；它前后两次无更新目标及 getter forward 必须逐字一致、注册对象/值/flags 不变。没有为了零步另做一个 MST。

继承 S30 C2a 的初始化控制：原 align_multiple_poses 只求一次原 s0/R0/T0，然后用 s=1、原 R0、T=mean(given_C)-R0@mean(pred_C)。完整原返回和使用值保存，允许原近零分支 s0 为 Python float；单位尺度只用于初始化，之后 pair scale 仍按原优化自由。不能把相机均值匹配称逐帧对齐或米制真值保证。

本窗控制阶段按原给定 timestamp 解析所选 TUM optical c2w，绝对米制 world、无额外 Y/Z flip，另存控制 npy 与来源 SHA。传感器深度完全不读。原 PIL 同样重新预处理一次，与 A 保存的所有四 img/true_shape 做 dtype/shape/bytes 比较；原完整 six-head star 与独立直接 star 比较。通过后写本窗新 compatibility receipt，再将同一组已核 views 交给原 worker；不伪造沿用旧 common4 PASS。

## 实际优化、端点与失败

每个可用窗口固定 400 次原 Adam、lr=.01、linear、400 原 backward、1 MST、3 PnP、1 clean；两次 getter 边界求值与一次末尾求值合计 403 objective call。相机/pp 固定，四张 depth/focal/pair 按原 trainability；四个注册 depth.grad 每步非 None 且 finite，其他训练参数与冻结值全程按原门检查。保留所有 400 条普通及梯度/深度轨迹、末态 raw、原完整输出和原科学量参考核验；不挑最好步数。

只有整个 GA 及所有原门 PASS，才保存同一个 window 的三个评分端点：

| 文件 | 唯一数组 key | 类型／形状 | 来源 |
|---|---|---|---|
| initial_0step.npz | depth | FP32，4×384×512 | 本次同内存 MST 后、Adam 前快照 |
| corrected_getter_400.npz | depth | FP32，4×384×512 | 本次原 400 步完整 PASS 输出 |
| global_rescaled_400.npz | depth | FP64，4×384×512 | 原 S31 decompose(D0,D400) 的一个完整全像素 k |

原 S31 函数原样导入：k=exp(-mean(log D400-log D0))，四帧全像素共享一个 k，0 GT/pose/conf 输入、不删点、不加 shift、无超参数选择。完整 decompose JSON 与附属数组保留；非正/非有限失败，不作局部有效集代替。本项只转换 depth，没有生成归一后的 world/pair state，也不是优化期间约束。

输出 `results/S32_consumer_windows/{window_id}/receipt.json`：所有状态均有 `window_id`、B `contract_sha256`、共同 `selection_sha256` 和 `outputs`（相对路径→SHA）。PASS 额外包含三个 `endpoint_files`，覆盖原完整 GA 证据；UNAVAILABLE 用于缺相机；FAILED 保留错误和所有部分文件。**只要整窗 GA 或后续科学门失败，该窗三端点都不能评分**，不把未独立通过的初态拿出来充作零步成功。

外控每窗 120 秒／4 GiB RSS／CPU8，继承原 S26B 10 GiB 空闲磁盘门；缺相机 worker 在任何 Torch/GT pose/数组前只写 UNAVAILABLE。一个窗口失败保留后，其他预先固定窗口仍可独立尝试，绝不重试同一窗口。外层最后记录四窗终态和全部 receipt SHA 为 `COMPLETE_FIXED_WINDOW_MATRIX_SEALED`，该状态不是所有窗口科学 PASS。

## 评分屏障与未完成项

独立评分作者使用 `results/S32_consumer_scoring`。只有四窗全部产生终态、三个端点全封存或明确整窗不可用，才读 sensor-depth PNG，先字节封存再解码。48 行／12 组完整域不变，缺失／失败 NA 计入原分母；不能以 available-only 均值替换原均值。沿已冻结原 AbsRel/RMSE/δ1 数学及完整分母规则，无 GT 尺度拟合、远点截断、confidence mask 或调参。scorer CPU1/120 秒/2 GiB 由独立作者维护，此 B 入口不自动调用未绑定 scorer。

准确性排序是科学结果，运行 PASS 不是改善；单位尺度起点未预称在新窗准确。零步/原400/单标量完整同表，不能只打较弱原终点。本轮尚无 Surfel 提交查询、长期记忆因果干预或视频生成，更不能把普通三个对照包装创新。

执行命令仅在 root 审后冻结 B 合同后使用：`.venv-cut3r/bin/python work/S32_preparation/run_consumer.py dispatch --contract work/S32_preparation/B_contract.json --sha256 <root冻结SHA>`。A 已成功，不再重跑。准备只做源 AST/diff/help，不新增合成测试、模型运行或真实数值复算。
