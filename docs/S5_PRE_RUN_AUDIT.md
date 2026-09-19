# S5 序列诊断独立预审

审查于 2026-09-05 15:18:05 UTC 开始；本终稿在 15:22:27 UTC（23:22:27 Asia/Shanghai）记录。输入、状态路径与精度问题在读取 S5 输出之前核查并通知主任务；终稿写入时主任务已通报 S5 评分完成，因此不把文档落盘时间倒写为运行前。另行独立重算实际结果，不以本预审代替数值验证。

对象：`docs/S5_SEQUENCE_PROTOCOL.md`、`data/cut3r/S5_inputs.json`、`scripts/run_cut3r_sequence.py`、`scripts/run_cut3r_local.py`、`scripts/evaluate_cut3r_sequence.py` 及其 S4 共享指标/身份检查。未修改这些文件或模型，没有启动序列推理。

## 结论与已处理问题

未发现实测深度或参考位姿进入模型推理，未发现后续帧参与首帧尺度拟合。固定三块选择和数值索引自洽。预审提出两项修正：

1. **精度措辞。** 官方 CroCo encoder 的 `src/croco/models/blocks.py:124–131` 在 RoPE 前把 q/k 转为 FP16，再转回原 dtype；`models/croco.py` 使用该 Block 构造 `enc_blocks`。另一方面，`dust3r/blocks.py` 的 decoder 在 RoPE 前显式转 float32。因此参数、外部输入、保存输出为 FP32，不表示所有中间算子为 FP32。已增加 `S5_PRECISION_CLARIFICATION.md`，原协议哈希不变；不是为速度新增降精度，也未据此重算模型。
2. **整个序列的完成状态。** 初版评分器只接收三块的 raw 成功标志，可能忽略外层因资源超限标记的失败。主任务已补 `sequence_metadata.json` 的 complete/ok、三块成功与退出码、冻结输入 SHA、controller 快照 SHA、块与总运行身份及实际峰值≤16 GiB 校验，并将 controller 证据纳入评测源码归档。本次末次读取已确认这些检查存在。

据已复核版本，没有阻断既定评分的其他问题。本结论不保证新机器可直接运行，也不等于模型预测准确。

## 固定数据与计数

协议 SHA256：`568dcea3788bb1e4ef9e35da6c147519d49ec509a8279ff4337e81aee43b1d8b`；S5 输入 SHA256：`7ffa1467f5640bee2013a1ed1d30313be14da339ab28f7c364cfc2790f16f126`。清单记录冻结于 15:17:44.121922 UTC。独立核对了源 S3 selection manifest 哈希、全部选择索引、RGB/depth 路径与时间、144 个实际图像文件 SHA，全部匹配。

三块各 24 帧，标签为 0…23，合计 72 个唯一 match、72 张唯一 RGB 与 72 张唯一 depth。各块 RGB 严格递增；跨度分别为 8.836127、8.835887、8.835962 s。RGB 采样间隔约 0.360–0.468 s，故应称按时间抽样的序列，不能暗示保留了原视频每一帧。RGB 时刻参考位姿插值最大间隔 10.300 ms，均满足 0.1 s 限制；最大 RGB/depth 偏移分别为 16.913、11.782、8.338 ms，仍需保留时间错位限制。

计数关系为 72 帧 = 3 校准帧 + 69 非校准帧；主测试 8 帧为 B1/B2 的 20…23，已包含在 69 内，不能写成 77 个非校准样本。B0 后 4 帧单列，三个块都是同一环境。每帧 MAE、中位差和 p90 先各自计算，再逐帧等权平均；平均逐帧 p90 不是将所有像素合并后的 p90。协议没有显著性检验或独立场景泛化声明。

## 状态与尺度边界

序列 controller 每块启动一个新的 Python 子进程，只给固定顺序的 24 张 RGB 路径。深度仅在 controller 做文件完整性核对，不在模型命令参数中。通用 runner 构造的真实输入是 RGB、模式掩码与占位张量：`img_mask=True`、`ray_mask=False`、`update=True`、`reset=False`，没有真实 camera pose 或 depth。每块 168 个需搬运字段均由共享 loader 守卫验证。

官方 `_encode_views` 把图像堆入 batch 作逐图编码；encoder attention 保持 batch 维独立，使用 LayerNorm，未见跨图 BatchNorm 或跨视图注意力。`_forward_impl` 从初始 state/memory 开始，按 i 递增调用 decoder，保存当前预测后用该帧更新状态。reset 分支在更新后执行，故全部 False 对应保留时序状态。批量准备未来 RGB 的特征不等于让当前 decoder 读到未来特征；本结论来自源码路径，不是另做的未来帧扰动实验。

评分帧 20…23 的 RGB 本身会正常参与估计，后一个评分帧可使用前一个评分帧的 RGB 状态。这是测量未进入拟合的因果 RGB 估计，不是排除了所有查询图像的检索记忆或视频外推。不能把这份最终状态直接称为只含前 20 历史图像的地图。

评分器按 `range(24)` 数值索引读取 `frame{i}_...`，没有按字符串排序导致 frame10 错位。每块仅 frame0 调一次 `first_frame_scale`，使用至少 100 个有效测量/正预测比值的中位数；三次独立尺度用于各自后 23 帧。第二帧以后没有逐帧拟合、偏置、ICP 或轨迹对齐。RGB 时刻 `inv(P0)@Pt` 与 `inv(G0)@Gt` 比较，预测相对平移乘对应首帧尺度。点图与位姿分别预测，共用尺度只是预定诊断假设。

固定 measured target 仍沿用经审查的 299×224 缩放及 `[37,0,261,224]` 裁剪、NEAREST depth/mask、原图 5×5/50 mm 有效性条件。全部剩余大残差保留，不按置信度挑选。身份检查要求所有块同模型、权重、runner、适配器、seed 与线程配置，最终必须包含全部三块与 72 帧，不能缺帧后静默计算更小的主平均。

## 资源与精度补充证据

controller 实际每 0.5 s 采样子进程 RSS，超过 16 GiB 或 900 s 时终止并保留记录；每块成功后也检查进程报告的最终峰值，捕捉采样之间发生的超预算峰值并停止后续块。这是采样式软预算，不保证从未瞬间超过阈值。默认顺序执行三块，不同时加载三个模型。

为覆盖官方 encoder 的内部类型，本审查另做了不加载模型的 FP16 非负 RoPE 对照，实际时间 15:21:49.575852–15:21:50.307432 UTC。先保存原 fallback 的 CPU/MPS 输出，再安装同一已审计 adapter；固定 seed0、base100、F0=1、输入 `[2,4,17,64]`、位置 0…13。两设备各自与原 fallback 逐值相同、最大差 0，保持 FP16、有限性、零位置恒等及输入不变。本组 CPU/MPS 输出间最大差也是 0。没有 CUDA 硬件对照，也没有处理图像或读取权重。

该补充初始保存于工作区 `work/s5_fp16_audit/check_fp16_nonnegative.py` 与 `fp16_nonnegative_check.json`，由 CUT3R 实现任务负责复制到它维护的结果目录。脚本 SHA 为 `fcbb35543cf98387e299de1a4abc46bb318f0697b21f20e5989a53b16e1d1dcf`；adapter SHA 仍为 `6939dcead1b87e920eafce9aae47c1cc9a46b7a651ef816b3f521c779582152e`。原 adapter 与原检查结果未修改。

实际 S5 输出需另看 `S5_INDEPENDENT_AUDIT.md` 的独立复算；本文件不填写未经独立重算的模型效果。
