# S68：五份已见 TUM 历史照片的真实外观缓存

这是执行前的模型组件桥接，非视频实验、选图算法或方法收益。目标是在本机把固定来源照片编码成原 VMem 可识别的逐来源 latent 和 CLIP embedding，补齐已有消费者数据的一部分。仍无相机位姿、完整几何/生成状态或消费者运行证据。

**结果前范围收缩。** 初始准备考虑历史 0–19；在任何真实 RGB/权重正文读取和编码前，root 根据旧 S12 已封存选择集把本轮正文白名单缩到其并集：按原历史 ID 升序 `[12,13,14,18,19]`。旧 geometry `[19,18,13,12]` 与 pose14 `[19,18,14,13]` 只说明未来条件性对照的来源用途；本程序不重算/执行选择或 gather。数据和旧目标早已见过，旧查询相机用过 query RGB，不能称为无目标照片在线检索、未见测试或完整 20 帧缓存。

## 固定输入与来源

`INPUTS.json` 绑定原 `results/S8_cut3r_cpu_v2/frozen_inputs.json` block0 的全部 20 份历史元数据、路径、RGB 时刻、旧 SHA 和当前文件大小；只允许上述五份 RGB 正文。预计压缩 PNG 文件读取合计 **2625997 B**，每份运行时从单个 FD 读取一次、核 SHA/大小，解码使用同一已核内存字节。禁止 query20–23 RGB、任何 depth、GT 位姿和旧 NPZ 科学正文。不会读目标 PNG 来探测尺寸。五份源的原 ID 与紧凑存储行 0–4 显式映射，绝不能把 ID19 当五行数组下标。

使用 S64 已验证的组件身份：`stabilityai/sd-vae-ft-mse` revision `31f26fdeee1355a5c34592e401dd41e45d25a493`，334643276 B；CLIP `ViT-H-14/laion2b_s32b_b79k`，3944517836 B。具体 SHA/配置/源码见 INPUTS。原 SD2.1 VAE 身份仍 UNKNOWN，ft-mse 是声明变体。作者阶段只核文件属性与既有 SHA 来源；真实运行才读取和哈希两份权重。

只提取固定原 `AutoEncoder`、`CLIPConditioner` 类及六个原工具定义；不导入 pipeline、VMem 视频模型或 CUT3R。沿 S35 的原构造器本地资产路由，原 VAE 的 local `from_pretrained` 使用复制的已核小配置；两个 safetensors loader 都改为消费刚从文件读取、已核 SHA 的内存字节，每份恰一次。VAE 本地权重路径仅为原 loader 解析用符号链接；实际 tensor load 不再次从链接读权重。保留原构造、state_dict 检查和数学；不启用 tiling/slicing、额外 L2 归一化或采样。CLIP 全原组件含其已知文字分支参数，但本步只调用图像分支，不加载 VMem 大模型。

## 固定计算

- 原 `load_img_and_K(..., size=None, K=None, device='cpu')` 读取 640×480 RGB，原 `transform_img_and_K(...,(576,576),mode='crop')` 以 area 插值覆盖再中心裁剪，范围为 [-1,1]。处理后的 RGB 数值实际进入两个编码器，但不导出/观看图像。
- VAE：原 `encode_vae_image`→原 wrapper `encode(...,1)`，posterior mean×0.18215，输出 FP32 `[4,72,72]`。CLIP：原 `encode_image`→Kornia bicubic 224、align_corners=True、antialias=True、原 mean/std，再原 `encode_image`，输出 FP32 `[1024]`；保持逐来源，不取跨来源均值。
- 原照片 K 固定为官方推荐 ROS 像素 K `[[525,0,319.5],[0,525,239.5],[0,0,1]]`，不去畸变。依据已存官方格式页。将该 K 以 `[1,3,3]` 交原 crop helper，同时调整为 `K_pixels_576`；另保存 `K_normalized_576`，只按原 `get_plucker_coordinates` 的归一化表达式把前两行除 576。两者清楚命名，后续只消费其中合适一种，不能二次归一化。此处不运行射线函数，未证明完整相机约定或实际 ray 接线；不复制旧 S14E 的 224 K，不生成伪 c2ws。

固定环境为 `.venv-cut3r`、Python3.12、Torch2.7.0、NumPy1.26.4，原 overlays 与其余包版本写在 INPUTS。CPU8、FP32、eval、关闭梯度，seed44 仅固定构造期随机初始化；使用均值 latent，无 posterior 随机采样。按五来源顺序逐张执行，每张恰一次 VAE/CLIP encode。内部 900 秒、外部观察器 960 秒、进程峰 RSS 20 GiB、至少 10 GiB 磁盘空闲；这些是停止上限，非完成保证。外部连续监测，内部在加载/帧边界检查；超限停止且保留部分产物，不自动重试。

## 运行与判读

仅在 root 与不同作者源审接受最终 SHA 后，由 root 执行一次：

```
.venv-cut3r/bin/python -B work/S68_tum_vmem_cache_bridge/encode_history.py
```

程序只能新建 `execution_01`。写五份 `history_ID.npz` 及逐来源 JSON（路径/时间/输入 SHA、storage_row、输出 shape/dtype/实际 body SHA、NPZ SHA），最后写 `receipt.json`。保存的四项为 latent、embedding、K_pixels_576、K_normalized_576；成功仅表示五份均存在、形状/精度/finite 与来源绑定合格。实际模型 load 回执、文件读清单、版本、时间、峰 RSS、完成分母 5 均保留；外部另封存 stdout/stderr/退出码及硬停止。异常时明确失败，已完成来源不删除；没有“部分成功当五份完成”的分支。worker 不串联后续选择/消费者/评分/查看。

作者自查仅编译和原定义 globals 接线检查，0 真实 RGB/权重正文、0 实例化/编码/模型。后续实际结果还需要不同作者核验来源与输出，不能以本协议或源码 PASS 代替编码成功。本步没有修改旧阶段、主账或当前入口。
