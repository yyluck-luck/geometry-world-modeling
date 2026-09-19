# S62：一份已成功 B0 档案的真实缓存接线

本协议在本次载荷读取和执行前固定。作者只实现与编译检查源码、读取档案描述符；实际数值载荷和 renderer 执行由 root 在不同作者源码审查后进行。原 C2 仍为失败记录，S62 不生成新图像或改变该记录。

**问题。** 在同一个成功 B0 第二动作 `turn_right` 的 567 个 surfel、五帧历史上，原 `get_context_info` 能否重现保存的选择与实际上下文？仅把 renderer 入口换成已审 S61 单位组件后，选择结果能否正确索引同一份真实缓存？这是一份已保存输入的工程回归，不是未见场景、全管线尺度不变或新方法验证。

**固定输入。** 只使用 `results/S40_declared_variant_generation/archive/events.jsonl` 的 seq56、58、60、62、64、66、68、70。程序内 `PINS` 固定原 pipeline/util/YAML、B0 manifest/archive、原运行配置实现及 S61 最终源码与作者票 SHA。每个实际读取的 tensor blob 按描述符的原 dtype、shape、little-endian/C 布局解码，并验证字节 SHA 与大小；唯一 blob 的实际读取记录立即追加到 `execution_01/readlist.jsonl`，复用同一路径时仍核描述符身份。

读取范围：seq56 target c2ws；seq58 surfel position/normal/radius/source_ids、surfel_to_timestep、五个 focal、原 renderer pose/focal/kwargs；seq60 原三张数值图；seq62 原权重/配额；seq64 initial_threshold；seq66 NMS 数值记录；seq68 五份真实 c2w、K、latent、embedding、focal 缓存与真实 context 输出。seq68/70 context_info 描述符须相同。只数五个 pil_frames 描述符，不读取或解码图像；不选择 surfel_depths 或 color。latent/embedding 是真实已存数组，未用人工标记替代。档案元数据的阅读不等于已读相应像素或数值 blob。

**原函数与配置。** AST 原样抽取 pipeline 的 `render_surfels_to_image`、`get_frame_distribution`、`process_retrieved_spatial_information`、`geodesic_distance`、`get_transformed_c2ws`、`get_context_info`，以及 util 的 `average_camera_pose`。不导入完整 pipeline、不实例化模型、不调用 get_cond、编码器或采样。沿用 CPU、Torch 2.7.0、NumPy 1.26.4、8 线程、FP32 context、context_num_frames=4、translation_distance_weight=0.1、surfel 512×288、NMS=True、visualize=False。SciPy 平均 pose、原混合 c2w dtype、float32[1] focal、Python float64 阈值与原 y/z 列翻转均保留。五帧触发原函数自行重算 NMS 阈值；不灌入预存答案阈值。

**顺序和判据。** 仅有以下两条路径，原 renderer 各调用一次，原 retrieval 各调用一次。每条路径用原输入的深拷贝创建轻量对象，完整调用原 `get_context_info`；不改选帧逻辑，不额外添加 fallback。

1. `original`：原函数构造的 renderer pose/focal 须与 seq58 逐值、dtype 和 shape 相同，kwargs 相同。原 index 图须逐项精确相同；depth/cos 固定 `atol=1e-6, rtol=1e-6`，报告最大绝对差。原权重固定 `atol=1e-6, rtol=0`，配额精确；最终 ID 顺序必须 `[0,2,4,1]`。五类 context 输出（四种条件及 ID）对 seq68 按 dtype、shape、逐值精确比较。任一步失败立即停止，不启动第二路径。
2. `canonical_units`：同一原函数先构造相同 renderer 输入，只在 renderer 边界调用固定 S61 `render_in_canonical_units`。S61 共同复制换算 position、radius、camera translation；depth 明确以正相机深度中位数为单位。完整报告原/新权重、配额、最终 ID 及顺序、单位票。这里不要求与原权重、图或 ID 相同。ID 必须为 int64、共四项且均在 0–4；四类 context 每个 slot 必须精确等于该 ID 对应的真实缓存经原 FP32 转换后的值。两条路径的初始 NMS 阈值仍须精确重现 seq64。

两条路径都逐字节指纹核输入/缓存在运行前后相同，包含 target、全部 geometry、ID 映射、原/运行 focal 与五份 c2w/K/latent/embedding。原 `initial_threshold` 是本次计算的状态，允许原函数更新；它不是缓存载荷。`pil_frames=[None]*5` 只提供原函数所需的历史长度，未替代任何条件值。

**执行与留存。** root 使用现有环境运行以下命令，并在外部设置 120 秒总时限；程序不自行重试。

```sh
.venv-cut3r/bin/python -B work/S62_b0_context_integration/replay_context.py
```

`execution_01` 必须不存在，程序用 create-only 方式建立。每条路径即时保存 `*_maps.npz` 和 `*_context.npz`，结束或 Python 异常时保存 `receipt.json`：实际 UTC/耗时、运行依赖、源身份、各条路径状态/调用次数、全部权重/配额/ID、精确缓存对应、前后指纹、readlist 计数和产物 SHA。失败保留已完成路径与部分数值产物。完成文件设为 0444。若外部超时/硬终止使 finally 无法运行，root 的外部终态与已落盘 readlist/部分文件描述该失败，缺少 receipt 不算通过。

本次结果止于 `get_context_info` 返回：不能核实编码器输出质量、get_cond 的 CLIP/射线条件、去噪或画质，也不证明权重变化必然改变最终选择。适配器改变检索的深度单位，是普通工程基线；后续生产接入及生成须另用明确变体，原源码与旧尝试保持不变。
