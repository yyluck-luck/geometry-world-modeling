# S34 独立保存量复核固定协议（准备阶段）

本目录作者不是 S34 GA producer 或 S34 主评分器作者；采用此前已冻结的 S28 独立 OpenCV 指标函数，未复用主评分器的 PIL 解码与整图计算实现。本作者写过 S34 consumer，所以这里**不独立核验 consumer 地图、渲染或票权算术**，只如实导入已封存的 consumer 终态；那部分由 root 另核。

当前只准备源码、协议和候选身份。准备不导入科学库，不读取真实 NPZ、RGB 或 sensor-depth PNG 字节，不运行任何数值结果检查。`preparation_receipt.json` 中的 PASS 仅指标准库 AST/编译及源身份准备，不是本复核或实验 PASS。

## 固定范围

- 一组已见八张真实输入，旧帧 0–3 固定、新帧 4–7；三个端点 `old_fixed_zero`、`old_fixed_free_400`、`old_fixed_common_scale_400`。只评分新 4，共 12 行、3 组。四 GT 身份逐字继承 S26 元数据，不重新匹配。
- 两个 400 步臂各检查完整 57 项 initial raw、57 项 final-before-clean raw 与元数据/原字节 SHA（合计 228 项）。独立列出 49 parameters+8 buffers 的域。共同初态 57 项、全部 decoded 字段与 objective、全部 controlled-alignment 保存字段跨臂精确匹配。
- 两臂 initial/final 全 8 depth 由保存 logdepth 的 `exp` 对接保存 depth；这是 FP64 `exp` 对 FP32 保存解码的数值比较，`atol=rtol=1e-6`，不是逐位复现 Torch exp。旧 0–3 raw depth、固定 camera/pp、其他冻结 raw 初末逐位一致；旧 depth 相对 common-old 的 log/exp 往返容差沿用 `1e-5/1e-5`。新 4 depth、focal 与 pair 参数允许优化。
- 每臂完整 400 optimization、400 gradient、400 scale 记录，共各 800。核 0–399 顺序、一次实际 Adam 计数、学习率和配对 loss；8 depth+focal+pair 的 10 个梯度字段完整，旧 4 为 None，新 4/focal/pair 存在、有限，零范数允许。旧 4 全步保存统计不变，前一步 after 与后一步 before 一致。保存梯度范数**不等于**独立重算梯度。
- 全部 1600 before/after 边界均有 7 个有效 scale；自由臂 factor=1；受约束臂 `factor=exp(m0-mean(raw_logscale))`、保存有效尺度的平均 log 保持 m0，绝对误差不超 1e-5。独立以 Python `math.log`/`math.fsum` 核平均及 factor，初末再从保存的 7×8 raw pair 最后一列核 exp×factor（绝对/相对 1e-5）。不拟合新 k、不改相对尺度、不运行优化。
- 没有逐步 raw-scale 数组或完整 3×4 矩阵，故 `full_3x4_exact` 只能作为 producer-recorded 检查保留，不能独立重建每步矩阵。参数对象同一性、MST/PnP/backward/clean 调用次数也只核实际回执与记录，不重新执行。
- zero 来自此次 free 臂同一新 MST 的保存初态，核 source seal、preclean/clean 后 non-conf 与新初态精确一致。它不是把历史 S29 场景冒充此次 8 帧零步状态。common-old 只核此次已经 PASS 的 packet 与 producer 身份，不重新跑或评分 S29、S32、S33。

## 必须先完成的身份屏障

root 源审后创建 `binding.json`，模式必须 FROZEN，绑定候选 SHA、正式 producer contract、正式 scoring manifest、实际 scoring PASS receipt，以及与候选及 producer contract 相同的最终 producer 源 SHA。候选本身不可执行。若任何源变化，先增量源审、留存旧候选，再更新，不默许最新文件。

执行先核主评分完整 PASS（12 行/3 组/4 次 GT 解码），所有 common+三端点 PASS，正式 producer/scorer/source 身份，terminal barrier 内所有 producer/consumer 保存文件字节与主评分 input SHA，再核全部评分产物 SHA。consumer 允许真实 `FAILED_PRESERVED`，几何评分仍须完整 PASS，consumer 失败不改成成功。

随后读取四份已评分 GT PNG **字节**并核 SHA，保存 `input_seal.json`。只有所有这些字节封存后，才导入 NumPy/OpenCV、解码任何 NPZ 或 PNG。四张 GT 各 OpenCV 解码一次并复用于三个端点；结束后重新核全输入/源码 SHA。GT 已在历史研究与本次主评分中使用，不能称新盲测。

## 独立评分算式和缺失规则

复用冻结 `work/S28_independent_numeric_review/recompute.py` 的 `independent_frame`、archive/metadata/数值比较纯 helper；不调用旧 main 或旧四帧 trace 函数。helper SHA 在候选固定。四张原 uint16 PNG 必须 640×480，整数取样 `source_index=5*(2*i+1)//8` 至 512×384，除以 5000 转米。逐行算绝对相对差与平方差，行和由 `math.fsum` 汇总；δ1 严格用 `p<1.25*g && g<1.25*p`。全正有效 GT 为分母，完整保留 invalid 计数，无置信度过滤、远点裁剪、GT scale fit 或 shift。

若帧的有效 GT 分母为 0，分数为 null；任何有效 GT 上预测非正或非有限，AbsRel/RMSE 为 null，δ1 以全有效 GT 分母把该像素计失败。组均值只在四个预定帧全部定义时等权平均，否则 null，不代换为可用帧均值。对完整 12 行 JSON/CSV 和 3 组的四项均值/全部计数/缺失集合逐一比较。沿用原独立精度 `abs_tol=1e-12, rel_tol=1e-10`；整数、域、顺序和 null 规则精确一致。

像素和邻近帧不当独立统计样本；不添加置信区间或显著性检验，不以数值复核 PASS 声称共同 scale 有收益、机制已证明、新方法或视频完成。

## 执行与预算

既有 `.venv-cut3r/bin/python`，NumPy 1.26.4，CPU 1，wall≤120 秒，RSS≤2 GiB；root 原外控执行 envelope 限时/限内存，脚本也在结束前核 wall。失败不扩预算、不重跑原 GA/模型/clean，不覆盖第一次 attempt/receipt；身份预检失败由调用者保存 stderr/外控回执，进入执行区后的失败另写 `FAILED_REVIEW_PRESERVED`。

CLI（只有 root 源审冻结与实际主评分 PASS 后才调用）：

```sh
.venv-cut3r/bin/python work/S34_independent_numeric_review/recompute.py --binding work/S34_independent_numeric_review/binding.json --sha256 FROZEN_BINDING_SHA256
```

输出本目录 `attempt.json`、`input_seal.json`、`progress.json`、`recomputed.json`、`receipt.json`，包含原始 12 重算行、3 均值、完整 800 步简表、全部计数、原始输入 SHA 和范围。没有新模型、GA、backward、clean、渲染或 k；不修改任何原 S34 产物或 canonical 账本。
