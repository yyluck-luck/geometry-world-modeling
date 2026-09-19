# S103 selector-free VMem baseline: PRE_RUN_READY manifest template

记录时间：2026-09-16 01:46:13（Asia/Shanghai，依据当前 UTC 时钟）

这个文件是**可填写的预运行清单模板**，当前状态是 `TEMPLATE_ONLY_BLOCKED`。它不提交 GPU 作业，也不表示 Gate0 已通过。它把已经实际核验的 VMem 运行参数、远程 checkpoint 名称和实验输入边界固定下来，避免在 Gate0 通过后临时改变配置。

## 已经固定的 VMem 参数

- 576×576 输出分辨率，latent 空间缩放 8。
- 4 张 context/history 帧 + 4 张 target 帧，共 8 帧。
- 50 个采样步，随机种子 42，CUDA 上 FP16。
- `cfg=2.0`、`cfg_min=1.2`、`camera_scale=2.0`；启用 surfel/NMS，保留原始推理配置。
- 远程实际文件名：`vmem_weights.pth`、`cut3r_512_dpt_4_64.pth`、`open_clip_model.safetensors`、`diffusion_pytorch_model.safetensors`。旧的 `vmem.ckpt` / `cut3r.pth` 别名禁止再写入正式清单。

## 输入边界

预测器只能看到 staged 目录中的 `history_rgb`、`history_depth`、`history_pose`，以及预先冻结的 `command_camera`。`command_camera` 是在预测前给定的目标相机命令（位姿/内参），不是未来真实 RGB、深度或位姿结果。

未来 `future_rgb`、`future_depth`、`future_pose` 和 `future_gt` 只属于 scorer。预测器不能打开这些路径，也不能打开整个数据压缩包。必须使用实际的容器挂载白名单、Linux namespace 或独立用户 ACL；字符串/子串路径检查不能作为隔离证明。隔离回执需要同时记录允许 history、拒绝 outcome 和不可见完整 archive 三个探针。

## 何时可以升级为 PRE_RUN_READY

只有在所有 `{{...}}` 占位符都替换为真实路径、时间窗、数据合同、SHA-256 和独立审查回执，并生成新的 Gate0 合约修订后，才运行 `validate_gate0_v2.py --stage pre-run`。本模板保持不变，不能直接作为正式合约。

即使获得 `PRE_RUN_READY`，它只允许执行声明的 selector-free development baseline；它不允许 GRC/SOCF 方法评分，也不构成创新或科学效果验证。正式方法比较需等待预测封存、未来结果后置读取和独立指标复算。
