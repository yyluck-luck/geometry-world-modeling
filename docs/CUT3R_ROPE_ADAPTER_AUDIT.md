# CUT3R 带符号 RoPE 本机兼容层独立审查

首次记录：2026-09-05 23:09:46 Asia/Shanghai（15:09:46 UTC，实际时钟）。本审查基于独立官方 CUT3R 提交 `8bc15dc92a6d7fd92920b4ec81540d3dec7d3ecf`；没有 CUDA 硬件运行或 CUDA 数值对照，不加载模型、不重复下载检查点。

## 原始失败与源码依据

`results/CUT3R_cpu_2frames/run_metadata.json` 保存了原始 CPU FP32 尝试。15:06:58.674546 UTC 开始，检查点全部键匹配，实际模型有 748,443,655 个参数；15:07:04.868183 UTC 因 `torch.nn.functional.embedding` 收到负下标失败。失败发生在推理阶段，不是检查点损坏或成功的几何实验。

官方 `src/dust3r/model.py:834–835` 为 pose token 设置 `(-1,-1)`，`:665–667` 将它拼入图像 token 的位置。相同设置也存在于 inference_step、ray-map 和 recurrent 路径；没有针对该 token 跳过 RoPE 的特殊规则。

官方备用实现 `src/croco/models/pos_embed.py:154–155` 直接用位置做 embedding 下标，`:171–172` 用 `positions.max()+1` 建立非负表，因此不能处理这些负位置。此前仅对随机非负位置通过部件测试，不能证明完整模型可运行。

## 数学语义核对

官方 CUDA `src/croco/models/curope/kernels.cu:39–55` 对每个 head 总维度 D 设 Q=D/4。token 的排列为 `[Y_u, Y_v, X_u, X_v]`，每段长 Q。对轴位置 p、局部频率序号 j=0,…,Q−1，角度为：

`theta = p * F0 / base**(j/Q)`。

`:77–80` 的输出为 `(u*cos(theta) - v*sin(theta), v*cos(theta) + u*sin(theta))`。位置为负时照常计算负角度，既不截为 0，也不解释成从缓存尾部倒数的下标。

因此，用 `abs(p)` 查非负缓存并令 `cos_signed=cos_abs`、`sin_signed=sign(p)*sin_abs` 与直接带符号角度在数学上相同；p=0 时 sin 为 0，旋转为恒等。缓存上界必须改为 `abs(positions).max()+1`，否则全负位置或负值绝对值较大时仍会越界。

备用实现将 token 前半用 Y 位置、后半用 X 位置，每半内部以 `rotate_half` 配对旋转。其频率指数 `arange(0,D_half,2)/D_half` 等于 `j/Q`，与 CUDA 排列一致。正式检查点 `RoPE100` 的 F0=1；原备用类虽然保存 F0，却未在 `get_cos_sin` 使用。若兼容层沿用该函数，应限制 F0=1，或显式实现并检查 F0 对角度的作用。

CUDA 使用 float 中间值、`powf/cosf/sinf`；本机 PyTorch 后端可能有浮点舍入差异。数学公式一致不等于已证明逐 bit 相同，也不等于已经执行 CUDA 硬件验证。

## 具体实现待复核

此首次记录时兼容层尚由实现任务准备。应独立核查实际类/方法替换范围、频率/二维拆分、FP32 与整数位置、缓存长度及不修改上游文件；再核查非负位置对原备用实现、混合正负位置对独立直接公式的测试记录。测试须包含全负、零、单轴负和负位置绝对值大于正位置最大值的情况。

运行元数据应包含兼容层名称与 SHA；CPU/MPS 对比必须同时冻结该身份。成功时应称“固定官方权重和源码配合本机兼容层的推理”，保留原始无兼容层失败，不宣称未经适配的完整官方执行或 CUDA 复现。

## 23:10:52 具体实现与检查记录复核

2026-09-05 15:10:52 UTC 追加。已只读核查 `scripts/cut3r_rope_compat.py`、更新后的 `scripts/run_cut3r_local.py` 和 `results/CUT3R_signed_rope_compat/check.json`，未由本审查任务重复运行测试或模型。

结论：本次 FP32、F0=1 的固定运行范围内，未发现数学语义、维度排列或集成阻断。

- `signed_forward` 限制每个 head 的 D 可被 4 整除，沿用原 `get_cos_sin` 的频率构造、device、dtype 与缓存，缓存长度确为 `abs(positions).max()+1`。两轴分别以绝对整数位置查表，sin 乘原轴位置符号；前半 Y、后半 X，每半沿用原 `rotate_half`，与上述 CUDA 公式一致。
- F0 非 1 会明确拒绝，不会默默使用原备用实现遗漏 F0 的行为。固定实际配置是 F0=1、base=100。结果仍为 FP32；位置保持整数，未做 clamp 或负索引 wrap。
- 兼容层只替换 `models.pos_embed.RoPE2D.forward`。官方各导入路径持有的是同一个类对象，构造出的 RoPE 模块会使用该方法；不要求修改官方文件。原官方非负 cache 构造与旋转配对没有改动。
- 检查程序在安装兼容层之前保存原备用实现的非负 CPU/MPS 输出，并验证原负位置 IndexError 可复现。参考公式单独用 NumPy float64 和每轴/频率循环计算，没有复用兼容层的 `rotate_axis` 或查表，能检查频率顺序、符号及二维拆分错误。
- 混合位置覆盖 pose 的 `(-1,-1)`、零、`(-19,2)`、`(2,-19)` 与其他正负值；−19 的绝对值超过当时正位置最大值 14。另有全负位置输入，其检查范围是有限性与缓存不越界，不应声称该例也单独完成了公式误差比较。

记录在 15:10:12.364292–15:10:13.203670 UTC 执行的部件检查使用预先写入的 `atol=1e-5, rtol=1e-4`，结果如下。这些是实现任务产生的实际记录，审查者核对了计算过程与数据文件。

| 检查 | 记录结果 |
|---|---|
| 非负 CPU 对原备用实现 | 逐值严格相等 |
| 非负 MPS 对原备用实现 | 逐值严格相等 |
| 带符号 CPU 对独立直接公式 | 通过；最大绝对差 8.748791729407124e-7 |
| 带符号 MPS 对 CPU | 通过；最大绝对差 4.76837158203125e-7 |
| 带符号 MPS 对独立直接公式 | 通过 |
| 全负输入与各后端输出有限性 | 通过 |

身份记录：

- adapter SHA256：`6939dcead1b87e920eafce9aae47c1cc9a46b7a651ef816b3f521c779582152e`。
- 部件检查 JSON SHA256：`84a30132c2cfb9c31720771b76bb068ad6edf7f9ea77cd75d39c4b3512f4fc78`。
- 已审查 runner SHA256：`165c9b379cc2118aacb4938429bbee36c07e232752c1f2c6979838c45e5d7f93`。
- 官方 CUDA kernel SHA256（检查记录）：`0fbd53befc0a31b058a98dd081604ed23751ad5b88d1b1fce8d5ea7616512e75`。

runner 已在安装前核对通过状态、adapter SHA 和官方 commit；`runtime_compatibility` 记录 adapter 与检查文件 SHA，并加入 CPU/MPS 相同条件检查。它分别记录 `upstream_source_files_unmodified` 与 `upstream_execution_unmodified`，避免把运行时适配隐去。

这些检查足以支持继续既定的新目录 CPU/MPS 推理尝试；不等于完整模型已成功，也不等于两图几何准确。没有 CUDA 硬件结果，不能宣称实测 CUDA 等价。正式 S4 仍须核验实际输出与 adapter 身份，沿用原第一帧尺度和第二帧留出指标，保留无适配版的失败。
