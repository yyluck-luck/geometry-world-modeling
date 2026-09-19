# GPU-compatible isolation investigation (Gate0 support only)

记录：2026-09-16（Asia/Shanghai）。目标是解释并修复 predictor 在 `unshare` 用户/挂载/PID/网络 namespace 下触发 CUDA error 304 的边界问题。此前 588625 的失败回执保持不变；本次不重跑模型、权重或数据。

## 实测能力

通过远端 tmux `gwm-cap-probe` 提交仅探测作业 588626（dgx-09，申请 1 GPU，但没有构造模型、读取数据或执行 forward）。Slurm 状态 `COMPLETED`, exit `0:0`。完整 stdout 和提交文件见 `container_probe_receipt/`。

- `/cm/local/apps/apptainer/current/bin/apptainer`, version **1.1.9**。
- Apptainer 的 `exec` 支持 `--nv`、`--bind`、`--no-home`、`--contain`/`--containall`；这可以把预测器放到 NVIDIA 设备可见、但 home 和未来数据目录不可见的容器中。
- Slurm Pyxis 选项已在计算节点的 `srun --help` 中出现：`--container-image`、`--container-mounts`、`--container-workdir`、`--container-readonly`、`--no-container-mount-home`、`--container-remap-root`。
- `/usr/bin/enroot` 在计算节点可见，但登录节点的 Enroot 配置指向无权限的 `/raid/local`，且当前没有可复用的本地镜像。不能把 Enroot 可执行文件存在误报成已经有可用镜像。
- 无 GPU 的能力探测被 SuperPOD `QOSMinGRES` 拒绝；因此成功能力探测仅为到达计算节点所申请的 GPU，不是科学实验。

## 推荐的 Gate0 实施边界

优先使用 **Slurm Pyxis** 的不可写容器，而不是 `unshare`。正式 predictor 的候选启动参数应在新的独立预运行审查中冻结：

```text
srun --account=mscitspod2026 --partition=normal --gpus=1 \
  --container-image=<validated_digest_pinned_image> \
  --no-container-mount-home \
  --container-readonly \
  --container-mounts=<staged_history>:<container_history>:ro,<command_camera>:<container_command>:ro,<run_output>:<container_output>:rw \
  --container-workdir=<container_workdir> \
  <predictor_command>
```

容器镜像必须先有独立的 bytes/SHA 或 digest、CUDA/PyTorch 兼容性和只读挂载实测回执；本报告没有下载或认证镜像。`<staged_history>` 只包含冻结的 history RGB-D/pose，`<command_camera>` 只包含预先声明的相机命令，未来 RGB/depth/pose/GT 目录不得挂载。scorer 应在另一个后置阶段独立开放 future outcome，预测输出封存后才能读答案。

`--container-remap-root` 会提升容器内权限，默认不建议使用；若集群要求，必须在独立安全审查中记录其影响，不能把它当作未来答案隔离本身。

## 结论与边界

这次把 588625 的 CUDA-304 namespace 失败与可用的 Pyxis/Apptainer 方案区分开：**发现了可行的 GPU-compatible enforcement path，但尚未证明隔离在正式 predictor 中工作。** 在新镜像和 staged mounts 经过小范围、无未来答案的容器 smoke 后，才能把 `isolation` 写为 Gate0 证据。当前 Gate0 仍 BLOCKED，未授权 VMem/GRC 运行。
