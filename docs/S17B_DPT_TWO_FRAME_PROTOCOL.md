# S17B：固定512 DPT检查点的两图真实前向协议

这是事前协议与待执行组件验证，不是已经完成的模型结果。阶段目的：确认 VMem 指定的公开 CUT3R 512 DPT 权重能否在本机产生完整两帧输出，消除把既有224 linear误作512基线的缺项。它不运行VMem生成器、几何全局对齐或视频消费者，不作深度准确率、创新或未见场景声明。

## 固定身份与允许读取范围

- 独立官方 CUT3R checkout：`/Users/rocket/Documents/Codex/2026-09-05/users-rocket-desktop-hkust-it-ip/work/cut3r-local`，commit `8bc15dc92a6d7fd92920b4ec81540d3dec7d3ecf`；同S15A的99份Python源码必须逐一入新manifest，运行前后核SHA，不修改官方源码。
- 新runner：`scripts/run_s17b_dpt_history.py`。旧 `run_s15_history.py` 和硬编码224的 `run_cut3r_local.py` 不改。
- 权重必须完整 **3,173,761,006字节**，SHA-256 **45f7e98a0a64dbeb54901ae2b878cd8cd125f20a4497316483f0bd6f109f8103**。来源为作者 `liguang0115/cut3r`，固定revision `b14faf986da0df405cff1b41e60e2975c4da2745`。根任务须在获取成功、完整SHA与压缩归档检查后冻结新manifest；不把部分文件或HTTP成功当完整权重。
- 只允许S15A原有Bonn RGB索引 **0、1**，顺序不可改：`1548340550.99864.png` 的SHA `7caa6f1b9fd1ac5b6938812682c55e3d7926a1348c7554c23e1012b47759cc39`；`1548340551.40132.png` 的SHA `77bebdb3ac737221ef05a4404a1124676bcff536dbffdbb6e197b59bcdf811ae`。原生640×480、RGB。它们在S15A已经实际看过，不是新照片或盲测。
- 身份集合严格限于上述99上游源码、两张RGB、新权重、新runner、原已核 `scripts/cut3r_rope_compat.py` 及其固定 `results/CUT3R_signed_rope_compat/check.json`、根任务明确列出的 `.md/.json/.py` 控制文件。控制项包括本协议、原则/勘误、外监控及新下载成功回执；不得加入其他RGB、原始轨迹、GT深度、旧预测NPZ或原20张图的文件身份。

## 预处理、模型和调用预算

直接使用官方 `load_images(paths,size=512)`，不重写图像插值/裁切：原640×480应到宽512、高384；每张输入为 `[1,3,384,512]`，`true_shape=[[384,512]]`。不沿用224的299×224裁切。运行前PIL只允许按固定顺序打开这两条路径，检查原生形状和模式，再完成解码；多开或错序立即失败。

预期模型是 `head_type='dpt'`、`output_mode='pts3d+pose'`、模型patch图片配置 `[512,512]`、实际下游类 `DPTPts3dPose`。训练配置写ManyAR_PatchEmbed；官方 `load_model` 会将它替换成 **PatchEmbedDust3R** 并强制 `landscape_only=False`，所以运行时image/ray patch类按后者核验。检查encoder为24层；动态记录实际参数量，不预填224参数数目。

CPU、FP32、8线程、seed0，单次 `inference` 调用，恰好两帧历史，0次目标射线查询，不训练。每帧 `img_mask=True,ray_mask=False,update=True,reset=False`；传递单位占位相机和被mask禁用的NaN ray_map，它们不是GT相机输入。沿用已经审过的有符号RoPE适配，不另换本轮VMem CPU试验版适配；该适配进入512真实路径是否成立由本阶段输出核验回答。

实际前向hook记录：image patch一次、真实image batch两帧；首尾image encoder block各一次，张量 `[2,768,1024]`。官方无有效ray时仍会对 `[1,6,384,512]` **全零dummy**执行一次ray encoder，再将其贡献乘0，因此预期ray patch hook一次、dummy batch一帧，**有效输入射线帧为0、query为0**。不能把dummy hook记为真实射线观测。应记录原始hook形状、dtype、dummy全零检查，而不只记录预填预算。

## 输出、失败与资源门

新输出目录不允许已存在；全部输出及失败都保留。输出共 **19个数组**：

| 文件 | 数组与固定形状 |
|---|---|
| `predictions.npz` | `frame0_*`、`frame1_*`，各六头。`pts3d_in_self_view/pts3d_in_other_view/rgb`: `[1,384,512,3]`；`conf_self/conf`: `[1,384,512]`；`camera_pose`: `[1,7]`；共12数组、FP32。模型rgb头不能称实拍照片。 |
| `state.npz` | `state_feat/init_state_feat`: `[1,768,768]` FP32；`state_pos`: `[1,768,2]` int64；`mem/init_mem`: `[1,256,1536]` FP32；共5数组。 |
| `history_poses.npz` | `history_pose_encodings`: `[2,7]`、`history_poses`: `[2,4,4]`，FP32；共2数组。 |

先保存真实返回的六头与最终状态，再作有限值/形状等语义门；失败时已有原始输出不删除。成功要求两帧、六头齐全且有限、固定state结构、pose底行为 `[0,0,0,1]`、旋转正交和行列式为1（`atol=1e-4,rtol=0`）。相机矩阵由官方 `pose_encoding_to_camera` 生成，独立核验者另用SciPy变换四元数，不能把代码相同的重复调用叫独立核验。

`run_metadata.json` 记录输入读取、前后SHA、checkpoint加载诊断、实际架构、hook观测、输出身份、实际UTC时间、耗时、RSS与失败traceback。另存冻结manifest、runner源副本、checkpoint加载文本和所有加载的上游Python模块身份。success只在完整验证之后写入；失败保留新目录和`FAILED`状态，不更换输入凑成功。

外部监控必须 **600秒墙钟 / 32GiB RSS**，使用项目既有caller工具的新输出目录；运行内也检查相同最终资源门。这个门是保护预算，不是已知512峰值。已有224两图CPU峰值为6,384,320,512字节，直接来源是 [S4两图实际回执](../results/CUT3R_cpu_2frames_signedrope_sync/run_metadata.json) 的 `peak_process_rss_bytes`，运行开始于2026-09-05 UTC15:13:00.219227。它只是参考，512 token/激活不同；此处没有拿S15A20帧峰值冒充两图。外caller需记录pid、实际读数、退出码和身份，超界应终止并保存失败，不静默改帧数、分辨率或精度。

## manifest和接口

```text
.venv-cut3r/bin/python scripts/run_s17b_dpt_history.py \
  --manifest ABS_FROZEN_MANIFEST.json --output ABS_FRESH_RESULT_DIRECTORY
```

这只是内部worker命令；正式真实执行必须由上述外caller包裹，不能直接靠worker末尾自检代替外监控。

Manifest顶层：`schema='s17b-dpt-two-frame-manifest-v1'`；`repo,commit,python,runner,checkpoint,rope_check,history_images,control_files,identities,contract`，沿S15A明确绝对路径和SHA语义。`history_images`只含index0/1。contract精确键值由runner的`EXPECTED_CONTRACT`给出，包括 `history_count=2,query_count=0,size=[384,512],loader_size=512,raw_image_size=[640,480],head_type='dpt',patch_image_size=[512,512],device='cpu',cpu_threads=8,seed=0,dtype='float32',wall_seconds=600,monitored_rss_bytes=34359738368,external_monitor_required=True` 及上述flags和GT/RGB范围。

预处理metadata字段：`processed_input_shapes`、`processed_true_shapes`、`history_flags`。架构字段 `architecture` 含 `head_type,output_mode,image_patch_class,ray_patch_class,patch_image_size,downstream_head_class,encoder_blocks,parameters`。`encoder_observations` 按真实发生顺序保存 `image_patch,image_encoder_first_block,image_encoder_last_block,dummy_ray_patch`，含input_shape/dtype，patch含output_token_shape，dummy含all_zero。`counters.supplied_ray_frames`由实际view flags求和。

## 人工前审与独立检查

本轮代码作者已用人工张量检查manifest错序、额外身份、错checkpoint、224误配置、宽高互换、非有限输入、dtype和输出保存失败边界；实际结果见 `work/S17B_preparation/artificial_checks.json`。人工假inference产生19数组只证明接口，不是512模型真实输出。

另一agent审代码并准备 `scripts/verify_s17b_dpt_history.py`，正式执行先等root下载核验/冻结/独立前审通过。真实输出成功后再封存，并由不同实现检查19数组、SciPy位姿、输入输出身份和实际hook计数。即使整个S17B成功，也仅完成独立512几何组件的本机运行，仍须另验VMem嵌入分支、生成器权重、VAE、CLIP、生成与记忆回路，完整视频状态不能提前更改。
