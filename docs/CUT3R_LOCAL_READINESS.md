# CUT3R 本机准备与实际推理记录

本文件维护独立 CUT3R 在本机的准备和运行状态。它与 S0–S3 的 NumPy/检索环境分开，不能作为 VMem 完整视频生成成功的证明。

## 当前状态

2026-09-05 23:13 北京时间：**官方 224 预训练模型已用固定两张真实 TUM 照片分别完成 CPU 和 MPS 推理**。两次均成功加载全部参数，点图、位姿、置信度等 14 个输出数组全部有限；CPU/MPS 数值均满足事前容差。运行需要下面记录的两项本机兼容处理，因此不能称为执行过程完全未改动，也不能称为 VMem 视频生成成功。

精度说明：本文及运行元数据中的 FP32 指模型参数、输入和保存的输出。官方 encoder 的 attention 会将 Q/K 暂时转成 FP16 执行 RoPE，再转回原 dtype；本轮保留该上游行为，没有为速度另行降低精度。因此不能写成“所有内部运算均为 FP32”。该实现细节在 S5 准备审查中补充确认，未改动 S4 原始结果。

23:21:50 补充的独立非负 FP16 检查已通过：CPU/MPS 各自的 adapter 输出均与原 fallback 逐值严格相同，差为 0，输出保持 FP16、有限且零位置为恒等；没有实例化模型或执行 CUDA。新证据保存在 `results/CUT3R_signed_rope_compat/fp16_nonnegative_check.json` 及同目录 `check_fp16_nonnegative.py`，原检查未覆盖或修改。

- 独立环境：项目 `.venv-cut3r`；现有 `.venv` 不修改。
- 官方源码目录：当前任务工作区 `work/cut3r-local`，固定提交 `8bc15dc92a6d7fd92920b4ec81540d3dec7d3ecf`；无已跟踪文件改动。仅取根目录、`src` 与 `config`，没有重新下载示例媒体。来源与文件哈希在该目录 `local_readiness/source_provenance.json`。
- 环境检查入口：`scripts/cut3r_local_smoke.py`。只导入模型类并以随机张量检查 RoPE 在 CPU/MPS 的一致性；不实例化模型、不加载检查点、不预测图像。
- 真实推理入口：`scripts/run_cut3r_local.py`。使用明确指定的真实图像、验证过哈希的检查点和未经修改的官方源码，保存点图、位姿、置信度、耗时、有限值检查及可选 CPU/MPS 对比。
- 可续传下载入口：`scripts/download_cut3r.py`。保留部分分段，验证每次 HTTP Range 返回范围，记录分段与最终 SHA-256，不覆盖不明来源的已有权重。

## 模型来源、大小与许可

模型名 `cut3r_224_linear_4.pth`；这是官方提供的 **224 linear 中间检查点**，不能称为论文最终的 512 DPT 检查点。[官方模型表](https://github.com/CUT3R/CUT3R#download-checkpoints)，[官方链接指向的公开文件](https://drive.google.com/file/d/11dAgFkWHpaOHsR6iuitlB_v4NFFBrWjy/view)。

匿名 HEAD 已返回 HTTP 200、`application/octet-stream`、正确文件名和 **2,994,205,002 字节**，约 2.79 GiB。匿名 1,024 字节 Range 请求返回 HTTP 206、`bytes 0-1023/2994205002`，开头为 ZIP 标记 `PK`。23:06:53 完整下载完成，全部 1,060 个 ZIP 成员 CRC 验证通过；完整 SHA-256 为 `7a7d83e47f822e040980c8f5aff4c15aa94366d469d3ceae51fa30cc2f62327d`。来源、实际大小与时间、分段记录在 `data/cut3r/download_manifest.json`，可打包副本为 `results/CUT3R_readiness/checkpoint_download_manifest.json`。

后续下载核对固定 URL、大小、分段大小及远端 `Last-Modified: Fri, 07 Feb 2025 20:32:21 GMT`，使用 `If-Range`，最终检查 ZIP CRC。早期分段发生在 HTTP 验证字段固定之前，清单明确保留此区别。发布者 SHA-256 未取得；最终 SHA-256 是本机计算的完整性与复现标识，不能说成已与发布者哈希匹配。

官方 CUT3R 许可证为 **CC BY-NC-SA 4.0**，源文件另保留继承的版权说明；不能用 VMem 顶层 MIT 许可覆盖这些文件的许可。[官方 LICENSE](https://github.com/CUT3R/CUT3R/blob/main/LICENSE)。本机检查时磁盘可用 1,438,864,580,608 字节，足够保存分段、完整模型和运行结果。没有访问账号凭据，也没有申请 gated 权重访问。

## 预先确定的验证顺序

1. 固定官方代码提交，保留许可证，确认源文件没有修改。
2. 导入 `ARCroco3DStereo`；验证可执行的纯 PyTorch RoPE fallback。
3. 用固定随机输入检查 CPU 输出有限、零位置是恒等变换、旋转保持向量范数；如 MPS 可用，再用相同输入比较，预设 `atol=1e-5, rtol=1e-4`。这一步只是环境/部件测试。
4. 用官方示例或 TUM 的前两张 RGB 图像，224 输入、FP32、CPU、无梯度，加载官方预训练参数；保存所有必要输出的数值与输入哈希。
5. 相同代码、权重、图像顺序再跑 MPS。有限值检查与 CPU 差异分别报告；数值对比预设 `atol=1e-3, rtol=1e-3`，不看到结果后悄悄改阈值。

22:41:37 已在看到任何 CUT3R 输出前固定实际输入：S2 原有 `qa_indices` 的前两项 `[0, 34]`，对应 TUM RGB 时间戳 `1305031102.175304` 与 `1305031103.475274`，间隔约 1.30 秒。数据和原 S2 选择清单的 SHA-256 保存在 `data/cut3r/inference_inputs.json`。选择依据是事先固定的时间抽样，不是预测误差或展示效果。

独立 CUT3R 成功输出真实图像几何后，仍需另外测试 VMem fork 的清理、对齐与写入接口。只有有限值不能证明几何准确；同一输入的 CPU/MPS 相近也不能替代数据集精度评测。任何适配修改应保留独立 patch，不能混入“原版未改动”的运行。

## 已实际通过的环境检查

22:55:40 完成第一次检查：`ARCroco3DStereo` 导入成功，实际 RoPE 实现来自固定官方 `src/croco/models/pos_embed.py` 的纯 PyTorch fallback。CPU 随机 FP32 张量输出全部有限，零位置恒等严格通过，向量范数在预设容差内保持；同一张量的 MPS 输出全部有限，最大绝对差 **4.76837158203125e-7**，满足事前 `atol=1e-5, rtol=1e-4`。这里处理的图像数为 0，未实例化模型，未加载检查点。

22:56:02 完成依赖一致性检查（`pip check` 无冲突）及运行配置 JSON 往返检查。官方模型基类保留的 `model.config` 是 backbone 配置，head 类型从实际 `model.head_type` 读取；LayerNorm partial 按稳定类名序列化，整数标签键统一转字符串并拒绝碰撞，避免 CPU 落盘再读取后导致 MPS 比较误报。CPU 与 MPS 必须使用相同 runner 哈希、依赖、模型配置、图像顺序和完整检查点哈希；数组先核对形状和数据类型，再检查数值。所有输出有限与数值一致性是两个分开的结果。

可打包的小文件已复制到 `results/CUT3R_readiness/`：环境验证、部件检查、固定源码来源、完整依赖版本、静态配置检查与预先选定输入。完整原始记录也保留在官方 clone 的 `local_readiness/`。

## 实际推理中发现并修复的兼容问题

**首次原样执行失败，保留负结果。** 23:07:04，CPU 已加载全部 **748,443,655** 个参数并报告全部键匹配，但前向在纯 PyTorch RoPE 的负索引处失败。官方 pose token 使用位置 `(-1,-1)`；CUDA 源码直接计算有符号角度，fallback 却把位置当作非负 embedding 索引。早先环境检查只覆盖非负位置，因此没有发现这个问题。失败元数据保存在 `results/CUT3R_cpu_2frames/`。

**有符号 RoPE 适配。** `scripts/cut3r_rope_compat.py` 使用绝对位置缓存余弦/正弦，并按位置符号改变正弦符号；缓存长度取绝对位置最大值加一。它保留官方旋转公式，明确限定本检查点的 `F0=1`，不是新模型或科研创新。23:10:13 的独立数学检查覆盖正负混合、零、绝对值大于正位置的负位置及全负输入；非负 CPU/MPS 输出均与原 fallback 严格相同。与官方 CUDA 源码公式的独立 NumPy 计算对照，CPU 最大差 `8.748791729407124e-7`；MPS 对 CPU 最大差 `4.76837158203125e-7`。这不是 CUDA 硬件实测。检查与固定 adapter 快照位于 `results/CUT3R_signed_rope_compat/`；adapter SHA-256 为 `6939dcead1b87e920eafce9aae47c1cc9a46b7a651ef816b3f521c779582152e`。

**MPS 输入搬运适配。** 使用有符号 RoPE 后，CPU 在 23:10:42 成功，但首次 MPS 在 23:10:51 因 ray mask 值发生改变而进入错误分支。当前栈的最小搬运测试中，异步替换来源的方式在 50/50 轮出现值改变（302 个字段），blocking 搬运在 50 轮中无改变。来源张量生命周期是可能的机制解释，尚未单独隔离证明。修复是在调用官方 inference 前先同步搬运每个输入字段，并逐字段核对数值（包括 NaN）没有改变，随后官方同设备转换不再跨设备复制。测试为合成搬运检查，位于 `results/CUT3R_mps_transfer_compat/check.json`，不能当作模型效果证据。

官方已跟踪源文件没有修改；运行时启用了明确记录的 adapter 和输入搬运处理。元数据分别记录 `upstream_source_files_unmodified=true` 和 `upstream_execution_unmodified=false`，以及 `runtime_compatibility`、adapter/校验文件哈希和所有真实输入的搬运检查。旧失败、旧成功结果全部保留。

## 两张真实图像的最终结果

| 项目 | CPU FP32 | MPS FP32 |
|---|---:|---:|
| 完成时点（北京时间） | 23:13:07.435913 | 23:13:20.984635 |
| 两张输入尺寸 | 224×224 | 224×224 |
| 模型加载时间 | 3.1774 秒 | 3.6432 秒 |
| 单次前向时间 | 0.8776 秒 | 6.2838 秒 |
| 进程峰值 RSS | 6.384 GB | 6.386 GB |
| 输出数组全部有限/必要字段齐全 | 通过 | 通过 |
| 对 CPU 的事前 `atol=rtol=1e-3` | 参考 | 14/14 数组通过 |

这些是本机一次未预热的两帧运行时间，不能据此推断长期吞吐、其他设备速度或 MPS 一般性能。RSS 是进程统计，不等于 GPU 专用显存峰值。

最终目录为 `results/CUT3R_cpu_2frames_signedrope_sync/` 与 `results/CUT3R_mps_2frames_signedrope_sync/`，各包含 `predictions.npz`、`run_metadata.json`、`checkpoint_load.txt` 及实际 runner 源码快照。MPS 另有逐数组 `cpu_comparison.json`。CPU 新结果与未加预搬运的已有成功 CPU 结果逐数组严格相同。

- 共同 runner SHA-256：`efb3c8b72ada668818d4211e6d5bb4aa357a3404778cf29d849f8551160bf923`。
- CPU NPZ SHA-256：`58b79301ee1b5019441000c0580894f968a167e46e55bda6146924384d2290f9`。
- MPS NPZ SHA-256：`a7388eff842069194fe4552bb114e401b7e88ae3423fa1eefbdc86f6820533aa`。
- MPS 对 CPU 的点坐标最大绝对差约 `2.69413e-4`，置信度约 `6.50883e-4`，位姿输出约 `7.98702e-6`；点坐标差使用模型坐标单位，不能直接解释为米。

这里只验证预训练模型能够实际处理这两张固定照片并输出数值一致的几何。没有在这里评估几何精度、多场景表现、长期记忆或生成视频。独立 S4 深度/位姿诊断由另一个预先冻结的协议负责，不能用本文件的 finite check 替代。

## 交付与资源记录

22:35 的失败记录：初次完整克隆因 GitHub HTTP/2 中断而退出（curl 92、early EOF、index-pack failed），未得到可用源码。随后采用 HTTP/1.1、blob 过滤和稀疏 checkout，只获取推理所需源码与根目录说明；不把下载失败写成模型兼容性失败。权重下载从 4 路恢复为 16 路，保留已有分段。

系统默认 `/usr/local/bin/git` 是 2.15.0，不支持本轮使用的 blob 过滤选项；该次尝试直接报参数错误。机器已有 `/usr/bin/git` 2.50.1，后续使用此路径，没有更改用户的全局 Git 安装或设置。

22:50 的准备检查：对已经下载的首段只做 pickle 操作码静态解析，没有反序列化或加载权重，发现检查点配置使用 OmegaConf。因此在隔离环境加入 `omegaconf==2.3.0`。PyTorch 2.7 延续了 2.6 起的 `weights_only=True` 默认值；实际运行保留该模式，并只在加载作用域内允许静态检查过的配置类型，不修改官方源码。完整文件到齐后仍会重新静态核验类型。检查记录在 `data/cut3r/checkpoint_pickle_static_preview.json`；此记录不能当成模型加载成功。[PyTorch 2.7 官方序列化说明](https://docs.pytorch.org/docs/2.7/notes/serialization.html#torch-load-with-weights-only-true)。

22:50 起下载改为 32 路，复用完整分段并从部分分段已保存的偏移继续；每次恢复的起始时点与并发数均保存在 `data/cut3r/download_attempts.jsonl`。一次性 CPU→MPS 运行流水线等待完整下载验证和实际环境检查通过，尚未运行的阶段不会生成成功记录。

所有 `.venv*`、数据原包、模型权重及下载分段不进入课程复现压缩包。交付保留下载脚本、官方来源、许可、最终哈希、依赖版本、运行脚本及小规模结果。下载重试和并发变化记录在本地日志，实际开始与完成时间以各 JSON 元数据为准；程序运行时间不充当用户课程工时。
